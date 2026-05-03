import pytest
from drf_routes.utils.resolver import get_all_routes
from drf_routes.utils.formatter_md import format_markdown

@pytest.fixture
def routes():
    return get_all_routes()

def test_render_markdown_returns_string(routes):
    md = format_markdown(routes)
    assert isinstance(md, str)
    assert "API Reference" in md

def test_request_schema_section_present(routes):
    md = format_markdown(routes)
    # MeView has a serializer in tests/urls.py
    assert "Request Schema" in md
    # We strip "Field" from the type in the formatter
    assert "Integer" in md

def test_response_examples_present(routes):
    md = format_markdown(routes)
    assert "Response Examples" in md
    assert "Success `200 OK`" in md

def test_common_error_states_present(routes):
    md = format_markdown(routes)
    assert "Common Error States" in md
    assert "400 Bad Request" in md
    assert "401 Unauthorized" in md
