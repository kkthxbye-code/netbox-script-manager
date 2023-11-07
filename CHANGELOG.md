# 0.2.1

* Initial public alpha release.

# 0.2.3

* Initial support for git sync (still WIP).

# 0.2.4

* Fix FileVar not working.
* Rewrote git sync support to use system git.

# 0.3.0

* Added optional tenant field to ScriptInstance.

# 0.3.1

* Added last_execution column to ScriptInstance table.
* Slight change in default columns for ScriptInstance table.

# 0.3.2

* Add scheduled/interval to script execution details
* Fix duration being calculed by created time when not started yet.
* Set new request id when scheduling the next task. Fixes exception when the next script was queued.

# 0.3.3

* Clear output when re-enqueuing a scheduled script.
* Set the initial value of checkboxes when rerunning scripts.

# 0.3.4

* Added git sync action to API.

# 0.3.5

* Fix API schema generation by adding docstring to rq-status endpoint.

# 0.3.6

* Cast log messages to string to prevent loggin None from throwing an error.
* Fix schema for ScriptInstance actions.

# 0.3.7

* Fix "Create" changelogs not being created when a scheduled script is re-enqueued.

# 0.3.8

* Fix "Script Data" being shown on no-input scripts.

# 0.3.9

* Omit _commit from saved input.
* Overwrite ScriptForm default_renderer to revert hack introduced in core netbox.

# 0.3.10

* Fix group not being shown on script instance details.
* Fix the ScriptExecution status field not being rendered as a proper netbox ChoiceField in the API.