from django import forms
from netbox.forms import NetBoxModelFilterSetForm, NetBoxModelForm
from tenancy.models import Contact, ContactGroup
from utilities.forms.fields import (
    CommentField,
    DynamicModelChoiceField,
    DynamicModelMultipleChoiceField,
    TagFilterField,
)
from utilities.forms.rendering import FieldSet

from .choices import (
    CAExpirationChoices,
    CertificateExpirationChoices,
    CertificateStatusChoices,
    EnvironmentChoices,
    ProtocolTypeChoices,
)
from .models import Certificate, CertificateAuthority, Protocol, Requestor

#
# Protocol
#


class ProtocolForm(NetBoxModelForm):
    comments = CommentField()

    fieldsets = (
        FieldSet('name', 'type', 'description', name='Protocol'),
        FieldSet(
            'acme_directory_url',
            'acme_challenge_type',
            'acme_account_key_ref',
            'acme_dns_provider',
            'acme_dns_credential_ref',
            'acme_eab_required',
            'acme_eab_kid',
            'acme_eab_hmac_ref',
            'acme_account_url',
            'acme_contact_email',
            'acme_tos_agreed',
            'acme_tos_agreed_at',
            'acme_preferred_chain',
            'acme_profile',
            name='ACME',
        ),
        FieldSet(
            'scep_url',
            'scep_ca_fingerprint',
            'scep_challenge_secret_ref',
            'scep_encryption_algorithm',
            'scep_digest_algorithm',
            'scep_renewal_mode',
            'scep_ca_identifier',
            'scep_capabilities',
            'scep_poll_interval',
            'scep_max_poll_attempts',
            'scep_ra_cert_ref',
            name='SCEP',
        ),
        FieldSet(
            'environment',
            'tls_trust_anchor',
            'tls_verify',
            'http_proxy',
            'timeout_seconds',
            'retry_count',
            name='Transport Options',
        ),
        FieldSet('tags', name='Tags'),
    )

    class Meta:
        model = Protocol
        fields = (
            'name',
            'type',
            'acme_directory_url',
            'acme_challenge_type',
            'acme_account_key_ref',
            'acme_dns_provider',
            'acme_dns_credential_ref',
            'acme_eab_required',
            'acme_eab_kid',
            'acme_eab_hmac_ref',
            'acme_account_url',
            'acme_contact_email',
            'acme_tos_agreed',
            'acme_tos_agreed_at',
            'acme_preferred_chain',
            'acme_profile',
            'scep_url',
            'scep_ca_fingerprint',
            'scep_challenge_secret_ref',
            'scep_encryption_algorithm',
            'scep_digest_algorithm',
            'scep_renewal_mode',
            'scep_ca_identifier',
            'scep_capabilities',
            'scep_poll_interval',
            'scep_max_poll_attempts',
            'scep_ra_cert_ref',
            'environment',
            'tls_trust_anchor',
            'tls_verify',
            'http_proxy',
            'timeout_seconds',
            'retry_count',
            'description',
            'comments',
            'tags',
        )
        widgets = {
            'acme_tos_agreed_at': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }


class ProtocolFilterForm(NetBoxModelFilterSetForm):
    model = Protocol
    fieldsets = (
        FieldSet('q', 'filter_id', 'tag'),
        FieldSet('type', 'environment', name='Attributes'),
    )
    type = forms.MultipleChoiceField(choices=ProtocolTypeChoices, required=False)
    environment = forms.MultipleChoiceField(choices=EnvironmentChoices, required=False)
    tag = TagFilterField(Protocol)


#
# Requestor
#


class RequestorForm(NetBoxModelForm):
    contact = DynamicModelMultipleChoiceField(queryset=Contact.objects.all(), required=False)
    contact_group = DynamicModelMultipleChoiceField(queryset=ContactGroup.objects.all(), required=False)
    comments = CommentField()

    fieldsets = (
        FieldSet('name', 'contact', 'contact_group', 'description', name='Requestor'),
        FieldSet('tags', name='Tags'),
    )

    class Meta:
        model = Requestor
        fields = ('name', 'contact', 'contact_group', 'description', 'comments', 'tags')


class RequestorFilterForm(NetBoxModelFilterSetForm):
    model = Requestor
    fieldsets = (FieldSet('q', 'filter_id', 'tag'),)
    tag = TagFilterField(Requestor)


#
# Certificate Authority
#


class CertificateAuthorityForm(NetBoxModelForm):
    protocol = DynamicModelChoiceField(queryset=Protocol.objects.all())
    parent_ca = DynamicModelChoiceField(queryset=CertificateAuthority.objects.all(), required=False)
    requestor = DynamicModelChoiceField(queryset=Requestor.objects.all(), required=False)
    comments = CommentField()

    fieldsets = (
        FieldSet('name', 'status', 'protocol', 'description', name='Certificate Authority'),
        FieldSet(
            'expiration',
            'default_cert_expiration',
            'created_date',
            'expiration_date',
            'parent_ca',
            'requestor',
            name='Lifecycle',
        ),
        FieldSet('cn', 'certificate', 'private_key', 'csr', name='Cryptographic Material'),
        FieldSet('tags', name='Tags'),
    )

    class Meta:
        model = CertificateAuthority
        fields = (
            'name',
            'status',
            'protocol',
            'expiration',
            'created_date',
            'expiration_date',
            'certificate',
            'private_key',
            'cn',
            'csr',
            'default_cert_expiration',
            'parent_ca',
            'requestor',
            'description',
            'comments',
            'tags',
        )
        widgets = {
            'created_date': forms.DateInput(attrs={'type': 'date'}),
            'expiration_date': forms.DateInput(attrs={'type': 'date'}),
            'certificate': forms.Textarea(attrs={'class': 'font-monospace', 'rows': 10}),
            'csr': forms.Textarea(attrs={'class': 'font-monospace', 'rows': 10}),
        }


class CertificateAuthorityFilterForm(NetBoxModelFilterSetForm):
    model = CertificateAuthority
    fieldsets = (
        FieldSet('q', 'filter_id', 'tag'),
        FieldSet('status', 'expiration', 'protocol_id', 'parent_ca_id', 'requestor_id', name='Attributes'),
    )
    status = forms.MultipleChoiceField(choices=CertificateStatusChoices, required=False)
    expiration = forms.MultipleChoiceField(choices=CAExpirationChoices, required=False)
    protocol_id = DynamicModelMultipleChoiceField(queryset=Protocol.objects.all(), required=False, label='Protocol')
    parent_ca_id = DynamicModelMultipleChoiceField(
        queryset=CertificateAuthority.objects.all(),
        required=False,
        label='Parent CA',
    )
    requestor_id = DynamicModelMultipleChoiceField(queryset=Requestor.objects.all(), required=False, label='Requestor')
    tag = TagFilterField(CertificateAuthority)


#
# Certificate
#


class CertificateForm(NetBoxModelForm):
    ca = DynamicModelChoiceField(queryset=CertificateAuthority.objects.all(), label='Certificate Authority')
    requestor = DynamicModelChoiceField(queryset=Requestor.objects.all(), required=False)
    comments = CommentField()

    fieldsets = (
        FieldSet('cn', 'ca', 'status', 'requestor', 'description', name='Certificate'),
        FieldSet('expiration', 'created_date', 'expiration_date', name='Lifecycle'),
        FieldSet('alt', 'certificate', 'private_key', 'csr', name='Cryptographic Material'),
        FieldSet('tags', name='Tags'),
    )

    class Meta:
        model = Certificate
        fields = (
            'cn',
            'ca',
            'expiration',
            'status',
            'certificate',
            'private_key',
            'requestor',
            'created_date',
            'expiration_date',
            'alt',
            'csr',
            'description',
            'comments',
            'tags',
        )
        widgets = {
            'created_date': forms.DateInput(attrs={'type': 'date'}),
            'expiration_date': forms.DateInput(attrs={'type': 'date'}),
            'certificate': forms.Textarea(attrs={'class': 'font-monospace', 'rows': 10}),
            'csr': forms.Textarea(attrs={'class': 'font-monospace', 'rows': 10}),
        }


class CertificateFilterForm(NetBoxModelFilterSetForm):
    model = Certificate
    fieldsets = (
        FieldSet('q', 'filter_id', 'tag'),
        FieldSet('status', 'expiration', 'ca_id', 'requestor_id', name='Attributes'),
    )
    status = forms.MultipleChoiceField(choices=CertificateStatusChoices, required=False)
    expiration = forms.MultipleChoiceField(choices=CertificateExpirationChoices, required=False)
    ca_id = DynamicModelMultipleChoiceField(
        queryset=CertificateAuthority.objects.all(),
        required=False,
        label='Certificate Authority',
    )
    requestor_id = DynamicModelMultipleChoiceField(queryset=Requestor.objects.all(), required=False, label='Requestor')
    tag = TagFilterField(Certificate)
