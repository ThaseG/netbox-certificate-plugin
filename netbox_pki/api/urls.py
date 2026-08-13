from netbox.api.routers import NetBoxRouter

from . import views

app_name = 'netbox_pki-api'

router = NetBoxRouter()
router.register('certificates', views.CertificateViewSet)
router.register('cas', views.CertificateAuthorityViewSet)
router.register('requestors', views.RequestorViewSet)
router.register('protocols', views.ProtocolViewSet)

urlpatterns = router.urls
