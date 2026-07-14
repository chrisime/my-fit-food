FROM node:22-alpine AS builder
WORKDIR /app

COPY pnpm-lock.yaml package.json pnpm-workspace.yaml ./
COPY web/package.json ./web/

RUN corepack enable && pnpm install --frozen-lockfile

COPY web/ ./web/
RUN cd web && pnpm build

FROM caddy:2-alpine
COPY --from=builder /app/web/dist /usr/share/caddy
COPY web/Caddyfile /etc/caddy/Caddyfile
EXPOSE 443
