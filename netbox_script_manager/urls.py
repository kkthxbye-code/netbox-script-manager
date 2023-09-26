from django.urls import path

from netbox.views.generic import ObjectChangeLogView
from . import models, views


urlpatterns = (
    # ScriptInstance
    path("script-instances/", views.ScriptInstanceListView.as_view(), name="scriptinstance_list"),
    path("script-instances/add/", views.ScriptInstanceEditView.as_view(), name="scriptinstance_add"),
    path("script-instances/<int:pk>/", views.ScriptInstanceView.as_view(), name="scriptinstance"),
    path("script-instances/<int:pk>/edit/", views.ScriptInstanceEditView.as_view(), name="scriptinstance_edit"),
    path("script-instances/<int:pk>/delete/", views.ScriptInstanceDeleteView.as_view(), name="scriptinstance_delete"),
    path("script-instances/<int:pk>/executions/", views.ScriptInstanceScriptExecutionsView.as_view(), name="scriptinstance_execution"),
    path(
        "script-instances/<int:pk>/changelog/",
        ObjectChangeLogView.as_view(),
        name="scriptinstance_changelog",
        kwargs={"model": models.ScriptInstance},
    ),
    path("script-instances/load/", views.ScriptInstanceLoadView.as_view(), name="scriptinstance_load"),
    # ScriptExecution
    path("script-executions/", views.ScriptExecutionListView.as_view(), name="scriptexecution_list"),
    path("script-executions/<int:pk>/", views.ScriptExecutionView.as_view(), name="scriptexecution"),
    path("script-executions/<int:pk>/htmx/", views.ScriptExecutionHtmx.as_view(), name="scriptexecution_htmx"),
    path("script-executions/<int:pk>/delete/", views.ScriptExecutionDeleteView.as_view(), name="scriptexecution_delete"),
    path(
        "script-executions/<int:pk>/changelog/",
        ObjectChangeLogView.as_view(),
        name="ScriptExecution_changelog",
        kwargs={"model": models.ScriptExecution},
    ),
    path("script-executions/delete/", views.ScriptExecutionBulkDeleteView.as_view(), name="scriptexecution_bulk_delete"),
    # ScriptArtifact
    path("script-artifacts/", views.ScriptArtifactListView.as_view(), name="scriptartifact_list"),
    path("script-artifacts/<int:pk>/", views.ScriptArtifactDownloadView.as_view(), name="scriptartifact_download"),
    path("script-artifacts/<int:pk>/delete/", views.ScriptArtifactDeleteView.as_view(), name="scriptartifact_delete"),
)
