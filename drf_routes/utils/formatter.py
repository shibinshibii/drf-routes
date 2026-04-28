"""
formatter.py
------------
Renders a list of RouteInfo objects into either:
  - A pretty table  (with `rich` if installed, plain ASCII fallback otherwise)
  - JSON output
"""

from __future__ import annotations

import json
from typing import Optional
from drf_routes.utils.resolver import RouteInfo

# Method color map for rich output
METHOD_COLORS = {
    "GET":     "green",
    "POST":    "blue",
    "PUT":     "yellow",
    "PATCH":   "cyan",
    "DELETE":  "red",
    "HEAD":    "dim",
    "OPTIONS": "dim",
}

# Column config: (header, attribute, max_width)
COLUMNS = [
    ("URL",         "url",              50),
    ("Methods",     "http_methods",     24),
    ("View",        "view_name",        30),
    ("Serializer",  "serializer_class", 25),
    ("Name",        "name",             25),
]


# ──────────────────────────────────────────────
#  JSON formatter
# ──────────────────────────────────────────────

def format_json(routes: list[RouteInfo], indent: int = 2) -> str:
    data = [
        {
            "url":              r.url,
            "name":             r.name,
            "view":             r.view_name,
            "module":           r.module,
            "methods":          r.http_methods,
            "serializer":       r.serializer_class,
            "app":              r.app_name,
            "is_drf":           r.is_drf,
        }
        for r in routes
    ]
    return json.dumps(data, indent=indent)


# ──────────────────────────────────────────────
#  Rich table formatter
# ──────────────────────────────────────────────

def _format_methods_rich(methods: list[str]) -> str:
    """Return a rich markup string for methods, each in its own color."""
    if not methods:
        return "[dim]—[/dim]"
    parts = []
    for m in methods:
        color = METHOD_COLORS.get(m, "white")
        parts.append(f"[{color}]{m}[/{color}]")
    return " ".join(parts)


def format_rich(routes: list[RouteInfo], no_color: bool = False) -> None:
    """Print a styled Rich table to stdout."""
    from rich.console import Console
    from rich.table import Table
    from rich import box

    console = Console(no_color=no_color, highlight=False)

    if not routes:
        console.print("[yellow]No routes found.[/yellow]")
        return

    table = Table(
        box=box.ROUNDED,
        show_header=True,
        header_style="bold white",
        border_style="bright_black",
        title="[bold cyan]DRF Route Map[/bold cyan]",
        title_justify="left",
        pad_edge=True,
        expand=False,
    )

    table.add_column("URL",        style="bright_white", max_width=52, no_wrap=False)
    table.add_column("Methods",    max_width=28, no_wrap=True)
    table.add_column("View",       style="magenta", max_width=32, no_wrap=True)
    table.add_column("Serializer", style="cyan", max_width=28, no_wrap=True)
    table.add_column("Name",       style="dim", max_width=28, no_wrap=True)

    for r in routes:
        methods_str = _format_methods_rich(r.http_methods) if not no_color else " ".join(r.http_methods) or "—"
        table.add_row(
            r.url,
            methods_str,
            r.view_name or "—",
            r.serializer_class or "[dim]—[/dim]",
            r.name or "[dim]—[/dim]",
        )

    console.print()
    console.print(table)
    console.print(f"  [dim]{len(routes)} route(s) found.[/dim]\n")


# ──────────────────────────────────────────────
#  Plain ASCII table formatter (no rich)
# ──────────────────────────────────────────────

def _truncate(value: Optional[str], width: int) -> str:
    if not value:
        return "—".ljust(width)
    if len(value) > width:
        return value[: width - 1] + "…"
    return value.ljust(width)


def format_plain(routes: list[RouteInfo]) -> str:
    if not routes:
        return "No routes found."

    widths = [col[2] for col in COLUMNS]
    headers = [col[0] for col in COLUMNS]

    sep = "+" + "+".join("-" * (w + 2) for w in widths) + "+"
    header_row = "|" + "|".join(f" {h.ljust(w)} " for h, w in zip(headers, widths)) + "|"

    lines = [sep, header_row, sep]

    for r in routes:
        methods_str = " ".join(r.http_methods) if r.http_methods else "—"
        values = [
            r.url,
            methods_str,
            r.view_name,
            r.serializer_class,
            r.name,
        ]
        row = "|" + "|".join(f" {_truncate(v, w)} " for v, w in zip(values, widths)) + "|"
        lines.append(row)

    lines.append(sep)
    lines.append(f"\n{len(routes)} route(s) found.")
    return "\n".join(lines)


# ──────────────────────────────────────────────
#  Public entry point
# ──────────────────────────────────────────────

def render(
    routes: list[RouteInfo],
    fmt: str = "table",
    no_color: bool = False,
    project_name: str = "Django",
) -> Optional[str]:
    """
    Render routes in the chosen format.

    Args:
        routes:       List of RouteInfo objects.
        fmt:          'table', 'json', or 'markdown'.
        no_color:     Disable color output (table mode only).
        project_name: Used in the markdown document title.

    Returns:
        A string for 'json', 'markdown', and plain 'table' modes.
        None for rich table mode (prints directly to stdout).
    """
    if fmt == "json":
        return format_json(routes)

    if fmt == "markdown":
        from drf_routes.utils.formatter_md import format_markdown
        return format_markdown(routes, project_name=project_name)

    # Table mode
    try:
        import rich  # noqa: F401
        format_rich(routes, no_color=no_color)
        return None
    except ImportError:
        return format_plain(routes)