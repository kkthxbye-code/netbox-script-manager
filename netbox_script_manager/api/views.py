import uuid

import django_rq
from django.conf import settings
from django_rq.views import get_statistics
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from netbox.api.authentication import IsAuthenticatedOrLoginNotRequired
from netbox.api.viewsets import NetBoxModelViewSet, NetBoxReadOnlyModelViewSet
from rest_framework import status as http_status
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.routers import APIRootView
from utilities.permissions import get_permission_for_model
from utilities.utils import copy_safe_request

from .. import util
from ..choices import ScriptExecutionStatusChoices
from ..filtersets import ScriptArtifactFilterSet, ScriptExecutionFilterSet, ScriptInstanceFilterSet, ScriptLogLineFilterSet
from ..models import ScriptArtifact, ScriptExecution, ScriptInstance, ScriptLogLine
from ..scripts import run_script
from .serializers import (
    ScriptArtifactSerializer,
    ScriptExecutionSerializer,
    ScriptInputSerializer,
    ScriptInstanceSerializer,
    ScriptLogLineSerializer,
)

plugin_config = settings.PLUGINS_CONFIG.get("netbox_script_manager")


class NetBoxScriptManagerView(APIRootView):
    def get_view_name(self):
        return "NetBoxScriptManager"


class ScriptInstanceViewSet(NetBoxModelViewSet):
    queryset = ScriptInstance.objects.all()
    serializer_class = ScriptInstanceSerializer
    filterset_class = ScriptInstanceFilterSet

    @extend_schema(
        methods=["post"],
        responses={200: ScriptInstanceSerializer(many=True)},
        request=OpenApiTypes.OBJECT,
    )
    @action(detail=False, methods=["post"], filterset_class=None, pagination_class=None)
    def load(self, request):
        """
        Load new scripts from `SCRIPT_ROOT`.
        """
        permission = get_permission_for_model(self.queryset.model, "add")

        if not request.user.has_perm(permission):
            raise PermissionDenied(f"Missing permission: {permission}")

        scripts, _ = util.load_scripts()
        script_instances = {script_instance.script_path: script_instance for script_instance in ScriptInstance.objects.all()}
        loaded_scripts = []

        for script_path, script in scripts.items():
            if script_path not in script_instances:
                script_name = getattr(script.Meta, "name", script_path)
                module_path, class_name = script_path.rsplit(".", 1)

                script_instance = ScriptInstance(
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
                loaded_scripts.append(script_instance)

        return Response(ScriptInstanceSerializer(loaded_scripts, many=True, context={"request": request}).data)

    @extend_schema(
        methods=["post"],
        responses={200: OpenApiTypes.OBJECT, 500: OpenApiTypes.OBJECT},
        request=None,
    )
    @action(detail=False, methods=["post"])
    def sync(self, request):
        """
        Pull script changes from git.
        """
        permission = get_permission_for_model(self.queryset.model, "sync")

        if not request.user.has_perm(permission):
            raise PermissionDenied(f"Missing permission: {permission}")

        try:
            result = util.pull_scripts()
        except Exception as e:
            return Response({"error": f"Failed to pull git repository: {e}"}, status=http_status.HTTP_500_INTERNAL_SERVER_ERROR)

        messages = [f"Pulled git repository"]
        if result:
            messages.append(result)

        return Response({"messages": messages}, status=http_status.HTTP_200_OK)

    @extend_schema(
        methods=["post"],
        responses={200: ScriptExecutionSerializer()},
        request=ScriptInputSerializer(),
    )
    @action(detail=True, methods=["post"])
    def run(self, request, pk):
        permission = get_permission_for_model(self.queryset.model, "run")
        if not request.user.has_perm(permission):
            raise PermissionDenied(f"Missing permission: {permission}")

        script_instance = self.get_object()
        input_serializer = ScriptInputSerializer(data=request.data, context={"script": script_instance.script})

        # TODO: Decide if we want this check
        # if not Worker.count(get_connection('default')):
        #    raise RQWorkerNotRunningException()

        if input_serializer.is_valid():
            schedule_at = input_serializer.validated_data.get("schedule_at")
            interval = input_serializer.validated_data.get("interval")
            status = ScriptExecutionStatusChoices.STATUS_SCHEDULED if schedule_at else ScriptExecutionStatusChoices.STATUS_PENDING

            task_queue = input_serializer.validated_data.get("task_queue", plugin_config.get("DEFAULT_QUEUE"))

            script_execution = ScriptExecution(
                script_instance=script_instance,
                task_id=uuid.uuid4(),
                request_id=request.id,
                user=request.user,
                status=status,
                scheduled=schedule_at,
                interval=interval,
                task_queue=task_queue,
            )

            # Save input data
            script_execution.data["input"] = input_serializer.data["data"]

            script_execution.full_clean()
            script_execution.save()

            queue = django_rq.get_queue(task_queue)

            if script_execution.scheduled:
                queue.enqueue_at(
                    script_execution.scheduled,
                    run_script,
                    job_id=str(script_execution.task_id),
                    data=input_serializer.data["data"],
                    request=copy_safe_request(request),
                    commit=input_serializer.data["commit"],
                    script_execution=script_execution,
                    interval=script_execution.interval,
                    job_timeout=script_instance.script.job_timeout,
                )
            else:
                queue.enqueue(
                    run_script,
                    job_id=str(script_execution.task_id),
                    data=input_serializer.data["data"],
                    request=copy_safe_request(request),
                    commit=input_serializer.data["commit"],
                    script_execution=script_execution,
                    job_timeout=script_instance.script.job_timeout,
                )

            serializer = ScriptExecutionSerializer(script_execution, context={"request": request})

            return Response(serializer.data)

        return Response(input_serializer.errors, status=http_status.HTTP_400_BAD_REQUEST)


class ScriptExecutionViewSet(NetBoxReadOnlyModelViewSet):
    queryset = ScriptExecution.objects.all()
    serializer_class = ScriptExecutionSerializer
    filterset_class = ScriptExecutionFilterSet


class ScriptLogLineViewSet(NetBoxReadOnlyModelViewSet):
    queryset = ScriptLogLine.objects.all()
    serializer_class = ScriptLogLineSerializer
    filterset_class = ScriptLogLineFilterSet


class ScriptArtifactViewSet(NetBoxModelViewSet):
    queryset = ScriptArtifact.objects.all()
    serializer_class = ScriptArtifactSerializer
    filterset_class = ScriptArtifactFilterSet


class RqStatusViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticatedOrLoginNotRequired]

    @extend_schema(responses={200: OpenApiTypes.OBJECT})
    def list(self, request):
        """
        Returns the status of the RQ workers.
        """
        return Response(get_statistics())
