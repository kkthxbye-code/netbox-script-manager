import inspect
import pkgutil
import sys
import threading

from django.conf import settings

# TODO: Refactor these settings
plugin_config = settings.PLUGINS_CONFIG.get("netbox_script_manager")
script_root = plugin_config.get("SCRIPT_ROOT") if plugin_config else None
custom_script_root = f"{script_root}/customscripts"

lock = threading.Lock()

sys.path.append(script_root)


def is_script(obj):
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
    with lock:
        clear_module_cache()
        scripts = {}
        modules = list(pkgutil.iter_modules([custom_script_root]))

        for importer, module_name, _ in modules:
            module_name = "customscripts." + module_name
            try:
                module = importer.find_module(module_name).load_module(module_name)
            except Exception as e:
                # TODO: Error handling
                print(f"Failed to load module {module_name}: {e}")
                import traceback

                traceback.print_exc()

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
