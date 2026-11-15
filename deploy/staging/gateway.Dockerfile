FROM node:24-slim AS frontend
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci --no-audit --no-fund
COPY frontend/ ./
COPY data/ /app/data/
ARG STAGING_ORIGIN
ENV VITE_USE_FIXTURES=false VITE_API_BASE_URL=${STAGING_ORIGIN}/api/v1
RUN test -n "$STAGING_ORIGIN" && npm run build

FROM caddy:2-alpine
COPY --from=frontend /app/frontend/dist /srv
COPY deploy/staging/Caddyfile /etc/caddy/Caddyfile
