from django.urls import path
from netbox.api.routers import NetBoxRouter

from netbox_script_manager.api.views import (
    RqStatusViewSet,
    ScriptArtifactViewSet,
    ScriptExecutionViewSet,
    ScriptInstanceViewSet,
    ScriptLogLineViewSet,
)

router = NetBoxRouter()
# router.APIRootView = NetBoxScriptManagerView

router.register("script-instances", ScriptInstanceViewSet)
router.register("script-executions", ScriptExecutionViewSet)
router.register("script-log-lines", ScriptLogLineViewSet)
router.register("script-artifacts", ScriptArtifactViewSet)
router.register("rq-status", RqStatusViewSet, basename="rq-status")

urlpatterns = router.urls
