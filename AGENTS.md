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
| Docker build | `docker compose build` | Baut beide Images (API + Web) |
| Docker start | `docker compose up -d` | Startet Container im Hintergrund |
| Docker start (lokal) | `docker compose -f docker-compose.yml -f docker-compose-local.yaml up -d` | Port 8443 statt 443 (Podman/macOS) |
| Docker stop | `docker compose down` | Stoppt und entfernt Container |
| DB seeden (Docker) | `docker compose exec api python /app/seed.py` | Nach `up -d` ausführen |
| Logs (Docker) | `docker compose logs -f` | Folgt allen Logs |

## API
- Python venv at `api/.venv`. Activate before running Python commands directly.
- DB file: `api/my_fit_food.db` (SQLite). Delete + re-seed for fresh data.
- All endpoints under FastAPI app at `api/app/main.py`. Routers: `auth`, `customers`, `dashboard`, `orders`, `products`, `stock`, `production`, `ws`.
- JWT auth via `python-jose`. Token in `Authorization: Bearer` header. Frontend stores in `localStorage`.
- Role guard: `require_role("admin")` from `app.core.deps`. Admin can access everything.

## Frontend
- Oruga v0.13.x configured globally in `web/src/main.ts` with Tailwind class overrides — **never import `@oruga-ui/theme-oruga/style.css`**.
- **Consistency rule: All interactive elements must use Oruga components** — `o-input` for inputs, `o-button` for buttons, `o-field` for field wrappers, `o-modal` for modals. Never use native `<input>`, `<button>`, `<textarea>`, or `<select>` directly. New components follow the same rule. Configure new Oruga component variants in `main.ts` when needed.
- **Oruga v0.13 prop:** use `type` (not `native-type`) to set native button type — e.g. `type="submit"`, `type="button"`.
- Icons: `@mdi/font` (class `mdi mdi-*`). Imported in `main.ts`.
- Route guard in `web/src/router/index.ts` via `meta.roles`. Unauthenticated → `/login`.
- Roles: `admin`, `sales`, `kitchen`. Nav links gated by role in `App.vue`. Frontend maps values via `composables/labels.ts`.
- `/dispatch` and `/users` are admin-only.
- Stores: `auth.ts`, `orders.ts` in `web/src/stores/`.

## Notable conventions
- `.env` ignored; API reads from `api/.env`.
- No testing framework set up. Run `pnpm build:web` to typecheck + build.
- Default users (from seed): `admin/admin`, `andressa/123`, `cozinha/123`.
- Stock adjust endpoint requires admin role.
- `__pycache__`, `*.db`, `dist`, `node_modules` gitignored.
