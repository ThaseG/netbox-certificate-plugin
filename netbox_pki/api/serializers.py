from django.core.exceptions import ValidationError as DjangoValidationError
from netbox.api.fields import ChoiceField
from netbox.api.serializers import NetBoxModelSerializer, WritableNestedSerializer
from rest_framework import serializers
from tenancy.api.serializers import ContactGroupSerializer, ContactSerializer

from ..choices import (
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
from ..models import Certificate, CertificateAuthority, Protocol, Requestor


def _run_model_clean(serializer, data):
    """
    Re-run the model's own clean() against the incoming data so the API enforces the same
    conditional-mandatory rules (e.g. Protocol type-specific fields, CA parent/CSR rules) as
    the web UI, which triggers clean() via ModelForm.full_clean().
    """
    instance = serializer.instance or serializer.Meta.model()
    skip = {'tags', 'custom_fields', 'contact', 'contact_group'}
    for field, value in data.items():
        if field in skip:
            continue
        setattr(instance, field, value)
    try:
        instance.clean()
    except DjangoValidationError as e:
        if hasattr(e, 'message_dict'):
            raise serializers.ValidationError(e.message_dict)
        raise serializers.ValidationError({'non_field_errors': e.messages})


#
# Nested serializers
#


class NestedProtocolSerializer(WritableNestedSerializer):
    class Meta:
        model = Protocol
        fields = ('id', 'url', 'display_url', 'display', 'name', 'type')


class NestedRequestorSerializer(WritableNestedSerializer):
    class Meta:
        model = Requestor
        fields = ('id', 'url', 'display_url', 'display', 'name')


class NestedCertificateAuthoritySerializer(WritableNestedSerializer):
    class Meta:
        model = CertificateAuthority
        fields = ('id', 'url', 'display_url', 'display', 'name', 'cn')


#
# Full serializers
#


class ProtocolSerializer(NetBoxModelSerializer):
    type = ChoiceField(choices=ProtocolTypeChoices)
    acme_challenge_type = ChoiceField(choices=AcmeChallengeTypeChoices, required=False, allow_blank=True)
    scep_encryption_algorithm = ChoiceField(choices=ScepEncryptionAlgorithmChoices, required=False, allow_blank=True)
    scep_digest_algorithm = ChoiceField(choices=ScepDigestAlgorithmChoices, required=False, allow_blank=True)
    scep_renewal_mode = ChoiceField(choices=ScepRenewalModeChoices, required=False, allow_blank=True)
    environment = ChoiceField(choices=EnvironmentChoices, required=False, allow_blank=True)

    class Meta:
        model = Protocol
        fields = (
            'id',
            'url',
            'display_url',
            'display',
            'name',
            'type',
            'acme_directory_url',
            'acme_challenge_type',
            'acme_account_key_ref',
            'acme_dns_provider',
            'acme_dns_credential_ref',
            'acme_eab_kid',
            'acme_eab_hmac_ref',
            'acme_account_url',
            'acme_contact_email',
            'acme_tos_agreed',
            'acme_tos_agreed_at',
            'acme_eab_required',
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
            'custom_fields',
            'created',
            'last_updated',
        )
        brief_fields = ('id', 'url', 'display', 'name', 'type')

    def validate(self, data):
        _run_model_clean(self, data)
        return super().validate(data)


class RequestorSerializer(NetBoxModelSerializer):
    contact = ContactSerializer(nested=True, many=True, required=False)
    contact_group = ContactGroupSerializer(nested=True, many=True, required=False)

    class Meta:
        model = Requestor
        fields = (
            'id',
            'url',
            'display_url',
            'display',
            'name',
            'contact',
            'contact_group',
            'description',
            'comments',
            'tags',
            'custom_fields',
            'created',
            'last_updated',
        )
        brief_fields = ('id', 'url', 'display', 'name')

    def create(self, validated_data):
        # DRF's ModelSerializer.create() refuses to handle M2M fields whose
        # value is still a list at this point (raise_errors_on_nested_writes)
        # — true here even though WritableNestedSerializer/many=True already
        # resolved each entry to a real Contact/ContactGroup instance, since
        # the *container* is still a plain list. Pop them and set the M2M
        # relations ourselves after the instance (and its tags/custom
        # fields, handled by the base classes' own create()) exists.
        contacts = validated_data.pop('contact', None)
        contact_groups = validated_data.pop('contact_group', None)
        instance = super().create(validated_data)
        if contacts is not None:
            instance.contact.set(contacts)
        if contact_groups is not None:
            instance.contact_group.set(contact_groups)
        return instance

    def update(self, instance, validated_data):
        contacts = validated_data.pop('contact', None)
        contact_groups = validated_data.pop('contact_group', None)
        instance = super().update(instance, validated_data)
        if contacts is not None:
            instance.contact.set(contacts)
        if contact_groups is not None:
            instance.contact_group.set(contact_groups)
        return instance


class CertificateAuthoritySerializer(NetBoxModelSerializer):
    status = ChoiceField(choices=CertificateStatusChoices, required=False)
    protocol = NestedProtocolSerializer()
    expiration = ChoiceField(choices=CAExpirationChoices, required=False, allow_blank=True)
    default_cert_expiration = ChoiceField(choices=DefaultCertExpirationChoices, required=False, allow_blank=True)
    parent_ca = NestedCertificateAuthoritySerializer(required=False, allow_null=True)
    requestor = NestedRequestorSerializer(required=False, allow_null=True)

    class Meta:
        model = CertificateAuthority
        fields = (
            'id',
            'url',
            'display_url',
            'display',
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
            'custom_fields',
            'created',
            'last_updated',
        )
        brief_fields = ('id', 'url', 'display', 'name', 'cn')

    def validate(self, data):
        _run_model_clean(self, data)
        return super().validate(data)


class CertificateSerializer(NetBoxModelSerializer):
    ca = NestedCertificateAuthoritySerializer()
    expiration = ChoiceField(choices=CertificateExpirationChoices, required=False)
    status = ChoiceField(choices=CertificateStatusChoices, required=False)
    requestor = NestedRequestorSerializer(required=False, allow_null=True)

    class Meta:
        model = Certificate
        fields = (
            'id',
            'url',
            'display_url',
            'display',
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
            'custom_fields',
            'created',
            'last_updated',
        )
        brief_fields = ('id', 'url', 'display', 'cn')
