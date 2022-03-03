from extras.plugins import PluginConfig


class Config(PluginConfig):
    name = 'netbox_interface_sync'
    verbose_name = 'NetBox interface synchronization'
    description = 'Compare and synchronize components (interfaces, ports, outlets, etc.) between NetBox device types ' \
                  'and devices'
    version = '0.2.0'
    author = 'Victor Golovanenko'
    author_email = 'drygdryg2014@yandex.ru'
    default_settings = {
        # Ignore case and spaces in names when matching components between device type and device
        'name_comparison': {
            'case-insensitive': True,
            'space-insensitive': True
        },
        # Exclude virtual interfaces (bridge, link aggregation group (LAG), "virtual") from comparison
        'exclude_virtual_interfaces': True,
        # Add a panel with information about the number of interfaces to the device page
        'include_interfaces_panel': False,
        # Consider component descriptions when comparing. If this option is set to True, then take into account
        # component descriptions when comparing components and synchronizing their attributes, otherwise - ignore
        'sync_descriptions': True
    }


config = Config
