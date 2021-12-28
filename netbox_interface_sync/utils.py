import re
from typing import Iterable
from django.shortcuts import render, redirect
from django.contrib import messages
from .comparison import UnifiedInterface, ComparisonPowerOutlet

def split(s):
    for x, y in re.findall(r'(\d*)(\D*)', s):
        yield '', int(x or '0')
        yield y, 0


def natural_keys(c):
    return tuple(split(c))


def human_sorted(iterable: Iterable):
    return sorted(iterable, key=natural_keys)

def get_components(request, device, components, component_templates):
    try:
        unified_components = [UnifiedInterface(i.id, i.name, i.type, i.get_type_display()) for i in components]
    except AttributeError:
        unified_components = [UnifiedInterface(i.id, i.name) for i in components]

    try:
        unified_component_templates = [
            UnifiedInterface(i.id, i.name, i.type, i.get_type_display(), is_template=True) for i in component_templates]
    except AttributeError:
        unified_component_templates = [
            UnifiedInterface(i.id, i.name, is_template=True) for i in component_templates]

    # List of interfaces and interface templates presented in the unified format
    overall_powers = list(set(unified_component_templates + unified_components))
    overall_powers.sort(key=lambda o: natural_keys(o.name))

    comparison_templates = []
    comparison_interfaces = []
    for i in overall_powers:
        try:
            comparison_templates.append(unified_component_templates[unified_component_templates.index(i)])
        except ValueError:
            comparison_templates.append(None)

        try:
            comparison_interfaces.append(unified_components[unified_components.index(i)])
        except ValueError:
            comparison_interfaces.append(None)

    comparison_items = list(zip(comparison_templates, comparison_interfaces))
    return render(
        request, "netbox_interface_sync/interface_comparison.html",
        {
            "comparison_items": comparison_items,
            "templates_count": len(unified_component_templates),
            "interfaces_count": len(components),
            "device": device
            }
    )

def post_components(request, device, components, component_templates, ObjectType, ObjectTemplateType):
    # Manually validating interfaces and interface templates lists
    add_to_device = filter(
        lambda i: i in component_templates.values_list("id", flat=True),
        map(int, filter(lambda x: x.isdigit(), request.POST.getlist("add_to_device")))
    )
    remove_from_device = filter(
        lambda i: i in components.values_list("id", flat=True),
        map(int, filter(lambda x: x.isdigit(), request.POST.getlist("remove_from_device")))
    )

    # Remove selected interfaces from the device and count them
    deleted = ObjectType.objects.filter(id__in=remove_from_device).delete()[0]

    # Add selected interfaces to the device and count them
    add_to_device_component = ObjectTemplateType.objects.filter(id__in=add_to_device)

    bulk_create = []
    keys_to_avoid = ["id"]

    for i in add_to_device_component.values():
        tmp = ObjectType()
        tmp.device = device
        for k in i.keys():
            if k not in keys_to_avoid:
                setattr(tmp, k, i[k])
        bulk_create.append(tmp)

    created = len(ObjectType.objects.bulk_create(bulk_create))

    # Getting and validating a list of interfaces to rename
    fix_name_components = filter(lambda i: str(i.id) in request.POST.getlist("fix_name"), components)
    # Casting interface templates into UnifiedInterface objects for proper comparison with interfaces for renaming
    try:
        unified_component_templates = [
            UnifiedInterface(i.id, i.name, i.type, i.get_type_display()) for i in component_templates]
    except AttributeError:
        unified_component_templates = [
            UnifiedInterface(i.id, i.name) for i in component_templates]

    # Rename selected interfaces
    fixed = 0
    for component in fix_name_components:
        try:
            unified_component = UnifiedInterface(component.id, component.name, component.type, component.get_type_display())
        except AttributeError:
            unified_component = UnifiedInterface(component.id, component.name)

        try:
            # Try to extract an interface template with the corresponding name
            corresponding_template = unified_component_templates[unified_component_templates.index(unified_component)]
            component.name = corresponding_template.name
            component.save()
            fixed += 1
        except ValueError:
            pass

    # Generating result message
    message = []
    if created > 0:
        message.append(f"created {created} interfaces")
    if deleted > 0:
        message.append(f"deleted {deleted} interfaces")
    if fixed > 0:
        message.append(f"fixed {fixed} interfaces")
    messages.success(request, "; ".join(message).capitalize())

    return redirect(request.path)
