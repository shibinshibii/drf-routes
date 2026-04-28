# drf-routes

**`python manage.py routes`** — A management command that lists all registered Django URL routes in a clean, readable table **and can generate a full API reference document**. DRF-aware: shows HTTP methods, serializers, permissions, filters, and more — automatically.

> Like `rails routes`, but for Django. With API docs.

---

## Why

Django has no built-in way to see all your registered routes at a glance. You have to trace through `urls.py` files manually. `drf-routes` solves this with a single command — and can generate a full Markdown API reference from your existing code with zero extra annotations.

```
╭──────────────────────────────────────────────────────────────────────────────────────────╮
│ DRF Route Map                                                                            │
├────────────────────────┬──────────────────────┬──────────────────┬─────────────────┬────┤
│ URL                    │ Methods              │ View             │ Serializer      │ Name│
├────────────────────────┼──────────────────────┼──────────────────┼─────────────────┼────┤
│ /api/users/            │ GET POST             │ UserViewSet      │ UserSerializer  │ …  │
│ /api/users/{id}/       │ GET PUT PATCH DELETE │ UserViewSet      │ UserSerializer  │ …  │
│ /api/posts/            │ GET POST             │ PostViewSet      │ PostSerializer  │ …  │
│ /api/auth/login/       │ POST                 │ LoginView        │ —               │ …  │
│ /health/               │ —                    │ health_check     │ —               │ …  │
╰────────────────────────┴──────────────────────┴──────────────────┴─────────────────┴────╯
```

---

## Install

```bash
pip install drf-routes
```

For colored output (recommended):

```bash
pip install drf-routes[pretty]
```

Add to `INSTALLED_APPS`:

```python
INSTALLED_APPS = [
    ...
    "drf_routes",
]
```

---

## Usage

```bash
# List all routes (rich table in terminal)
python manage.py routes

# Filter by app
python manage.py routes --app users

# Search by URL or view name
python manage.py routes --search login

# JSON output (pipe-friendly)
python manage.py routes --format json

# Generate a Markdown API reference (saved to api_docs.md)
python manage.py routes --format markdown

# Markdown with a custom output path
python manage.py routes --format markdown --output docs/api.md

# Generate a separate api_docs.md inside EACH app directory
python manage.py routes --format markdown --per-app

# Per-app docs, filtered to a specific app only
python manage.py routes --format markdown --per-app --app users

# Custom project name in the doc title
python manage.py routes --format markdown --project-name "My API"

# Include Django admin routes (hidden by default)
python manage.py routes --include-admin

# Disable color
python manage.py routes --no-color
```

---

## Options

| Flag | Description |
|---|---|
| `--app <name>` | Filter by Django app name or module |
| `--search <term>` | Search by URL, view name, or route name (case-insensitive) |
| `--format table\|json\|markdown` | Output format (default: `table`) |
| `--output <file>` | Write output to a file (auto-defaults to `api_docs.md` for markdown) |
| `--per-app` | Generate a separate `api_docs.md` inside each Django app directory |
| `--project-name <name>` | Project name used in the markdown document title |
| `--include-admin` | Show Django admin routes |
| `--no-color` | Disable colored output |

---

## API Documentation Output

Running `--format markdown` generates a full `api_docs.md` file with:

- **Cover page** — timestamp, total route count, method breakdown summary
- **Table of contents** — per app, per endpoint with anchor links
- **Per-endpoint sections** — with:
  - Method badges (🟢 `GET`, 🔵 `POST`, 🔴 `DELETE`, etc.)
  - Path parameters table (`{id}`, `{pk}`, etc.)
  - Serializer class
  - Permission classes
  - Authentication classes
  - Filter backends, search fields, ordering fields
  - Pagination class
  - Docstring (from the view class)
- **Appendix** — flat table of all routes

All metadata is extracted **automatically** from your existing views — no annotations needed.

### Example endpoint section

```markdown
### `/api/users/{id}/`

🔷 **DRF**  |  **View:** `UserDetailView`  |  **Module:** `users.views`

**Methods**

🟢 `GET`  🟡 `PUT`  🟠 `PATCH`  🔴 `DELETE`

**Path Parameters**

| Parameter | Type   |
|-----------|--------|
| `{id}`    | string |

**Details**

| Field           | Value                  |
|-----------------|------------------------|
| URL Name        | `user-detail`          |
| Serializer      | `UserSerializer`       |
| Permissions     | `IsAuthenticated`      |
| Authentication  | `JWTAuthentication`    |
| Search Fields   | `username` `email`     |
```

---

## What it detects

| View type | Methods | Serializer | Permissions | Filters |
|---|---|---|---|---|
| DRF `ViewSet` / `ModelViewSet` | ✅ From router actions | ✅ `serializer_class` | ✅ | ✅ |
| DRF `APIView` | ✅ From defined handlers | ✅ `serializer_class` | ✅ | ✅ |
| Django CBV | ✅ From `http_method_names` | — | — | — |
| Django FBV | — | — | — | — |

---

## JSON output

```bash
python manage.py routes --format json | jq '.[0]'
```

```json
{
  "url": "/api/users/",
  "name": "user-list",
  "view": "UserViewSet",
  "module": "myapp.views",
  "methods": ["GET", "POST"],
  "serializer": "UserSerializer",
  "app": "users",
  "is_drf": true
}
```

---

## Requirements

- Python ≥ 3.9
- Django ≥ 3.2
- djangorestframework ≥ 3.12
- `rich` ≥ 13.0 *(optional, for colored table output)*

---

## Contributing

Contributions are welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) for the full guide — setup, branch naming, commit style, PR checklist, and how to report bugs.

---

## License

MIT