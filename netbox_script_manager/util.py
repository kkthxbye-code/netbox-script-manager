import inspect
import pkgutil
import sys
import threading

from django.conf import settings

from utilities.utils import copy_safe_request, normalize_querydict

# Fields not included when saving script input
EXCLUDED_POST_FIELDS = ["csrfmiddlewaretoken", "_schedule_at", "_interval", "_run"]

# Name of the subpackage where custom scripts are stored
CUSTOM_SCRIPT_SUBPACKAGE = "customscripts"

plugin_config = settings.PLUGINS_CONFIG.get("netbox_script_manager")
script_root = plugin_config.get("SCRIPT_ROOT") if plugin_config else None

# The script root is appended with customscripts as this is the supported structure of the plugin
# The main reason is to avoid name collisions with the built-in netbox apps
custom_script_root = f"{script_root}/{CUSTOM_SCRIPT_SUBPACKAGE}"

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

        # Iterate over all modules in the custom script root
        for importer, module_name, _ in modules:
            # We need to manually prepend the subpackage name to the module name to get the full module path
            # TODO: There might be a better way of doing this.
            module_name = f"{CUSTOM_SCRIPT_SUBPACKAGE}.{module_name}"

            try:
                # Manually load the module
                module = importer.find_module(module_name).load_module(module_name)
            except Exception as e:
                # TODO: Error handling
                print(f"Failed to load module {module_name}: {e}")
                import traceback

                traceback.print_exc()

            # Find all CustomScript members
            for name, cls in inspect.getmembers(module, is_script):
                scripts[f"{module.__name__}.{name}"] = cls

        return scripts


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
    post_data = normalize_querydict(request.POST)

    # Remove unwanted elements
    for field in EXCLUDED_POST_FIELDS:
        post_data.pop(field, None)

    return post_data
