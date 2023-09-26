from rest_framework.routers import APIRootView

from netbox.api.viewsets import NetBoxModelViewSet

from .serializers import (
    ScriptInstanceSerializer,
    ScriptExecutionSerializer,
    ScriptLogLineSerializer,
    ScriptArtifactSerializer,
)

# from netbox_dns.filters import ViewFilter, ZoneFilter, NameServerFilter, RecordFilter
from ..models import ScriptInstance, ScriptArtifact, ScriptExecution, ScriptLogLine
from ..filtersets import ScriptInstanceFilterSet, ScriptArtifactFilterSet, ScriptExecutionFilterSet, ScriptLogLineFilterSet


class NetBoxScriptManagerView(APIRootView):
    def get_view_name(self):
        return "NetBoxScriptManager"


class ScriptInstanceViewSet(NetBoxModelViewSet):
    queryset = ScriptInstance.objects.all()
    serializer_class = ScriptInstanceSerializer
    filterset_class = ScriptInstanceFilterSet


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
