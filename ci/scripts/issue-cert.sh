#!/usr/bin/env bash
# Issues (or reuses) a Let's Encrypt certificate for $NETBOX_DOMAIN via a
# DNS-01 challenge against Websupport DNS, using acme.sh's built-in
# `dns_websupport` provider (https://github.com/acmesh-official/acme.sh).
#
# Unlike a per-repo nginx setup, the certificate is written directly into
# the *shared* front-door proxy's cert directory (see
# ci/shared-proxy/README.md) — there is no local nginx in this repo's own
# docker-compose.yml to serve it from.
#
# acme.sh is idempotent: if a valid certificate already exists and is not
# yet within its ~60-day renewal window, `--issue` is a no-op ("Skip, Next
# renewal time is ..." / exit code 2). Otherwise it performs the DNS-01
# challenge and issues or renews the certificate. This is what gives us
# "reuse if it exists, else challenge" without any extra bookkeeping.
set -euo pipefail

: "${NETBOX_DOMAIN:?NETBOX_DOMAIN must be set}"
: "${ACME_EMAIL:?ACME_EMAIL must be set}"
: "${WS_ApiKey:?WS_ApiKey must be set (Websupport REST API key)}"
: "${WS_ApiSecret:?WS_ApiSecret must be set (Websupport REST API secret)}"

ACME_HOME="${ACME_HOME:-$HOME/.acme.sh}"
ACME="$ACME_HOME/acme.sh"
# Shared front door's cert directory (see ci/shared-proxy/docker-compose.yml
# EDGE_CERTS_DIR); one subdirectory per domain, since multiple plugin repos'
# certs live there side by side.
CERT_DIR="${CERT_DIR:-${EDGE_CERTS_DIR:-/opt/netbox-edge-proxy/certs}/$NETBOX_DOMAIN}"
EDGE_PROXY_CONTAINER="${EDGE_PROXY_CONTAINER:-netbox-edge-proxy}"

mkdir -p "$CERT_DIR"
chmod 700 "$CERT_DIR"

if [ ! -x "$ACME" ]; then
  echo "acme.sh not found at $ACME_HOME — installing..."
  curl -fsSL https://get.acme.sh | sh -s email="$ACME_EMAIL"
fi

export WS_ApiKey WS_ApiSecret

set +e
"$ACME" --issue --dns dns_websupport -d "$NETBOX_DOMAIN" --home "$ACME_HOME"
rc=$?
set -e

if [ "$rc" -ne 0 ] && [ "$rc" -ne 2 ]; then
  echo "acme.sh --issue failed with exit code $rc" >&2
  exit "$rc"
fi

"$ACME" --install-cert -d "$NETBOX_DOMAIN" --home "$ACME_HOME" \
  --key-file       "$CERT_DIR/privkey.pem" \
  --fullchain-file "$CERT_DIR/fullchain.pem" \
  --reloadcmd      "docker exec '$EDGE_PROXY_CONTAINER' nginx -s reload || true"

chmod 600 "$CERT_DIR/privkey.pem"
chmod 644 "$CERT_DIR/fullchain.pem"
echo "Certificate ready at $CERT_DIR/fullchain.pem"
