"""
inspector.py
------------
Introspects a view callable and extracts:
  - View class/function name
  - Module path
  - Allowed HTTP methods
  - Serializer class name (DRF only)
  - Whether it's a DRF view
  - Docstring
  - Permission classes
  - Authentication classes
  - Filter / search / ordering fields
  - Pagination class
  - Path parameters (parsed from URL)
"""

from __future__ import annotations

import inspect
from typing import Any, Optional

# HTTP methods we care about — in display order
ALL_HTTP_METHODS = ["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"]


def _is_drf_view(view: Any) -> bool:
    """Check if a view is a DRF APIView or ViewSet."""
    try:
        from rest_framework.views import APIView
        from rest_framework.viewsets import ViewSetMixin

        cls = _get_view_class(view)
        if cls is None:
            return False
        return issubclass(cls, (APIView, ViewSetMixin))
    except ImportError:
        return False


def _get_view_class(view: Any) -> Optional[type]:
    """
    Unwrap a view callable to get the underlying class, if any.
    Handles: as_view() closures, ViewSetMixin.as_view(), functools.partial, initkwargs.
    """
    # Direct class reference
    if inspect.isclass(view):
        return view

    # CBV: view.view_class is set by as_view()
    if hasattr(view, "view_class"):
        return view.view_class

    # ViewSet: cls attribute set during router registration
    if hasattr(view, "cls"):
        return view.cls

    # functools.partial wrapping
    if hasattr(view, "func"):
        return _get_view_class(view.func)

    return None


def _get_drf_methods(cls: type, view: Any) -> list[str]:
    """
    For a DRF view, determine the allowed HTTP methods.
    ViewSets expose `actions` dict on the bound view (e.g. {'get': 'list', 'post': 'create'}).
    APIViews expose defined handler methods directly on the class.
    """
    try:
        from rest_framework.viewsets import ViewSetMixin

        if issubclass(cls, ViewSetMixin):
            # The router binds actions as a dict on the view function
            actions: dict = getattr(view, "actions", {}) or getattr(view, "initkwargs", {}).get("actions", {})
            if actions:
                return sorted(
                    [m.upper() for m in actions.keys() if m.upper() in ALL_HTTP_METHODS]
                )
            # Fallback: inspect which action methods the viewset defines
            defined = []
            action_map = {
                "list": ["GET"],
                "create": ["POST"],
                "retrieve": ["GET"],
                "update": ["PUT"],
                "partial_update": ["PATCH"],
                "destroy": ["DELETE"],
            }
            for action, methods in action_map.items():
                if hasattr(cls, action):
                    defined.extend(methods)
            return sorted(set(defined))
    except ImportError:
        pass

    # APIView: check which HTTP verb methods are defined on the class
    defined = []
    for method in ALL_HTTP_METHODS:
        if hasattr(cls, method.lower()) and method.lower() in [
            m.lower() for m in (getattr(cls, "http_method_names", ALL_HTTP_METHODS))
        ]:
            defined.append(method)
    return defined


def _get_django_methods(view: Any) -> list[str]:
    """For plain Django views, extract http_method_names or infer from defined handlers."""
    cls = _get_view_class(view)
    if cls and hasattr(cls, "http_method_names"):
        return sorted(
            [m.upper() for m in cls.http_method_names if m.upper() in ALL_HTTP_METHODS]
        )
    # Function-based view — we can't easily know the methods
    return []


def _get_serializer_name(cls: type) -> Optional[str]:
    """Return the serializer_class name if the view defines one."""
    serializer_cls = getattr(cls, "serializer_class", None)
    if serializer_cls is None:
        return None
    return serializer_cls.__name__


def _get_view_name(view: Any, cls: Optional[type]) -> str:
    """Return a human-readable view name."""
    if cls:
        return cls.__name__
    # Function-based view
    return getattr(view, "__name__", str(view))


def _get_module(view: Any, cls: Optional[type]) -> str:
    """Return the dotted module path of the view."""
    target = cls or view
    return getattr(target, "__module__", "") or ""


def _get_docstring(cls: Optional[type]) -> Optional[str]:
    """Return the cleaned docstring of the view class, if any."""
    if cls is None:
        return None
    doc = inspect.getdoc(cls)
    return doc if doc else None


def _get_class_names(cls: Optional[type], attr: str) -> list[str]:
    """Return a list of class names from a view attribute (e.g. permission_classes)."""
    if cls is None:
        return []
    items = getattr(cls, attr, None)
    if not items:
        return []
    names = []
    for item in items:
        if inspect.isclass(item):
            names.append(item.__name__)
        else:
            names.append(type(item).__name__)
    return names


def _get_string_list(cls: Optional[type], attr: str) -> list[str]:
    """Return a list of strings from a view attribute (e.g. search_fields)."""
    if cls is None:
        return []
    value = getattr(cls, attr, None)
    if not value:
        return []
    return [str(v) for v in value]


def _get_pagination_class(cls: Optional[type]) -> Optional[str]:
    """Return the pagination_class name if set on the view."""
    if cls is None:
        return None
    pagination_cls = getattr(cls, "pagination_class", None)
    if pagination_cls is None:
        return None
    if inspect.isclass(pagination_cls):
        return pagination_cls.__name__
    return type(pagination_cls).__name__


def _get_path_params(url: str) -> list[str]:
    """Extract path parameter names from a URL string like /api/users/{id}/."""
    import re
    return re.findall(r"\{(\w+)\}", url)


def inspect_view(view: Any, url: str = "") -> tuple:
    """
    Inspect a view and return a dict of all extracted metadata.

    For backwards compatibility the first five positional values are:
      (view_name, module, http_methods, serializer_class_name, is_drf)

    The full dict is also returned as the 6th element for the markdown formatter.
    """
    cls = _get_view_class(view)
    is_drf = _is_drf_view(view)

    view_name = _get_view_name(view, cls)
    module = _get_module(view, cls)
    serializer_class = _get_serializer_name(cls) if (cls and is_drf) else None

    if is_drf and cls:
        http_methods = _get_drf_methods(cls, view)
    else:
        http_methods = _get_django_methods(view)

    extra = {
        "docstring":           _get_docstring(cls),
        "permission_classes":  _get_class_names(cls, "permission_classes"),
        "authentication_classes": _get_class_names(cls, "authentication_classes"),
        "filter_backends":     _get_class_names(cls, "filter_backends"),
        "search_fields":       _get_string_list(cls, "search_fields"),
        "ordering_fields":     _get_string_list(cls, "ordering_fields"),
        "filterset_fields":    _get_string_list(cls, "filterset_fields"),
        "pagination_class":    _get_pagination_class(cls),
        "path_params":         _get_path_params(url),
    }

    return view_name, module, http_methods, serializer_class, is_drf, extra