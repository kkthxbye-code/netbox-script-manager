import uuid

import django_rq
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.routers import APIRootView
from rest_framework import status as http_status

from netbox.api.viewsets import NetBoxModelViewSet
from utilities.utils import copy_safe_request
from ..choices import ScriptExecutionStatusChoices
from utilities.permissions import get_permission_for_model

from .serializers import (
    ScriptInstanceSerializer,
    ScriptExecutionSerializer,
    ScriptLogLineSerializer,
    ScriptArtifactSerializer,
    ScriptInputSerializer,
)

# from netbox_dns.filters import ViewFilter, ZoneFilter, NameServerFilter, RecordFilter
from ..models import ScriptInstance, ScriptArtifact, ScriptExecution, ScriptLogLine
from ..filtersets import ScriptInstanceFilterSet, ScriptArtifactFilterSet, ScriptExecutionFilterSet, ScriptLogLineFilterSet
from ..scripts import run_script


class NetBoxScriptManagerView(APIRootView):
    def get_view_name(self):
        return "NetBoxScriptManager"


class ScriptInstanceViewSet(NetBoxModelViewSet):
    queryset = ScriptInstance.objects.all()
    serializer_class = ScriptInstanceSerializer
    filterset_class = ScriptInstanceFilterSet

    @action(detail=True, methods=["post"])
    def run(self, request, pk):
        # TODO: Add schema definitions.
        # TODO: Consider refactoring serializers

        permission = get_permission_for_model(self.queryset.model, "sync")
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

            # TODO: Fix this
            # task_queue = input_serializer.validated_data.get('task_queue', None)
            task_queue = "high"

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


class ScriptExecutionViewSet(NetBoxModelViewSet):
    queryset = ScriptExecution.objects.all()
    serializer_class = ScriptExecutionSerializer
    filterset_class = ScriptExecutionFilterSet


class ScriptLogLineViewSet(NetBoxModelViewSet):
    queryset = ScriptLogLine.objects.all()
    serializer_class = ScriptLogLineSerializer
    filterset_class = ScriptLogLineFilterSet


class ScriptArtifactViewSet(NetBoxModelViewSet):
    queryset = ScriptArtifact.objects.all()
    serializer_class = ScriptArtifactSerializer
    filterset_class = ScriptArtifactFilterSet
