import json
import traceback

from django import template
from utilities.utils import dict_to_querydict

register = template.Library()


@register.filter
def format_exception(e):
    return "".join(traceback.format_exception(e))


@register.filter
def pretty_json(value):
    return json.dumps(value, indent=4)


@register.filter
def urlencode_dict(value):
    try:
        qd = dict_to_querydict(value)
        return f"?{qd.urlencode()}"
    except Exception:
        return ""


@register.inclusion_tag("netbox_script_manager/script_artifact_htmx_table.html", takes_context=True)
def htmx_table(context, viewname, return_url=None, **kwargs):
    """
    Embed an object list table retrieved using HTMX. Any extra keyword arguments are passed as URL query parameters.

    Args:
        context: The current request context
        viewname: The name of the view to use for the HTMX request (e.g. `dcim:site_list`)
        return_url: The URL to pass as the `return_url`. If not provided, the current request's path will be used.
    """
    url_params = dict_to_querydict(kwargs)
    url_params["return_url"] = return_url or context["request"].path
    return {
        "viewname": viewname,
        "url_params": url_params,
    }
