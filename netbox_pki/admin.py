from django.contrib import admin

from .models import Certificate, CertificateAuthority, Protocol, Requestor


@admin.register(Protocol)
class ProtocolAdmin(admin.ModelAdmin):
    list_display = ('name', 'type', 'environment', 'description')
    list_filter = ('type', 'environment')
    search_fields = ('name', 'description')


@admin.register(Requestor)
class RequestorAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name', 'description')


@admin.register(CertificateAuthority)
class CertificateAuthorityAdmin(admin.ModelAdmin):
    list_display = ('name', 'cn', 'status', 'protocol', 'parent_ca', 'expiration_date')
    list_filter = ('status', 'protocol')
    search_fields = ('name', 'cn')


@admin.register(Certificate)
class CertificateAdmin(admin.ModelAdmin):
    list_display = ('cn', 'ca', 'status', 'requestor', 'expiration_date')
    list_filter = ('status', 'ca')
    search_fields = ('cn', 'alt')
