import inspect
import logging
import traceback
from datetime import timedelta

from django.utils.functional import classproperty
from django.db import transaction

import django_rq
import rq

from extras.context_managers import change_logging
from extras.scripts import ScriptVariable
from .forms import ScriptForm

# from extras.models import ScriptModule
from extras.signals import clear_webhooks
from utilities.exceptions import AbortScript, AbortTransaction

from .models import ScriptLogLine, ScriptArtifact
from .choices import LogLevelChoices, JobStatusChoices

# from .forms import ScriptForm


class CustomScript:
    """
    Base class for all custom scripts.
    """

    # Prevent django from instantiating the class on all accesses
    do_not_call_in_templates = True

    class Meta:
        pass

    def __init__(self):
        self.logger = logging.getLogger(f"netbox.scripts.{self.__module__}.{self.__class__.__name__}")
        self.log = []

        # TODO: This must be set by the script executor
        self.script_execution = None
        self.request = None

        self.filename = inspect.getfile(self.__class__)
        self.source = inspect.getsource(self.__class__)

    def __str__(self):
        return self.name

    @classproperty
    def module(self):
        return self.__module__

    @classproperty
    def class_name(self):
        return self.__name__

    @classproperty
    def full_name(self):
        return f"{self.module}.{self.class_name}"

    @classmethod
    def root_module(cls):
        return cls.__module__.split(".")[0]

    # Author-defined attributes

    @classproperty
    def name(self):
        return getattr(self.Meta, "name", self.__name__)

    @classproperty
    def description(self):
        return getattr(self.Meta, "description", "")

    @classproperty
    def field_order(self):
        return getattr(self.Meta, "field_order", None)

    @classproperty
    def fieldsets(self):
        return getattr(self.Meta, "fieldsets", None)

    @classproperty
    def commit_default(self):
        return getattr(self.Meta, "commit_default", True)

    @classproperty
    def job_timeout(self):
        return getattr(self.Meta, "job_timeout", None)

    @classproperty
    def scheduling_enabled(self):
        return getattr(self.Meta, "scheduling_enabled", True)

    @classproperty
    def task_queue(self):
        return getattr(self.Meta, "task_queue", "default")

    @classmethod
    def _get_vars(cls):
        vars = {}

        # Iterate all base classes looking for ScriptVariables
        for base_class in inspect.getmro(cls):
            # When object is reached there's no reason to continue
            if base_class is object:
                break

            for name, attr in base_class.__dict__.items():
                if name not in vars and issubclass(attr.__class__, ScriptVariable):
                    vars[name] = attr

        # Order variables according to field_order
        if not cls.field_order:
            return vars
        ordered_vars = {field: vars.pop(field) for field in cls.field_order if field in vars}
        ordered_vars.update(vars)

        return ordered_vars

    def run(self, data, commit):
        raise NotImplementedError("The script must define a run() method.")

    # Form rendering

    def get_fieldsets(self):
        fieldsets = []

        if self.fieldsets:
            fieldsets.extend(self.fieldsets)
        else:
            fields = (name for name, _ in self._get_vars().items())
            fieldsets.append(("Script Data", fields))

        # Append the default fieldset if defined in the Meta class
        exec_parameters = ("_schedule_at", "_interval", "_task_queue", "_commit") if self.scheduling_enabled else ("_task_queue", "_commit")
        fieldsets.append(("Script Execution Parameters", exec_parameters))

        return fieldsets

    def as_form(self, data=None, files=None, initial=None, script_instance=None):
        """
        Return a Django form suitable for populating the context data required to run this Script.
        """
        # Create a dynamic ScriptForm subclass from script variables
        fields = {name: var.as_field() for name, var in self._get_vars().items()}
        FormClass = type("ScriptForm", (ScriptForm,), fields)

        form = FormClass(data, files, initial=initial)

        # Set initial "commit" checkbox state based on the script's Meta parameter
        form.fields["_commit"].initial = self.commit_default
        form.fields["_task_queue"].choices = task_queue_choices(script_instance.task_queues)

        return form

    def _log_message(self, level, message):
        if not self.script_execution:
            raise RuntimeError("Script execution not set.")

        script_log_line = ScriptLogLine(script_execution=self.script_execution, level=level, message=message)
        script_log_line.full_clean()
        script_log_line.save(using="script_log")

    def save_artifact(self, name, data, content_type="text/plain", encoding="utf-8"):
        """
        Save an arbitrary data blob as an artifact of this script execution.
        """
        if not self.script_execution:
            raise RuntimeError("Script execution not set.")

        if not isinstance(data, bytes):
            data = data.encode(encoding)

        artifact = ScriptArtifact(script_execution=self.script_execution, data=data, name=name, content_type=content_type)
        artifact.full_clean()
        artifact.save()

    def log_debug(self, message):
        self.logger.log(logging.DEBUG, message)
        self._log_message(LogLevelChoices.LOG_DEBUG, message)

    def log_success(self, message):
        self.logger.log(logging.INFO, message)  # No syslog equivalent for SUCCESS
        self._log_message(LogLevelChoices.LOG_SUCCESS, message)

    def log_info(self, message):
        self.logger.log(logging.INFO, message)
        self._log_message(LogLevelChoices.LOG_INFO, message)

    def log_warning(self, message):
        self.logger.log(logging.WARNING, message)
        self._log_message(LogLevelChoices.LOG_WARNING, message)

    def log_failure(self, message):
        self.logger.log(logging.ERROR, message)
        self._log_message(LogLevelChoices.LOG_FAILURE, message)


def run_script(data, request, script_execution, commit=True, **kwargs):
    """
    A wrapper for calling Script.run(). This performs error handling and provides a hook for committing changes. It
    exists outside the Script class to ensure it cannot be overridden by a script author.
    """

    script_execution.start()

    script = script_execution.script_instance.script
    script.script_execution = script_execution

    logger = logging.getLogger(f"netbox.scripts.{script.full_name}")
    logger.info(f"Running script (commit={commit})")

    # Add files to form data
    files = request.FILES
    for field_name, fileobj in files.items():
        data[field_name] = fileobj

    # Add the current request as a property of the script
    script.request = request

    def _run_script():
        """
        Core script execution task. We capture this within a subfunction to allow for conditionally wrapping it with
        the change_logging context manager (which is bypassed if commit == False).
        """
        try:
            try:
                with transaction.atomic():
                    script.output = script.run(data=data, commit=commit)
                    if not commit:
                        raise AbortTransaction()
            except AbortTransaction:
                script.log_info("Database changes have been reverted automatically.")
                clear_webhooks.send(request)

            # ScriptExecution.data = ScriptOutputSerializer(script).data
            script_execution.terminate()
        except Exception as e:
            if type(e) is AbortScript:
                script.log_failure(f"Script aborted with error: {e}")
                logger.error(f"Script aborted with error: {e}")
            else:
                stacktrace = traceback.format_exc()
                script.log_failure(f"An exception occurred: `{type(e).__name__}: {e}`\n```\n{stacktrace}\n```")
                logger.error(f"Exception raised during script execution: {e}")
            script.log_info("Database changes have been reverted due to error.")
            # job.data = ScriptOutputSerializer(script).data

            script_execution.terminate(status=JobStatusChoices.STATUS_ERRORED)
            clear_webhooks.send(request)

        # logger.info(f"Script completed in {script_execution.duration}")

    # Execute the script. If commit is True, wrap it with the change_logging context manager to ensure we process
    # change logging, webhooks, etc.
    if commit:
        with change_logging(request):
            _run_script()
    else:
        _run_script()

    # Schedule the next job if an interval has been set
    if script_execution.interval:
        new_scheduled_time = script_execution.scheduled + timedelta(minutes=script_execution.interval)
        logger.info(f"Scheduling next job for {new_scheduled_time}")
        """ TODO
        Job.enqueue(
            run_script,
            instance=script_execution.object,
            name=script_execution.name,
            user=script_execution.user,
            schedule_at=new_scheduled_time,
            interval=script_execution.interval,
            job_timeout=script.job_timeout,
            data=data,
            request=request,
            commit=commit
        )
        """


def task_queue_choices(task_queues):
    choices = []
    queues = django_rq.settings.QUEUES_LIST
    for queue in queues:
        if queue["name"] not in task_queues:
            continue

        workers = rq.Worker.count(queue=django_rq.get_queue(queue["name"]))
        description = f"{queue['name']} ({workers} workers)"
        choices.append((queue["name"], description))
    return choices
