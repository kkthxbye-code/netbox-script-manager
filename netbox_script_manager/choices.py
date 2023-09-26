from utilities.choices import ChoiceSet


class LogLevelChoices(ChoiceSet):
    LOG_DEBUG = "debug"
    LOG_SUCCESS = "success"
    LOG_INFO = "info"
    LOG_WARNING = "warning"
    LOG_FAILURE = "failure"

    CHOICES = (
        (LOG_DEBUG, "Default", "gray"),
        (LOG_SUCCESS, "Success", "green"),
        (LOG_INFO, "Info", "cyan"),
        (LOG_WARNING, "Warning", "yellow"),
        (LOG_FAILURE, "Failure", "red"),
    )


class ScriptExecutionStatusChoices(ChoiceSet):
    STATUS_PENDING = "pending"
    STATUS_SCHEDULED = "scheduled"
    STATUS_RUNNING = "running"
    STATUS_COMPLETED = "completed"
    STATUS_ERRORED = "errored"
    STATUS_FAILED = "failed"

    CHOICES = (
        (STATUS_PENDING, "Pending", "cyan"),
        (STATUS_SCHEDULED, "Scheduled", "gray"),
        (STATUS_RUNNING, "Running", "blue"),
        (STATUS_COMPLETED, "Completed", "green"),
        (STATUS_ERRORED, "Errored", "red"),
        (STATUS_FAILED, "Failed", "red"),
    )

    TERMINAL_STATE_CHOICES = (
        STATUS_COMPLETED,
        STATUS_ERRORED,
        STATUS_FAILED,
    )
