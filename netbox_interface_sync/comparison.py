from typing import Optional

import attr
from attrs import fields
from django.conf import settings

from netbox.models import PrimaryModel

config = settings.PLUGINS_CONFIG["netbox_interface_sync"]
SYNC_DESCRIPTIONS: bool = config["sync_descriptions"]


@attr.s(frozen=True, auto_attribs=True)
class BaseComparison:
    """Common fields of a device component"""
    # Do not compare IDs
    id: int = attr.ib(eq=False, metadata={'printable': False, 'netbox_exportable': False})
    # Compare names case-insensitively and spaces-insensitively
    name: str = attr.ib(metadata={'printable': False})
    label: str = attr.ib()
    # Compare descriptions if it is set by the configuration
    description: str = attr.ib(eq=SYNC_DESCRIPTIONS, metadata={'synced': SYNC_DESCRIPTIONS})
    # Do not compare `is_template` properties
    is_template: bool = attr.ib(
        default=False, kw_only=True, eq=False,
        metadata={'printable': False, 'netbox_exportable': False}
    )

    @property
    def fields_display(self) -> str:
        """Generate human-readable list of printable fields to display in the comparison table"""
        fields_to_display = []
        for field in fields(self.__class__):
            if not field.metadata.get('printable', True):
                continue
            field_value = getattr(self, field.name)
            if not field_value:
                continue
            field_caption = field.metadata.get('displayed_caption') or field.name.replace('_', ' ').capitalize()
            if isinstance(field_value, BaseComparison):
                field_value = f'{field_value.name} (ID: {field_value.id})'
            fields_to_display.append(f'{field_caption}: {field_value}')
        return '\n'.join(fields_to_display)

    def get_fields_for_netbox_component(self, sync=False):
        """
        Returns a dict of fields and values for creating or updating a NetBox component object
        :param sync: if True, returns fields for syncing an existing component, otherwise - for creating a new one.
        """

        def field_filter(field: attr.Attribute, _):
            result = field.metadata.get('netbox_exportable', True)
            if sync:
                result &= field.metadata.get('synced', True)
            return result

        return attr.asdict(self, recurse=True, filter=field_filter)


@attr.s(frozen=True, auto_attribs=True)
class BaseTypedComparison(BaseComparison):
    """Common fields of a device typed component"""
    type: str = attr.ib(metadata={'printable': False})
    type_display: str = attr.ib(eq=False, metadata={'displayed_caption': 'Type', 'netbox_exportable': False})


@attr.s(frozen=True, auto_attribs=True)
class ConsolePortComparison(BaseTypedComparison):
    """A unified way to represent the consoleport and consoleport template"""
    pass


@attr.s(frozen=True, auto_attribs=True)
class ConsoleServerPortComparison(BaseTypedComparison):
    """A unified way to represent the consoleserverport and consoleserverport template"""
    pass


@attr.s(frozen=True, auto_attribs=True)
class PowerPortComparison(BaseTypedComparison):
    """A unified way to represent the power port and power port template"""
    maximum_draw: str = attr.ib()
    allocated_draw: str = attr.ib()


@attr.s(frozen=True, auto_attribs=True)
class PowerOutletComparison(BaseTypedComparison):
    """A unified way to represent the power outlet and power outlet template"""
    power_port: PowerPortComparison = attr.ib()
    feed_leg: str = attr.ib()


@attr.s(frozen=True, auto_attribs=True)
class InterfaceComparison(BaseTypedComparison):
    """A unified way to represent the interface and interface template"""
    mgmt_only: bool = attr.ib()


@attr.s(frozen=True, auto_attribs=True)
class FrontPortComparison(BaseTypedComparison):
    """A unified way to represent the front port and front port template"""
    color: str = attr.ib()
    # rear_port_id: int
    rear_port_position: int = attr.ib(metadata={'displayed_caption': 'Position'})


@attr.s(frozen=True, auto_attribs=True)
class RearPortComparison(BaseTypedComparison):
    """A unified way to represent the rear port and rear port template"""
    color: str = attr.ib()
    positions: int = attr.ib()


@attr.s(frozen=True, auto_attribs=True)
class DeviceBayComparison(BaseComparison):
    """A unified way to represent the device bay and device bay template"""
    pass


def from_netbox_object(netbox_object: PrimaryModel) -> Optional[BaseComparison]:
    """Makes a comparison object from the NetBox object"""
    type_map = {
        "DeviceBay": DeviceBayComparison,
        "Interface": InterfaceComparison,
        "FrontPort": FrontPortComparison,
        "RearPort": RearPortComparison,
        "ConsolePort": ConsolePortComparison,
        "ConsoleServerPort": ConsoleServerPortComparison,
        "PowerPort": PowerPortComparison,
        "PowerOutlet": PowerOutletComparison
    }

    obj_name = netbox_object._meta.object_name
    if obj_name.endswith("Template"):
        is_template = True
        obj_name = obj_name[:-8]  # TODO: use `removesuffix` introduced in Python 3.9
    else:
        is_template = False

    comparison = type_map.get(obj_name)
    if not comparison:
        return

    values = {}
    for field in fields(comparison):
        if field.name == "is_template":
            continue
        if field.name == "type_display":
            values[field.name] = netbox_object.get_type_display()
        else:
            field_value = getattr(netbox_object, field.name)
            if isinstance(field_value, PrimaryModel):
                field_value = from_netbox_object(field_value)
            values[field.name] = field_value

    return comparison(**values, is_template=is_template)
