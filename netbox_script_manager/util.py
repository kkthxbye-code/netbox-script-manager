import inspect
import logging
import os
import pkgutil
import subprocess
import sys
import threading

from django.conf import settings
from utilities.utils import normalize_querydict

logger = logging.getLogger("netbox.plugins.netbox_script_manager")

# Timeout of git system commands in seconds
GIT_TIMEOUT = 5

# Fields not included when saving script input
EXCLUDED_POST_FIELDS = ["csrfmiddlewaretoken", "_schedule_at", "_interval", "_run", "_commit"]

# Name of the subpackage where custom scripts are stored
CUSTOM_SCRIPT_SUBPACKAGE = "customscripts"

plugin_config = settings.PLUGINS_CONFIG.get("netbox_script_manager")
script_root = plugin_config.get("SCRIPT_ROOT") if plugin_config else None

# The script root is appended with customscripts as this is the supported structure of the plugin
# The main reason is to avoid name collisions with the built-in netbox apps
custom_script_root = os.path.join(script_root, CUSTOM_SCRIPT_SUBPACKAGE)

# The custom script root needs to be appended to the path for relative imports to work properly
sys.path.append(script_root)

lock = threading.Lock()


def is_script(obj):
    """
    Used to identify custom scripts that work with the plugin.
    """
    from .scripts import CustomScript

    try:
        return issubclass(obj, CustomScript) and obj != CustomScript
    except TypeError:
        return False


def load_scripts():
    """
    Loads scripts from the SCRIPT_ROOT. To avoid potential name collisons, scripts are loaded from a subpackage named customscripts.
    The function returns a list of all scripts in the following format:

    ```
    {
        "module_path.class_name": ScriptClass,
        "module_path.class_name": ScriptClass2
    }
    ```
    """
    # Deleting from sys.modules and reloading the module is not thread-safe so we wrap it all in a lock.
    with lock:
        # Always start by clearing the module cache. Not clearing the cache presents issues with script inputs.
        clear_module_cache()

        scripts = {}
        modules = list(pkgutil.iter_modules([custom_script_root]))
        failed_modules = {}

        # Iterate over all modules in the custom script root
        for importer, module_name, _ in modules:
            # We need to manually prepend the subpackage name to the module name to get the full module path
            module_name = f"{CUSTOM_SCRIPT_SUBPACKAGE}.{module_name}"

            try:
                # Manually load the module
                module = importer.find_module(module_name).load_module(module_name)
            except Exception as e:
                failed_modules[module_name] = e
                logger.warning(f"Failed to load module {module_name}: {e}")
                logger.exception(e)
                continue

            # Find all CustomScript members
            for name, cls in inspect.getmembers(module, is_script):
                scripts[f"{module.__name__}.{name}"] = cls

        return scripts, failed_modules


def clear_module_cache():
    """
    Clears the module cache to prevent changes to script inputs being ignored.
    """
    for module_name in list(sys.modules.keys()):
        if module_name.startswith("customscripts"):
            del sys.modules[module_name]


def prepare_post_data(request):
    """
    Normalize QueryDict to a normal dict and remove unwanted fields.
    """
    if not hasattr(request, "POST"):
        return None

    post_data = normalize_querydict(request.POST)

    # Remove unwanted elements
    for field in EXCLUDED_POST_FIELDS:
        post_data.pop(field, None)

    return post_data


def pull_scripts():
    """
    Pulls the git repository at the custom script root.
    While dulwich could have been used here, there are some pretty stark limitations
    to what dulwich supports. The simplest approach was just to call the system git command.
    """
    try:
        result = subprocess.run(
            ["git", "pull"],
            cwd=custom_script_root,  # git recursively checks parent folders until it finds a git directory
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,  # git uses stderr as stdout for some reason
            timeout=GIT_TIMEOUT,  # As we currently don't background this, we need a fairly low timeout
        )
        return result.stdout.decode()
    except subprocess.CalledProcessError as e:
        raise ValueError(f"Failed to pull git repository at {custom_script_root}: {e.output.decode()}")
