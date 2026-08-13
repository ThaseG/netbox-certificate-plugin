import django_filters
from django.db.models import Q
from netbox.filtersets import NetBoxModelFilterSet

from .choices import CertificateStatusChoices, ProtocolTypeChoices
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

    class Meta:
        model = Certificate
        fields = ('id', 'cn', 'status', 'expiration')

    def search(self, queryset, name, value):
        if not value.strip():
            return queryset
        return queryset.filter(
            Q(cn__icontains=value)
            | Q(alt__icontains=value)
            | Q(description__icontains=value)
            | Q(comments__icontains=value)
        )
