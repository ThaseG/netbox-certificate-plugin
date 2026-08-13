from datetime import timedelta

from django.core.exceptions import ValidationError
from django.db import models
from django.urls import reverse
from django.utils import timezone
from netbox.models import NetBoxModel

from .choices import (
    DURATION_DAYS,
    AcmeChallengeTypeChoices,
    CAExpirationChoices,
    CertificateExpirationChoices,
    CertificateStatusChoices,
    DefaultCertExpirationChoices,
    EnvironmentChoices,
    ProtocolTypeChoices,
    ScepDigestAlgorithmChoices,
    ScepEncryptionAlgorithmChoices,
    ScepRenewalModeChoices,
)


class Protocol(NetBoxModel):
    name = models.CharField(
        max_length=100,
        unique=True,
        help_text='Custom name for this Certificate Management Protocol',
    )
    type = models.CharField(
        max_length=20,
        choices=ProtocolTypeChoices,
        default=ProtocolTypeChoices.TYPE_ACME,
        verbose_name='Service type',
    )

    # --- ACME (mandatory when type == ACME) ---
    acme_directory_url = models.URLField(
        blank=True,
        verbose_name='Directory URL',
        help_text='e.g. https://acme-v02.api.letsencrypt.org/directory',
    )
    acme_challenge_type = models.CharField(
        max_length=20,
        choices=AcmeChallengeTypeChoices,
        blank=True,
    )
    acme_account_key_ref = models.CharField(
        max_length=500,
        blank=True,
        verbose_name='Account key reference',
        help_text='Vault URL for key',
    )
    # mandatory if acme_challenge_type == dns-01
    acme_dns_provider = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='DNS provider plugin',
        help_text='e.g. rfc2136, cloudflare',
    )
    acme_dns_credential_ref = models.CharField(
        max_length=500,
        blank=True,
        verbose_name='DNS credential reference',
    )
    # mandatory if acme_eab_required is True
    acme_eab_kid = models.CharField(max_length=200, blank=True, verbose_name='EAB Key Identifier')
    acme_eab_hmac_ref = models.CharField(max_length=500, blank=True, verbose_name='EAB HMAC key reference')

    # ACME extras
    acme_account_url = models.URLField(
        blank=True,
        verbose_name='Account URL (kid)',
        help_text='Populated after registration',
    )
    acme_contact_email = models.CharField(max_length=254, blank=True, verbose_name='Contact e-mail')
    acme_tos_agreed = models.BooleanField(default=False, verbose_name='Terms of service accepted')
    acme_tos_agreed_at = models.DateTimeField(blank=True, null=True, verbose_name='Terms accepted at')
    acme_eab_required = models.BooleanField(default=False, verbose_name='External Account Binding required')
    acme_preferred_chain = models.CharField(max_length=200, blank=True, verbose_name='Preferred issuer chain')
    acme_profile = models.CharField(max_length=100, blank=True, verbose_name='Certificate profile')

    # --- SCEP (mandatory when type == SCEP) ---
    scep_url = models.URLField(blank=True, verbose_name='SCEP endpoint URL')
    scep_ca_fingerprint = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='CA certificate fingerprint (SHA-256)',
    )
    scep_challenge_secret_ref = models.CharField(
        max_length=500,
        blank=True,
        verbose_name='Challenge password reference',
    )
    scep_encryption_algorithm = models.CharField(
        max_length=20,
        choices=ScepEncryptionAlgorithmChoices,
        blank=True,
    )
    scep_digest_algorithm = models.CharField(
        max_length=20,
        choices=ScepDigestAlgorithmChoices,
        blank=True,
    )
    scep_renewal_mode = models.CharField(
        max_length=20,
        choices=ScepRenewalModeChoices,
        blank=True,
    )

    # SCEP extras
    scep_ca_identifier = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='CA identifier',
        help_text='For GetCACert?message=<id>',
    )
    scep_capabilities = models.JSONField(
        blank=True,
        null=True,
        verbose_name='Cached GetCACaps response',
    )
    scep_poll_interval = models.PositiveIntegerField(
        blank=True,
        null=True,
        verbose_name='Poll interval (s)',
        help_text='Manual-approval CAs',
    )
    scep_max_poll_attempts = models.PositiveIntegerField(blank=True, null=True, verbose_name='Max poll attempts')
    scep_ra_cert_ref = models.CharField(max_length=500, blank=True, verbose_name='RA certificate reference')

    # --- Common transport/operational options (all types) ---
    environment = models.CharField(max_length=20, choices=EnvironmentChoices, blank=True)
    tls_trust_anchor = models.CharField(max_length=500, blank=True, verbose_name='Transport TLS trust anchor')
    tls_verify = models.BooleanField(default=True, verbose_name='Verify server TLS certificate')
    http_proxy = models.CharField(max_length=200, blank=True, verbose_name='HTTP proxy')
    timeout_seconds = models.PositiveIntegerField(default=30, verbose_name='Request timeout')
    retry_count = models.PositiveIntegerField(default=3, verbose_name='Retry attempts')

    description = models.CharField(max_length=200, blank=True)
    comments = models.TextField(blank=True)

    clone_fields = ['type', 'environment', 'tls_verify', 'timeout_seconds', 'retry_count']

    class Meta:
        ordering = ('name',)
        verbose_name = 'Protocol'
        verbose_name_plural = 'Protocols'

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('plugins:netbox_pki:protocol', args=[self.pk])

    def get_type_color(self):
        return ProtocolTypeChoices.colors.get(self.type)

    def get_environment_color(self):
        return EnvironmentChoices.colors.get(self.environment)

    def clean(self):
        super().clean()
        errors = {}

        if self.type == ProtocolTypeChoices.TYPE_ACME:
            for field in ('acme_directory_url', 'acme_challenge_type', 'acme_account_key_ref'):
                if not getattr(self, field):
                    errors[field] = 'Required when protocol type is ACME.'
            if self.acme_challenge_type == AcmeChallengeTypeChoices.CHALLENGE_DNS01:
                for field in ('acme_dns_provider', 'acme_dns_credential_ref'):
                    if not getattr(self, field):
                        errors[field] = 'Required when the ACME challenge type is dns-01.'
            if self.acme_eab_required:
                for field in ('acme_eab_kid', 'acme_eab_hmac_ref'):
                    if not getattr(self, field):
                        errors[field] = 'Required when External Account Binding is required.'

        elif self.type == ProtocolTypeChoices.TYPE_SCEP:
            for field in (
                'scep_url',
                'scep_ca_fingerprint',
                'scep_challenge_secret_ref',
                'scep_encryption_algorithm',
                'scep_digest_algorithm',
                'scep_renewal_mode',
            ):
                if not getattr(self, field):
                    errors[field] = 'Required when protocol type is SCEP.'

        if errors:
            raise ValidationError(errors)


class Requestor(NetBoxModel):
    name = models.CharField(
        max_length=200,
        unique=True,
        verbose_name='Requestor name',
        help_text='Name of the entity or team requesting this certificate (e.g. Firewall Team or Security team)',
    )
    contact = models.ManyToManyField(
        to='tenancy.Contact',
        related_name='pki_requestors',
        blank=True,
        verbose_name='Contact users',
    )
    contact_group = models.ManyToManyField(
        to='tenancy.ContactGroup',
        related_name='pki_requestors',
        blank=True,
        verbose_name='Contact user groups',
    )
    description = models.CharField(max_length=200, blank=True)
    comments = models.TextField(blank=True)

    clone_fields = ['contact', 'contact_group']

    class Meta:
        ordering = ('name',)
        verbose_name = 'Requestor'
        verbose_name_plural = 'Requestors'

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('plugins:netbox_pki:requestor', args=[self.pk])


class CertificateAuthority(NetBoxModel):
    name = models.CharField(max_length=200, verbose_name='CA Name')
    status = models.CharField(
        max_length=30,
        choices=CertificateStatusChoices,
        default=CertificateStatusChoices.STATUS_MANUAL,
        verbose_name='Certificate Status',
    )
    protocol = models.ForeignKey(
        to='netbox_pki.Protocol',
        on_delete=models.PROTECT,
        related_name='certificate_authorities',
        verbose_name='Certificate Management Protocol',
    )

    expiration = models.CharField(
        max_length=20,
        choices=CAExpirationChoices,
        blank=True,
        verbose_name='CA Expiration time',
        help_text="If a parent CA is chosen, expiration cannot be later than the parent CA's expiration",
    )
    created_date = models.DateField(
        blank=True,
        null=True,
        verbose_name='Certificate creation date',
        help_text='Defaults to the current date',
    )
    expiration_date = models.DateField(
        blank=True,
        null=True,
        verbose_name='Certificate expiration date',
        help_text='Defaults to created date + expiration time',
    )
    certificate = models.TextField(blank=True)
    private_key = models.CharField(max_length=500, blank=True, verbose_name='Vault URL to Private Key')
    # Unique but optional: null=True (rather than relying on blank='') keeps multiple unset CAs
    # from colliding on the unique constraint.
    cn = models.CharField(
        max_length=255,
        unique=True,
        blank=True,
        null=True,
        verbose_name='CN',
        help_text='Unique Common Name',
    )
    csr = models.TextField(
        blank=True,
        verbose_name='Certificate Signing Request',
        help_text='Only allowed when a parent CA is chosen',
    )
    default_cert_expiration = models.CharField(
        max_length=20,
        choices=DefaultCertExpirationChoices,
        blank=True,
        verbose_name='Default Certificate Expiration time',
    )
    parent_ca = models.ForeignKey(
        to='self',
        on_delete=models.PROTECT,
        related_name='child_cas',
        blank=True,
        null=True,
        verbose_name='Parent Certificate Authority',
    )
    requestor = models.ForeignKey(
        to='netbox_pki.Requestor',
        on_delete=models.SET_NULL,
        related_name='certificate_authorities',
        blank=True,
        null=True,
        verbose_name='Requesting entity/department/team',
    )
    description = models.CharField(max_length=200, blank=True)
    comments = models.TextField(blank=True)

    clone_fields = ['status', 'protocol', 'expiration', 'default_cert_expiration', 'parent_ca', 'requestor']

    class Meta:
        ordering = ('name',)
        verbose_name = 'Certificate Authority'
        verbose_name_plural = 'Certificate Authorities'

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('plugins:netbox_pki:certificateauthority', args=[self.pk])

    def get_status_color(self):
        return CertificateStatusChoices.colors.get(self.status)

    def clean(self):
        super().clean()
        errors = {}

        if self.csr and not self.parent_ca_id:
            errors['csr'] = 'A CSR can only be set when a parent CA is chosen.'

        if self.parent_ca_id and self.pk and self.parent_ca_id == self.pk:
            errors['parent_ca'] = 'A CA cannot be its own parent.'

        if self.parent_ca_id and self.expiration_date and self.parent_ca.expiration_date:
            if self.expiration_date > self.parent_ca.expiration_date:
                errors['expiration_date'] = "Expiration date cannot be later than the parent CA's expiration date."

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        if not self.created_date:
            self.created_date = timezone.now().date()
        if not self.expiration_date and self.expiration in DURATION_DAYS:
            self.expiration_date = self.created_date + timedelta(days=DURATION_DAYS[self.expiration])
        super().save(*args, **kwargs)


class Certificate(NetBoxModel):
    cn = models.CharField(max_length=255, unique=True, verbose_name='CN', help_text='Unique Common Name')
    ca = models.ForeignKey(
        to='netbox_pki.CertificateAuthority',
        on_delete=models.PROTECT,
        related_name='certificates',
        verbose_name='Certificate Authority',
    )
    expiration = models.CharField(
        max_length=20,
        choices=CertificateExpirationChoices,
        default=CertificateExpirationChoices.EXPIRATION_AUTOMATIC,
        verbose_name='Expiration time',
        help_text='If Automatic, the expiration is taken from the chosen CA',
    )
    status = models.CharField(
        max_length=30,
        choices=CertificateStatusChoices,
        default=CertificateStatusChoices.STATUS_MANUAL,
        verbose_name='Certificate Status',
    )
    certificate = models.TextField()
    private_key = models.CharField(max_length=500, verbose_name='Vault URL to Private Key')

    requestor = models.ForeignKey(
        to='netbox_pki.Requestor',
        on_delete=models.SET_NULL,
        related_name='certificates',
        blank=True,
        null=True,
        verbose_name='Requesting entity/department/team',
    )
    created_date = models.DateField(
        blank=True,
        null=True,
        verbose_name='Certificate Creation Date',
        help_text='Defaults to the current date',
    )
    expiration_date = models.DateField(
        blank=True,
        null=True,
        verbose_name='Certificate Expiration Date',
        help_text='Defaults to created date + expiration time',
    )
    alt = models.CharField(
        max_length=2000,
        blank=True,
        verbose_name='Alternative Names',
        help_text='One or more names separated by commas (e.g. alt1, alt2)',
    )
    csr = models.TextField(blank=True, verbose_name='Certificate Signing Request')
    description = models.CharField(max_length=200, blank=True)
    comments = models.TextField(blank=True)

    clone_fields = ['ca', 'expiration', 'status', 'requestor']

    class Meta:
        ordering = ('cn',)
        verbose_name = 'Certificate'
        verbose_name_plural = 'Certificates'

    def __str__(self):
        return self.cn

    def get_absolute_url(self):
        return reverse('plugins:netbox_pki:certificate', args=[self.pk])

    def get_status_color(self):
        return CertificateStatusChoices.colors.get(self.status)

    def save(self, *args, **kwargs):
        if not self.created_date:
            self.created_date = timezone.now().date()
        if not self.expiration_date:
            duration = self.expiration
            if duration == CertificateExpirationChoices.EXPIRATION_AUTOMATIC and self.ca_id:
                duration = self.ca.expiration
            if duration in DURATION_DAYS:
                self.expiration_date = self.created_date + timedelta(days=DURATION_DAYS[duration])
        super().save(*args, **kwargs)
