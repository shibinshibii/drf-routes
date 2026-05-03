import pytest
from drf_routes.utils.inspector import inspect_view
from tests.urls import MeView, UserViewSet

def test_inspect_view_extra_fields():
    # Test a view with serializer (MeView has serializer_class = UserSerializer)
    # We pass the view function and the URL
    view = MeView.as_view()
    v_name, mod, methods, s_name, is_drf, extra = inspect_view(view, "/api/auth/me/")
    
    assert extra["docstring"] is None or isinstance(extra["docstring"], str)
    assert "serializer_fields" in extra
    assert len(extra["serializer_fields"]) > 0
    assert extra["serializer_fields"][0]["name"] == "id"
    
    assert "query_params" in extra
    assert "response_example" in extra
    assert "permissions_detailed" in extra

def test_inspect_viewset_list_detection():
    # Test UserViewSet list action
    view = UserViewSet.as_view({'get': 'list'})
    _, _, _, _, _, extra = inspect_view(view, "/api/users/")
    assert extra["is_list_view"] is True

def test_inspect_viewset_detail_detection():
    # Test UserViewSet retrieve action
    view = UserViewSet.as_view({'get': 'retrieve'})
    _, _, _, _, _, extra = inspect_view(view, "/api/users/{pk}/")
    assert extra["is_list_view"] is False

def test_query_params_extraction():
    # We could mock a view with filterset_fields to test extraction
    from rest_framework.views import APIView
    class FilteredView(APIView):
        filterset_fields = ["status", "category"]
    
    _, _, _, _, _, extra = inspect_view(FilteredView.as_view(), "/api/filter/")
    param_names = [p["name"] for p in extra["query_params"]]
    assert "status" in param_names
    assert "category" in param_names
