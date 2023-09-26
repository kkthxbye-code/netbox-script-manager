"""Top-level package for NetBox Script Manager Plugin."""

__author__ = """Simon Toft"""
__email__ = "toft1988@gmail.com"
__version__ = "0.1.0"


from extras.plugins import PluginConfig


class ScriptInstanceConfig(PluginConfig):
    name = "netbox_script_manager"
    verbose_name = "Script Manager"
    description = "Improved custom script support for netbox"
    version = "0.1"
    base_url = "script-manager"


config = ScriptInstanceConfig

from django.db import connections

connections.databases["script_log"] = connections.databases["default"]
