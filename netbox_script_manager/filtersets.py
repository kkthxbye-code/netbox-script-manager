import django_filters
from django.db.models import Q
from django.utils.translation import gettext as _
from netbox.filtersets import BaseFilterSet, NetBoxModelFilterSet
from tenancy.models import Tenant

from .choices import LogLevelChoices, ScriptExecutionStatusChoices
from .models import ScriptArtifact, ScriptExecution, ScriptInstance, ScriptLogLine


class ScriptInstanceFilterSet(NetBoxModelFilterSet):
    tenant_id = django_filters.ModelMultipleChoiceFilter(
        queryset=Tenant.objects.all(),
        label=_("Tenant (ID)"),
    )
    tenant = django_filters.ModelMultipleChoiceFilter(
        queryset=Tenant.objects.all(),
        field_name="tenant__slug",
        to_field_name="slug",
        label=_("Tenant (slug)"),
    )

    class Meta:
        model = ScriptInstance
        fields = ["name", "description", "group", "weight"]

    def search(self, queryset, name, value):
        if not value.strip():
            return queryset
        qs_filter = Q(name__icontains=value) | Q(description__icontains=value) | Q(group__icontains=value)
        return queryset.filter(qs_filter).distinct()


class ScriptArtifactFilterSet(BaseFilterSet):
    q = django_filters.CharFilter(method="search")
    script_execution_id = django_filters.ModelMultipleChoiceFilter(
        queryset=ScriptExecution.objects.all(),
    )

    class Meta:
        model = ScriptArtifact
        fields = [
            "name",
        ]

    def search(self, queryset, name, value):
        if not value.strip():
            return queryset
        qs_filter = (Q(name__icontains=value),)
        return queryset.filter(qs_filter).distinct()


class ScriptExecutionFilterSet(BaseFilterSet):
    q = django_filters.CharFilter(method="search")
    created = django_filters.DateTimeFilter()
    created__before = django_filters.DateTimeFilter(field_name="created", lookup_expr="lte")
    created__after = django_filters.DateTimeFilter(field_name="created", lookup_expr="gte")
    scheduled = django_filters.DateTimeFilter()
    scheduled__before = django_filters.DateTimeFilter(field_name="scheduled", lookup_expr="lte")
    scheduled__after = django_filters.DateTimeFilter(field_name="scheduled", lookup_expr="gte")
    started = django_filters.DateTimeFilter()
    started__before = django_filters.DateTimeFilter(field_name="started", lookup_expr="lte")
    started__after = django_filters.DateTimeFilter(field_name="started", lookup_expr="gte")
    completed = django_filters.DateTimeFilter()
    completed__before = django_filters.DateTimeFilter(field_name="completed", lookup_expr="lte")
    completed__after = django_filters.DateTimeFilter(field_name="completed", lookup_expr="gte")
    status = django_filters.MultipleChoiceFilter(choices=ScriptExecutionStatusChoices, null_value=None)

    class Meta:
        model = ScriptExecution
        fields = ("id", "interval", "status", "user")

    def search(self, queryset, name, value):
        if not value.strip():
            return queryset
        return queryset.filter(Q(user__username__icontains=value) | Q(script_instance__name__icontains=value))


class ScriptLogLineFilterSet(BaseFilterSet):
    q = django_filters.CharFilter(method="search")
    timestamp = django_filters.DateTimeFilter()
    timestamp__before = django_filters.DateTimeFilter(field_name="timestamp", lookup_expr="lte")
    timestamp__after = django_filters.DateTimeFilter(field_name="timestamp", lookup_expr="gte")
    level = django_filters.MultipleChoiceFilter(choices=LogLevelChoices, null_value=None)

    class Meta:
        model = ScriptLogLine
        fields = ("id", "script_execution", "level")

    def search(self, queryset, name, value):
        if not value.strip():
            return queryset
        return queryset.filter(Q(message__icontains=value) | Q(script_execution__script_instance__name__icontains=value))
