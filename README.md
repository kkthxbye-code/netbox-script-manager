# NetBox Script Manager

Improved custom script support for netbox. Netbox version 3.5 removed several features related to custom scripts. This plugin attempts to undo these changes and add other improvements to scripts in netbox.

The plugin can be used in addition to the built-in script support and does not disable any netbox features.

## Features

* Scripts can be stored in nested modules.
* Scripts can rely on non-script module files.
* Scripts are loaded from a file-system folder.
* It's possible to sync scripts by pulling any git repo located in the `SCRIPT_ROOT`
* Name, group, description, task queues, comments and tags are editable in the UI.
* Task queue is selectable in the UI.
* Exceptions caused by errors in script files are displayed in the UI.
* Log messages are saved and displayed when the script is running allowing live output for long running scripts.
* It's possible to filter log lines by message and/or log level.
* Changelog entries are listed in a tab when viewing a finished script execution.
* It's possible to save script artifacts during the execution of a script. These artifacts will show up as downloadable files.
* It's possible to re-run scripts.

## What is not supported

* Reports
* DataSource/DataFile
* `load_json` and `load_yaml` convenience methods
* `script_order` - the ordering of scripts is instead based on `group` and `weight`

## Compatibility

| NetBox Version | Plugin Version |
|----------------|----------------|
|     3.5        |      0.1.0     |


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
    "netbox_script_manager": {
        "SCRIPT_ROOT": "/path/to/script/folder/",
        "DEFAULT_QUEUE": "high"
    },
}
```

## Configuration

The following options are required:

* `SCRIPT_ROOT`: Path to the script folder containing the customscripts module. 

The following options are optional:

* `DEFAULT_QUEUE`: Specifies what queue scripts are run in by default. Defaults to the `default` queue.


## Migrating scripts

The most important change is to change the import and name of the base `Script` class.

Netbox Script:

```python
from extras.scripts import Script

class MyCustomScript(Script):
...
```

Netbox Script Manager Script:

```python
from netbox_script_manager.scripts import CustomScript

class MyCustomScript(CustomScript):
...
```

It is strongly recommended to do relative imports in your scripts, when using a nested structure or utility code.

```python
from .util import my_utility_method
from ..subfolder import myCustomScript
```

The alternative is to do an absolute import:

```python
from customscripts.nested_folder.util import my_utility_method
from customscripts.subfolder import myCustomScript
```

Please see the `Script folder` section for instructions regarding folder structure.

## Script folder

The loading of scripts is a little different with netbox-script-manager. The `SCRIPT_ROOT` plugin setting must be set to define the path of the custom scripts, however the scripts must be located in a folder named `customscripts` in this path.

A folder structure like this is required (`SCRIPT_ROOT` pointing to the `netboxscripts` folder):

```bash
├── netboxscripts # SCRIPT_ROOT
│   ├── customscripts # Scripts will be discovered in this module, must be present
│   │   ├── __init__.py
│   │   ├── nestedmodule
│   │   ├── root_script.py
│   │   └── util
│   └── __init__.py
```

The reason for requiring this layout with a `customscripts` folder is to avoid name collisions when dynamically loading scripts. It also makes it easier to clear the internal python module cache which is needed for reloading scripts.

Loading scripts is done either through the UI by pressing the `Load Scripts` button on the script view, or by calling the API endpoint `/api/plugins/script-manager/script-instances/load/`. Both of these require that the user has the `Can Add` action for the `Script Instance` object permission.

## Git Sync

> :grey_exclamation: git must be installed on the system.

> :grey_exclamation: The netbox user must have the `sync` additional action for the `Script Instance` object permission.

> :warning: git recurses parent directories until finding a git directory. Make sure the `SCRIPT_ROOT` is a git directory.

Netbox Script Manager has basic support for pulling down changes for git repositories. The Sync button is located on the script list and simply calls `git pull` on in the `SCRIPT_ROOT/customscripts` folder. If the git reposity requires authentication, it's recommended to setup SSH auth for the repo and provide the key in the users `$HOME/.ssh` folder.

If more advanced syncing is required, its recommended to handle this outside of netbox or alternatively use a custom script to do the sync.

## Screenshots

TODO
