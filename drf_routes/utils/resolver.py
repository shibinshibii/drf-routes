"""
resolver.py
-----------
Walks Django's URL tree and returns a flat list of RouteInfo objects.
Handles:
  - Simple URL patterns (path / re_path)
  - Nested includes
  - DRF routers (SimpleRouter, DefaultRouter)
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Optional
from django.urls import URLPattern, URLResolver
from django.urls.resolvers import get_resolver


@dataclass
class RouteInfo:
    url: str
    name: Optional[str]
    view: Any                     # the raw view callable / class
    view_name: str
    module: str
    http_methods: list[str] = field(default_factory=list)
    serializer_class: Optional[str] = None
    app_name: Optional[str] = None
    is_drf: bool = False
    extra: dict = field(default_factory=dict)


def _clean_pattern(pattern: str) -> str:
    """Convert a regex pattern to a readable URL string."""
    # Remove regex anchors
    pattern = pattern.lstrip("^").rstrip("$")
    # Convert named groups (?P<pk>[^/.]+) → {pk}
    pattern = re.sub(r"\(\?P<(\w+)>[^)]+\)", r"{\1}", pattern)
    # Remove non-named groups
    pattern = re.sub(r"\([^)]+\)", "{param}", pattern)
    return pattern or "/"


def _get_pattern_str(pattern) -> str:
    """Extract the string representation of a URL pattern."""
    try:
        # Django 2+: RoutePattern vs RegexPattern
        if hasattr(pattern.pattern, "_route"):
            return pattern.pattern._route
        elif hasattr(pattern.pattern, "_regex"):
            return _clean_pattern(pattern.pattern._regex)
        else:
            return str(pattern.pattern)
    except Exception:
        return str(pattern.pattern)


def _infer_app_from_module(module: str) -> Optional[str]:
    """
    Infer a Django app label from a view's dotted module path.

    Walks all installed app configs and returns the label of the app
    whose module path is the longest prefix match for the given module.
    This handles projects that use plain include() without app_name namespacing.

    Example:
        module = 'users.views.profile'
        → matched app config with name='users', module='users'
        → returns 'users'
    """
    if not module:
        return None
    try:
        from django.apps import apps
        best_label: Optional[str] = None
        best_len = 0
        for config in apps.get_app_configs():
            # app module path e.g. 'users' or 'myproject.users'
            app_module = config.name
            if module == app_module or module.startswith(app_module + "."):
                if len(app_module) > best_len:
                    best_len = len(app_module)
                    best_label = config.label
        return best_label
    except Exception:
        return None


def _walk_patterns(
    patterns,
    prefix: str = "",
    app_name: Optional[str] = None,
) -> list[RouteInfo]:
    """Recursively walk urlpatterns and collect RouteInfo objects."""
    routes: list[RouteInfo] = []

    for pattern in patterns:
        current_prefix = prefix + _get_pattern_str(pattern)

        if isinstance(pattern, URLResolver):
            # It's an include() — recurse into it
            nested_app = getattr(pattern, "app_name", None) or app_name
            routes.extend(
                _walk_patterns(
                    pattern.url_patterns,
                    prefix=current_prefix,
                    app_name=nested_app,
                )
            )

        elif isinstance(pattern, URLPattern):
            view = pattern.callback
            route = _build_route_info(
                url=current_prefix,
                name=pattern.name,
                view=view,
                app_name=app_name,
            )
            routes.append(route)

    return routes


def _build_route_info(
    url: str,
    name: Optional[str],
    view: Any,
    app_name: Optional[str],
) -> RouteInfo:
    """Build a RouteInfo from a resolved URL pattern."""
    from drf_routes.utils.inspector import inspect_view

    view_name, module, http_methods, serializer_class, is_drf, extra = inspect_view(view, url=url)

    # Normalize URL
    if not url.startswith("/"):
        url = "/" + url
    # Remove double slashes
    url = re.sub(r"//+", "/", url)

    # Re-parse path params from the normalized URL
    extra["path_params"] = re.findall(r"\{(\w+)\}", url)

    # If no app_name came from URL namespacing, infer it from the view module
    resolved_app = app_name or _infer_app_from_module(module)

    return RouteInfo(
        url=url,
        name=name,
        view=view,
        view_name=view_name,
        module=module,
        http_methods=http_methods,
        serializer_class=serializer_class,
        app_name=resolved_app,
        is_drf=is_drf,
        extra=extra,
    )


def get_all_routes(
    urlconf=None,
    filter_app: Optional[str] = None,
    search: Optional[str] = None,
    include_admin: bool = False,
) -> list[RouteInfo]:
    """
    Entry point. Returns all routes as a flat list of RouteInfo.

    Args:
        urlconf:       Custom urlconf module (defaults to ROOT_URLCONF).
        filter_app:    Only return routes from this Django app name.
        search:        Filter by URL or view name (case-insensitive substring).
        include_admin: Include Django admin routes (default: False).
    """
    resolver = get_resolver(urlconf)
    routes = _walk_patterns(resolver.url_patterns)

    if not include_admin:
        routes = [r for r in routes if not r.url.startswith("/admin")]

    if filter_app:
        routes = [
            r for r in routes
            if (r.app_name or "").lower() == filter_app.lower()
            or filter_app.lower() in (r.module or "").lower()
        ]

    if search:
        term = search.lower()
        routes = [
            r for r in routes
            if term in r.url.lower()
            or term in (r.view_name or "").lower()
            or term in (r.name or "").lower()
        ]

    return routes