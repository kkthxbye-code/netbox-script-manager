from netbox.api.routers import NetBoxRouter

from netbox_script_manager.api.views import (
    NetBoxScriptManagerView,
    ScriptInstanceViewSet,
    ScriptExecutionViewSet,
    ScriptLogLineViewSet,
    ScriptArtifactViewSet,
)

router = NetBoxRouter()
# router.APIRootView = NetBoxScriptManagerView

router.register("script-instances", ScriptInstanceViewSet)
router.register("script-executions", ScriptExecutionViewSet)
router.register("script-log-lines", ScriptLogLineViewSet)
router.register("script-artifacts", ScriptArtifactViewSet)

urlpatterns = router.urls
