from netbox.api.viewsets import NetBoxModelViewSet

from .. import filtersets, models
from . import serializers


class ProtocolViewSet(NetBoxModelViewSet):
    queryset = models.Protocol.objects.prefetch_related('tags')
    serializer_class = serializers.ProtocolSerializer
    filterset_class = filtersets.ProtocolFilterSet


class RequestorViewSet(NetBoxModelViewSet):
    queryset = models.Requestor.objects.prefetch_related('contact', 'contact_group', 'tags')
    serializer_class = serializers.RequestorSerializer
    filterset_class = filtersets.RequestorFilterSet


class CertificateAuthorityViewSet(NetBoxModelViewSet):
    queryset = models.CertificateAuthority.objects.prefetch_related(
        'protocol',
        'parent_ca',
        'requestor',
        'tags',
    )
    serializer_class = serializers.CertificateAuthoritySerializer
    filterset_class = filtersets.CertificateAuthorityFilterSet


class CertificateViewSet(NetBoxModelViewSet):
    queryset = models.Certificate.objects.prefetch_related('ca', 'requestor', 'tags')
    serializer_class = serializers.CertificateSerializer
    filterset_class = filtersets.CertificateFilterSet
