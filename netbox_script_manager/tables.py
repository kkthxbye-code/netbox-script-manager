import django_tables2 as tables
from django_tables2.tables import Accessor

from netbox.tables import NetBoxTable, columns
from .models import ScriptInstance, ScriptExecution, ScriptLogLine, ScriptArtifact


class ScriptInstanceTable(NetBoxTable):
    name = tables.Column(linkify=True)
    group = tables.Column(order_by=("group", "-weight", "name"))
    tags = columns.TagColumn(url_name="plugins:netbox_script_manager:scriptinstance_list")

    class Meta(NetBoxTable.Meta):
        model = ScriptInstance
        fields = ("pk", "id", "name", "group", "weight", "description", "module_path", "class_name", "created", "last_updated", "tags")
        default_columns = ("name", "group", "description", "module_path", "class_name", "tags")


class ScriptExecutionTable(NetBoxTable):
    name = tables.Column(accessor=Accessor("script_instance__name"), linkify=True)
    actions = columns.ActionsColumn(actions=("delete",))

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
