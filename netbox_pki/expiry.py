"""
Expiry state of Certificates, derived from status + expiration_date against today's date.

Single source of truth for the Certificate Report's counters and for the `expiry_state` filter
that narrows its table, so a card's number always matches the rows it links to:

- Revoked:               status is Revoked, regardless of dates.
- Expired:               not revoked, expiration_date before today.
- Valid:                 not revoked, expiration_date today or later.
- Expiration in N days:  not revoked, expiration_date between today and today + N (inclusive) —
                         a subset of Valid, and the 10-day set is a subset of the 30-day set.

A Certificate without an expiration_date is in none of these except Revoked.
"""

from datetime import timedelta

from django.db.models import Count, Q
from django.utils import timezone

from .choices import CertificateExpiryStateChoices, CertificateStatusChoices

EXPIRING_SOON_DAYS = 30
EXPIRING_CRITICAL_DAYS = 10


def expiry_state_q(state, today=None):
    """Q object selecting Certificates in the given CertificateExpiryStateChoices state."""
    today = today or timezone.localdate()
    revoked = Q(status=CertificateStatusChoices.STATUS_REVOKED)
    states = {
        CertificateExpiryStateChoices.STATE_REVOKED: revoked,
        CertificateExpiryStateChoices.STATE_EXPIRED: ~revoked & Q(expiration_date__lt=today),
        CertificateExpiryStateChoices.STATE_VALID: ~revoked & Q(expiration_date__gte=today),
        CertificateExpiryStateChoices.STATE_EXPIRING_30: ~revoked
        & Q(expiration_date__gte=today, expiration_date__lte=today + timedelta(days=EXPIRING_SOON_DAYS)),
        CertificateExpiryStateChoices.STATE_EXPIRING_10: ~revoked
        & Q(expiration_date__gte=today, expiration_date__lte=today + timedelta(days=EXPIRING_CRITICAL_DAYS)),
    }
    return states[state]


def expiry_counts(queryset, today=None):
    """Number of Certificates in `queryset` per expiry state, plus those without an
    expiration_date, in a single query."""
    today = today or timezone.localdate()
    aggregates = {
        state: Count('pk', filter=expiry_state_q(state, today)) for state in CertificateExpiryStateChoices.values()
    }
    aggregates['no_date'] = Count(
        'pk',
        filter=Q(expiration_date__isnull=True) & ~Q(status=CertificateStatusChoices.STATUS_REVOKED),
    )
    return queryset.aggregate(**aggregates)
