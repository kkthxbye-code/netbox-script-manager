import django_tables2 as tables
from django.utils.translation import gettext_lazy as _
from django_tables2.tables import Accessor
from netbox.tables import NetBoxTable, columns
from tenancy.tables.columns import TenantColumn

from .models import ScriptArtifact, ScriptExecution, ScriptInstance, ScriptLogLine


class ScriptInstanceTable(NetBoxTable):
    name = tables.Column(linkify=True)
    group = tables.Column(order_by=("group", "weight", "name"))
    tags = columns.TagColumn(url_name="plugins:netbox_script_manager:scriptinstance_list")
    tenant = TenantColumn(
        verbose_name=_("Tenant"),
    )
    last_execution = tables.TemplateColumn(
        template_code="""
            {% if value %}
                {{ value.created }}
            {% else %}
                <span class="text-muted">Never</span>
            {% endif %}
        """,
        accessor="last_execution",
        linkify=lambda value: value.get_absolute_url() if value else None,
    )

    class Meta(NetBoxTable.Meta):
        model = ScriptInstance
        fields = (
            "pk",
            "id",
            "name",
            "group",
            "weight",
            "description",
            "module_path",
            "class_name",
            "created",
            "last_updated",
            "tags",
            "last_execution",
        )
        default_columns = ("group", "name", "description", "tags")


class ScriptExecutionTable(NetBoxTable):
    name = tables.Column(accessor=Accessor("script_instance__name"), linkify=True)
    actions = columns.ActionsColumn(actions=("delete",))
    status = columns.ChoiceFieldColumn()

    class Meta(NetBoxTable.Meta):
        model = ScriptExecution
        fields = ("pk", "id", "name", "user", "created", "started", "completed", "status", "scheduled", "interval", "task_id")
        default_columns = (
            "id",
            "name",
            "script_instance",
            "user",
            "created",
            "started",
            "completed",
            "status",
            "scheduled",
            "interval",
            "task_id",
        )


class ScriptLogLineTable(NetBoxTable):
    script_execution = tables.Column(linkify=True)
    message = columns.MarkdownColumn()
    level = columns.ChoiceFieldColumn()
    actions = columns.ActionsColumn(actions=tuple())

    class Meta(NetBoxTable.Meta):
        model = ScriptLogLine
        fields = ("pk", "script_execution", "level", "message", "timestamp")
        default_columns = ("script_execution", "level", "message", "timestamp")


class ScriptArtifactTable(NetBoxTable):
    name = tables.Column(linkify=True)
    actions = columns.ActionsColumn(actions=("delete",))

    class Meta(NetBoxTable.Meta):
        model = ScriptArtifact
        fields = ("id", "name")
        default_columns = ("name",)
