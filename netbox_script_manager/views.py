import json
import uuid

import django_rq
from django.conf import settings
from django.contrib import messages
from django.contrib.contenttypes.models import ContentType
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.utils.safestring import mark_safe
from django.views.generic import View
from extras.filtersets import ObjectChangeFilterSet
from extras.models import ObjectChange
from extras.tables import ObjectChangeTable
from netbox.views import generic
from utilities.utils import copy_safe_request, normalize_querydict
from utilities.views import ContentTypePermissionRequiredMixin, ViewTab, register_model_view

from . import filtersets, forms, models, tables, util
from .api.serializers import ScriptLogLineMinimalSerializer
from .choices import ScriptExecutionStatusChoices
from .models import ScriptExecution
from .scripts import run_script
from .templatetags.scriptmanager import format_exception

plugin_config = settings.PLUGINS_CONFIG.get("netbox_script_manager")


class ScriptInstanceView(generic.ObjectView):
    queryset = models.ScriptInstance.objects.all()

    def get_extra_context(self, request, instance):
        try:
            script = instance.script
        except Exception as e:
            return {"exception": e}

        fieldsets = script.get_fieldsets(instance=instance)
        return {"form": script.as_form(initial=normalize_querydict(request.GET), script_instance=instance), "fieldsets": fieldsets}

    def post(self, request, pk):
        instance = self.get_object(pk=pk)
        form = instance.script.as_form(request.POST, files=request.FILES, script_instance=instance)
        fieldsets = instance.script.get_fieldsets(instance=instance)

        if form.is_valid():
            schedule_at = form.cleaned_data.pop("_schedule_at")
            interval = form.cleaned_data.pop("_interval")

            status = ScriptExecutionStatusChoices.STATUS_SCHEDULED if schedule_at else ScriptExecutionStatusChoices.STATUS_PENDING

            task_queue = form.cleaned_data.pop("_task_queue", None)
            if not task_queue:
                task_queue = plugin_config.get("DEFAULT_QUEUE")

            script_execution = models.ScriptExecution(
                script_instance=instance,
                task_id=uuid.uuid4(),
                request_id=request.id,
                user=request.user,
                status=status,
                scheduled=schedule_at,
                interval=interval,
                task_queue=task_queue,
            )

            # Save script input
            script_execution.data["input"] = util.prepare_post_data(request)

            script_execution.full_clean()
            script_execution.save()

            queue = django_rq.get_queue(task_queue)

            if script_execution.scheduled:
                queue.enqueue_at(
                    script_execution.scheduled,
                    run_script,
                    job_id=str(script_execution.task_id),
                    data=form.cleaned_data,
                    request=copy_safe_request(request),
                    commit=form.cleaned_data.pop("_commit"),
                    script_execution=script_execution,
                    interval=script_execution.interval,
                    job_timeout=instance.script.job_timeout,
                )
            else:
                queue.enqueue(
                    run_script,
                    job_id=str(script_execution.task_id),
                    data=form.cleaned_data,
                    request=copy_safe_request(request),
                    commit=form.cleaned_data.pop("_commit"),
                    script_execution=script_execution,
                    job_timeout=instance.script.job_timeout,
                )

            return redirect("plugins:netbox_script_manager:scriptexecution", pk=script_execution.pk)

        return render(request, "netbox_script_manager/scriptinstance.html", {"form": form, "object": instance, "fieldsets": fieldsets})


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
        return "netbox_script_manager.add_scriptinstance"

    def get(self, request):
        scripts_found = False

        scripts, failed_modules = util.load_scripts()
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

        for module_name, exception in failed_modules.items():
            # This is hackish but it works. Toast messages are kinda limited in netbox.
            messages.error(
                request,
                mark_safe(
                    f'Failed to load module {module_name}: <pre style="overflow-x: scroll; width: 350px;">{format_exception(exception)}</pre>'
                ),
            )

        if not scripts_found:
            messages.info(request, "No new scripts found")

        return redirect("plugins:netbox_script_manager:scriptinstance_list")


class ScriptInstanceSyncView(ContentTypePermissionRequiredMixin, View):
    def get_required_permission(self):
        return "netbox_script_manager.sync_scriptinstance"

    def get(self, request):
        try:
            result = util.pull_scripts()
        except Exception as e:
            messages.error(request, f"Failed to pull git repository: {e}")
            return redirect("plugins:netbox_script_manager:scriptinstance_list")

        message = [f"Pulled git repository"]
        if result:
            message.append(f"<pre>{result}</pre>")

        messages.info(request, mark_safe("\n".join(message)))

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
        permission="netbox_script_manager.view_script_execution",
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


@register_model_view(models.ScriptExecution, "changes")
class ScriptExecutionObjectChangeView(generic.ObjectChildrenView):
    queryset = models.ScriptExecution.objects.all()
    child_model = ObjectChange
    table = ObjectChangeTable
    filterset = ObjectChangeFilterSet
    actions = ("delete", "bulk_delete")
    template_name = "netbox_script_manager/script_execution_objectchange_list.html"
    tab = ViewTab(
        label="Changes",
        badge=lambda obj: ObjectChange.objects.filter(request_id=str(obj.request_id))
        .exclude(changed_object_type=ContentType.objects.get_for_model(ScriptExecution))
        .count(),
        permission="netbox_script_manager.view_scriptexecution",
        weight=500,
        hide_if_empty=False,
    )

    def get_children(self, request, parent):
        return (
            ObjectChange.objects.restrict(request.user, "view")
            .filter(request_id=str(parent.request_id))
            .exclude(changed_object_type=ContentType.objects.get_for_model(ScriptExecution))
        )


@register_model_view(models.ScriptExecution, "data")
class ScriptExecutionDataView(generic.ObjectView):
    queryset = models.ScriptExecution.objects.all()
    template_name = "netbox_script_manager/scriptexecution_data.html"
    tab = ViewTab(label="Data", permission="", weight=1000)


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
