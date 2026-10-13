import django_filters
from django.db.models import Q
from netbox.filtersets import NetBoxModelFilterSet
from tenancy.models import Tenant

from .choices import CertificateExpiryStateChoices, CertificateStatusChoices, ProtocolTypeChoices
from .expiry import expiry_state_q
from .models import Certificate, CertificateAuthority, Protocol, Requestor


class ProtocolFilterSet(NetBoxModelFilterSet):
    type = django_filters.MultipleChoiceFilter(choices=ProtocolTypeChoices, null_value=None)

    class Meta:
        model = Protocol
        fields = ('id', 'name', 'type', 'environment')

    def search(self, queryset, name, value):
        if not value.strip():
            return queryset
        return queryset.filter(
            Q(name__icontains=value) | Q(description__icontains=value) | Q(comments__icontains=value)
        )


class RequestorFilterSet(NetBoxModelFilterSet):
    class Meta:
        model = Requestor
        fields = ('id', 'name')

    def search(self, queryset, name, value):
        if not value.strip():
            return queryset
        return queryset.filter(
            Q(name__icontains=value) | Q(description__icontains=value) | Q(comments__icontains=value)
        )


class CertificateAuthorityFilterSet(NetBoxModelFilterSet):
    status = django_filters.MultipleChoiceFilter(choices=CertificateStatusChoices, null_value=None)
    protocol_id = django_filters.ModelMultipleChoiceFilter(
        queryset=Protocol.objects.all(),
        label='Protocol (ID)',
    )
    parent_ca_id = django_filters.ModelMultipleChoiceFilter(
        queryset=CertificateAuthority.objects.all(),
        label='Parent CA (ID)',
    )
    requestor_id = django_filters.ModelMultipleChoiceFilter(
        queryset=Requestor.objects.all(),
        label='Requestor (ID)',
    )

    class Meta:
        model = CertificateAuthority
        fields = ('id', 'name', 'cn', 'status', 'expiration')

    def search(self, queryset, name, value):
        if not value.strip():
            return queryset
        return queryset.filter(
            Q(name__icontains=value)
            | Q(cn__icontains=value)
            | Q(description__icontains=value)
            | Q(comments__icontains=value)
        )


class CertificateFilterSet(NetBoxModelFilterSet):
    status = django_filters.MultipleChoiceFilter(choices=CertificateStatusChoices, null_value=None)
    ca_id = django_filters.ModelMultipleChoiceFilter(
        queryset=CertificateAuthority.objects.all(),
        label='Certificate Authority (ID)',
    )
    requestor_id = django_filters.ModelMultipleChoiceFilter(
        queryset=Requestor.objects.all(),
        label='Requestor (ID)',
    )
    tenant_id = django_filters.ModelMultipleChoiceFilter(
        queryset=Tenant.objects.all(),
        label='Tenant (ID)',
    )
    tenant = django_filters.ModelMultipleChoiceFilter(
        field_name='tenant__slug',
        queryset=Tenant.objects.all(),
        to_field_name='slug',
        label='Tenant (slug)',
    )
    expiry_state = django_filters.MultipleChoiceFilter(
        choices=CertificateExpiryStateChoices,
        method='filter_expiry_state',
        label='Expiry state',
    )

    class Meta:
        model = Certificate
        fields = ('id', 'cn', 'status', 'expiration', 'created_date', 'expiration_date')

    def filter_expiry_state(self, queryset, name, value):
        if not value:
            return queryset
        q = Q()
        for state in value:
            q |= expiry_state_q(state)
        return queryset.filter(q)

    def search(self, queryset, name, value):
        if not value.strip():
            return queryset
        return queryset.filter(
            Q(cn__icontains=value)
            | Q(alt__icontains=value)
            | Q(description__icontains=value)
            | Q(comments__icontains=value)
        )
