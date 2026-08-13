# Shared front-door reverse proxy

Multiple NetBox plugin demo deployments (this repo's, and potentially
sibling plugin repos like `netbox-service-offerings-plugin`) can share one
runner. Only one process can bind host ports 80/443 at a time, so instead of
each plugin repo's pipeline running its own nginx bound directly to those
ports, there's a single shared front-door nginx that owns 80/443 and routes
to each plugin's `netbox` container by domain name (SNI on 443, `Host` on
80->443 redirect) — real name-based virtual hosting, not a port-per-plugin
hack.

This directory is **not** part of this repo's own CI/CD pipeline. It's
infrastructure shared across repos, so it's set up **once, by hand**, and
left running indefinitely; no plugin's `ci-cd.yml` starts, stops, or rebuilds
it. What each plugin's pipeline *does* do, every deploy: write its own
domain's server-block file into the shared conf.d directory below, and ask
this container to reload — see `ci/scripts/render-proxy-conf.sh` in this
repo.

## One-time setup (per runner)

```bash
# 1. Create the shared external network every plugin stack's `netbox`
#    service joins (see ci/docker/docker-compose.yml's `edge` network).
docker network create netbox-edge

# 2. Create the host directories the front door bind-mounts. conf.d holds
#    one rendered *.conf per domain (one per plugin); certs holds one
#    subdirectory per domain (fullchain.pem + privkey.pem), written by each
#    plugin's own ci/scripts/issue-cert.sh.
sudo mkdir -p /opt/netbox-edge-proxy/conf.d /opt/netbox-edge-proxy/certs
sudo chown "$(whoami)" /opt/netbox-edge-proxy/conf.d /opt/netbox-edge-proxy/certs

# 3. Start the front door itself. It will boot with an empty conf.d (no
#    domains configured yet) — that's fine, each plugin's own next deploy
#    populates its own file and reloads it.
docker compose -f ci/shared-proxy/docker-compose.yml up -d
```

After this, deploying (or re-deploying) any plugin repo against this runner
"just works" — its pipeline renders its own `<domain>.conf`, issues its own
cert, reloads this container, and brings up its own stack joined to
`netbox-edge`.

## Adding another plugin repo to the same runner

1. Its `docker-compose.yml` `netbox` service needs to join the `edge`
   external network (`name: netbox-edge`) under its **own** stable alias —
   see this repo's `ci/docker/docker-compose.yml` for the pattern
   (`aliases: [netbox-certificate-plugin]`). Aliases must be unique across
   every repo sharing this runner, or the front door's `proxy_pass` can't
   tell them apart.
2. It needs its own `ci/shared-proxy/<its-alias>.conf.template` and its own
   `ci/scripts/render-proxy-conf.sh` (or equivalent), writing to
   `$EDGE_CONF_DIR/<its-domain>.conf` — a distinct filename from every other
   plugin's, so deploys never overwrite each other's routing.
3. Its `ci/scripts/issue-cert.sh` needs `CERT_DIR` pointed at
   `$EDGE_CERTS_DIR/<its-domain>` (this repo's script already defaults there
   — see that script's own `CERT_DIR` default).

## Removing this repo's own routing (e.g. decommissioning the demo)

```bash
rm -f /opt/netbox-edge-proxy/conf.d/<this-repo's-NETBOX_DOMAIN>.conf
rm -rf /opt/netbox-edge-proxy/certs/<this-repo's-NETBOX_DOMAIN>
docker exec netbox-edge-proxy nginx -s reload
```

Only tear down the front door itself (`docker compose -f
ci/shared-proxy/docker-compose.yml down`) once **no** plugin repo on this
runner still needs it.
