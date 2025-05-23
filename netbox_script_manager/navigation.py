from netbox.plugins import PluginMenuButton, PluginMenuItem

menu_items = (
    PluginMenuItem(
        link="plugins:netbox_script_manager:scriptinstance_list",
        link_text="Scripts",
        permissions=["netbox_script_manager.view_scriptinstance"],
        buttons=(
            PluginMenuButton(
                link="plugins:netbox_script_manager:scriptinstance_load",
                title="Load Scripts",
                icon_class="mdi mdi-refresh",
                permissions=["netbox_script_manager.add_scriptinstance"],
            ),
        ),
    ),
    PluginMenuItem(
        link="plugins:netbox_script_manager:scriptexecution_list",
        link_text="Executions",
        permissions=["netbox_script_manager.view_scriptexecution"],
    ),
)
