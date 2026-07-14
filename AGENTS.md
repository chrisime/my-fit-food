# my-fit-food — AGENTS.md

## Project structure
- **Monorepo** (pnpm workspace). `web/` = Vue 3 + Vite + Pinia + Oruga v0.9 + TailwindCSS. `api/` = FastAPI + SQLAlchemy + SQLite.
- Lockfile at root: `pnpm-lock.yaml`. Add new packages with `pnpm add <pkg> --filter web`.

## Commands
| Task | Command | Notes |
|---|---|---|
| Dev (parallel) | `pnpm dev` | Runs web + API concurrently |
| Dev web only | `pnpm dev:web` | Vite on :5173 |
| Dev API only | `pnpm dev:api` | uvicorn on :8000, activates `.venv` |
| Build web | `pnpm build:web` | Runs `vue-tsc --noEmit` then `vite build` |
| Init DB | `pnpm db:init` | Calls `init_db()` in Python |
| Seed DB | `cd api && source .venv/bin/activate && python seed.py` | Must import all model classes in `seed.py` |

## API
- Python venv at `api/.venv`. Activate before running Python commands directly.
- DB file: `api/my_fit_food.db` (SQLite). Delete + re-seed for fresh data.
- All endpoints under FastAPI app at `api/app/main.py`. Routers: `auth`, `customers`, `dashboard`, `orders`, `products`, `stock`, `production`, `ws`.
- JWT auth via `python-jose`. Token in `Authorization: Bearer` header. Frontend stores in `localStorage`.
- Role guard: `require_role("admin")` from `app.core.deps`. Admin can access everything.

## Frontend
- Oruga v0.9.x configured globally in `web/src/main.ts` with Tailwind class overrides — **never import `@oruga-ui/theme-oruga/style.css`**.
- Icons: `@mdi/font` (class `mdi mdi-*`). Imported in `main.ts`.
- Route guard in `web/src/router/index.ts` via `meta.roles`. Unauthenticated → `/login`.
- Roles: `admin`, `vendas`, `cozinha`. Nav links gated by role in `App.vue`.
- `/expedicao` and `/usuarios` are admin-only.
- Stores: `auth.ts`, `orders.ts` in `web/src/stores/`.

## Notable conventions
- `.env` ignored; API reads from `api/.env`.
- No testing framework set up. Run `pnpm build:web` to typecheck + build.
- Default users (from seed): `admin/admin`, `andressa/123`, `cozinha/123`.
- Stock adjust endpoint requires admin role.
- `__pycache__`, `*.db`, `dist`, `node_modules` gitignored.
