import importlib
import json
import threading
from functools import cached_property

import django_rq
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.postgres.fields import ArrayField
from django.core import serializers
from django.core.validators import MinValueValidator
from django.db import models
from django.urls import reverse
from django.utils import timezone
from netbox.models import PrimaryModel
from netbox.models.features import ChangeLoggingMixin, ExportTemplatesMixin, WebhooksMixin
from utilities.querysets import RestrictedQuerySet

from .choices import LogLevelChoices, ScriptExecutionStatusChoices
from .util import clear_module_cache

lock = threading.Lock()
plugin_config = settings.PLUGINS_CONFIG.get("netbox_script_manager")


class ScriptLogLine(models.Model):
    script_execution = models.ForeignKey(
        to="ScriptExecution",
        on_delete=models.CASCADE,
        related_name="script_log_lines",
    )
    level = models.CharField(max_length=50, choices=LogLevelChoices)
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    objects = RestrictedQuerySet.as_manager()

    class Meta:
        ordering = ("timestamp",)
        indexes = [
            models.Index(fields=["level"]),
            models.Index(fields=["timestamp"]),
        ]

    def __str__(self):
        return str(self.pk)

    def get_absolute_url(self):
        return reverse("plugins:netbox_script_manager:script_log_line", args=[self.pk])

    def get_level_color(self):
        return LogLevelChoices.colors.get(self.level)


class ScriptArtifact(models.Model):
    data = models.BinaryField()
    name = models.CharField(max_length=100, default="text/plain")
    content_type = models.CharField(max_length=100)
    script_execution = models.ForeignKey(
        to="ScriptExecution",
        on_delete=models.CASCADE,
        related_name="script_artifacts",
    )

    objects = RestrictedQuerySet.as_manager()

    class Meta:
        ordering = ("id",)

    def __str__(self):
        return str(self.pk)

    def get_absolute_url(self):
        return reverse("plugins:netbox_script_manager:scriptartifact_download", args=[self.pk])


class ScriptExecution(ExportTemplatesMixin, WebhooksMixin, ChangeLoggingMixin, models.Model):
    script_instance = models.ForeignKey(
        to="ScriptInstance",
        on_delete=models.CASCADE,
        related_name="script_executions",
    )
    user = models.ForeignKey(to=User, on_delete=models.SET_NULL, related_name="+", blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True)
    started = models.DateTimeField(
        null=True,
        blank=True,
    )
    completed = models.DateTimeField(
        null=True,
        blank=True,
    )
    status = models.CharField(
        max_length=30,
        choices=ScriptExecutionStatusChoices,
        default=ScriptExecutionStatusChoices.STATUS_PENDING,
    )
    scheduled = models.DateTimeField(
        null=True,
        blank=True,
    )
    task_queue = models.CharField(max_length=100, default="default")
    interval = models.PositiveIntegerField(
        blank=True,
        null=True,
        validators=(MinValueValidator(1),),
    )
    task_id = models.UUIDField(
        unique=True,
    )
    request_id = models.UUIDField(
        unique=True,
    )
    data = models.JSONField(
        null=True,
        blank=True,
        default=dict,
    )

    objects = RestrictedQuerySet.as_manager()

    class Meta:
        ordering = ("-created",)
        indexes = [
            models.Index(fields=["started"]),
            models.Index(fields=["completed"]),
        ]

    def start(self):
        if self.started is not None:
            return

        self.started = timezone.now()
        self.status = ScriptExecutionStatusChoices.STATUS_RUNNING
        self.save()

    def terminate(self, status=ScriptExecutionStatusChoices.STATUS_COMPLETED):
        valid_statuses = ScriptExecutionStatusChoices.TERMINAL_STATE_CHOICES

        if status not in valid_statuses:
            raise ValueError(f"Invalid status for job termination. Choices are: {', '.join(valid_statuses)}")

        self.status = status
        self.completed = timezone.now()
        self.save()

    def delete(self, *args, **kwargs):
        super().delete(*args, **kwargs)

        queue = django_rq.get_queue(self.task_queue)
        task = queue.fetch_job(str(self.task_id))

        if task:
            task.cancel()

    def serialize_object(obj, resolve_tags=True, extra=None):
        """
        While the netbox serialize_object claims to support excluding fields, it doesn't in reality.
        """
        json_str = serializers.serialize("json", [obj])
        data = json.loads(json_str)[0]["fields"]

        # Don't serialize the data field as it can be quite large
        data.pop("data")

        return data

    @property
    def duration(self):
        start_time = self.started

        if not start_time:
            return ""

        if self.completed:
            duration = self.completed - start_time
        else:
            duration = timezone.now() - start_time

        minutes, seconds = divmod(duration.total_seconds(), 60)

        return f"{int(minutes)} minutes, {seconds:.2f} seconds"

    @property
    def is_completed(self):
        return bool(self.completed)

    def __str__(self):
        return f"{self.script_instance.name} ({self.pk})"

    def get_absolute_url(self):
        return reverse("plugins:netbox_script_manager:scriptexecution", args=[self.pk])

    def get_status_color(self):
        return ScriptExecutionStatusChoices.colors.get(self.status)


class ScriptInstance(PrimaryModel):
    name = models.CharField(max_length=100, null=False, blank=False)
    module_path = models.CharField(max_length=1000, null=False, blank=False)
    class_name = models.CharField(max_length=1000, null=False, blank=False)
    group = models.CharField(max_length=100, null=True, blank=True)
    weight = models.PositiveSmallIntegerField(default=1000)
    task_queues = ArrayField(
        base_field=models.CharField(max_length=100, blank=True),
        blank=True,
        default=list,
        help_text="Comma separated list of available task queues for the script",
    )
    tenant = models.ForeignKey(
        to="tenancy.Tenant",
        on_delete=models.SET_NULL,
        related_name="+",
        blank=True,
        null=True,
    )

    @cached_property
    def script(self):
        with lock:
            clear_module_cache()

            module = importlib.import_module(self.module_path)
            script_class = getattr(module, self.class_name, None)

            return script_class()

    @property
    def last_execution(self):
        return self.script_executions.order_by("-created").first()

    class Meta:
        ordering = ("group", "weight", "name")
        indexes = [
            models.Index(fields=["name"]),
        ]
        constraints = (
            models.UniqueConstraint(fields=("module_path", "class_name"), name="%(app_label)s_%(class)s_unique_module_path_class_name"),
        )

    def __str__(self):
        return self.name

    @property
    def script_path(self):
        return f"{self.module_path}.{self.class_name}"

    def get_absolute_url(self):
        return reverse("plugins:netbox_script_manager:scriptinstance", args=[self.pk])
