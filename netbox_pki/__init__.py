from netbox.plugins import PluginConfig


class NetBoxPKIConfig(PluginConfig):
    name = 'netbox_pki'
    verbose_name = 'PKI'
    description = (
        'Manage Certificate Authorities, Certificates, Requestors and enrollment Protocols directly in NetBox.'
    )
    version = '0.1.0'
    author = 'ThaseG'
    author_email = ''
    base_url = 'pki'
    min_version = '4.0.0'
    max_version = '4.99'
    default_settings = {}


config = NetBoxPKIConfig
