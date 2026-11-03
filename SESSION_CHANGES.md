# Session Changes — 2026-11-03

## Setup
- Cloned `https://github.com/beck-source/inventory-management` into `anthropic_bootcamp/inventory-management`.
- Created and switched to branch `new_features`.
- Installed backend dependencies with `uv sync` (in `server/`).
- Installed frontend dependencies with `npm install` (in `client/`).
- Started backend on http://localhost:8001 and frontend on http://localhost:3000.
- Server logs are written to `anthropic_bootcamp/backend.log` and `anthropic_bootcamp/frontend.log`.

## CLAUDE.md (root)
- Added the standard Claude Code header line at the top.
- Replaced "Quick Start" with a "Commands" section (start/stop scripts, per-server commands, build).
- Added working test commands; they must run from `server/` (the `tests/README.md` command fails).
- Added how to run a single test.
- Noted there are no frontend tests and no linter configured.
- Added an "Architecture" section (single-file backend, in-memory JSON data, filter logic, shared filter state, i18n).
- Listed known gaps: missing `/api/tasks` and `/api/purchase-orders` routes, unrouted `Backlog.vue`, missing `test_orders.py`.
- Added missing endpoints to the API list (`/{id}` routes and `/api/reports/*`).

## Architecture page
- Created `docs/architecture.html`: system diagram, tech stack, filter data flow, API table, data model, known gaps.
- Supports light/dark mode and phone width.

## Restocking feature
### Data
- `server/data/demand_forecasts.json`: added `unit_cost` and `lead_time_days` to all 9 items.
- PSU-501 uses its real inventory price ($18.99); the other 8 prices and all lead times are made-up demo values.

### Backend (`server/main.py`)
- Added `unit_cost` and `lead_time_days` to the `DemandForecast` model.
- Added request models `RestockLine` (SKU + quantity > 0) and `CreateRestockOrderRequest` (at least 1 line).
- Added `POST /api/restock-orders`: validates SKUs, computes line totals, total cost, lead time (slowest item) and expected delivery date.
- Added `GET /api/restock-orders`: returns submitted orders, newest first.
- Orders are stored in memory and are lost when the server restarts.

### Tests
- Added `tests/backend/test_restock_orders.py` (9 tests: totals, lead time, listing order, unknown SKU, invalid payloads).
- Full suite: 49 passed.

### Frontend
- New page `client/src/views/Restocking.vue`:
  - budget slider ($0 to the cost of restocking everything, starts at half),
  - recommendations for items whose forecast exceeds current demand, biggest gap first, with partial quantities when the budget runs out,
  - summary cards for items recommended, budget used, budget remaining and lead time,
  - "Place Order" button with a confirmation and a link to Orders.
- `client/src/main.js`: added the `/restocking` route.
- `client/src/App.vue`: added a "Restocking" nav link after Orders.
- `client/src/api.js`: added `getRestockOrders()` and `createRestockOrder()`.
- `client/src/views/Orders.vue`: added a "Submitted Orders" section above "All Orders" (lead time and expected delivery shown; not affected by the top-bar filters).
- `client/src/locales/en.js` and `ja.js`: added English and Japanese text for the new tab and section.

## Not done / notes
- Nothing has been committed yet; all changes are on branch `new_features`.
- The UI was built and served successfully but not clicked through in a browser by Claude.
- `.vue` files were written directly because the repo's `vue-expert` agent was not loaded in this session.
