#!/usr/bin/env python3
"""Seeds the freshly-deployed NetBox instance with representative demo data
(contacts, contact groups, and one of every netbox_pki object type) via the
REST API, so there's something real to look at when showcasing/testing the
plugin manually — per its own request, this deployment seeds only what's
needed to exercise netbox_pki itself, not a full core-NetBox inventory.

Every CI deploy wipes the database (ci/scripts/pre-cleanup.sh), so this
always runs against an empty instance — no need to worry about existing
data or idempotency. Run after smoke-test.sh, against the same live HTTPS
instance and superuser token.

All the actual data lives in test-deployment.json, next to this script, as
an ordered mapping of {api_endpoint_path: [payload, ...]}. This script is a
generic engine, not per-object-type logic: it POSTs every payload to its
endpoint, in file order, resolving any field listed in REFERENCE_FIELDS
below from a slug/name/cn string into the real id of an object created
earlier in the same run.

File order in the JSON *is* creation order — an object referenced by a
later entry (by slug for Contact Groups, by name for Contacts/Protocols/
Requestors/Certificate Authorities, or by cn for Certificates — the one
netbox_pki model with neither a slug nor a name) must be listed earlier in
the file. A Certificate Authority's own `parent_ca` field references another
entry *within the same list*, by name — the root CA must simply be listed
before any of its children. JSON can't hold comments, so that ordering
requirement — and the object graph itself — is documented here and in
REFERENCE_FIELDS instead.

Stdlib-only (urllib), matching smoke-test.sh's dependency-free approach —
no extra `pip install` needed on the runner.
"""

import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

BASE_URL = None
API_AUTH_HEADER = None

DATA_FILE = Path(__file__).with_name('test-deployment.json')

# For each endpoint, which fields hold references to other objects rather
# than literal values, and which endpoint those references resolve
# against. A referenced object is looked up by its own `slug` if it has
# one, else by `name`, else by `cn` (see resolve()) — deliberately explicit
# per field/endpoint rather than inferred from the value itself, so a
# typo'd or wrong-endpoint reference fails loudly instead of silently
# resolving against the wrong thing. This table is also the object graph's
# documentation.
REFERENCE_FIELDS = {
    'tenancy/contacts/': {
        'groups': 'tenancy/contact-groups/',
    },
    'plugins/pki/requestors/': {
        'contact': 'tenancy/contacts/',
        'contact_group': 'tenancy/contact-groups/',
    },
    'plugins/pki/cas/': {
        'protocol': 'plugins/pki/protocols/',
        'parent_ca': 'plugins/pki/cas/',
        'requestor': 'plugins/pki/requestors/',
    },
    'plugins/pki/certificates/': {
        'ca': 'plugins/pki/cas/',
        'requestor': 'plugins/pki/requestors/',
    },
}


def env(name):
    value = os.environ.get(name)
    if not value:
        fail(f'{name} must be set')
    return value


def fail(message):
    print(f'TEST DEPLOYMENT FAILED: {message}', file=sys.stderr)
    sys.exit(1)


def api(method, path, payload=None):
    url = f'{BASE_URL}/api/{path}'
    data = json.dumps(payload).encode() if payload is not None else None
    request = urllib.request.Request(
        url,
        data=data,
        method=method,
        headers={
            'Authorization': API_AUTH_HEADER,
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            body = response.read()
            return json.loads(body) if body else None
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors='replace')
        fail(f'{method} {path} -> HTTP {e.code}\n{body}')
    except urllib.error.URLError as e:
        fail(f'{method} {path} -> {e}')


def created(endpoint, obj):
    print(f'  created {endpoint}: {obj["display"]} (id={obj["id"]})')
    return obj


def resolve(value, target_endpoint, created_objects):
    """Look up a single slug/name/cn reference against objects already
    created (earlier in the JSON file) at target_endpoint."""
    cache = created_objects.get(target_endpoint, {})
    if value not in cache:
        fail(
            f'Cannot resolve reference {value!r} against {target_endpoint} — no object with that slug/name/cn has '
            f'been created yet. Check test-deployment.json lists it earlier, and that the value is spelled '
            f'exactly right.'
        )
    return cache[value]


def resolve_field(value, target_endpoint, created_objects):
    """A reference field's value is either a single slug/name/cn (FK) or a
    list of them (M2M) — resolve whichever shape it is."""
    if isinstance(value, list):
        return [resolve(v, target_endpoint, created_objects) for v in value]
    return resolve(value, target_endpoint, created_objects)


def create_all(data):
    created_objects = {}  # endpoint -> {slug-or-name-or-cn: id}
    for endpoint, payloads in data.items():
        print(f'Creating {len(payloads)} object(s) at {endpoint}...')
        reference_fields = REFERENCE_FIELDS.get(endpoint, {})
        cache = created_objects.setdefault(endpoint, {})
        for payload in payloads:
            resolved = dict(payload)
            for field, target_endpoint in reference_fields.items():
                if field in resolved and resolved[field] is not None:
                    resolved[field] = resolve_field(resolved[field], target_endpoint, created_objects)
            obj = api('POST', endpoint, resolved)
            created(endpoint, obj)
            # Almost everything is keyed by slug-else-name (see resolve()),
            # but Certificate has neither — its own identity field is `cn`
            # instead (see models.py's Certificate.__str__).
            key = payload.get('slug') or payload.get('name') or payload.get('cn')
            if key is not None:
                if key in cache:
                    fail(f'Duplicate slug/name/cn {key!r} for {endpoint} in {DATA_FILE.name}')
                cache[key] = obj['id']


def main():
    global BASE_URL, API_AUTH_HEADER
    BASE_URL = f'https://{env("NETBOX_DOMAIN")}'
    # Same v2-token bearer scheme as smoke-test.sh: Bearer nbt_<key>.<secret>
    API_AUTH_HEADER = f'Bearer nbt_{env("NETBOX_SUPERUSER_API_KEY")}.{env("NETBOX_SUPERUSER_API_TOKEN")}'

    with DATA_FILE.open() as f:
        data = json.load(f)

    create_all(data)

    print('Test deployment data created successfully.')


if __name__ == '__main__':
    main()
