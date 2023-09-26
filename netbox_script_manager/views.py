import json

import django_rq
import uuid

from django.contrib import messages
from django.http import HttpResponse
from django.shortcuts import redirect
from django.views.generic import View

from netbox.views import generic
from utilities.views import ContentTypePermissionRequiredMixin, ViewTab, register_model_view
from utilities.utils import copy_safe_request, normalize_querydict

from . import filtersets, forms, models, tables
from . import util
from .scripts import run_script
from .api.serializers import ScriptLogLineMinimalSerializer


class ScriptInstanceView(generic.ObjectView):
    queryset = models.ScriptInstance.objects.all()

    def get_extra_context(self, request, instance):
        try:
            script = instance.script
        except Exception as e:
            return {"exception": e}

        return {"form": script.as_form(initial=normalize_querydict(request.GET), script_instance=instance)}

    def post(self, request, pk):
        instance = self.get_object(pk=pk)
        form = instance.script.as_form(request.POST, script_instance=instance)

        if form.is_valid():
            script_execution = models.ScriptExecution(
                script_instance=instance,
                task_id=uuid.uuid4(),
                user=request.user,
            )
            script_execution.full_clean()
            script_execution.save()

            task_queue = form.cleaned_data.pop("_task_queue")
            if not task_queue:
                task_queue = "default"

            queue = django_rq.get_queue(task_queue)
            queue.enqueue(
                run_script,
                data=form.cleaned_data,
                request=copy_safe_request(request),
                commit=form.cleaned_data.pop("_commit"),
                script_execution=script_execution,
            )

            return redirect("plugins:netbox_script_manager:scriptexecution", pk=script_execution.pk)

        return redirect("plugins:netbox_script_manager:scriptinstance_list")


class ScriptInstanceListView(generic.ObjectListView):
    queryset = models.ScriptInstance.objects.all()
    table = tables.ScriptInstanceTable
    filterset = filtersets.ScriptInstanceFilterSet
    filterset_form = forms.ScriptInstanceFilterForm
    template_name = "netbox_script_manager/script_list.html"
    actions = ("delete", "bulk_delete")


class ScriptInstanceEditView(generic.ObjectEditView):
    queryset = models.ScriptInstance.objects.all()
    form = forms.ScriptInstanceForm


class ScriptInstanceDeleteView(generic.ObjectDeleteView):
    queryset = models.ScriptInstance.objects.all()


class ScriptInstanceBulkDeleteView(generic.BulkDeleteView):
    queryset = models.ScriptInstance.objects.all()
    filterset = filtersets.ScriptInstanceFilterSet
    table = tables.ScriptInstanceTable


class ScriptInstanceLoadView(ContentTypePermissionRequiredMixin, View):
    def get_required_permission(self):
        # TODO: Use correct permission
        return "extras.view_script"

    def get(self, request):
        scripts_found = False

        scripts = util.load_scripts()
        script_instances = {script_instance.script_path: script_instance for script_instance in models.ScriptInstance.objects.all()}

        for script_path, script in scripts.items():
            if script_path not in script_instances:
                scripts_found = True

                script_name = getattr(script.Meta, "name", script_path)
                module_path, class_name = script_path.rsplit(".", 1)

                script_instance = models.ScriptInstance(
                    name=script_name,
                    module_path=module_path,
                    class_name=class_name,
                    description=script.description,
                    task_queues=script.task_queues,
                    group=script.group,
                    weight=script.weight,
                )
                script_instance.full_clean()
                script_instance.save()

                messages.success(request, f'Script "{script_name}" loaded')

        if not scripts_found:
            messages.info(request, f"No new scripts found")

        return redirect("plugins:netbox_script_manager:scriptinstance_list")


@register_model_view(models.ScriptInstance, "execution")
class ScriptInstanceScriptExecutionsView(generic.ObjectChildrenView):
    queryset = models.ScriptInstance.objects.all()
    child_model = models.ScriptExecution
    table = tables.ScriptExecutionTable
    filterset = filtersets.ScriptExecutionFilterSet
    actions = ("delete", "bulk_delete")
    template_name = "netbox_script_manager/script_instance_execution_list.html"
    tab = ViewTab(
        label="Executions",
        badge=lambda obj: obj.script_executions.count(),
        permission="dcim.view_interface",  # TODO: Fix permission
        weight=520,
        hide_if_empty=False,
    )

    def get_children(self, request, parent):
        return parent.script_executions.restrict(request.user, "view")


class ScriptExecutionView(generic.ObjectView):
    queryset = models.ScriptExecution.objects.all()
    actions = ("delete",)

    def get_extra_context(self, request, instance):
        log_lines = instance.script_log_lines.all()
        serialized_logs = ScriptLogLineMinimalSerializer(log_lines, many=True).data

        return {
            "log_lines": json.dumps(serialized_logs),
        }


class ScriptExecutionHtmx(generic.ObjectView):
    queryset = models.ScriptExecution.objects.all()
    template_name = "netbox_script_manager/htmx/script_execution.html"


class ScriptExecutionListView(generic.ObjectListView):
    queryset = models.ScriptExecution.objects.all()
    table = tables.ScriptExecutionTable
    actions = ("export", "delete", "bulk_delete")
    filterset = filtersets.ScriptExecutionFilterSet
    filterset_form = forms.ScriptExecutionFilterForm


class ScriptExecutionDeleteView(generic.ObjectDeleteView):
    queryset = models.ScriptExecution.objects.all()


class ScriptExecutionBulkDeleteView(generic.BulkDeleteView):
    queryset = models.ScriptExecution.objects.all()
    filterset = filtersets.ScriptExecutionFilterSet
    table = tables.ScriptExecutionTable


class ScriptArtifactListView(generic.ObjectListView):
    queryset = models.ScriptArtifact.objects.all()
    table = tables.ScriptArtifactTable
    filterset = filtersets.ScriptArtifactFilterSet
    actions = tuple()


class ScriptArtifactDownloadView(generic.ObjectView):
    queryset = models.ScriptArtifact.objects.all()

    def get(self, request, **kwargs):
        instance = self.get_object(**kwargs)

        response = HttpResponse(instance.data, content_type=instance.content_type)
        filename = instance.name
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        return response


class ScriptArtifactDeleteView(generic.ObjectDeleteView):
    queryset = models.ScriptArtifact.objects.all()
