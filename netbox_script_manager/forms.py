from django import forms
from django.contrib.auth.models import User
from django.utils.translation import gettext as _
from extras.choices import DurationChoices
from extras.forms.mixins import SavedFiltersMixin
from netbox.forms import NetBoxModelFilterSetForm, NetBoxModelForm
from tenancy.models import Tenant
from utilities.forms import BootstrapMixin, FilterForm
from utilities.forms.fields import DynamicModelChoiceField, DynamicModelMultipleChoiceField, TagFilterField
from utilities.forms.widgets import APISelectMultiple, DateTimePicker, NumberWithOptions
from utilities.utils import local_now

from .choices import ScriptExecutionStatusChoices
from .models import ScriptExecution, ScriptInstance


class ScriptInstanceForm(NetBoxModelForm):
    tenant = DynamicModelChoiceField(
        label=_("Tenant"),
        queryset=Tenant.objects.all(),
        required=False,
        query_params={
            "group_id": "$tenant_group",
        },
    )
    module_path = forms.CharField(
        required=True,
        help_text="The path to the python module. Can be changed if the script has been moved.",
    )
    class_name = forms.CharField(
        required=True,
        help_text="The name of the CustomScript class. Can be changed if the script class has been renamed.",
    )

    class Meta:
        model = ScriptInstance
        fields = ("name", "module_path", "class_name", "group", "weight", "description", "task_queues", "comments", "tenant", "tags")

        widgets = {
            "description": forms.Textarea(attrs={"rows": 3}),
        }


class ScriptInstanceFilterForm(NetBoxModelFilterSetForm):
    model = ScriptInstance
    name = forms.CharField(required=False)
    group = forms.CharField(required=False)
    tag = TagFilterField(model)
    tenant_id = DynamicModelMultipleChoiceField(
        queryset=Tenant.objects.all(),
        required=False,
        null_option="None",
        query_params={"group_id": "$tenant_group_id"},
        label=_("Tenant"),
    )


class ScriptExecutionFilterForm(SavedFiltersMixin, FilterForm):
    fieldsets = (
        (None, ("q", "filter_id")),
        (
            "Creation",
            (
                "created__before",
                "created__after",
                "scheduled__before",
                "scheduled__after",
                "started__before",
                "started__after",
                "completed__before",
                "completed__after",
                "user",
            ),
        ),
    )
    model = ScriptExecution

    status = forms.MultipleChoiceField(choices=ScriptExecutionStatusChoices, required=False)
    created__after = forms.DateTimeField(required=False, widget=DateTimePicker())
    created__before = forms.DateTimeField(required=False, widget=DateTimePicker())
    scheduled__after = forms.DateTimeField(required=False, widget=DateTimePicker())
    scheduled__before = forms.DateTimeField(required=False, widget=DateTimePicker())
    started__after = forms.DateTimeField(required=False, widget=DateTimePicker())
    started__before = forms.DateTimeField(required=False, widget=DateTimePicker())
    completed__after = forms.DateTimeField(required=False, widget=DateTimePicker())
    completed__before = forms.DateTimeField(required=False, widget=DateTimePicker())
    user = DynamicModelMultipleChoiceField(
        queryset=User.objects.all(),
        required=False,
        label=_("User"),
        widget=APISelectMultiple(
            api_url="/api/users/users/",
        ),
    )


class ScriptForm(BootstrapMixin, forms.Form):
    default_renderer = forms.renderers.DjangoTemplates()

    _commit = forms.BooleanField(
        required=False, initial=True, label=_("Commit changes"), help_text=_("Commit changes to the database (uncheck for a dry-run)")
    )
    _schedule_at = forms.DateTimeField(
        required=False,
        widget=DateTimePicker(),
        label=_("Schedule at"),
        help_text=_("Schedule execution of script to a set time"),
    )
    _interval = forms.IntegerField(
        required=False,
        min_value=1,
        label=_("Recurs every"),
        widget=NumberWithOptions(options=DurationChoices),
        help_text=_("Interval at which this script is re-run (in minutes)"),
    )
    _task_queue = forms.ChoiceField(
        required=False,
        help_text="The script will be run on the chosen queue",
        label=_("Task queue"),
    )

    def __init__(self, *args, scheduling_enabled=True, **kwargs):
        super().__init__(*args, **kwargs)

        # Annotate the current system time for reference
        now = local_now().strftime("%Y-%m-%d %H:%M:%S")
        self.fields["_schedule_at"].help_text += f" (current time: <strong>{now}</strong>)"

        # Remove scheduling fields if scheduling is disabled
        if not scheduling_enabled:
            self.fields.pop("_schedule_at")
            self.fields.pop("_interval")

    def clean(self):
        scheduled_time = self.cleaned_data.get("_schedule_at")
        if scheduled_time and scheduled_time < local_now():
            raise forms.ValidationError(_("Scheduled time must be in the future."))

        # When interval is used without schedule at, schedule for the current time
        if self.cleaned_data.get("_interval") and not scheduled_time:
            self.cleaned_data["_schedule_at"] = local_now()

        return self.cleaned_data
