"""
management/commands/routes.py
------------------------------
Usage:
    python manage.py routes
    python manage.py routes --app users
    python manage.py routes --search login
    python manage.py routes --format json
    python manage.py routes --format markdown
    python manage.py routes --format markdown --output api_docs.md
    python manage.py routes --format markdown --per-app
    python manage.py routes --include-admin
    python manage.py routes --no-color
"""

from __future__ import annotations

import os
from collections import defaultdict

from django.core.management.base import BaseCommand

from drf_routes.utils.resolver import get_all_routes
from drf_routes.utils.formatter import render


class Command(BaseCommand):
    help = "List all registered URL routes (DRF-aware). Like `rails routes` for Django."

    def add_arguments(self, parser):
        parser.add_argument(
            "--app",
            dest="app",
            default=None,
            metavar="APP_NAME",
            help="Filter routes by Django app name or module (e.g. --app users).",
        )
        parser.add_argument(
            "--search",
            dest="search",
            default=None,
            metavar="TERM",
            help="Search routes by URL pattern or view name (case-insensitive).",
        )
        parser.add_argument(
            "--format",
            dest="format",
            default="table",
            choices=["table", "json", "markdown"],
            help="Output format: 'table' (default), 'json', or 'markdown'.",
        )
        parser.add_argument(
            "--include-admin",
            dest="include_admin",
            action="store_true",
            default=False,
            help="Include Django admin routes (hidden by default).",
        )
        parser.add_argument(
            "--output",
            dest="output",
            default=None,
            metavar="FILE",
            help=(
                "Write output to a file instead of stdout. "
                "Defaults to 'api_docs.md' when --format markdown is used without a filename. "
                "Ignored when --per-app is set."
            ),
        )
        parser.add_argument(
            "--project-name",
            dest="project_name",
            default=None,
            metavar="NAME",
            help=(
                "Project name used in the markdown document title. "
                "Defaults to the value of settings.ROOT_URLCONF project prefix."
            ),
        )
        parser.add_argument(
            "--per-app",
            dest="per_app",
            action="store_true",
            default=False,
            help=(
                "Generate a separate api_docs.md inside each Django app directory. "
                "Only works with --format markdown."
            ),
        )

    # ──────────────────────────────────────────────────────────
    #  Helpers
    # ──────────────────────────────────────────────────────────

    def _resolve_project_name(self, supplied: str | None) -> str:
        if supplied:
            return supplied
        try:
            from django.conf import settings
            root = getattr(settings, "ROOT_URLCONF", "")
            return root.split(".")[0].replace("_", " ").title() if root else "Django"
        except Exception:
            return "Django"

    def _get_app_path(self, app_name: str) -> str | None:
        """Return the filesystem path of a Django app, or None if not found."""
        try:
            from django.apps import apps
            config = apps.get_app_config(app_name)
            return config.path
        except LookupError:
            return None

    def _write_file(self, path: str, content: str) -> bool:
        """Write content to path. Returns True on success, prints error on failure."""
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
            return True
        except OSError as e:
            self.stderr.write(self.style.ERROR(f"Failed to write {path}: {e}"))
            return False

    # ──────────────────────────────────────────────────────────
    #  Per-app markdown generation
    # ──────────────────────────────────────────────────────────

    def _handle_per_app(self, routes, project_name: str) -> None:
        """Split routes by app and write api_docs.md inside each app directory."""
        from drf_routes.utils.formatter_md import format_markdown

        grouped: dict[str, list] = defaultdict(list)
        for r in routes:
            grouped[r.app_name or ""].append(r)

        if not grouped:
            self.stdout.write(self.style.WARNING("No routes found."))
            return

        written = 0
        skipped = 0

        for app_name, app_routes in sorted(grouped.items()):
            if not app_name:
                # Routes with no app label — skip or warn
                self.stdout.write(
                    self.style.WARNING(
                        f"  ⚠️  {len(app_routes)} route(s) have no app label — skipped."
                    )
                )
                skipped += len(app_routes)
                continue

            app_path = self._get_app_path(app_name)
            if not app_path:
                self.stdout.write(
                    self.style.WARNING(
                        f"  ⚠️  Could not resolve path for app '{app_name}' — skipped."
                    )
                )
                skipped += len(app_routes)
                continue

            doc_path = os.path.join(app_path, "api_docs.md")
            app_title = f"{project_name} — {app_name.replace('_', ' ').title()} API"
            content = format_markdown(app_routes, project_name=app_title)

            if self._write_file(doc_path, content):
                self.stdout.write(
                    self.style.SUCCESS(
                        f"  ✅ [{app_name}] {len(app_routes)} route(s) → {doc_path}"
                    )
                )
                written += 1

        self.stdout.write("")
        self.stdout.write(
            self.style.SUCCESS(
                f"Done. {written} app doc(s) written."
            )
            + (f"  {skipped} route(s) skipped." if skipped else "")
        )

    # ──────────────────────────────────────────────────────────
    #  Main handler
    # ──────────────────────────────────────────────────────────

    def handle(self, *args, **options):
        app_filter    = options["app"]
        search        = options["search"]
        fmt           = options["format"]
        include_admin = options["include_admin"]
        no_color      = options["no_color"]
        output_path   = options["output"]
        per_app       = options["per_app"]
        project_name  = self._resolve_project_name(options["project_name"])

        # --per-app only makes sense with markdown
        if per_app and fmt != "markdown":
            self.stderr.write(
                self.style.ERROR("--per-app can only be used with --format markdown.")
            )
            raise SystemExit(1)

        # Default output filename for single-file markdown
        if fmt == "markdown" and not per_app and output_path is None:
            output_path = "api_docs.md"

        try:
            routes = get_all_routes(
                filter_app=app_filter,
                search=search,
                include_admin=include_admin,
            )
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"Error resolving routes: {e}"))
            raise SystemExit(1)

        if not routes:
            self.stdout.write(self.style.WARNING("No routes found matching your filters."))
            return

        # ── Per-app mode ──────────────────────────────────────
        if per_app:
            self.stdout.write(
                self.style.HTTP_INFO(
                    f"Generating per-app API docs for {len(routes)} route(s)...\n"
                )
            )
            self._handle_per_app(routes, project_name)
            return

        # ── Single output mode ────────────────────────────────
        output = render(routes, fmt=fmt, no_color=no_color, project_name=project_name)

        # Rich table prints directly — nothing further to do
        if output is None:
            return

        if output_path:
            abs_path = os.path.abspath(output_path)
            if self._write_file(abs_path, output):
                self.stdout.write(
                    self.style.SUCCESS(f"✅ API docs written to: {abs_path}")
                )
        else:
            self.stdout.write(output)