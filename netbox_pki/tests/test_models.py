from datetime import date, timedelta

from django.core.exceptions import ValidationError
from django.test import TestCase

from netbox_pki.choices import ProtocolTypeChoices
from netbox_pki.models import Certificate, CertificateAuthority, Protocol


class ProtocolValidationTestCase(TestCase):
    def test_acme_requires_directory_url_challenge_type_and_key_ref(self):
        protocol = Protocol(name='acme-incomplete', type=ProtocolTypeChoices.TYPE_ACME)
        with self.assertRaises(ValidationError):
            protocol.clean()

    def test_acme_dns01_requires_dns_provider_and_credential(self):
        protocol = Protocol(
            name='acme-dns01',
            type=ProtocolTypeChoices.TYPE_ACME,
            acme_directory_url='https://acme.example.com/directory',
            acme_challenge_type='dns-01',
            acme_account_key_ref='vault://acme/key',
        )
        with self.assertRaises(ValidationError):
            protocol.clean()

    def test_acme_complete_passes(self):
        protocol = Protocol(
            name='acme-ok',
            type=ProtocolTypeChoices.TYPE_ACME,
            acme_directory_url='https://acme.example.com/directory',
            acme_challenge_type='http-01',
            acme_account_key_ref='vault://acme/key',
        )
        protocol.clean()

    def test_scep_requires_core_fields(self):
        protocol = Protocol(name='scep-incomplete', type=ProtocolTypeChoices.TYPE_SCEP)
        with self.assertRaises(ValidationError):
            protocol.clean()

    def test_scep_complete_passes(self):
        protocol = Protocol(
            name='scep-ok',
            type=ProtocolTypeChoices.TYPE_SCEP,
            scep_url='https://scep.example.com',
            scep_ca_fingerprint='ab:cd:ef',
            scep_challenge_secret_ref='vault://scep/secret',
            scep_encryption_algorithm='aes256',
            scep_digest_algorithm='sha256',
            scep_renewal_mode='renewal',
        )
        protocol.clean()


class CertificateAuthorityValidationTestCase(TestCase):
    def setUp(self):
        self.protocol = Protocol.objects.create(
            name='manual-protocol',
            type=ProtocolTypeChoices.TYPE_SCEP,
            scep_url='https://scep.example.com',
            scep_ca_fingerprint='ab:cd:ef',
            scep_challenge_secret_ref='vault://scep/secret',
            scep_encryption_algorithm='aes256',
            scep_digest_algorithm='sha256',
            scep_renewal_mode='renewal',
        )

    def test_csr_requires_parent_ca(self):
        ca = CertificateAuthority(name='root-ca', protocol=self.protocol, csr='-----BEGIN CSR-----')
        with self.assertRaises(ValidationError):
            ca.clean()

    def test_ca_cannot_be_its_own_parent(self):
        ca = CertificateAuthority.objects.create(name='root-ca', protocol=self.protocol)
        ca.parent_ca = ca
        with self.assertRaises(ValidationError):
            ca.clean()

    def test_expiration_date_auto_calculated_from_duration(self):
        ca = CertificateAuthority(name='root-ca-2', protocol=self.protocol, expiration='1_year')
        ca.save()
        self.assertEqual(ca.created_date, date.today())
        self.assertEqual(ca.expiration_date, date.today() + timedelta(days=365))

    def test_child_expiration_cannot_exceed_parent_expiration(self):
        parent = CertificateAuthority.objects.create(
            name='parent-ca',
            protocol=self.protocol,
            expiration='1_year',
        )
        child = CertificateAuthority(
            name='child-ca',
            protocol=self.protocol,
            parent_ca=parent,
            expiration_date=parent.expiration_date + timedelta(days=1),
        )
        with self.assertRaises(ValidationError):
            child.clean()


class CertificateValidationTestCase(TestCase):
    def setUp(self):
        self.protocol = Protocol.objects.create(
            name='manual-protocol',
            type=ProtocolTypeChoices.TYPE_SCEP,
            scep_url='https://scep.example.com',
            scep_ca_fingerprint='ab:cd:ef',
            scep_challenge_secret_ref='vault://scep/secret',
            scep_encryption_algorithm='aes256',
            scep_digest_algorithm='sha256',
            scep_renewal_mode='renewal',
        )
        self.ca = CertificateAuthority.objects.create(
            name='issuing-ca',
            protocol=self.protocol,
            expiration='2_years',
        )

    def test_automatic_expiration_inherits_from_ca(self):
        cert = Certificate(
            cn='host.example.com',
            ca=self.ca,
            certificate='-----BEGIN CERTIFICATE-----',
            private_key='vault://certs/host',
        )
        cert.save()
        self.assertEqual(cert.expiration_date, date.today() + timedelta(days=730))

    def test_explicit_expiration_overrides_ca(self):
        cert = Certificate(
            cn='host2.example.com',
            ca=self.ca,
            certificate='-----BEGIN CERTIFICATE-----',
            private_key='vault://certs/host2',
            expiration='45_days',
        )
        cert.save()
        self.assertEqual(cert.expiration_date, date.today() + timedelta(days=45))
