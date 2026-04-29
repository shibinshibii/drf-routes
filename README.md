# drf-routes

**Zero-config API documentation generator for Django REST Framework.**

One command. No YAML. No decorators. No OpenAPI schema maintenance.  
Just point it at your existing Django project and get a full API reference — automatically.

```bash
pip install drf-routes
python manage.py routes --format markdown
# → api_docs.md generated. Done.
```

> Like `rails routes`, but for Django. With full API docs.

---

## 🚀 In 10 Seconds

```bash
# 1. Install
pip install drf-routes

# 2. Add to INSTALLED_APPS (one line)
# "drf_routes"

# 3. Generate your full API reference
python manage.py routes --format markdown
```

That's it. Open `api_docs.md` — your entire API is documented.  
Serializers, permissions, auth classes, filters, path params, docstrings — all extracted automatically from your existing views. No annotations. No config files. No extra code.

---

## 🆚 How It Compares

| Feature | Swagger / drf-yasg | drf-spectacular | **drf-routes** |
|---|---|---|---|
| Setup complexity | Heavy (OpenAPI schema config) | Medium (schema hooks) | **Zero** |
| Annotations required | Yes (`@swagger_auto_schema`) | Yes (`@extend_schema`) | **No** |
| Works on existing projects | Partial | Partial | **Yes, out of the box** |
| Terminal route table | ❌ | ❌ | ✅ |
| Per-app doc generation | ❌ | ❌ | ✅ |
| JSON output | ❌ | ❌ | ✅ |
| Markdown docs | ❌ | ❌ | ✅ |
| Interactive UI | ✅ | ✅ | ❌ (roadmap) |

**The tradeoff:** drf-routes doesn't generate interactive Swagger UI — it generates clean, portable Markdown that lives in your repo. Use it for internal docs, quick audits, and onboarding — without the Swagger maintenance burden.

---

## 📦 Install

```bash
pip install drf-routes
```

For colored terminal output (recommended):

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

## 📋 Terminal Route Table

```bash
python manage.py routes
```

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

## 📝 Generated API Reference (Markdown)

Running `--format markdown` produces a complete `api_docs.md` with:

- **Cover page** — timestamp, total route count, method breakdown summary  
- **Table of contents** — per app, per endpoint with anchor links  
- **Per-endpoint sections** including:
  - Method badges (🟢 `GET`, 🔵 `POST`, 🔴 `DELETE`, etc.)
  - Path parameters table (`{id}`, `{pk}`, etc.)
  - Serializer class
  - Permission classes
  - Authentication classes
  - Filter backends, search fields, ordering fields
  - Pagination class
  - Docstring (extracted from the view class)
- **Appendix** — flat table of all routes

All metadata is extracted **automatically** from your existing views. **Zero annotations needed.**

### Example endpoint output

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

| Field           | Value               |
|-----------------|---------------------|
| URL Name        | `user-detail`       |
| Serializer      | `UserSerializer`    |
| Permissions     | `IsAuthenticated`   |
| Authentication  | `JWTAuthentication` |
| Search Fields   | `username` `email`  |
```

---

## 🔧 Usage

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

# Per-app docs, filtered to a specific app
python manage.py routes --format markdown --per-app --app users

# Custom project name in the doc title
python manage.py routes --format markdown --project-name "My API"

# Include Django admin routes (hidden by default)
python manage.py routes --include-admin

# Disable color
python manage.py routes --no-color
```

---

## ⚙️ Options

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

## 🔍 What It Detects

| View type | Methods | Serializer | Permissions | Filters |
|---|---|---|---|---|
| DRF `ViewSet` / `ModelViewSet` | ✅ From router actions | ✅ `serializer_class` | ✅ | ✅ |
| DRF `APIView` | ✅ From defined handlers | ✅ `serializer_class` | ✅ | ✅ |
| Django CBV | ✅ From `http_method_names` | — | — | — |
| Django FBV | — | — | — | — |

---

## 📤 JSON Output

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

Pipe into `jq`, scripts, CI pipelines — whatever you need.

---

## ✅ Tests

The package ships with a test suite covering route resolution, view inspection, and Markdown formatting:

```bash
pip install drf-routes[dev]
pytest
```

Tests use `pytest-django` and run against a minimal in-memory Django project — no external services needed.

---

## 📋 Requirements

- Python ≥ 3.9
- Django ≥ 3.2
- djangorestframework ≥ 3.12
- `rich` ≥ 13.0 *(optional, for colored table output)*

---

## 🤝 Contributing

Contributions are welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) for the full guide — setup, branch naming, commit style, PR checklist, and how to report bugs.

---

## License

MIT