import re
from typing import Iterable, List
from django.conf import settings

config = settings.PLUGINS_CONFIG['netbox_interface_sync']


def split(s):
    for x, y in re.findall(r"(\d*)(\D*)", s):
        yield "", int(x or "0")
        yield y, 0


def natural_keys(c):
    return tuple(split(c))


def human_sorted(iterable: Iterable):
    return sorted(iterable, key=natural_keys)


def make_integer_list(lst: List[str]):
    return [int(i) for i in lst if i.isdigit()]


def get_permissions_for_model(model, actions: Iterable[str]) -> List[str]:
    """
    Resolve a list of permissions for a given model (or instance).

    :param model: A model or instance
    :param actions: List of actions: view, add, change, or delete
    """
    permissions = []
    for action in actions:
        if action not in ("view", "add", "change", "delete"):
            raise ValueError(f"Unsupported action: {action}")
        permissions.append(f'{model._meta.app_label}.{action}_{model._meta.model_name}')

    return permissions
