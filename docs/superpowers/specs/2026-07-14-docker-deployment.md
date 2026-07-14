# Docker Deployment — My Fit Food on Oracle Cloud Free Tier

## Architecture

```
Internet :443
    │
Caddy (Container: web)
├── TLS (self-signed via `tls internal`)
├── HTTP/2
├── serves static files from /usr/share/caddy
├── reverse proxy /api/* → api:8000 (HTTP/1.1)
└── WebSocket /api/ws  → api:8000
    │
API (Container: api)
├── uvicorn app.main:app --host 0.0.0.0 --port 8000
├── SQLite in persistent volume
└── config via .env (DB_URL, SECRET_KEY)
```

## Containers

### API — Python FastAPI

- Base: `python:3.12-slim`
- Installs dependencies from `requirements.txt`
- Runs `uvicorn app.main:app --host 0.0.0.0 --port 8000`
- SQLite database stored on a Docker named volume (`api-data`)
- Configuration via `api/.env` (env_file in compose) — supports PostgreSQL later by changing `database_url`

### Web — Caddy + Static Frontend

Multi-stage build:
1. **Builder** (`node:22-alpine`): installs dependencies, runs `pnpm build`
2. **Runtime** (`caddy:2-alpine`): copies `/app/dist` → `/usr/share/caddy`, copies `Caddyfile` → `/etc/caddy/Caddyfile`

Caddy handles:
- TLS termination with self-signed cert (`tls internal`)
- HTTP/2
- Static file serving
- Reverse proxy of `/api/*` to the API container (strips `/api` prefix)
- WebSocket passthrough for `/api/ws`

## Files

```
api/Dockerfile          — Python image, copy source, run uvicorn
web/Dockerfile          — Multi-stage: node build → caddy runtime
web/Caddyfile           — Caddy config for production
docker-compose.yml      — Root-level orchestration
```

## Deployment Steps (Oracle Cloud Free Tier)

1. Install Docker + Docker Compose on Oracle Linux instance
2. Clone repository or copy files
3. Place `api/.env` with production values
4. Run `docker compose up -d`
5. Access via `https://<instance-public-ip>`

## PostgreSQL Migration

- Already prepared via `database_url` env var (pydantic-settings)
- Change `database_url` in `.env` to PostgreSQL connection string
- Update `connect_args` in `database.py` (remove `check_same_thread`)
- No other code changes needed
