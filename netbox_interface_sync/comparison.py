from dataclasses import dataclass, fields
from django.conf import settings

config = settings.PLUGINS_CONFIG["netbox_interface_sync"]


@dataclass(frozen=True)
class ParentComparison:
    """Common fields of a device component"""

    id: int
    name: str
    label: str
    description: str

    _non_printable_fields = ('id', 'name', 'is_template')

    def __eq__(self, other):
        # Ignore some fields when comparing; ignore component name case and whitespaces
        eq = (
            self.name.lower().replace(" ", "") == other.name.lower().replace(" ", "")
        ) and (self.label == other.label)

        if config["compare_description"]:
            eq = eq and (self.description == other.description)

        return eq

    def __hash__(self):
        # Ignore some fields when hashing; ignore component name case and whitespaces
        return hash(self.name.lower().replace(" ", ""))

    @staticmethod
    def __field_name_caption__(field_name: str):
        field_captions = {
            'type_display': 'Type',
            'rear_port_position': 'Position'
        }
        return field_captions.get(field_name) or field_name.replace('_', ' ').capitalize()

    def __str__(self):
        fields_to_display = []
        for field in fields(self):
            if field.name in self._non_printable_fields:
                continue
            field_value = getattr(self, field.name)
            if not field_value:
                continue
            field_name_display = self.__field_name_caption__(field.name)
            fields_to_display.append(f'{field_name_display}: {field_value}')
        return '\n'.join(fields_to_display)


@dataclass(frozen=True)
class ParentTypedComparison(ParentComparison):
    """Common fields of a device typed component"""

    type: str
    type_display: str

    _non_printable_fields = ParentComparison._non_printable_fields + ('type',)

    def __eq__(self, other):
        eq = (
            (self.name.lower().replace(" ", "") == other.name.lower().replace(" ", ""))
            and (self.label == other.label)
            and (self.type == other.type)
        )

        if config["compare_description"]:
            eq = eq and (self.description == other.description)

        return eq

    def __hash__(self):
        return hash((self.name.lower().replace(" ", ""), self.type))


@dataclass(frozen=True)
class InterfaceComparison(ParentTypedComparison):
    """A unified way to represent the interface and interface template"""

    mgmt_only: bool
    is_template: bool = False

    def __eq__(self, other):
        eq = (
            (self.name.lower().replace(" ", "") == other.name.lower().replace(" ", ""))
            and (self.label == other.label)
            and (self.type == other.type)
            and (self.mgmt_only == other.mgmt_only)
        )

        if config["compare_description"]:
            eq = eq and (self.description == other.description)

        return eq

    def __hash__(self):
        return hash((self.name.lower().replace(" ", ""), self.type))


@dataclass(frozen=True)
class FrontPortComparison(ParentTypedComparison):
    """A unified way to represent the front port and front port template"""

    color: str
    # rear_port_id: int
    rear_port_position: int
    is_template: bool = False

    def __eq__(self, other):
        eq = (
            (self.name.lower().replace(" ", "") == other.name.lower().replace(" ", ""))
            and (self.label == other.label)
            and (self.type == other.type)
            and (self.color == other.color)
            and (self.rear_port_position == other.rear_port_position)
        )

        if config["compare_description"]:
            eq = eq and (self.description == other.description)

        return eq

    def __hash__(self):
        return hash((self.name.lower().replace(" ", ""), self.type))


@dataclass(frozen=True)
class RearPortComparison(ParentTypedComparison):
    """A unified way to represent the rear port and rear port template"""

    color: str
    positions: int
    is_template: bool = False

    def __eq__(self, other):
        eq = (
            (self.name.lower().replace(" ", "") == other.name.lower().replace(" ", ""))
            and (self.label == other.label)
            and (self.type == other.type)
            and (self.color == other.color)
            and (self.positions == other.positions)
        )

        if config["compare_description"]:
            eq = eq and (self.description == other.description)

        return eq

    def __hash__(self):
        return hash((self.name.lower().replace(" ", ""), self.type))


@dataclass(frozen=True, eq=False)
class ConsolePortComparison(ParentTypedComparison):
    """A unified way to represent the consoleport and consoleport template"""

    is_template: bool = False


@dataclass(frozen=True, eq=False)
class ConsoleServerPortComparison(ParentTypedComparison):
    """A unified way to represent the consoleserverport and consoleserverport template"""

    is_template: bool = False


@dataclass(frozen=True)
class PowerPortComparison(ParentTypedComparison):
    """A unified way to represent the power port and power port template"""

    maximum_draw: str
    allocated_draw: str
    is_template: bool = False

    def __eq__(self, other):
        eq = (
            (self.name.lower().replace(" ", "") == other.name.lower().replace(" ", ""))
            and (self.label == other.label)
            and (self.type == other.type)
            and (self.maximum_draw == other.maximum_draw)
            and (self.allocated_draw == other.allocated_draw)
        )

        if config["compare_description"]:
            eq = eq and (self.description == other.description)

        return eq

    def __hash__(self):
        return hash((self.name.lower().replace(" ", ""), self.type))


@dataclass(frozen=True)
class PowerOutletComparison(ParentTypedComparison):
    """A unified way to represent the power outlet and power outlet template"""

    power_port_name: str = ""
    feed_leg: str = ""
    is_template: bool = False

    def __eq__(self, other):
        eq = (
            (self.name.lower().replace(" ", "") == other.name.lower().replace(" ", ""))
            and (self.label == other.label)
            and (self.type == other.type)
            and (self.power_port_name == other.power_port_name)
            and (self.feed_leg == other.feed_leg)
        )

        if config["compare_description"]:
            eq = eq and (self.description == other.description)

        return eq

    def __hash__(self):
        return hash(
            (self.name.lower().replace(" ", ""), self.type, self.power_port_name)
        )


@dataclass(frozen=True, eq=False)
class DeviceBayComparison(ParentComparison):
    """A unified way to represent the device bay and device bay template"""

    is_template: bool = False
