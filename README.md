# netbox-certificate-plugin (PKI)

A [NetBox](https://github.com/netbox-community/netbox) plugin that lets you manage Certificate Authorities and
Certificates directly in NetBox: track who requested what, which CA issued it, how it's enrolled (ACME/SCEP), and
where its material actually lives (a Vault URL, not the key itself), alongside the rest of your infrastructure data.

The plugin's Django app label is `netbox_pki`.

## Screenshots

> _TODO: add screenshots here._


| Certificate list | Certificate Authority detail | PKI navigation menu |
| --- | --- | --- |
| _placeholder_ | _placeholder_ | _placeholder_ |

## Data model

| Model | Description |
| --- | --- |
| **Certificate** | An issued certificate: CN, issuing CA, status, lifecycle dates, alternative names, and a reference to where its material lives (`private_key` is a Vault URL, never the key itself). |
| **CertificateAuthority** | A CA's own metadata: status, enrollment protocol, an optional parent CA (for intermediate/sub-CAs — a CSR can only be set when a parent is chosen, and a child's expiration can't outlive its parent's), and a default certificate expiration for certs it issues. |
| **Requestor** | The team/entity that requested a Certificate or CA, optionally linked to NetBox Contacts and/or Contact Groups. |
| **Protocol** | Enrollment protocol configuration — ACME or SCEP — with fields required conditionally on the chosen type (e.g. DNS-01 challenge settings only when `acme_challenge_type` is `dns-01`; SCEP's endpoint/fingerprint/algorithm fields only when `type` is `scep`). |

All four models support NetBox's standard object features: tags, comments (Markdown), custom fields, and change
logging.

Validation rules enforced identically by the web UI and the REST API (see each model's `clean()` in
[`netbox_pki/models.py`](netbox_pki/models.py)):
- A CSR can only be set on a Certificate Authority if a parent CA is chosen.
- A CA cannot be its own parent.
- A child CA's expiration date cannot be later than its parent CA's expiration date.
- Protocol fields required for ACME (directory URL, challenge type, account key reference — plus DNS
  provider/credential when the challenge type is `dns-01`, and EAB key ID/HMAC reference when External Account
  Binding is required) or for SCEP (endpoint URL, CA fingerprint, challenge secret, encryption/digest algorithm,
  renewal mode) are enforced only for the selected protocol type.
- `created_date`/`expiration_date` on Certificates and CAs default to today and `created_date + expiration`
  respectively when left blank; a Certificate's "Automatic" expiration inherits its issuing CA's expiration
  duration.

## Compatibility

| Plugin Version | NetBox Version | Python Version |
| --- | --- | --- |
| 0.1.* | 4.6.x | \>= 3.10 |

The pinned combination actually built and deployed by this repo's CI/CD pipeline is tracked in
[`versions.sh`](versions.sh) (currently NetBox `v4.6.8`).

## Installation

### Option A: existing NetBox installation

Install the plugin into NetBox's virtual environment:

```bash
source /opt/netbox/venv/bin/activate
pip install git+https://github.com/ThaseG/netbox-certificate-plugin.git
```

Enable it in `/opt/netbox/netbox/netbox/configuration.py` (or `plugins.py` if you split your config that way):

```python
PLUGINS = [
    "netbox_pki",
]
```

Then run migrations and collect static files as usual:

```bash
python manage.py migrate
python manage.py collectstatic --no-input
```

Restart NetBox (`systemctl restart netbox netbox-rq` or equivalent).

### Option B: Docker (bundled demo/CI stack)

This repo includes a Docker Compose deployment under [`ci/docker/`](ci/docker/) that builds NetBox with this plugin
(and nothing else — no third-party plugins bundled, since this stack exists solely to build/test/showcase
netbox_pki itself) baked in via [`ci/docker/Dockerfile-Plugins`](ci/docker/Dockerfile-Plugins). It's what
[`.github/workflows/ci-cd.yml`](.github/workflows/ci-cd.yml) deploys automatically on every push. HTTPS is provided
by a separate nginx project (see [Reverse proxy and TLS](#reverse-proxy-and-tls)). To run it yourself, once the
`netbox-edge` Docker network exists:

```bash
source versions.sh
cp ci/docker/.env.example ci/docker/.env   # fill in real values, see comments in the file
docker compose --env-file ci/docker/.env -f ci/docker/docker-compose.yml up -d --build
```

## Usage

### Web UI

Once enabled, a **PKI** entry appears in NetBox's plugins navigation menu, listing Certificates, Certificate
Authorities, Requestors and Protocols. Each model gets the standard NetBox list/detail/add/edit/delete views; a
Certificate Authority's detail page also shows its child CAs and the certificates it has issued.

### REST API

All models are exposed under `/api/plugins/pki/`, following NetBox's usual REST conventions (list/detail views,
filtering, `?brief=true`, bulk operations):

- `/api/plugins/pki/certificates/`
- `/api/plugins/pki/cas/`
- `/api/plugins/pki/requestors/`
- `/api/plugins/pki/protocols/`

Example — create a `Requestor`, then read it back:

```bash
curl -X POST https://<netbox-host>/api/plugins/pki/requestors/ \
  -H "Authorization: Bearer nbt_<key>.<secret>" \
  -H "Content-Type: application/json" \
  -d '{"name": "Firewall Team"}'

curl https://<netbox-host>/api/plugins/pki/requestors/ \
  -H "Authorization: Bearer nbt_<key>.<secret>"
```

(Use `Authorization: Token <value>` instead if you're using a legacy v1 API token.)

### Permissions

Access is controlled by NetBox's standard per-model permissions, e.g. `netbox_pki.view_certificate`,
`netbox_pki.add_certificate`, `netbox_pki.change_certificate`, `netbox_pki.delete_certificate` (and equivalently
for `certificateauthority`, `requestor` and `protocol`).

## Development

| Path | Purpose |
| --- | --- |
| [`netbox_pki/`](netbox_pki/) | The plugin itself — models, REST API, UI views, migrations, tests. |
| [`ci/docker/`](ci/docker/) | Docker Compose stack + Dockerfile used both for local runs and the CI/CD deploy. |
| [`ci/scripts/`](ci/scripts/) | Scripts used by the CI/CD pipeline (pre-cleanup, smoke tests, demo data seeding). |
| [`versions.sh`](versions.sh) | Single source of truth for the pinned NetBox version and the plugin's own release version. |
| [`pyproject.toml`](pyproject.toml) | Package metadata, plus `ruff` lint/format configuration. |

Run the test suite and linters the same way CI does:

```bash
ruff check netbox_pki/
ruff format --check netbox_pki/
python manage.py test netbox_pki
```

### CI/CD

[`.github/workflows/ci-cd.yml`](.github/workflows/ci-cd.yml) runs on every push, as seven staged jobs:

1. **Pre-Clean** — tears down this repo's own previously running stack *and wipes its named volumes*
   ([`ci/scripts/pre-cleanup.sh`](ci/scripts/pre-cleanup.sh)), so every deploy starts NetBox from a completely
   empty database. Never touches the shared nginx proxy or a sibling plugin's own stack.
2. **Code-Review** — `ruff`, `shellcheck`, `yamllint`, JSON validation of the seed data, and a check that
   `pyproject.toml`'s version matches `versions.sh`.
3. **Build** — builds the NetBox + plugin Docker image per `versions.sh`.
4. **Test** — deploys the stack, then runs `manage.py check`, a migration drift check, the Django test suite, and a live HTTPS smoke test
   (session login + a full API POST/GET/PATCH/DELETE round trip).
5. **Test Deployment** — seeds the now-verified instance with demo data (contacts, contact groups, and one of
   every netbox_pki object type — Protocols, Requestors, Certificate Authorities including a parent/child pair,
   and Certificates) via the REST API ([`ci/scripts/test-deployment.py`](ci/scripts/test-deployment.py) +
   [`test-deployment.json`](ci/scripts/test-deployment.json)), so the showcase instance has real, linked objects to
   look at.
6. **Deploy** — tags the repo `v<NETBOX_PKI_PLUGIN_VERSION>` (from `versions.sh`), if that tag doesn't already
   exist.
7. **Post-Clean** — always runs, whatever happened in the stages above (success, a failure partway through, or a
   cancellation): prunes dangling Docker images and build cache older than 24h on the runner, so disk usage doesn't
   grow unboundedly between infrequent pushes. Never touches the running stack — pruning
   only removes images/cache nothing is currently using.

The instance left running after a successful **Test** stage doubles as a live showcase — but since every deploy
wipes the database, it starts empty each time and never carries data over from a previous deploy. This is also why
the plugin's own migration ([`netbox_pki/migrations/0001_initial.py`](netbox_pki/migrations/0001_initial.py)) is
hand-edited in place for schema changes rather than accumulating incremental migration files: there's never an
already-migrated instance whose existing data a later migration would need to preserve.

#### Reverse proxy and TLS

This repo doesn't run nginx or manage TLS certificates. Both, including certificate renewal, are handled by a
separate nginx project, which routes to this repo's `netbox` container over the shared `netbox-edge` Docker network
(alias `netbox-certificate-plugin`, port 8080). That network must already exist on the runner before a deploy.

## License

[MIT](LICENSE)
