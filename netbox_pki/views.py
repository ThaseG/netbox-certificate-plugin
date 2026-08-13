from netbox.views import generic

from . import filtersets, forms, models, tables

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
