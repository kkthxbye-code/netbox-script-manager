from django.template.defaultfilters import date as date_filter
from rest_framework import serializers

from netbox.api.serializers import NetBoxModelSerializer
from netbox.config import get_config
from utilities.templatetags.builtins.filters import render_markdown
from netbox_script_manager.models import ScriptInstance, ScriptExecution, ScriptLogLine, ScriptArtifact


class MarkdownField(serializers.Field):
    def to_representation(self, value):
        return render_markdown(value)


class FormattedDateTimeField(serializers.Field):
    """
    Output a django rendered date/time field using the user's preferred format
    """

    DATE_FORMAT = get_config().DATETIME_FORMAT

    def to_representation(self, value):
        return date_filter(value, self.DATE_FORMAT)


class ScriptInstanceSerializer(NetBoxModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name="plugins-api:netbox_script_manager-api:scriptinstance-detail")
    name = serializers.CharField(required=True)

    class Meta:
        model = ScriptInstance
        fields = (
            "id",
            "url",
            "name",
            "group",
            "weight",
            "display",
            "task_queues",
            "tags",
            "created",
            "last_updated",
        )


class ScriptExecutionSerializer(NetBoxModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name="plugins-api:netbox_script_manager-api:scriptexecution-detail")
    script_instance = ScriptInstanceSerializer(read_only=True)

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


class ScriptLogLineSerializer(NetBoxModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name="plugins-api:netbox_script_manager-api:scriptlogline-detail")
    script_execution = ScriptExecutionSerializer(read_only=True)
    message_markdown = MarkdownField(source="message", read_only=True)
    timestamp_formatted = FormattedDateTimeField(source="timestamp", read_only=True)

    class Meta:
        model = ScriptLogLine
        fields = (
            "id",
            "url",
            "display",
            "script_execution",
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
    script_execution = ScriptExecutionSerializer(read_only=True)

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

    def validate_schedule_at(self, value):
        if value and not self.context['script'].scheduling_enabled:
            raise serializers.ValidationError("Scheduling is not enabled for this script.")
        return value

    def validate_interval(self, value):
        if value and not self.context['script'].scheduling_enabled:
            raise serializers.ValidationError("Scheduling is not enabled for this script.")
        return value
