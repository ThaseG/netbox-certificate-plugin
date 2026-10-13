import django_tables2 as tables
from django.utils.html import format_html
from netbox.tables import NetBoxTable, columns

from .choices import CertificateStatusChoices
from .expiry import EXPIRING_CRITICAL_DAYS, EXPIRING_SOON_DAYS
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
    tenant = tables.Column(linkify=True)
    expiration_date = columns.DateColumn(verbose_name='Expires')
    # Computed from expiration_date (see Certificate.days_remaining), so it sorts by that field.
    days_remaining = tables.Column(verbose_name='Days Left', empty_values=(), order_by=('expiration_date',))
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
            'tenant',
            'expiration',
            'created_date',
            'expiration_date',
            'days_remaining',
            'alt',
            'description',
            'comments',
            'tags',
            'created',
            'last_updated',
        )
        default_columns = ('cn', 'ca', 'tenant', 'status', 'requestor', 'expiration_date', 'days_remaining')

    def render_days_remaining(self, record):
        days = record.days_remaining
        if record.status == CertificateStatusChoices.STATUS_REVOKED:
            return format_html('<span class="badge text-bg-{}">{}</span>', 'secondary', 'Revoked')
        if days is None:
            return '—'
        if days < 0:
            color, text = 'red', f'Expired {-days}d ago'
        elif days <= EXPIRING_CRITICAL_DAYS:
            color, text = 'red', f'{days}d'
        elif days <= EXPIRING_SOON_DAYS:
            color, text = 'orange', f'{days}d'
        else:
            color, text = 'green', f'{days}d'
        return format_html('<span class="badge text-bg-{}">{}</span>', color, text)

    def value_days_remaining(self, record):
        # Plain number for CSV export instead of the badge HTML.
        return record.days_remaining
