from django.urls import path
from netbox.views.generic import ObjectChangeLogView

from . import models, views

app_name = 'netbox_pki'

urlpatterns = (
    # Certificate Authorities
    path('cas/', views.CertificateAuthorityListView.as_view(), name='certificateauthority_list'),
    path('cas/add/', views.CertificateAuthorityEditView.as_view(), name='certificateauthority_add'),
    path('cas/delete/', views.CertificateAuthorityBulkDeleteView.as_view(), name='certificateauthority_bulk_delete'),
    path('cas/<int:pk>/', views.CertificateAuthorityView.as_view(), name='certificateauthority'),
    path('cas/<int:pk>/edit/', views.CertificateAuthorityEditView.as_view(), name='certificateauthority_edit'),
    path('cas/<int:pk>/delete/', views.CertificateAuthorityDeleteView.as_view(), name='certificateauthority_delete'),
    path(
        'cas/<int:pk>/changelog/',
        ObjectChangeLogView.as_view(),
        name='certificateauthority_changelog',
        kwargs={'model': models.CertificateAuthority},
    ),
    # Certificates
    path('certificates/', views.CertificateListView.as_view(), name='certificate_list'),
    path('certificates/add/', views.CertificateEditView.as_view(), name='certificate_add'),
    path('certificates/delete/', views.CertificateBulkDeleteView.as_view(), name='certificate_bulk_delete'),
    path('certificates/<int:pk>/', views.CertificateView.as_view(), name='certificate'),
    path('certificates/<int:pk>/edit/', views.CertificateEditView.as_view(), name='certificate_edit'),
    path('certificates/<int:pk>/delete/', views.CertificateDeleteView.as_view(), name='certificate_delete'),
    path(
        'certificates/<int:pk>/changelog/',
        ObjectChangeLogView.as_view(),
        name='certificate_changelog',
        kwargs={'model': models.Certificate},
    ),
    # Requestors
    path('requestors/', views.RequestorListView.as_view(), name='requestor_list'),
    path('requestors/add/', views.RequestorEditView.as_view(), name='requestor_add'),
    path('requestors/delete/', views.RequestorBulkDeleteView.as_view(), name='requestor_bulk_delete'),
    path('requestors/<int:pk>/', views.RequestorView.as_view(), name='requestor'),
    path('requestors/<int:pk>/edit/', views.RequestorEditView.as_view(), name='requestor_edit'),
    path('requestors/<int:pk>/delete/', views.RequestorDeleteView.as_view(), name='requestor_delete'),
    path(
        'requestors/<int:pk>/changelog/',
        ObjectChangeLogView.as_view(),
        name='requestor_changelog',
        kwargs={'model': models.Requestor},
    ),
    # Protocols
    path('protocols/', views.ProtocolListView.as_view(), name='protocol_list'),
    path('protocols/add/', views.ProtocolEditView.as_view(), name='protocol_add'),
    path('protocols/delete/', views.ProtocolBulkDeleteView.as_view(), name='protocol_bulk_delete'),
    path('protocols/<int:pk>/', views.ProtocolView.as_view(), name='protocol'),
    path('protocols/<int:pk>/edit/', views.ProtocolEditView.as_view(), name='protocol_edit'),
    path('protocols/<int:pk>/delete/', views.ProtocolDeleteView.as_view(), name='protocol_delete'),
    path(
        'protocols/<int:pk>/changelog/',
        ObjectChangeLogView.as_view(),
        name='protocol_changelog',
        kwargs={'model': models.Protocol},
    ),
)
