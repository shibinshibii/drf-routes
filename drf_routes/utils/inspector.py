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


def _get_serializer_class(cls: type) -> Optional[type]:
    """
    Try to find the serializer class used by the view.
    Checks for:
      - serializer_class
      - request_serializer / response_serializer
      - Static analysis of handler methods (post, put, patch)
    """
    # 1. Standard DRF attribute
    serializer_cls = getattr(cls, "serializer_class", None)
    if serializer_cls:
        return serializer_cls

    # 2. Common custom attributes
    for attr in ["request_serializer", "response_serializer"]:
        serializer_cls = getattr(cls, attr, None)
        if serializer_cls:
            return serializer_cls

    # 3. Static analysis (for APIView subclasses)
    try:
        import re
        methods = ["post", "put", "patch"]
        for m_name in methods:
            method = getattr(cls, m_name, None)
            if not method:
                continue
            source = inspect.getsource(method)
            # Find PatternSerializer( or PatternSerializer. or serializers.PatternSerializer(
            # We look for something that ends in Serializer followed by (
            matches = re.findall(r'([\w\.]+Serializer)\(', source)
            if matches:
                module = inspect.getmodule(cls)
                if module:
                    for serializer_path in matches:
                        # Try to resolve the path (e.g. 'serializers.MySerializer')
                        parts = serializer_path.split('.')
                        target = module
                        for part in parts:
                            target = getattr(target, part, None)
                            if target is None:
                                break
                        
                        if target and inspect.isclass(target):
                            return target
    except Exception:
        pass

    return None


def _get_serializer_name(serializer_cls: Optional[type]) -> Optional[str]:
    """Return the serializer class name."""
    if serializer_cls is None:
        return None
    return serializer_cls.__name__


def _get_serializer_fields(serializer_cls: type) -> list[dict]:
    """Extract metadata for each field in the serializer."""
    try:
        # Avoid circular imports or errors if DRF is missing
        from rest_framework.serializers import BaseSerializer
        if not issubclass(serializer_cls, BaseSerializer):
            return []

        # We try to get fields from the class's _declared_fields first.
        # This works for most cases without needing to instantiate.
        fields = getattr(serializer_cls, "_declared_fields", {})
        if not fields:
            # If it's a ModelSerializer or similar, _declared_fields might be empty.
            # We try to instantiate it with no data to trigger field generation.
            try:
                instance = serializer_cls()
                fields = getattr(instance, "fields", {})
            except Exception:
                return []

        field_data = []
        for name, field in fields.items():
            info = {
                "name":      name,
                "type":      type(field).__name__,
                "required":  getattr(field, "required", False),
                "read_only": getattr(field, "read_only", False),
                "label":     getattr(field, "label", None),
                "help_text": getattr(field, "help_text", None),
            }
            # Collect common validation rules
            for attr in ["min_value", "max_value", "min_length", "max_length"]:
                val = getattr(field, attr, None)
                if val is not None:
                    info[attr] = val

            # Choices
            choices = getattr(field, "choices", None)
            if choices:
                info["choices"] = list(choices.keys()) if hasattr(choices, "keys") else list(choices)

            field_data.append(info)
        return field_data
    except Exception:
        return []


def _is_list_view(view: Any, cls: Optional[type]) -> bool:
    """Determine if the view likely returns a list of objects."""
    # 1. ViewSet check (action-based)
    actions = getattr(view, "actions", {}) or getattr(view, "initkwargs", {}).get("actions", {})
    if actions and actions.get("get") == "list":
        return True

    if cls is None:
        return False

    # 2. Generic View check (inheritance-based)
    # Check if 'List' is in the class name or its base classes (e.g. ListAPIView, ListModelMixin)
    class_hierarchy = [c.__name__ for c in cls.__mro__]
    for name in class_hierarchy:
        if "List" in name:
            return True
    return False


def _generate_mock_data(serializer_cls: type, depth: int = 0) -> Any:
    """Generate mock JSON data based on serializer fields."""
    if depth > 3:
        return "..."

    try:
        from rest_framework.serializers import BaseSerializer, ListSerializer
        # Handle cases where serializer_cls might not be a class (unlikely here but safe)
        if not inspect.isclass(serializer_cls) or not issubclass(serializer_cls, BaseSerializer):
            return None

        # Try to get fields without full instantiation if possible
        fields = getattr(serializer_cls, "_declared_fields", {})
        if not fields:
            try:
                # Some fields only appear after instantiation (like ModelSerializer)
                instance = serializer_cls()
                fields = getattr(instance, "fields", {})
            except Exception:
                return {}

        mock_obj = {}
        for name, field in fields.items():
            # Skip write-only fields in response examples
            if getattr(field, "write_only", False):
                continue

            field_type = type(field).__name__

            # Handle nested serializers
            if hasattr(field, "fields"):
                mock_obj[name] = _generate_mock_data(type(field), depth + 1)
            elif isinstance(field, ListSerializer):
                child = getattr(field, "child", None)
                if child:
                    mock_obj[name] = [_generate_mock_data(type(child), depth + 1)]
                else:
                    mock_obj[name] = []
            elif "List" in field_type:
                mock_obj[name] = []
            elif "Integer" in field_type or "Decimal" in field_type or "Float" in field_type:
                mock_obj[name] = 0
            elif "Boolean" in field_type:
                mock_obj[name] = True
            elif "DateTime" in field_type:
                mock_obj[name] = "2023-10-27T10:00:00Z"
            elif "Date" in field_type:
                mock_obj[name] = "2023-10-27"
            elif "Email" in field_type:
                mock_obj[name] = "user@example.com"
            elif "UUID" in field_type:
                mock_obj[name] = "00000000-0000-0000-0000-000000000000"
            elif "URL" in field_type:
                mock_obj[name] = "https://example.com"
            else:
                mock_obj[name] = "string"

        return mock_obj
    except Exception:
        return {}
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
    """
    Return the cleaned docstring of the view class, if any.

    To avoid the "Base Class Docstring Trap", we ignore docstrings inherited
    from generic DRF or Django base classes (like APIView or GenericAPIView).
    """
    if cls is None:
        return None

    doc = inspect.getdoc(cls)
    if not doc:
        return None

    # Check if this docstring was inherited from a generic base class
    # We find which class in the MRO actually defines this docstring
    defining_class = None
    for base in cls.__mro__:
        # Compare against the cleandoc version of the base's docstring
        base_doc = getattr(base, "__doc__", None)
        if base_doc and inspect.cleandoc(base_doc) == doc:
            defining_class = base
            break

    if defining_class and defining_class is not cls:
        module = getattr(defining_class, "__module__", "")
        # Blacklist generic docstrings from these frameworks if they are inherited
        if module.startswith(("rest_framework.", "django.")):
            return None

    return doc


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


def _get_permission_info(cls: Optional[type]) -> list[dict]:
    """Extract detailed info about permission classes (names, docs, and custom logic)."""
    if cls is None:
        return []

    perms = getattr(cls, "permission_classes", None)
    if not perms:
        return []

    results = []
    for perm_cls in perms:
        # Resolve to class if it's an instance
        actual_cls = perm_cls if inspect.isclass(perm_cls) else type(perm_cls)

        info = {
            "name": actual_cls.__name__,
            "doc":  inspect.getdoc(actual_cls),
        }

        # For custom permissions, try to extract the logic summary
        module = getattr(actual_cls, "__module__", "")
        if not module.startswith("rest_framework.permissions"):
            try:
                # We look for has_permission or has_object_permission overrides
                logic = []
                for m_name in ["has_permission", "has_object_permission"]:
                    method = getattr(actual_cls, m_name, None)
                    if method:
                        # Check if the method itself is defined in a custom module
                        # (not in rest_framework.permissions)
                        method_module = getattr(inspect.getmodule(method), "__name__", "")
                        if not method_module.startswith("rest_framework.permissions"):
                            try:
                                source = inspect.getsource(method)
                                logic.append(inspect.cleandoc(source))
                            except Exception:
                                pass

                if logic:
                    info["logic"] = "\n\n".join(logic)
            except Exception:
                pass

        results.append(info)
    return results


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


def _get_query_params(cls: Optional[type]) -> list[dict]:
    """Extract query parameters (search, filters, ordering, pagination)."""
    if cls is None:
        return []

    params = []

    # 1. Search
    search_fields = getattr(cls, "search_fields", None)
    if search_fields:
        params.append({
            "name": "search",
            "type": "string",
            "description": f"Search by: {', '.join(map(str, search_fields))}"
        })

    # 2. Ordering
    ordering_fields = getattr(cls, "ordering_fields", None)
    if ordering_fields:
        params.append({
            "name": "ordering",
            "type": "string",
            "description": f"Order by: {', '.join(map(str, ordering_fields))}"
        })

    # 3. Filtering
    filterset_fields = getattr(cls, "filterset_fields", None)
    if filterset_fields:
        if isinstance(filterset_fields, dict):
            for field, lookups in filterset_fields.items():
                params.append({
                    "name": field,
                    "type": "filter",
                    "description": f"Filter by {field} (lookups: {', '.join(map(str, lookups))})"
                })
        else:
            for field in filterset_fields:
                params.append({
                    "name": field,
                    "type": "filter",
                    "description": f"Filter by {field}"
                })

    filterset_cls = getattr(cls, "filterset_class", None)
    if filterset_cls and hasattr(filterset_cls, "base_filters"):
        for field_name in filterset_cls.base_filters:
            # Avoid duplicates if also in filterset_fields
            if not any(p["name"] == field_name for p in params):
                params.append({
                    "name": field_name,
                    "type": "filter",
                    "description": f"Filter by {field_name}"
                })

    # 4. Pagination
    pagination_cls = getattr(cls, "pagination_class", None)
    if pagination_cls:
        p_inst = None
        try:
            if inspect.isclass(pagination_cls):
                p_inst = pagination_cls()
            else:
                p_inst = pagination_cls
        except Exception:
            pass

        if p_inst:
            # Common DRF pagination attributes
            if hasattr(p_inst, "page_query_param"):
                params.append({"name": p_inst.page_query_param, "type": "integer", "description": "Page number"})
            if getattr(p_inst, "page_size_query_param", None):
                params.append({"name": p_inst.page_size_query_param, "type": "integer", "description": "Number of results per page"})
            if hasattr(p_inst, "limit_query_param"):
                params.append({"name": p_inst.limit_query_param, "type": "integer", "description": "Number of results to return"})
            if hasattr(p_inst, "offset_query_param"):
                params.append({"name": p_inst.offset_query_param, "type": "integer", "description": "The initial index from which to return the results"})
            if hasattr(p_inst, "cursor_query_param"):
                params.append({"name": p_inst.cursor_query_param, "type": "string", "description": "The pagination cursor value"})

    return params


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

    serializer_cls = _get_serializer_class(cls) if (cls and is_drf) else None
    serializer_name = _get_serializer_name(serializer_cls)

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
        "serializer_fields":   _get_serializer_fields(serializer_cls) if serializer_cls else [],
        "query_params":        _get_query_params(cls),
        "response_example":    _generate_mock_data(serializer_cls) if serializer_cls else None,
        "is_list_view":        _is_list_view(view, cls),
        "permissions_detailed": _get_permission_info(cls),
    }

    return view_name, module, http_methods, serializer_name, is_drf, extra