import django_tables2 as tables
from netbox.tables import NetBoxTable, columns

from .models import Certificate, CertificateAuthority, Protocol, Requestor


class ProtocolTable(NetBoxTable):
    name = tables.Column(linkify=True)
    type = columns.ChoiceFieldColumn()
    environment = columns.ChoiceFieldColumn()
    tags = columns.TagColumn(url_name='plugins:netbox_pki:protocol_list')

    class Meta(NetBoxTable.Meta):
        model = Protocol
        fields = (
            'pk',
            'id',
            'name',
            'type',
            'environment',
            'acme_directory_url',
            'scep_url',
            'description',
            'comments',
            'tags',
            'created',
            'last_updated',
        )
        default_columns = ('name', 'type', 'environment', 'description')


class RequestorTable(NetBoxTable):
    name = tables.Column(linkify=True)
    tags = columns.TagColumn(url_name='plugins:netbox_pki:requestor_list')

    class Meta(NetBoxTable.Meta):
        model = Requestor
        fields = (
            'pk',
            'id',
            'name',
            'description',
            'comments',
            'tags',
            'created',
            'last_updated',
        )
        default_columns = ('name', 'description')


class CertificateAuthorityTable(NetBoxTable):
    name = tables.Column(linkify=True)
    cn = tables.Column(verbose_name='CN')
    status = columns.ChoiceFieldColumn()
    protocol = tables.Column(linkify=True)
    parent_ca = tables.Column(linkify=True, verbose_name='Parent CA')
    requestor = tables.Column(linkify=True)
    expiration_date = columns.DateColumn(verbose_name='Expires')
    tags = columns.TagColumn(url_name='plugins:netbox_pki:certificateauthority_list')

    class Meta(NetBoxTable.Meta):
        model = CertificateAuthority
        fields = (
            'pk',
            'id',
            'name',
            'cn',
            'status',
            'protocol',
            'parent_ca',
            'requestor',
            'expiration',
            'created_date',
            'expiration_date',
            'description',
            'comments',
            'tags',
            'created',
            'last_updated',
        )
        default_columns = ('name', 'cn', 'status', 'protocol', 'parent_ca', 'expiration_date')


class CertificateTable(NetBoxTable):
    cn = tables.Column(linkify=True, verbose_name='CN')
    ca = tables.Column(linkify=True, verbose_name='Certificate Authority')
    status = columns.ChoiceFieldColumn()
    requestor = tables.Column(linkify=True)
    expiration_date = columns.DateColumn(verbose_name='Expires')
    tags = columns.TagColumn(url_name='plugins:netbox_pki:certificate_list')

    class Meta(NetBoxTable.Meta):
        model = Certificate
        fields = (
            'pk',
            'id',
            'cn',
            'ca',
            'status',
            'requestor',
            'expiration',
            'created_date',
            'expiration_date',
            'alt',
            'description',
            'comments',
            'tags',
            'created',
            'last_updated',
        )
        default_columns = ('cn', 'ca', 'status', 'requestor', 'expiration_date')
