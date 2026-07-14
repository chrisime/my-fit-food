# Docker Deployment Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create Dockerfiles and docker-compose.yml to deploy My Fit Food on Oracle Cloud Free Tier.

**Architecture:** Two containers: Caddy serves the built frontend + terminates TLS (self-signed) + reverse-proxies `/api/*` to the Python backend. uvicorn runs the FastAPI app with SQLite in a persistent volume.

**Tech Stack:** Docker, Docker Compose, Caddy 2, Python 3.12, Node 22

## Global Constraints

- Oracle Cloud Free Tier → ARM64 (Ampere A1). Use `--platform linux/amd64` if ARM build issues arise.
- SQLite must be on a named volume for persistence.
- API config via `api/.env` (env_file) — no hardcoded secrets.
- Caddy TLS via `tls internal` (self-signed) for IP-based access.
- Frontend fetch uses `/api` prefix, WebSocket connects to `${location.host}/api/ws` — Caddy must strip prefix and handle WS upgrades.

---

### Task 1: API Dockerfile

**Files:**
- Create: `api/Dockerfile`

**Interfaces:**
- Consumes: `api/requirements.txt`, `api/app/` directory, Python 3.12
- Produces: Docker image that runs uvicorn on port 8000

- [ ] **Step 1: Create `api/Dockerfile`**

```dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

- [ ] **Step 2: Build and verify API image**

```bash
docker build -t my-fit-food-api ./api
docker run --rm -p 8001:8000 my-fit-food-api
```

In another terminal:
```bash
curl -s -X POST http://localhost:8001/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"username":"admin","password":"admin"}' | python3 -c "import sys,json; d=json.load(sys.stdin); print('OK' if 'access_token' in d else 'FAIL')"
```

Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add api/Dockerfile
git commit -m "feat: add API Dockerfile for FastAPI + uvicorn"
```

---

### Task 2: Frontend Dockerfile (Multi-stage with Caddy)

**Files:**
- Create: `web/Dockerfile`
- Create: `web/Caddyfile`

**Interfaces:**
- Consumes: `web/` source (Vue app), built via `pnpm build`, served by Caddy
- Produces: Docker image with Caddy serving frontend + reverse proxy to API

- [ ] **Step 1: Create production `web/Caddyfile`**

```
https://:443 {
	tls internal

	root * /usr/share/caddy

	@api {
		path /api/*
	}
	handle @api {
		uri strip_prefix /api
		reverse_proxy api:8000
	}

	handle {
		file_server
	}
}
```

- [ ] **Step 2: Create `web/Dockerfile`**

```dockerfile
FROM node:22-alpine AS builder
WORKDIR /app
COPY package.json pnpm-lock.yaml ./
RUN corepack enable && pnpm install --frozen-lockfile
COPY . .
RUN pnpm build

FROM caddy:2-alpine
COPY --from=builder /app/dist /usr/share/caddy
COPY Caddyfile /etc/caddy/Caddyfile
EXPOSE 443
```

- [ ] **Step 3: Verify frontend build**

```bash
docker build -t my-fit-food-web ./web
docker run --rm -p 443:443 my-fit-food-web
```

In another terminal:
```bash
curl -sk --http2 https://localhost:443/ -o /dev/null -w "HTTP %{http_version}, status %{http_code}\n"
```

Expected: `HTTP 2, status 200`

- [ ] **Step 4: Commit**

```bash
git add web/Dockerfile web/Caddyfile
git commit -m "feat: add frontend Dockerfile with Caddy (multi-stage build)"
```

---

### Task 3: Docker Compose

**Files:**
- Create: `docker-compose.yml`

**Interfaces:**
- Consumes both Docker images from Tasks 1 and 2
- Orchestrates them with networking, volumes, env vars

- [ ] **Step 1: Create `docker-compose.yml`**

```yaml
services:
  api:
    build: ./api
    volumes:
      - api-data:/app
    env_file:
      - ./api/.env
    restart: unless-stopped

  web:
    build:
      context: ./web
      dockerfile: Dockerfile
    ports:
      - "443:443"
    depends_on:
      - api
    restart: unless-stopped

volumes:
  api-data:
```

- [ ] **Step 2: Create a sample `api/.env` for production**

```bash
cat > api/.env << 'EOF'
database_url=sqlite:///./data/my_fit_food.db
secret_key=replace-with-a-real-secret
EOF
```

Note: `database_url` uses `./data/` subdirectory so the volume mount at `/app` maps cleanly.

- [ ] **Step 3: Update `api/app/core/config.py` to use `/app/data/` in Docker**

The SQLite path is relative. In Docker the working dir is `/app`, and the volume is mounted at `/app`. The current default `sqlite:///./my_fit_food.db` creates the DB at `/app/my_fit_food.db`. The `.env` above points to `./data/my_fit_food.db` — create the `data` directory in the volume. No code change needed since pydantic-settings reads `database_url` from the env file.

- [ ] **Step 4: Add `.gitignore` entries**

Add to `.gitignore`:
```
docker-data/
```

- [ ] **Step 5: Verify compose builds and starts**

```bash
docker compose build
docker compose up -d
sleep 3
curl -sk --http2 https://localhost:443/ -o /dev/null -w "Frontend: HTTP %{http_version}, status %{http_code}\n"
curl -sk --http2 https://localhost:443/api/auth/login -X POST \
  -H 'Content-Type: application/json' \
  -d '{"username":"admin","password":"admin"}' -o /dev/null -w "API: HTTP %{http_version}, status %{http_code}\n"
docker compose down
```

Expected:
```
Frontend: HTTP 2, status 200
API: HTTP 2, status 200
```

- [ ] **Step 6: Seed the database**

```bash
docker compose run api python seed.py
```

- [ ] **Step 7: Commit**

```bash
git add docker-compose.yml api/.env .gitignore
git commit -m "feat: add docker-compose orchestration for production deployment"
```
