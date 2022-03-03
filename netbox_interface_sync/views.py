from collections import namedtuple
from typing import Type, Tuple

from django.db.models import QuerySet
from django.shortcuts import get_object_or_404, redirect, render
from django.views.generic import View
from dcim.models import (Device, Interface, InterfaceTemplate, PowerPort, PowerPortTemplate, ConsolePort,
                         ConsolePortTemplate, ConsoleServerPort, ConsoleServerPortTemplate, DeviceBay,
                         DeviceBayTemplate, FrontPort, FrontPortTemplate, PowerOutlet, PowerOutletTemplate, RearPort,
                         RearPortTemplate)
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.conf import settings
from django.contrib import messages

from netbox.models import PrimaryModel
from dcim.constants import VIRTUAL_IFACE_TYPES

from . import comparison
from .utils import get_permissions_for_model, make_integer_list, human_sorted

config = settings.PLUGINS_CONFIG['netbox_interface_sync']
ComparisonTableRow = namedtuple('ComparisonTableRow', ('component_template', 'component'))


class GenericComparisonView(PermissionRequiredMixin, View):
    """
    Generic object comparison view

    obj_model: Model of the object involved in the comparison (for example, Interface)
    obj_template_model: Model of the object template involved in the comparison (for example, InterfaceTemplate)
    """
    obj_model: Type[PrimaryModel] = None
    obj_template_model: Type[PrimaryModel] = None

    def get_permission_required(self):
        # User must have permission to view the device whose components are being compared
        permissions = ["dcim.view_device"]

        # Resolve permissions related to the object and the object template
        permissions.extend(get_permissions_for_model(self.obj_model, ("view", "add", "change", "delete")))
        permissions.extend(get_permissions_for_model(self.obj_template_model, ("view",)))

        return permissions

    @staticmethod
    def filter_comparison_components(component_templates: QuerySet, components: QuerySet) -> Tuple[QuerySet, QuerySet]:
        """Override this in the inherited View to implement special comparison objects filtering logic"""
        return component_templates, components

    def _fetch_comparison_objects(self, device_id: int):
        self.device = get_object_or_404(Device, id=device_id)
        component_templates = self.obj_template_model.objects.filter(device_type_id=self.device.device_type.id)
        components = self.obj_model.objects.filter(device_id=device_id)
        self.component_templates, self.components = self.filter_comparison_components(component_templates, components)
        self.comparison_component_templates = [comparison.from_netbox_object(obj) for obj in self.component_templates]
        self.comparison_components = [comparison.from_netbox_object(obj) for obj in self.components]

        name_comparison_config = config['name_comparison']

        def name_key(obj_name: str) -> str:
            name = obj_name
            if name_comparison_config.get('case-insensitive'):
                name = name.lower()
            if name_comparison_config.get('space-insensitive'):
                name = name.replace(' ', '')
            return name

        component_templates_dict = {name_key(obj.name): obj for obj in self.comparison_component_templates}
        components_dict = {name_key(obj.name): obj for obj in self.comparison_components}

        self.comparison_table = tuple(
            ComparisonTableRow(
                component_template=component_templates_dict.get(component_name),
                component=components_dict.get(component_name)
            )
            for component_name in human_sorted(set().union(component_templates_dict.keys(), components_dict.keys()))
        )

    def get(self, request, device_id):
        self._fetch_comparison_objects(device_id)

        return render(request, "netbox_interface_sync/components_comparison.html", {
            "component_type_name": self.obj_model._meta.verbose_name_plural,
            "comparison_items": self.comparison_table,
            "templates_count": len(self.comparison_component_templates),
            "components_count": len(self.comparison_components),
            "device": self.device,
        })

    def post(self, request, device_id):
        components_to_add = make_integer_list(request.POST.getlist("add"))
        components_to_delete = make_integer_list(request.POST.getlist("remove"))
        components_to_sync = make_integer_list(request.POST.getlist("sync"))
        if not any((components_to_add, components_to_delete, components_to_sync)):
            messages.warning(request, "No actions selected")
            return redirect(request.path)

        self._fetch_comparison_objects(device_id)

        component_ids_to_delete = []
        components_to_bulk_create = []
        synced_count = 0
        for template, component in self.comparison_table:
            if template and (template.id in components_to_add):
                # Add component to the device from the template
                components_to_bulk_create.append(
                    self.obj_model(device=self.device, **template.get_fields_for_netbox_component())
                )
            elif component and (component.id in components_to_delete):
                # Delete component from the device
                component_ids_to_delete.append(component.id)
            elif (template and component) and (component.id in components_to_sync):
                # Update component attributes from the template
                synced_count += self.components.filter(id=component.id).update(
                    **template.get_fields_for_netbox_component(sync=True)
                )

        deleted_count = self.obj_model.objects.filter(id__in=component_ids_to_delete).delete()[0]
        created_count = len(self.obj_model.objects.bulk_create(components_to_bulk_create))

        # Generating result message
        component_type_name = self.obj_model._meta.verbose_name_plural
        message = []
        if synced_count > 0:
            message.append(f"synced {synced_count} {component_type_name}")
        if created_count > 0:
            message.append(f"created {created_count} {component_type_name}")
        if deleted_count > 0:
            message.append(f"deleted {deleted_count} {component_type_name}")
        messages.success(request, "; ".join(message).capitalize())

        return redirect(request.path)


class ConsolePortComparisonView(GenericComparisonView):
    """Comparison of console ports between a device and a device type and beautiful visualization"""
    obj_model = ConsolePort
    obj_template_model = ConsolePortTemplate


class ConsoleServerPortComparisonView(GenericComparisonView):
    """Comparison of console server ports between a device and a device type and beautiful visualization"""
    obj_model = ConsoleServerPort
    obj_template_model = ConsoleServerPortTemplate


class InterfaceComparisonView(GenericComparisonView):
    """Comparison of interfaces between a device and a device type and beautiful visualization"""
    obj_model = Interface
    obj_template_model = InterfaceTemplate

    @staticmethod
    def filter_comparison_components(component_templates: QuerySet, components: QuerySet) -> Tuple[QuerySet, QuerySet]:
        if config["exclude_virtual_interfaces"]:
            components = components.exclude(type__in=VIRTUAL_IFACE_TYPES)
            component_templates = component_templates.exclude(type__in=VIRTUAL_IFACE_TYPES)
        return component_templates, components


class PowerPortComparisonView(GenericComparisonView):
    """Comparison of power ports between a device and a device type and beautiful visualization"""
    obj_model = PowerPort
    obj_template_model = PowerPortTemplate


class PowerOutletComparisonView(GenericComparisonView):
    """Comparison of power outlets between a device and a device type and beautiful visualization"""
    obj_model = PowerOutlet
    obj_template_model = PowerOutletTemplate

    def post(self, request, device_id):
        device = get_object_or_404(Device.objects.filter(id=device_id))

        poweroutlets = device.poweroutlets.all()
        poweroutlets_templates = PowerOutletTemplate.objects.filter(device_type=device.device_type)

        # Generating result message
        message = []
        created = 0
        updated = 0
        fixed = 0

        remove_from_device = filter(
            lambda i: i in poweroutlets.values_list("id", flat=True),
            map(int, filter(lambda x: x.isdigit(), request.POST.getlist("remove")))
        )

        # Remove selected power outlets from the device and count them
        deleted = PowerOutlet.objects.filter(id__in=remove_from_device).delete()[0]

        # Get device power ports to check dependency between power outlets
        device_pp = PowerPort.objects.filter(device_id=device.id)

        matching = {}
        mismatch = False
        for i in poweroutlets_templates:
            found = False
            if i.power_port_id is not None:
                ppt = PowerPortTemplate.objects.get(id=i.power_port_id)
                for pp in device_pp:
                    if pp.name == ppt.name:
                        # Save matching to add the correct power port later
                        matching[i.id] = pp.id
                        found = True

                # If at least one power port is not found in device there is a dependency
                # Better not to sync at all
                if not found:
                    mismatch = True
                    break

        if not mismatch:
            add_to_device = filter(
                lambda i: i in poweroutlets_templates.values_list("id", flat=True),
                map(int, filter(lambda x: x.isdigit(), request.POST.getlist("add")))
            )

            # Add selected component to the device and count them
            add_to_device_component = PowerOutletTemplate.objects.filter(id__in=add_to_device)

            bulk_create = []
            updated = 0
            keys_to_avoid = ["id"]

            if not config["compare_description"]:
                keys_to_avoid.append("description")

            for i in add_to_device_component.values():
                to_create = False

                try:
                    # If power outlets already exists, update and do not recreate
                    po = device.poweroutlets.get(name=i["name"])
                except PowerOutlet.DoesNotExist:
                    po = PowerOutlet()
                    po.device = device
                    to_create = True

                # Copy all fields from template
                for k in i.keys():
                    if k not in keys_to_avoid:
                        setattr(po, k, i[k])
                po.power_port_id = matching.get(i["id"], None)

                if to_create:
                    bulk_create.append(po)
                else:
                    po.save()
                    updated += 1

            created = len(PowerOutlet.objects.bulk_create(bulk_create))

            # Getting and validating a list of components to rename
            fix_name_components = filter(lambda i: str(i.id) in request.POST.getlist("fix_name"), poweroutlets)

            # Casting component templates into Unified objects for proper comparison with component for renaming
            unified_component_templates = [
                PowerOutletComparison(i.id, i.name, i.label, i.description, i.type, i.get_type_display(),
                                      power_port_name=PowerPortTemplate.objects.get(id=i.power_port_id).name
                                      if i.power_port_id is not None else "",
                                      feed_leg=i.feed_leg, is_template=True)
                for i in poweroutlets_templates]

            # Rename selected power outlets
            fixed = 0
            for component in fix_name_components:
                unified_poweroutlet = PowerOutletComparison(
                    component.id, component.name, component.label, component.description, component.type,
                    component.get_type_display(),
                    power_port_name=PowerPort.objects.get(id=component.power_port_id).name
                    if component.power_port_id is not None else "",
                    feed_leg=component.feed_leg
                )
                try:
                    # Try to extract a component template with the corresponding name
                    corresponding_template = unified_component_templates[
                        unified_component_templates.index(unified_poweroutlet)
                    ]
                    component.name = corresponding_template.name
                    component.save()
                    fixed += 1
                except ValueError:
                    pass
        else:
            messages.error(request, "Dependency detected, sync power ports first!")

        if created > 0:
            message.append(f"created {created} power outlets")
        if updated > 0:
            message.append(f"updated {updated} power outlets")
        if deleted > 0:
            message.append(f"deleted {deleted} power outlets")
        if fixed > 0:
            message.append(f"fixed {fixed} power outlets")

        messages.info(request, "; ".join(message).capitalize())

        return redirect(request.path)


class RearPortComparisonView(GenericComparisonView):
    """Comparison of rear ports between a device and a device type and beautiful visualization"""
    obj_model = RearPort
    obj_template_model = RearPortTemplate


class DeviceBayComparisonView(GenericComparisonView):
    """Comparison of device bays between a device and a device type and beautiful visualization"""
    obj_model = DeviceBay
    obj_template_model = DeviceBayTemplate
#
#
# class FrontPortComparisonView(LoginRequiredMixin, PermissionRequiredMixin, View):
#     """Comparison of front ports between a device and a device type and beautiful visualization"""
#     permission_required = get_permissions_for_object("dcim", "frontport")
#
#     def get(self, request, device_id):
#
#         device = get_object_or_404(Device.objects.filter(id=device_id))
#
#         frontports = device.frontports.all()
#         frontports_templates = FrontPortTemplate.objects.filter(device_type=device.device_type)
#
#         unified_frontports = [
#             FrontPortComparison(
#                 i.id, i.name, i.label, i.description, i.type, i.get_type_display(), i.color, i.rear_port_position)
#             for i in frontports]
#         unified_frontports_templates = [
#             FrontPortComparison(
#                 i.id, i.name, i.label, i.description, i.type, i.get_type_display(), i.color,
#                 i.rear_port_position, is_template=True)
#             for i in frontports_templates]
#
#         return get_components(request, device, frontports, unified_frontports, unified_frontports_templates)
#
#     def post(self, request, device_id):
#         form = ComponentComparisonForm(request.POST)
#         if form.is_valid():
#             device = get_object_or_404(Device.objects.filter(id=device_id))
#
#             frontports = device.frontports.all()
#             frontports_templates = FrontPortTemplate.objects.filter(device_type=device.device_type)
#
#             # Generating result message
#             message = []
#             created = 0
#             updated = 0
#             fixed = 0
#
#             remove_from_device = filter(
#                 lambda i: i in frontports.values_list("id", flat=True),
#                 map(int, filter(lambda x: x.isdigit(), request.POST.getlist("remove_from_device")))
#             )
#
#             # Remove selected front ports from the device and count them
#             deleted = FrontPort.objects.filter(id__in=remove_from_device).delete()[0]
#
#             # Get device rear ports to check dependency between front ports
#             device_rp = RearPort.objects.filter(device_id=device.id)
#
#             matching = {}
#             mismatch = False
#             for i in frontports_templates:
#                 found = False
#                 if i.rear_port_id is not None:
#                     rpt = RearPortTemplate.objects.get(id=i.rear_port_id)
#                     for rp in device_rp:
#                         if rp.name == rpt.name:
#                             # Save matching to add the correct rear port later
#                             matching[i.id] = rp.id
#                             found = True
#
#                     # If at least one rear port is not found in device there is a dependency
#                     # Better not to sync at all
#                     if not found:
#                         mismatch = True
#                         break
#
#             if not mismatch:
#                 add_to_device = filter(
#                     lambda i: i in frontports_templates.values_list("id", flat=True),
#                     map(int, filter(lambda x: x.isdigit(), request.POST.getlist("add_to_device")))
#                 )
#
#                 # Add selected component to the device and count them
#                 add_to_device_component = FrontPortTemplate.objects.filter(id__in=add_to_device)
#
#                 bulk_create = []
#                 updated = 0
#                 keys_to_avoid = ["id"]
#
#                 if not config["compare_description"]:
#                     keys_to_avoid.append("description")
#
#                 for i in add_to_device_component.values():
#                     to_create = False
#
#                     try:
#                         # If front port already exists, update and do not recreate
#                         fp = device.frontports.get(name=i["name"])
#                     except FrontPort.DoesNotExist:
#                         fp = FrontPort()
#                         fp.device = device
#                         to_create = True
#
#                     # Copy all fields from template
#                     for k in i.keys():
#                         if k not in keys_to_avoid:
#                             setattr(fp, k, i[k])
#                     fp.rear_port_id = matching.get(i["id"], None)
#
#                     if to_create:
#                         bulk_create.append(fp)
#                     else:
#                         fp.save()
#                         updated += 1
#
#                 created = len(FrontPort.objects.bulk_create(bulk_create))
#
#                 # Getting and validating a list of components to rename
#                 fix_name_components = filter(lambda i: str(i.id) in request.POST.getlist("fix_name"), frontports)
#
#                 # Casting component templates into Unified objects for proper comparison with component for renaming
#                 unified_frontports_templates = [
#                     FrontPortComparison(
#                         i.id, i.name, i.label, i.description, i.type, i.get_type_display(),
#                         i.color, i.rear_port_position, is_template=True)
#                     for i in frontports_templates]
#                 # Rename selected front ports
#                 fixed = 0
#                 for component in fix_name_components:
#                     unified_frontport = FrontPortComparison(
#                         component.id, component.name, component.label, component.description, component.type,
#                         component.get_type_display(), component.color, component.rear_port_position
#                     )
#
#                     try:
#                         # Try to extract a component template with the corresponding name
#                         corresponding_template = unified_frontports_templates[
#                             unified_frontports_templates.index(unified_frontport)
#                         ]
#                         component.name = corresponding_template.name
#                         component.save()
#                         fixed += 1
#                     except ValueError:
#                         pass
#             else:
#                 messages.error(request, "Dependency detected, sync rear ports first!")
#
#             if created > 0:
#                 message.append(f"created {created} front ports")
#             if updated > 0:
#                 message.append(f"updated {updated} front ports")
#             if deleted > 0:
#                 message.append(f"deleted {deleted} front ports")
#             if fixed > 0:
#                 message.append(f"fixed {fixed} front ports")
#
#             messages.info(request, "; ".join(message).capitalize())
#
#             return redirect(request.path)
