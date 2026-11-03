# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

Factory Inventory Management System Demo with GitHub integration - Full-stack application with Vue 3 frontend, Python FastAPI backend, and in-memory mock data (no database).

> ⚠️ **This repository and any fork you create are PUBLIC.** Do not commit credentials, internal hostnames, or private registry URLs. `client/.npmrc` pins the public npm registry and `client/package-lock.json` is gitignored to prevent locally-configured registries from leaking into commits — leave both in place.

## Critical Tool Usage Rules

### Subagents
Use the Task tool with these specialized subagents for appropriate tasks:

- **vue-expert**: Use for Vue 3 frontend features, UI components, styling, and client-side functionality
  - Examples: Creating components, fixing reactivity issues, performance optimization, complex state management
  - **MANDATORY RULE: ANY time you need to create or significantly modify a .vue file, you MUST delegate to vue-expert**
- **code-reviewer**: Use after writing significant code to review quality and best practices
- **Explore**: Use for understanding codebase structure, searching for patterns, or answering questions about how components work
- **general-purpose**: Use for complex multi-step tasks or when other agents don't fit

### Skills
- **backend-api-test** skill: Use when writing or modifying tests in `tests/backend` directory with pytest and FastAPI TestClient

### MCP Tools
- **ALWAYS use GitHub MCP tools** (`mcp__github__*`) for ALL GitHub operations
  - Exception: Local branches only - use `git checkout -b` instead of `mcp__github__create_branch`
- **ALWAYS use Playwright MCP tools** (`mcp__playwright__*`) for browser testing
  - Test against: `http://localhost:3000` (frontend), `http://localhost:8001` (API)

## Stack
- **Frontend**: Vue 3 + Composition API + Vite (port 3000)
- **Backend**: Python FastAPI (port 8001)
- **Data**: JSON files in `server/data/` loaded via `server/mock_data.py`

## Commands

```bash
./scripts/start.sh            # Both servers (installs deps if missing); logs in /tmp/inventory-*.log
./scripts/stop.sh

cd server && uv sync && uv run python main.py   # Backend only (API docs: http://localhost:8001/docs)
cd client && npm install && npm run dev         # Frontend only
cd client && npm run build                      # Production build -> client/dist/
```

**Tests** (backend only; there are no frontend tests and no linter configured). Run pytest from `server/` so uv uses the server venv — `cd tests && uv run pytest` (as written in `tests/README.md`) fails with `ModuleNotFoundError: fastapi`:

```bash
cd server && uv run pytest -c ../tests/pytest.ini ../tests                     # all
cd server && uv run pytest -c ../tests/pytest.ini \
  ../tests/backend/test_inventory.py::TestInventoryEndpoints::test_get_all_inventory  # single test
```

`tests/backend/conftest.py` puts `server/` on `sys.path` and imports `main.app` directly; tests use the `client` fixture (FastAPI `TestClient`). `tests/README.md` mentions `test_orders.py`, but that file does not exist.

## Architecture

- **Backend is a single file**: all Pydantic models, filter helpers, and routes live in `server/main.py`. `mock_data.py` loads `server/data/*.json` once at import into module-level lists, so all state is in memory and resets on restart. `generate_data.py` regenerates the JSON.
- **Filtering**: `apply_filters()` (warehouse/category/status) and `filter_by_month()` in `main.py`. Month filtering is a substring match on `order_date`; quarters go through the hardcoded `QUARTER_MAP` (Q1–Q4 2025 only).
- **Frontend filter state** is a module-level singleton in `client/src/composables/useFilters.js` (shared across all views via `FilterBar.vue`); views call `getCurrentFilters()` and pass the result to `client/src/api.js`. `'all'` values are stripped before building query params.
- **Other composables**: `useI18n.js` with `client/src/locales/{en,ja}.js` (UI strings go in both locale files), `useAuth.js`; currency formatting in `client/src/utils/currency.js`.
- **Routing** is defined in `client/src/main.js`. `views/Backlog.vue` exists but is not routed.
- **Frontend/backend drift**: `api.js` calls `/api/tasks` (GET/POST/DELETE/PATCH) and `/api/purchase-orders`, which have no backend routes (`PurchaseOrder` models exist in `main.py`, but only the backlog endpoint reads `purchase_orders`). Expect 404s there until those endpoints are implemented.
- `client/CLAUDE.md` and `server/CLAUDE.md` contain detailed frontend/backend conventions.

## Key Patterns

**Filter System**: 4 filters (Time Period, Warehouse, Category, Order Status) apply to all data via query params
**Data Flow**: Vue filters → `client/src/api.js` → FastAPI → In-memory filtering → Pydantic validation → Computed properties
**Reactivity**: Raw data in refs (`allOrders`, `inventoryItems`), derived data in computed properties

## API Endpoints
- `GET /api/inventory`, `/api/inventory/{id}` - Filters: warehouse, category
- `GET /api/orders`, `/api/orders/{id}` - Filters: warehouse, category, status, month
- `GET /api/dashboard/summary` - All filters
- `GET /api/demand`, `/api/backlog` - No filters
- `GET /api/spending/*` - Summary, monthly, categories, transactions
- `GET /api/reports/quarterly`, `/api/reports/monthly-trends`

## Common Issues
1. Use unique keys in v-for (not `index`) - use `sku`, `month`, etc.
2. Validate dates before `.getMonth()` calls
3. Update Pydantic models when changing JSON data structure
4. Inventory filters don't support month (no time dimension)
5. Revenue goals: $800K/month single, $9.6M YTD all months

## File Locations
- Views: `client/src/views/*.vue`
- API Client: `client/src/api.js`
- Backend: `server/main.py`, `server/mock_data.py`
- Data: `server/data/*.json`
- Styles: `client/src/App.vue`

## Design System
- Colors: Slate/gray (#0f172a, #64748b, #e2e8f0)
- Status: green/blue/yellow/red
- Charts: Custom SVG, CSS Grid for layouts
- No emojis in UI
