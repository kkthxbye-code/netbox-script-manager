"""Top-level package for NetBox Script Manager Plugin."""

__author__ = """Simon Toft"""
__email__ = "festll234@gmail.com"
__version__ = "0.3.13"


from extras.plugins import PluginConfig


class NetboxScriptManagerConfig(PluginConfig):
    name = "netbox_script_manager"
    verbose_name = "Script Manager"
    description = "Improved custom script support for netbox"
    version = "0.3.13"
    base_url = "script-manager"
    default_settings = {
        "DEFAULT_QUEUE": "default",
    }
    required_settings = ["SCRIPT_ROOT"]
    min_version = "3.5.0"


config = NetboxScriptManagerConfig

# To allow comitting script logs inside the transaction of a running script,
# we must use a seperate database connection.
from django.db import connections  # noqa: E402

connections.databases["script_log"] = connections.databases["default"]
