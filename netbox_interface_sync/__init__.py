from extras.plugins import PluginConfig


class Config(PluginConfig):
    name = 'netbox_interface_sync'
    verbose_name = 'NetBox interface synchronization'
    description = 'Syncing interfaces with the interfaces from device type for NetBox devices'
    version = '0.1.2'
    author = 'Victor Golovanenko'
    author_email = 'drygdryg2014@yandex.ru'
    default_settings = {
        'exclude_virtual_interfaces': True
    }


config = Config
