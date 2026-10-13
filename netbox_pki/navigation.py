from netbox.plugins import PluginMenu, PluginMenuButton, PluginMenuItem

menu_items = (
    PluginMenuItem(
        link='plugins:netbox_pki:certificate_list',
        link_text='Certificates',
        buttons=(PluginMenuButton('plugins:netbox_pki:certificate_add', 'Add', 'mdi mdi-plus-thick'),),
    ),
    PluginMenuItem(
        link='plugins:netbox_pki:certificateauthority_list',
        link_text='Certificate Authorities',
        buttons=(PluginMenuButton('plugins:netbox_pki:certificateauthority_add', 'Add', 'mdi mdi-plus-thick'),),
    ),
    PluginMenuItem(
        link='plugins:netbox_pki:requestor_list',
        link_text='Requestors',
        buttons=(PluginMenuButton('plugins:netbox_pki:requestor_add', 'Add', 'mdi mdi-plus-thick'),),
    ),
    PluginMenuItem(
        link='plugins:netbox_pki:protocol_list',
        link_text='Protocols',
        buttons=(PluginMenuButton('plugins:netbox_pki:protocol_add', 'Add', 'mdi mdi-plus-thick'),),
    ),
)

report_items = (
    PluginMenuItem(
        link='plugins:netbox_pki:certificate_report',
        link_text='Certificate Report',
        permissions=['netbox_pki.view_certificate'],
    ),
)

menu = PluginMenu(
    label='PKI',
    groups=(('Certificates', menu_items), ('Reports', report_items)),
    icon_class='mdi mdi-certificate-outline',
)
