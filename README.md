# NetBox Script Manager

Improved custom script support for netbox. Netbox version 3.5 removed several features related to custom scripts. This plugin attempts to undo these changes and add other improvements to scripts in netbox.

The plugin can be used in addition to the built-in script support and does not disable any netbox features.

## Features

* Scripts can be stored in nested modules.
* Scripts can rely on non-script module files.
* Scripts are loaded from a file-system folder.
* It's possible to sync scripts by pulling any git repo located in the `SCRIPT_ROOT` (WIP)
* Name, group, description, task queues, comments and tags are editable in the UI.
* Task queue is selectable in the UI.
* Exceptions caused by errors in script files are displayed in the UI.
* Log messages are saved and displayed when the script is running allowing live output for long running scripts.
* It's possible to filter log lines by message and/or log level.
* Script executions are listed in a tab when viewing a script.
* Changelog entries are listed in a tab when viewing a finished script execution.
* It's possible to save script artifacts during the execution of a script. These artifacts will show up as downloadable files.
* Possibility to re-run scripts.

## What is not supported

* Reports
* DataSource/DataFile
* `load_json` and `load_yaml` convenience methods
* `script_order` - the ordering of scripts is instead based on `group` and `weight`

## Compatibility

| NetBox Version | Plugin Version |
|----------------|----------------|
|     3.5        |      0.1.0     |

## Script folder

The loading of scripts is a little different with netbox-script-manager. The `SCRIPT_ROOT` plugin setting must be set to define the path of the custom scripts, however the scripts must be located in a folder named `customscripts` in this path.

A folder structure like this is required (`SCRIPT_ROOT` pointing to the `netboxscripts` folder):

```bash
├── netboxscripts
│   ├── customscripts
│   │   ├── __init__.py
│   │   ├── nestedmodule
│   │   ├── root_script.py
│   │   └── util
│   └── __init__.py
```

The reason for requiring this layout with a `customscripts` folder is to avoid name collisions when dynamically loading scripts. It also makes it easier to clear the internal python module cache which is needed for reloading scripts.

## Installing

Add the plugin to `local_requirements.txt` or `plugin_requirements.txt` (netbox-docker):

```
netbox-script-manager
```

Enable the plugin in `/opt/netbox/netbox/netbox/configuration.py`,
 or if you use netbox-docker, your `/configuration/plugins.py` file:

```python
PLUGINS = [
    'netbox_script_manager'
]

PLUGINS_CONFIG = {
    "netbox_script_manager Manager": {
        "SCRIPT_ROOT": "/path/to/script/folder/",
        "DEFAULT_QUEUE": "high"
    },
}
```
