from dataclasses import dataclass


@dataclass(frozen=True)
class ParentComparison:
    id: int
    name: str
    label: str
    description: str

    def __eq__(self, other):
        # Ignore some fields when comparing; ignore interface name case and whitespaces
        return self.name.lower().replace(" ", "") == other.name.lower().replace(" ", "")

    def __hash__(self):
        # Ignore some fields when hashing; ignore interface name case and whitespaces
        return hash(self.name.lower().replace(" ", ""))


@dataclass(frozen=True)
class ParentTypedComparison(ParentComparison):
    type: str
    type_display: str

    def __eq__(self, other):
        # Ignore some fields when comparing; ignore interface name case and whitespaces
        return (
            self.name.lower().replace(" ", "") == other.name.lower().replace(" ", "")
        ) and (self.type == other.type)

    def __hash__(self):
        # Ignore some fields when hashing; ignore interface name case and whitespaces
        return hash((self.name.lower().replace(" ", ""), self.type))


@dataclass(frozen=True)
class UnifiedInterface:
    """A unified way to represent the interface and interface template"""

    id: int
    name: str
    type: str = ""
    type_display: str = ""
    is_template: bool = False

    def __eq__(self, other):
        # Ignore some fields when comparing; ignore interface name case and whitespaces
        return (
            self.name.lower().replace(" ", "") == other.name.lower().replace(" ", "")
        ) and (self.type == other.type)

    def __hash__(self):
        # Ignore some fields when hashing; ignore interface name case and whitespaces
        return hash((self.name.lower().replace(" ", ""), self.type))


@dataclass(frozen=True)
class ComparisonPowerOutlet(ParentTypedComparison):

    power_port_name: str = ""
    feed_leg: str = ""
    is_template: bool = False

    def __eq__(self, other):
        # Ignore some fields when comparing; ignore interface name case and whitespaces
        return (
            (self.name.lower().replace(" ", "") == other.name.lower().replace(" ", ""))
            and (self.label == other.label)
            and (self.type == other.type)
            and (self.power_port_name == other.power_port_name)
            and (self.feed_leg == other.feed_leg)
            and (self.description == other.description)
        )

    def __hash__(self):
        # Ignore some fields when hashing; ignore interface name case and whitespaces
        return hash(
            (self.name.lower().replace(" ", ""), self.type, self.power_port_name)
        )
