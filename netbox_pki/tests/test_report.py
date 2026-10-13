from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from tenancy.models import Tenant
from users.models import User

from netbox_pki.choices import CertificateExpiryStateChoices, CertificateStatusChoices, ProtocolTypeChoices
from netbox_pki.expiry import expiry_counts
from netbox_pki.filtersets import CertificateFilterSet
from netbox_pki.models import Certificate, CertificateAuthority, Protocol


class CertificateExpiryTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        protocol = Protocol.objects.create(
            name='manual-protocol',
            type=ProtocolTypeChoices.TYPE_SCEP,
            scep_url='https://scep.example.com',
            scep_ca_fingerprint='ab:cd:ef',
            scep_challenge_secret_ref='vault://scep/secret',
            scep_encryption_algorithm='aes256',
            scep_digest_algorithm='sha256',
            scep_renewal_mode='renewal',
        )
        cls.ca = CertificateAuthority.objects.create(name='ca-1', protocol=protocol)
        cls.other_ca = CertificateAuthority.objects.create(name='ca-2', protocol=protocol)
        cls.tenant = Tenant.objects.create(name='Tenant 1', slug='tenant-1')
        today = timezone.localdate()

        def cert(cn, days, status=CertificateStatusChoices.STATUS_MANUAL, ca=None, tenant=None):
            return Certificate.objects.create(
                cn=cn,
                ca=ca or cls.ca,
                tenant=tenant,
                status=status,
                certificate='-----BEGIN CERTIFICATE-----',
                private_key=f'vault://certs/{cn}',
                created_date=today - timedelta(days=400),
                expiration_date=today + timedelta(days=days) if days is not None else None,
            )

        cert('expired.example.com', -1)
        cert('today.example.com', 0)
        cert('in-10.example.com', 10, tenant=cls.tenant)
        cert('in-11.example.com', 11)
        cert('in-30.example.com', 30)
        cert('in-31.example.com', 31, ca=cls.other_ca)
        cert('revoked-future.example.com', 100, status=CertificateStatusChoices.STATUS_REVOKED)
        cert('revoked-past.example.com', -5, status=CertificateStatusChoices.STATUS_REVOKED)
        # Automatic expiration with a CA that has no duration leaves expiration_date unset.
        cert('no-date.example.com', None)

    def _filtered_cns(self, **params):
        return set(CertificateFilterSet(params, Certificate.objects.all()).qs.values_list('cn', flat=True))

    def test_counts(self):
        counts = expiry_counts(Certificate.objects.all())
        self.assertEqual(counts[CertificateExpiryStateChoices.STATE_VALID], 5)
        self.assertEqual(counts[CertificateExpiryStateChoices.STATE_EXPIRED], 1)
        self.assertEqual(counts[CertificateExpiryStateChoices.STATE_REVOKED], 2)
        self.assertEqual(counts[CertificateExpiryStateChoices.STATE_EXPIRING_30], 4)
        self.assertEqual(counts[CertificateExpiryStateChoices.STATE_EXPIRING_10], 2)
        self.assertEqual(counts['no_date'], 1)

    def test_filter_matches_counts(self):
        self.assertEqual(
            self._filtered_cns(expiry_state=[CertificateExpiryStateChoices.STATE_EXPIRING_10]),
            {'today.example.com', 'in-10.example.com'},
        )
        self.assertEqual(
            self._filtered_cns(expiry_state=[CertificateExpiryStateChoices.STATE_EXPIRED]),
            {'expired.example.com'},
        )
        self.assertEqual(
            self._filtered_cns(expiry_state=[CertificateExpiryStateChoices.STATE_REVOKED]),
            {'revoked-future.example.com', 'revoked-past.example.com'},
        )

    def test_filter_by_tenant_and_ca(self):
        self.assertEqual(self._filtered_cns(tenant_id=[self.tenant.pk]), {'in-10.example.com'})
        self.assertEqual(self._filtered_cns(ca_id=[self.other_ca.pk]), {'in-31.example.com'})

    def test_days_remaining(self):
        self.assertEqual(Certificate.objects.get(cn='in-10.example.com').days_remaining, 10)
        self.assertEqual(Certificate.objects.get(cn='expired.example.com').days_remaining, -1)
        self.assertIsNone(Certificate.objects.get(cn='no-date.example.com').days_remaining)

    def test_report_view_renders(self):
        user = User.objects.create_superuser(username='report-admin', password='x')
        self.client.force_login(user)
        response = self.client.get(
            reverse('plugins:netbox_pki:certificate_report'),
            {'tenant_id': self.tenant.pk, 'expiry_state': CertificateExpiryStateChoices.STATE_EXPIRING_10},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Expiration in 10 days')
