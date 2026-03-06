# Project Folders Structure Blueprint

_Last updated: March 7, 2026_

---

## 1. Structural Overview

**Project Type:** Python (Flask backend, MySQL database, Vue.js 3 frontend, ECharts visualization)
**Monorepo:** No (单仓库，前后端分离建议，当前未分离)
**Microservices:** No (modular monolith, not microservices)
**Frontend:** Vue.js/ECharts（建议前端独立，见下文结构）

**Architectural Principles:**
- Modular organization: `app/` contains all backend logic, separated by domain (api, models, services)
- Data and configuration are externalized (`data/`, `config.py`, `requirements.txt`)
- Tests are isolated in `tests/`
- Documentation is under `docs/`
- 前端页面建议放置于 `frontend/` 文件夹，便于前后端分离开发与部署。


## 2. Directory Visualization

```
.
├── config.py
├── requirements.txt
├── wsgi.py
├── app/
│   ├── __init__.py
│   ├── extensions.py
│   ├── api/
│   │   ├── __init__.py
│   │   └── ingestion_bp.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── call_graph.py
│   │   ├── ms_resource.py
│   │   ├── ms_rt_mcr.py
│   │   └── node_metrics.py
│   └── services/
│       ├── __init__.py
│       └── ingestion_service.py
├── data/
│   ├── CallGraph/
│   ├── MSResource/
│   ├── MSRTMCR/
│   └── Node/
├── docs/
│   └── ways-of-work/
│       └── plan/
│           └── database-and-data-integration/
│               ├── arch.md
│               ├── epic.md
│               └── data-ingestion-pipeline/
│                   ├── implementation-plan.md
│                   └── prd.md
├── frontend/           # 前端项目（Vue 3 + Vite + ECharts）
│   ├── src/
│   ├── public/
│   ├── package.json
│   ├── vite.config.js
│   └── index.html
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_ingestion_bp.py
│   ├── test_ingestion_service.py
│   └── test_models.py
```


## 3. Key Directory Analysis

- **app/**: Main backend application logic. Contains:
  - **api/**: Flask Blueprints and API route definitions.
  - **models/**: ORM models and data structures.
  - **services/**: Business logic, service layer abstractions.
  - **extensions.py**: Flask extensions setup (DB, CORS, etc).
- **data/**: External CSV datasets for ingestion and analysis.
- **docs/**: Project documentation, architecture, and planning.
- **frontend/**: 前端项目文件夹，包含 Vue.js 源码、静态资源、依赖配置（如 package.json），实现页面展示与交互。
- **tests/**: Unit and integration tests for backend modules.
- **config.py**: Application configuration (env, DB, etc).
- **requirements.txt**: Python dependencies.
- **wsgi.py**: WSGI entry point for deployment.


## 4. File Placement Patterns

- **Configuration**: `config.py`, `.env` (后端)；`frontend/package.json`, `.env`（前端）
- **Models/Entities**: `app/models/`
- **Business Logic**: `app/services/`
- **API/Interface**: `app/api/`（后端），`frontend/src/`（前端页面组件）
- **Tests**: `tests/`（后端），`frontend/tests/`（前端如有）
- **Documentation**: `docs/`


## 5. Naming and Organization Conventions

- Folders: Lowercase, underscore-separated
- Files: Lowercase, underscore-separated, descriptive
- Python modules: `snake_case`
- Test files: `test_*.py`
- Documentation: Markdown, organized by topic/feature

---

## 6. Navigation and Development Workflow

- **Entry Points**: `wsgi.py` (production), `app/__init__.py` (app factory)
- **Common Tasks**: Run tests (`pytest tests/`), start server (`flask run` or WSGI)
- **Dependencies**: Install via `pip install -r requirements.txt`
- **Data**: Place CSVs in `data/` subfolders

---

## 7. Build and Output Organization

- No build scripts (Python interpreted)
- Output: Logs, processed data (if any) in `data/` or external
- Environment-specific config via `config.py` or `.env`

---

## 8. Technology-Specific Organization

- **Flask**: Modular app, Blueprints, service layer, models
- **MySQL**: Managed via Flask extensions, config in `config.py`
- **Vue.js 3/ECharts**: 推荐前端独立于 `frontend/` 文件夹，使用 **Vue 3 + Vite** 构建（`src/`, `public/`, `package.json`, `vite.config.js`），ECharts 作为依赖集成于页面组件。Vue 3 使用选项式 API（Options API）实现组件，ECharts 实例需在 `beforeUnmount` 钩子中调用 `dispose()` 释放资源（Vue 3 生命周期钩子名称由 `beforeDestroy` 改为 `beforeUnmount`）。


## 9. Extension and Evolution

- Add new features: Create new service/model/api files in `app/`
- Add tests: Create new `test_*.py` in `tests/`
- Documentation: Add Markdown files in `docs/`
- Refactoring: Maintain modular separation, update blueprint

---

## 10. Structure Templates

- **New API**: `app/api/<feature>_bp.py`
- **New Model**: `app/models/<feature>.py`
- **New Service**: `app/services/<feature>_service.py`
- **New Test**: `tests/test_<feature>.py`

---

## Maintaining This Blueprint

- Update this document when adding/removing major folders, changing structure, or introducing new technologies.
- Last updated: March 7, 2026
