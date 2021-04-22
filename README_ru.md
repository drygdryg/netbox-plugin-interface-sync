# netbox-interface-sync
[English version](./README.md)
## Обзор
Плагин для NetBox, позволяющий сравнивать и синхронизировать интерфейсы между устройствами (devices) и типами устройств (device types). Полезен для поиска и исправления несоответствий между интерфейсами. Работа проверена с NetBox версий 2.10, 2.11
## Установка
Если NetBox использует virtualenv, то активируйте его, например, так:
```
source /opt/netbox/venv/bin/activate
```
Склонируйте этот репозиторий, затем перейдите в папку с ним и установите плагин:
```
pip install .
```
Включите плагин в файле `configuration.py` (обычно он находится в `/opt/netbox/netbox/netbox/`), добавьте его имя в список `PLUGINS`:
```
PLUGINS = [
    'netbox_interface_sync'
]
```
Перезапустите NetBox:
```
sudo systemctl restart netbox
```
## Использование
Для того чтобы сравнить интерфейсы, откройте страницу нужного устройства и найдите кнопку "Interface sync" справа сверху:
![Device page](docs/images/1_device_page.png)
Отметьте требуемые действия напротив интерфейсов флажками и нажмите "Apply".
![Interface comparison](docs/images/2_interface_comparison.png)
### Настройки плагина
Если вы хотите переопределить значения по умолчанию, настройте переменную `PLUGINS_CONFIG` в вашем файле `configuration.py`:
```
PLUGINS_CONFIG = {
    'netbox_interface_sync': {
        'exclude_virtual_interfaces': True
    }
}
```
| Настройка | Значение по умолчанию | Описание |
| --- | --- | --- |
| exclude_virtual_interfaces | `True` | Не учитывать виртуальные интерфейсы (VLAN, LAG) при сравнении
