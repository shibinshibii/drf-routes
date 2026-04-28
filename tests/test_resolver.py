import pytest
from drf_routes.utils.resolver import get_all_routes


@pytest.fixture
def routes():
    return get_all_routes(include_admin=False)


def test_returns_list(routes):
    assert isinstance(routes, list)
    assert len(routes) > 0


def test_route_has_required_fields(routes):
    for r in routes:
        assert hasattr(r, "url")
        assert hasattr(r, "view_name")
        assert hasattr(r, "http_methods")
        assert hasattr(r, "is_drf")


def test_urls_start_with_slash(routes):
    for r in routes:
        assert r.url.startswith("/"), f"URL missing leading slash: {r.url}"


def test_drf_routes_detected(routes):
    drf_routes = [r for r in routes if r.is_drf]
    assert len(drf_routes) > 0, "Expected at least one DRF route"


def test_user_viewset_routes_present(routes):
    user_routes = [r for r in routes if "users" in r.url]
    assert len(user_routes) >= 2, "Expected list + detail routes for UserViewSet"


def test_login_view_present(routes):
    login_routes = [r for r in routes if "login" in r.url]
    assert len(login_routes) == 1


def test_health_check_present(routes):
    health = [r for r in routes if "health" in r.url]
    assert len(health) == 1
    assert not health[0].is_drf


def test_filter_by_search(routes):
    results = get_all_routes(search="login")
    assert all("login" in r.url.lower() or "login" in (r.name or "").lower() for r in results)


def test_admin_excluded_by_default(routes):
    admin = [r for r in routes if r.url.startswith("/admin")]
    assert len(admin) == 0


def test_include_admin(routes):
    all_routes = get_all_routes(include_admin=True)
    # Our test URLs don't include admin, so count should be same
    # but the flag should not crash
    assert isinstance(all_routes, list)