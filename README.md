# NetBox Script Manager Plugin

Improved custom script support for netbox


* Free software: MIT
* Documentation: https://kkthxbye-code.github.io/netbox-plugin-script-manager/


## Features

The features the plugin provides should be listed here.

## Compatibility

| NetBox Version | Plugin Version |
|----------------|----------------|
|     3.4        |      0.1.0     |

## Installing

For adding to a NetBox Docker setup see
[the general instructions for using netbox-docker with plugins](https://github.com/netbox-community/netbox-docker/wiki/Using-Netbox-Plugins).

While this is still in development and not yet on pypi you can install with pip:

```bash
pip install git+https://github.com/kkthxbye-code/netbox_script_manager
```

or by adding to your `local_requirements.txt` or `plugin_requirements.txt` (netbox-docker):

```bash
git+https://github.com/kkthxbye-code/netbox_script_manager
```

Enable the plugin in `/opt/netbox/netbox/netbox/configuration.py`,
 or if you use netbox-docker, your `/configuration/plugins.py` file :

```python
PLUGINS = [
    'Script Manager'
]

PLUGINS_CONFIG = {
    "Script Manager": {},
}
```
