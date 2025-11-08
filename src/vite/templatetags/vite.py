from django import template
from django.conf import settings

from vite import get_config

register = template.Library()


def get_manifest():
    """Load and return the Vite manifest as a dictionary."""
    import json
    from pathlib import Path

    manifest_path = Path(get_config("VITE_MANIFEST_PATH"))
    with manifest_path.open() as f:
        manifest = json.load(f)
    return manifest


@register.inclusion_tag("vite/tags/enable_vite_tags.html")
def enable_vite(entry="index.html"):
    manifest = get_manifest()
    js_src = manifest.get(entry, {}).get("file", "")
    css_src = manifest.get(entry, {}).get("css", [])

    return {
        "vite_js_entry": get_config("VITE_JS_ENTRYPOINT"),
        "vite_css_entry": get_config("VITE_CSS_ENTRYPOINT"),
        "vite_hmr": f"{get_config('VITE_DEV_SERVER_URL')}/@vite/client" if get_config("VITE_DEV_MODE") else None,
        "js_src": js_src,
        "css_src": css_src,
        "django_dev": getattr(settings, "DEBUG", True),
    }
