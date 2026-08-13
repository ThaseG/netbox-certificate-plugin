#!/usr/bin/env bash
# Pre-deploy cleanup. Deliberately destructive on the stack's own named
# volumes (Postgres/Redis/media/reports/scripts — everything declared under
# `volumes:` in docker-compose.yml): every deploy starts NetBox from a
# completely empty database, migrated fresh via this repo's own
# migrations/0001_initial.py. There is never an "already migrated" instance
# to preserve, which is also why this plugin hand-edits 0001_initial.py in
# place for schema changes instead of accumulating incremental migrations —
# see that file's own header comment.
#
# Scoped to THIS repo's own compose project only. `docker compose down`
# never removes networks marked `external: true` (the shared `netbox-edge`
# network) regardless of --volumes, so the shared front-door proxy and any
# sibling plugin's stack are untouched — see ci/shared-proxy/README.md.
set -euo pipefail

# .. here is ci/ (this script lives in ci/scripts/), not the repo root
CI_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
COMPOSE_FILE="${COMPOSE_FILE:-$CI_ROOT/docker/docker-compose.yml}"
# docker-compose.yml requires every service's env vars to resolve (via
# ${VAR:?err} guards) just to *parse* the file — `down` needs this file
# present just as much as `up` does, even though it isn't writing/reading
# any of the actual values.
ENV_FILE="${ENV_FILE:-$CI_ROOT/docker/.env}"

if [ -f "$COMPOSE_FILE" ]; then
  echo "Stopping current stack and wiping its named volumes (fresh NetBox on next 'up')..."
  compose_args=(-f "$COMPOSE_FILE")
  if [ -f "$ENV_FILE" ]; then
    compose_args=(--env-file "$ENV_FILE" "${compose_args[@]}")
  else
    echo "WARNING: $ENV_FILE not found — 'docker compose down' will likely fail to parse" \
         "docker-compose.yml's required environment variables." >&2
  fi
  # Deliberately don't hard-fail the deploy if this errors (e.g. nothing
  # was running yet) — but DO surface it loudly, since a silently-swallowed
  # failure here leaves stale containers/volumes behind that the next `up`
  # won't necessarily reconcile with, which is exactly the kind of thing
  # that produces confusing "container is up but can't reach its peers" (or
  # "schema looks half-migrated") failures downstream.
  if ! docker compose "${compose_args[@]}" down --remove-orphans --volumes; then
    echo "WARNING: 'docker compose down' failed (see above) — stale containers/volumes may remain." >&2
  fi
fi

echo "Pruning dangling images..."
docker image prune -f

echo "Pruning build cache older than 24h..."
docker builder prune -f --filter "until=24h"
