#!/usr/bin/env bash
# Live end-to-end smoke test against the actually-deployed instance over
# real HTTPS — deliberately separate from netbox_pki's Django test suite
# (`manage.py test netbox_pki`, run earlier in the Test stage), which only
# exercises the app in-process and can't see problems in the real
# nginx -> TLS -> WSGI path (misconfigured proxying, a cert that didn't
# actually get installed, the shared front door not routing to this
# plugin's container, etc). This script is what would actually notice
# those.
#
# Covers:
#   - web:  /login/ reachable anonymously; an authenticated-only plugin
#           page is reachable only after a real session login (proves
#           LOGIN_REQUIRED enforcement AND that the UI routes resolve).
#   - api:  POST -> GET -> PATCH -> DELETE round trip against
#           /api/plugins/pki/requestors/ — chosen because Requestor is the
#           only netbox_pki model with no other mandatory fields or
#           conditionally-required siblings (Protocol/CertificateAuthority/
#           Certificate all need either a FK to another object or
#           type-specific fields — see models.py's clean() methods) —
#           ending in DELETE so the showcase instance isn't left with a
#           leftover test row after a pass.
set -euo pipefail

: "${NETBOX_DOMAIN:?NETBOX_DOMAIN must be set}"
: "${NETBOX_SUPERUSER_API_TOKEN:?NETBOX_SUPERUSER_API_TOKEN must be set}"
: "${NETBOX_SUPERUSER_API_KEY:?NETBOX_SUPERUSER_API_KEY must be set}"
: "${NETBOX_SUPERUSER_PASSWORD:?NETBOX_SUPERUSER_PASSWORD must be set}"

BASE_URL="https://${NETBOX_DOMAIN}"
# The superuser's bootstrap token is a v2 token (netbox-docker's
# super_user.py default), which authenticates completely differently from
# the classic single-opaque-string v1 scheme: Bearer <TOKEN_PREFIX><key>.<secret>,
# not "Authorization: Token <value>". TOKEN_PREFIX ('nbt_') is a fixed
# NetBox constant (users/constants.py), not configurable.
API_AUTH_HEADER="Authorization: Bearer nbt_${NETBOX_SUPERUSER_API_KEY}.${NETBOX_SUPERUSER_API_TOKEN}"
COOKIE_JAR="$(mktemp)"
RESPONSE_FILE="$(mktemp)"
trap 'rm -f "$COOKIE_JAR" "$RESPONSE_FILE"' EXIT

fail() {
  echo "SMOKE TEST FAILED: $1" >&2
  exit 1
}

expect_status() {
  # Optional 4th arg: path to the response body, echoed on failure so a
  # rejection reason (DRF's "detail" message, a validation error, etc.)
  # is visible directly in the CI log instead of just a bare status code.
  local description="$1" actual="$2" expected="$3" body_file="${4:-}"
  if [ "$actual" != "$expected" ]; then
    if [ -n "$body_file" ] && [ -s "$body_file" ]; then
      echo "Response body:" >&2
      cat "$body_file" >&2
    fi
    fail "$description — expected HTTP $expected, got $actual"
  fi
  echo "OK: $description ($actual)"
}

#
# Web: anonymous /login/ + real session login + authenticated plugin page
#

status=$(curl -sS -o /dev/null -w '%{http_code}' "$BASE_URL/login/")
expect_status "GET /login/ (anonymous)" "$status" "200"

curl -sS -c "$COOKIE_JAR" -o /dev/null "$BASE_URL/login/"
# Netscape cookie-jar format is tab-separated with the value as the last
# field; `|| true` stops a no-match `grep` (exit 1) from tripping `set -e`
# before the explicit check below can give a clearer error message.
csrf_token=$(grep 'csrftoken' "$COOKIE_JAR" | awk '{print $NF}' || true)
[ -n "$csrf_token" ] || fail "could not extract CSRF token from login page"

login_status=$(curl -sS -b "$COOKIE_JAR" -c "$COOKIE_JAR" -o /dev/null -w '%{http_code}' \
  -H "Referer: $BASE_URL/login/" \
  -H "X-CSRFToken: $csrf_token" \
  --data-urlencode "csrfmiddlewaretoken=$csrf_token" \
  --data-urlencode "username=admin" \
  --data-urlencode "password=$NETBOX_SUPERUSER_PASSWORD" \
  "$BASE_URL/login/")
# NetBox redirects (302) to the dashboard on a successful session login
expect_status "POST /login/ (session login)" "$login_status" "302"

status=$(curl -sS -b "$COOKIE_JAR" -o /dev/null -w '%{http_code}' "$BASE_URL/plugins/pki/requestors/")
expect_status "GET /plugins/pki/requestors/ (authenticated session)" "$status" "200"

#
# API: POST -> GET -> PATCH -> DELETE against /api/plugins/pki/requestors/
#

status=$(curl -sS -o "$RESPONSE_FILE" -w '%{http_code}' -X POST "$BASE_URL/api/plugins/pki/requestors/" \
  -H "$API_AUTH_HEADER" -H "Content-Type: application/json" \
  -d '{"name": "Smoke Test Requestor"}')
expect_status "POST /api/plugins/pki/requestors/" "$status" "201" "$RESPONSE_FILE"
requestor_id=$(python3 -c "import json; print(json.load(open('$RESPONSE_FILE'))['id'])")
detail_url="$BASE_URL/api/plugins/pki/requestors/$requestor_id/"

status=$(curl -sS -o "$RESPONSE_FILE" -w '%{http_code}' "$detail_url" -H "$API_AUTH_HEADER")
expect_status "GET $detail_url" "$status" "200" "$RESPONSE_FILE"
name=$(python3 -c "import json; print(json.load(open('$RESPONSE_FILE'))['name'])")
[ "$name" = "Smoke Test Requestor" ] || fail "GET returned unexpected name: $name"

status=$(curl -sS -o "$RESPONSE_FILE" -w '%{http_code}' -X PATCH "$detail_url" \
  -H "$API_AUTH_HEADER" -H "Content-Type: application/json" \
  -d '{"description": "Created by ci/scripts/smoke-test.sh"}')
expect_status "PATCH $detail_url" "$status" "200" "$RESPONSE_FILE"
description=$(python3 -c "import json; print(json.load(open('$RESPONSE_FILE'))['description'])")
[ "$description" = "Created by ci/scripts/smoke-test.sh" ] || fail "PATCH did not persist: got '$description'"

status=$(curl -sS -o "$RESPONSE_FILE" -w '%{http_code}' -X DELETE "$detail_url" -H "$API_AUTH_HEADER")
expect_status "DELETE $detail_url" "$status" "204" "$RESPONSE_FILE"

echo "All smoke tests passed."
