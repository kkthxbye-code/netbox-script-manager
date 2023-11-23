from django.template.defaultfilters import date as date_filter
from django.templatetags.tz import localtime
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema_field
from netbox.api.fields import ChoiceField
from netbox.api.serializers import NetBoxModelSerializer
from netbox.config import get_config
from rest_framework import serializers
from tenancy.api.nested_serializers import NestedTenantSerializer
from utilities.templatetags.builtins.filters import render_markdown

from netbox_script_manager.choices import ScriptExecutionStatusChoices
from netbox_script_manager.models import ScriptArtifact, ScriptExecution, ScriptInstance, ScriptLogLine


@extend_schema_field(OpenApiTypes.STR)
class MarkdownField(serializers.Field):
    def to_representation(self, value):
        return render_markdown(value)


@extend_schema_field(OpenApiTypes.STR)
class FormattedDateTimeField(serializers.Field):
    """
    Output a django rendered date/time field using the user's preferred format
    """

    DATE_FORMAT = get_config().DATETIME_FORMAT

    def to_representation(self, value):
        return date_filter(localtime(value), self.DATE_FORMAT)


class ScriptInstanceSerializer(NetBoxModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name="plugins-api:netbox_script_manager-api:scriptinstance-detail")
    name = serializers.CharField(required=True)
    tenant = NestedTenantSerializer(required=False, allow_null=True)

    class Meta:
        model = ScriptInstance
        fields = (
            "id",
            "url",
            "name",
            "group",
            "weight",
            "module_path",
            "class_name",
            "display",
            "task_queues",
            "tenant",
            "tags",
            "created",
            "last_updated",
        )


class NestedScriptInstanceSerializer(NetBoxModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name="plugins-api:netbox_script_manager-api:scriptinstance-detail")
    name = serializers.CharField(required=True)

    class Meta:
        model = ScriptInstance
        fields = (
            "id",
            "url",
            "name",
            "display",
        )


class ScriptExecutionSerializer(NetBoxModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name="plugins-api:netbox_script_manager-api:scriptexecution-detail")
    script_instance = NestedScriptInstanceSerializer(read_only=True)
    status = ChoiceField(choices=ScriptExecutionStatusChoices)

    class Meta:
        model = ScriptExecution
        fields = (
            "id",
            "url",
            "display",
            "created",
            "started",
            "completed",
            "scheduled",
            "interval",
            "status",
            "task_id",
            "script_instance",
        )


class NestedScriptExecutionSerializer(NetBoxModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name="plugins-api:netbox_script_manager-api:scriptexecution-detail")

    class Meta:
        model = ScriptExecution
        fields = (
            "id",
            "url",
            "display",
            "status",
        )


class ScriptLogLineSerializer(NetBoxModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name="plugins-api:netbox_script_manager-api:scriptlogline-detail")
    message_markdown = MarkdownField(source="message", read_only=True)
    timestamp_formatted = FormattedDateTimeField(source="timestamp", read_only=True)

    class Meta:
        model = ScriptLogLine
        fields = (
            "id",
            "url",
            "display",
            "level",
            "message",
            "message_markdown",
            "timestamp",
            "timestamp_formatted",
        )


class ScriptLogLineMinimalSerializer(NetBoxModelSerializer):
    message_markdown = MarkdownField(source="message", read_only=True)
    timestamp_formatted = FormattedDateTimeField(source="timestamp", read_only=True)

    class Meta:
        model = ScriptLogLine
        fields = (
            "id",
            "display",
            "level",
            "message",
            "message_markdown",
            "timestamp",
            "timestamp_formatted",
        )


class ScriptArtifactSerializer(NetBoxModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name="plugins-api:netbox_script_manager-api:scriptartifact-detail")
    script_execution = NestedScriptExecutionSerializer(read_only=True)

    class Meta:
        model = ScriptArtifact
        fields = (
            "id",
            "url",
            "display",
            "script_execution",
            "name",
            "content_type",
        )


class ScriptInputSerializer(serializers.Serializer):
    data = serializers.JSONField()
    commit = serializers.BooleanField()
    schedule_at = serializers.DateTimeField(required=False, allow_null=True)
    interval = serializers.IntegerField(required=False, allow_null=True)
    task_queue = serializers.CharField(required=False, allow_null=True)

    def validate_schedule_at(self, value):
        if value and not self.context["script"].scheduling_enabled:
            raise serializers.ValidationError("Scheduling is not enabled for this script.")
        return value

    def validate_interval(self, value):
        if value and not self.context["script"].scheduling_enabled:
            raise serializers.ValidationError("Scheduling is not enabled for this script.")
        return value
