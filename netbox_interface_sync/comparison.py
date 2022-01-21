import attr
from attrs import fields

from django.conf import settings

config = settings.PLUGINS_CONFIG["netbox_interface_sync"]
COMPARE_DESCRIPTIONS: bool = config["compare_description"]


@attr.s(frozen=True, auto_attribs=True)
class BaseComparison:
    """Common fields of a device component"""

    # Do not compare IDs
    id: int = attr.ib(eq=False, hash=False, metadata={'printable': False})
    # Compare names case-insensitively and spaces-insensitively
    name: str = attr.ib(eq=lambda name: name.lower().replace(" ", ""), metadata={'printable': False})
    label: str = attr.ib(hash=False)
    # Compare descriptions if it is set by the configuration
    description: str = attr.ib(eq=COMPARE_DESCRIPTIONS, hash=False)
    # Do not compare `is_template` properties
    is_template: bool = attr.ib(kw_only=True, default=False, eq=False, hash=False, metadata={'printable': False})

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
            fields_to_display.append(f'{field_caption}: {field_value}')
        return '\n'.join(fields_to_display)


@attr.s(frozen=True, auto_attribs=True)
class BaseTypedComparison(BaseComparison):
    """Common fields of a device typed component"""

    type: str = attr.ib(hash=False, metadata={'printable': False})
    type_display: str = attr.ib(eq=False, hash=False, metadata={'displayed_caption': 'Type'})


@attr.s(frozen=True, auto_attribs=True)
class DeviceBayComparison(BaseComparison):
    """A unified way to represent the device bay and device bay template"""
    pass


@attr.s(frozen=True, auto_attribs=True)
class InterfaceComparison(BaseTypedComparison):
    """A unified way to represent the interface and interface template"""

    mgmt_only: bool = attr.ib(hash=False)


@attr.s(frozen=True, auto_attribs=True)
class FrontPortComparison(BaseTypedComparison):
    """A unified way to represent the front port and front port template"""

    color: str = attr.ib(hash=False)
    # rear_port_id: int
    rear_port_position: int = attr.ib(hash=False, metadata={'displayed_caption': 'Position'})


@attr.s(frozen=True, auto_attribs=True)
class RearPortComparison(BaseTypedComparison):
    """A unified way to represent the rear port and rear port template"""

    color: str = attr.ib(hash=False)
    positions: int = attr.ib(hash=False)


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

    maximum_draw: str = attr.ib(hash=False)
    allocated_draw: str = attr.ib(hash=False)


@attr.s(frozen=True, auto_attribs=True)
class PowerOutletComparison(BaseTypedComparison):
    """A unified way to represent the power outlet and power outlet template"""

    power_port_name: str = attr.ib(hash=False)
    feed_leg: str = attr.ib(hash=False)
