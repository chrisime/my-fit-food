# Docker / Podman Guide

## Voraussetzungen

- **Docker Desktop** (empfohlen) oder **Podman** (macOS: `brew install podman && podman machine init && podman machine start`)
- Docker Compose (bei Docker Desktop enthalten, Podman: `brew install docker-compose`)

## docker-compose

### Starten

```bash
docker compose up -d
```

### DB initialisieren (nach erstem Start)

```bash
docker compose exec api python /app/seed.py
```

### Logs verfolgen

```bash
docker compose logs -f
```

### Stoppen

```bash
docker compose down
```

### Komplett zurücksetzen (Datenbank löschen)

```bash
docker compose down -v
docker compose up -d
docker compose exec api python /app/seed.py
```

---

## podman-compose

### Bekannte Probleme

**1. Credential Helper (`docker-credential-desktop` nicht gefunden)**

Die Docker-Config zeigt auf `credsStore: "desktop"`, der nur mit laufendem Docker Desktop funktioniert.

**Lösung:** Leere Config verwenden:

```bash
mkdir -p /tmp/docker-clean-config
echo '{"auths":{}}' > /tmp/docker-clean-config/config.json
alias dc='DOCKER_CONFIG=/tmp/docker-clean-config docker-compose'
```

**2. Port 443 wird von gvproxy abgefangen (macOS)**

Podman verwendet `gvproxy`, das Port 443 auf dem Host blockiert.

**Lösung:** Anderen Host-Port verwenden:

```bash
# docker-compose.yml anpassen:
ports:
  - "8443:443"  # Host:8443 → Container:443
```

Oder Container direkt via `podman run` starten (siehe unten).

### Starten (mit Workaround)

```bash
DOCKER_CONFIG=/tmp/docker-clean-config docker-compose up -d
```

### DB seeden

```bash
DOCKER_CONFIG=/tmp/docker-clean-config docker-compose exec api python /app/seed.py
```

### Stoppen

```bash
DOCKER_CONFIG=/tmp/docker-clean-config docker-compose down
```

---

## Manuell mit podman run (Alternative zu compose)

Nur wenn docker-compose nicht funktioniert.

### 1. Images bauen

```bash
podman build -t my-fit-food-api ./api
podman build -t my-fit-food-web -f web/Dockerfile .
```

### 2. Netzwerk + Volume erstellen

```bash
podman network create my-fit-food-net
podman volume create api-data
```

### 3. API starten

```bash
podman run -d --name my-fit-food-api \
  --network my-fit-food-net \
  -v api-data:/app/data \
  --env-file api/.env \
  localhost/my-fit-food-api
```

### 4. DB seeden

```bash
podman exec my-fit-food-api python /app/seed.py
```

### 5. Web-Container starten

```bash
API_IP=$(podman inspect my-fit-food-api | python3 -c \
  "import sys,json;print(json.load(sys.stdin)[0]['NetworkSettings']['Networks']['my-fit-food-net']['IPAddress'])")

podman run -d --name my-fit-food-web \
  --network my-fit-food-net \
  --add-host api:${API_IP} \
  -p 8443:443 \
  localhost/my-fit-food-web
```

### 6. Testen

```bash
curl -sk https://localhost:8443/
curl -sk -X POST https://localhost:8443/api/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"username":"admin","password":"admin"}'
```

### Aufräumen

```bash
podman rm -f my-fit-food-api my-fit-food-web
podman volume rm api-data
podman network rm my-fit-food-net
```

---

## Zugriff

| Umgebung | URL |
|---|---|
| docker-compose | https://localhost:443 |
| podman-compose (Port-Konflikt) | https://localhost:8443 |
| manuell (podman run) | https://localhost:8443 |

Standard-Logins: `admin` / `admin`, `andressa` / `123`, `cozinha` / `123`

## Architektur

```
Browser → :443/:8443
  Caddy (Container: web)
    ├── TLS (self-signed via tls internal)
    ├── HTTP/2
    ├── served static files (dist/)
    ├── SPA fallback (try_files → index.html)
    └── proxy /api/* → api:8000
        └── FastAPI (Container: api)
              └── SQLite (/app/data/my_fit_food.db)
```
