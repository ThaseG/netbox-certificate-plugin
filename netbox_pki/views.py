from django.shortcuts import render
from django.urls import reverse
from django.views.generic import View
from netbox.views import generic
from utilities.querydict import dict_to_querydict
from utilities.views import ContentTypePermissionRequiredMixin

from . import filtersets, forms, models, tables
from .choices import CertificateExpiryStateChoices
from .expiry import expiry_counts

#
# Protocol
#


class ProtocolListView(generic.ObjectListView):
    queryset = models.Protocol.objects.all()
    table = tables.ProtocolTable
    filterset = filtersets.ProtocolFilterSet
    filterset_form = forms.ProtocolFilterForm


class ProtocolView(generic.ObjectView):
    queryset = models.Protocol.objects.all()

    def get_extra_context(self, request, instance):
        cas = models.CertificateAuthority.objects.filter(protocol=instance)
        return {
            'cas_table': tables.CertificateAuthorityTable(cas, exclude=('protocol',), orderable=False),
        }


class ProtocolEditView(generic.ObjectEditView):
    queryset = models.Protocol.objects.all()
    form = forms.ProtocolForm


class ProtocolDeleteView(generic.ObjectDeleteView):
    queryset = models.Protocol.objects.all()


class ProtocolBulkDeleteView(generic.BulkDeleteView):
    queryset = models.Protocol.objects.all()
    table = tables.ProtocolTable
    filterset = filtersets.ProtocolFilterSet


#
# Requestor
#


class RequestorListView(generic.ObjectListView):
    queryset = models.Requestor.objects.all()
    table = tables.RequestorTable
    filterset = filtersets.RequestorFilterSet
    filterset_form = forms.RequestorFilterForm


class RequestorView(generic.ObjectView):
    queryset = models.Requestor.objects.all()

    def get_extra_context(self, request, instance):
        cas = models.CertificateAuthority.objects.filter(requestor=instance)
        certificates = models.Certificate.objects.filter(requestor=instance)
        return {
            'cas_table': tables.CertificateAuthorityTable(cas, exclude=('requestor',), orderable=False),
            'certificates_table': tables.CertificateTable(
                certificates,
                exclude=('requestor',),
                orderable=False,
            ),
        }


class RequestorEditView(generic.ObjectEditView):
    queryset = models.Requestor.objects.all()
    form = forms.RequestorForm


class RequestorDeleteView(generic.ObjectDeleteView):
    queryset = models.Requestor.objects.all()


class RequestorBulkDeleteView(generic.BulkDeleteView):
    queryset = models.Requestor.objects.all()
    table = tables.RequestorTable
    filterset = filtersets.RequestorFilterSet


#
# Certificate Authority
#


class CertificateAuthorityListView(generic.ObjectListView):
    queryset = models.CertificateAuthority.objects.all()
    table = tables.CertificateAuthorityTable
    filterset = filtersets.CertificateAuthorityFilterSet
    filterset_form = forms.CertificateAuthorityFilterForm


class CertificateAuthorityView(generic.ObjectView):
    queryset = models.CertificateAuthority.objects.all()

    def get_extra_context(self, request, instance):
        child_cas = models.CertificateAuthority.objects.filter(parent_ca=instance)
        certificates = models.Certificate.objects.filter(ca=instance)
        return {
            'child_cas_table': tables.CertificateAuthorityTable(
                child_cas,
                exclude=('parent_ca',),
                orderable=False,
            ),
            'certificates_table': tables.CertificateTable(certificates, exclude=('ca',), orderable=False),
        }


class CertificateAuthorityEditView(generic.ObjectEditView):
    queryset = models.CertificateAuthority.objects.all()
    form = forms.CertificateAuthorityForm


class CertificateAuthorityDeleteView(generic.ObjectDeleteView):
    queryset = models.CertificateAuthority.objects.all()


class CertificateAuthorityBulkDeleteView(generic.BulkDeleteView):
    queryset = models.CertificateAuthority.objects.all()
    table = tables.CertificateAuthorityTable
    filterset = filtersets.CertificateAuthorityFilterSet


#
# Certificate
#


class CertificateListView(generic.ObjectListView):
    queryset = models.Certificate.objects.all()
    table = tables.CertificateTable
    filterset = filtersets.CertificateFilterSet
    filterset_form = forms.CertificateFilterForm


class CertificateView(generic.ObjectView):
    queryset = models.Certificate.objects.all()


class CertificateEditView(generic.ObjectEditView):
    queryset = models.Certificate.objects.all()
    form = forms.CertificateForm


class CertificateDeleteView(generic.ObjectDeleteView):
    queryset = models.Certificate.objects.all()


class CertificateBulkDeleteView(generic.BulkDeleteView):
    queryset = models.Certificate.objects.all()
    table = tables.CertificateTable
    filterset = filtersets.CertificateFilterSet


#
# Reports
#


class CertificateReportView(ContentTypePermissionRequiredMixin, View):
    """The Certificate Report: five expiry counters on top, then every matching certificate in a
    table sorted by expiration date, all narrowed by the CA / tenant filters.

    Clicking a counter narrows the table to that state (?expiry_state=...). The table is the
    Certificate list view embedded via HTMX, so it pages, sorts and exports on its own; both the
    counters and the table use expiry.py, so a counter always matches the rows it links to.
    """

    template_name = 'netbox_pki/certificate_report.html'
    CARDS = (
        (CertificateExpiryStateChoices.STATE_VALID, 'Valid Certificates', 'green', 'mdi-check-decagram'),
        (CertificateExpiryStateChoices.STATE_EXPIRED, 'Expired Certificates', 'red', 'mdi-alert-octagon'),
        (CertificateExpiryStateChoices.STATE_REVOKED, 'Revoked Certificates', 'secondary', 'mdi-cancel'),
        (CertificateExpiryStateChoices.STATE_EXPIRING_30, 'Expiration in 30 days', 'orange', 'mdi-clock-alert-outline'),
        (CertificateExpiryStateChoices.STATE_EXPIRING_10, 'Expiration in 10 days', 'red', 'mdi-clock-alert'),
    )

    def get_required_permission(self):
        return 'netbox_pki.view_certificate'

    def get(self, request):
        form = forms.CertificateReportFilterForm(request.GET or None)
        filters = form.cleaned_data if form.is_valid() else {}
        ca_ids = [str(ca.pk) for ca in filters.get('ca_id') or []]
        tenant_ids = [str(tenant.pk) for tenant in filters.get('tenant_id') or []]
        state = request.GET.get('expiry_state')
        if state not in CertificateExpiryStateChoices.values():
            state = None

        queryset = models.Certificate.objects.restrict(request.user, 'view')
        if ca_ids:
            queryset = queryset.filter(ca_id__in=ca_ids)
        if tenant_ids:
            queryset = queryset.filter(tenant_id__in=tenant_ids)
        counts = expiry_counts(queryset)

        base_params = {'ca_id': ca_ids, 'tenant_id': tenant_ids}
        report_url = reverse('plugins:netbox_pki:certificate_report')
        cards = []
        for key, label, color, icon in self.CARDS:
            # Clicking the active card clears the state filter again.
            params = base_params if key == state else {**base_params, 'expiry_state': key}
            cards.append(
                {
                    'key': key,
                    'label': label,
                    'color': color,
                    'icon': icon,
                    'count': counts[key],
                    'active': key == state,
                    'url': f'{report_url}?{dict_to_querydict(params).urlencode()}',
                }
            )

        table_params = {**base_params, 'sort': 'expiration_date'}
        if state:
            table_params['expiry_state'] = state

        return render(
            request,
            self.template_name,
            {
                'filter_form': form,
                'cards': cards,
                'state_label': next((card['label'] for card in cards if card['active']), None),
                'clear_state_url': f'{report_url}?{dict_to_querydict(base_params).urlencode()}',
                'no_date_count': counts['no_date'],
                'table_params': dict_to_querydict(table_params),
                'export_url': f'{reverse("plugins:netbox_pki:certificate_list")}?'
                f'{dict_to_querydict({**table_params, "export": "table"}).urlencode()}',
            },
        )
