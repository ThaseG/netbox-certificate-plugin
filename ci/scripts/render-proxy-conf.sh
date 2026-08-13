#!/usr/bin/env bash
# Renders ci/shared-proxy/netbox-certificate-plugin.conf.template for the
# current $NETBOX_DOMAIN and writes it into the shared front-door proxy's
# conf.d directory (see ci/shared-proxy/README.md), then reloads that
# container so the new/updated server block takes effect. This repo's own
# routing only — never touches any other domain's file in that directory.
set -euo pipefail

: "${NETBOX_DOMAIN:?NETBOX_DOMAIN must be set}"

# .. here is ci/ (this script lives in ci/scripts/), not the repo root
CI_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TEMPLATE="$CI_ROOT/shared-proxy/netbox-certificate-plugin.conf.template"
EDGE_CONF_DIR="${EDGE_CONF_DIR:-/opt/netbox-edge-proxy/conf.d}"
EDGE_PROXY_CONTAINER="${EDGE_PROXY_CONTAINER:-netbox-edge-proxy}"

mkdir -p "$EDGE_CONF_DIR"

# Restricted to ${NETBOX_DOMAIN} only, so nginx's own $host/$scheme/etc
# runtime variables in the template are left untouched — see the
# template's own header comment. The single quotes are deliberate: this is
# envsubst's own "which variables to substitute" argument, not a shell
# expansion.
# shellcheck disable=SC2016
envsubst '${NETBOX_DOMAIN}' < "$TEMPLATE" > "$EDGE_CONF_DIR/$NETBOX_DOMAIN.conf.new"
mv "$EDGE_CONF_DIR/$NETBOX_DOMAIN.conf.new" "$EDGE_CONF_DIR/$NETBOX_DOMAIN.conf"

echo "Wrote $EDGE_CONF_DIR/$NETBOX_DOMAIN.conf"

if docker inspect "$EDGE_PROXY_CONTAINER" >/dev/null 2>&1; then
  docker exec "$EDGE_PROXY_CONTAINER" nginx -t
  docker exec "$EDGE_PROXY_CONTAINER" nginx -s reload
  echo "Reloaded $EDGE_PROXY_CONTAINER"
else
  echo "WARNING: front-door container '$EDGE_PROXY_CONTAINER' not found — is" \
       "ci/shared-proxy/ set up on this runner yet? See ci/shared-proxy/README.md." >&2
  exit 1
fi
