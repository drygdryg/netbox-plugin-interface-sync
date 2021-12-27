from django.db.models.fields.related import ForeignKey
from django.shortcuts import get_object_or_404, render, redirect
from django.views.generic import View
from dcim.choices import PortTypeChoices
from dcim.models import Device, Interface, InterfaceTemplate, PowerPort, PowerPortTemplate, ConsolePort, ConsolePortTemplate, ConsoleServerPort, ConsoleServerPortTemplate, DeviceBay, DeviceBayTemplate, FrontPort, FrontPortTemplate,PowerOutlet, PowerOutletTemplate, RearPort, RearPortTemplate
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.conf import settings
from django.contrib import messages

from .utils import ComparisonPowerOutlet, UnifiedInterface, natural_keys, get_components, post_components
from .forms import InterfaceComparisonForm

config = settings.PLUGINS_CONFIG['netbox_interface_sync']


class InterfaceComparisonView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """Comparison of interfaces between a device and a device type and beautiful visualization"""
    permission_required = ("dcim.view_interface", "dcim.add_interface", "dcim.change_interface", "dcim.delete_interface")

    def get(self, request, device_id):
        device = get_object_or_404(Device.objects.filter(id=device_id))
        interfaces = device.vc_interfaces()
        if config["exclude_virtual_interfaces"]:
            interfaces = list(filter(lambda i: not i.is_virtual, interfaces))
        interface_templates = InterfaceTemplate.objects.filter(device_type=device.device_type)

        return get_components(request, device, interfaces, interface_templates)

    def post(self, request, device_id):
        form = InterfaceComparisonForm(request.POST)
        if form.is_valid():
            device = get_object_or_404(Device.objects.filter(id=device_id))
            interfaces = device.vc_interfaces()
            if config["exclude_virtual_interfaces"]:
                interfaces = interfaces.exclude(type__in=["virtual", "lag"])
            interface_templates = InterfaceTemplate.objects.filter(device_type=device.device_type)
            
            return post_components(request, device, interfaces, interface_templates, Interface, InterfaceTemplate)

class PowerPortComparisonView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """Comparison of interfaces between a device and a device type and beautiful visualization"""
    permission_required = ("dcim.view_interface", "dcim.add_interface", "dcim.change_interface", "dcim.delete_interface")

    def get(self, request, device_id):
        device = get_object_or_404(Device.objects.filter(id=device_id))
        
        powerports = device.powerports.all()
        powerports_templates = PowerPortTemplate.objects.filter(device_type=device.device_type)

        return get_components(request, device, powerports, powerports_templates)

    def post(self, request, device_id):
        form = InterfaceComparisonForm(request.POST)
        if form.is_valid():
            device = get_object_or_404(Device.objects.filter(id=device_id))

            powerports = device.powerports.all()
            powerports_templates = PowerPortTemplate.objects.filter(device_type=device.device_type)
            
            return post_components(request, device, powerports, powerports_templates, PowerPort, PowerPortTemplate)

class ConsolePortComparisonView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """Comparison of interfaces between a device and a device type and beautiful visualization"""
    permission_required = ("dcim.view_interface", "dcim.add_interface", "dcim.change_interface", "dcim.delete_interface")

    def get(self, request, device_id):
        device = get_object_or_404(Device.objects.filter(id=device_id))
        
        consoleports = device.consoleports.all()
        consoleports_templates = ConsolePortTemplate.objects.filter(device_type=device.device_type)

        return get_components(request, device, consoleports, consoleports_templates)

    def post(self, request, device_id):
        form = InterfaceComparisonForm(request.POST)
        if form.is_valid():
            device = get_object_or_404(Device.objects.filter(id=device_id))

            consoleports = device.consoleports.all()
            consoleports_templates = ConsolePortTemplate.objects.filter(device_type=device.device_type)
            
            return post_components(request, device, consoleports, consoleports_templates, ConsolePort, ConsolePortTemplate)

class ConsoleServerPortComparisonView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """Comparison of interfaces between a device and a device type and beautiful visualization"""
    permission_required = ("dcim.view_interface", "dcim.add_interface", "dcim.change_interface", "dcim.delete_interface")

    def get(self, request, device_id):
        device = get_object_or_404(Device.objects.filter(id=device_id))
        
        consoleserverports = device.consoleserverports.all()
        consoleserverports_templates = ConsoleServerPortTemplate.objects.filter(device_type=device.device_type)

        return get_components(request, device, consoleserverports, consoleserverports_templates)

    def post(self, request, device_id):
        form = InterfaceComparisonForm(request.POST)
        if form.is_valid():
            device = get_object_or_404(Device.objects.filter(id=device_id))

            consoleserverports = device.consoleserverports.all()
            consoleserverports_templates = ConsoleServerPortTemplate.objects.filter(device_type=device.device_type)
            
            return post_components(request, device, consoleserverports, consoleserverports_templates, ConsoleServerPort, ConsoleServerPortTemplate)

class PowerOutletComparisonView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """Comparison of interfaces between a device and a device type and beautiful visualization"""
    permission_required = ("dcim.view_interface", "dcim.add_interface", "dcim.change_interface", "dcim.delete_interface")

    def get(self, request, device_id):
        device = get_object_or_404(Device.objects.filter(id=device_id))
        
        poweroutlets = device.poweroutlets.all()
        poweroutlets_templates = PowerOutletTemplate.objects.filter(device_type=device.device_type)
        
        unified_components = [ComparisonPowerOutlet(i.id, i.name, i.type, i.get_type_display(), power_port_name=PowerPort.objects.get(id=i.power_port_id).name if i.power_port_id is not None else "") for i in poweroutlets]
        unified_component_templates = [
            ComparisonPowerOutlet(i.id, i.name, i.type, i.get_type_display(), is_template=True, power_port_name=PowerPortTemplate.objects.get(id=i.power_port_id).name if i.power_port_id is not None else "") for i in poweroutlets_templates]

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
                "interfaces_count": len(poweroutlets),
                "device": device
                }
        )

    def post(self, request, device_id):
        form = InterfaceComparisonForm(request.POST)
        if form.is_valid():
            device = get_object_or_404(Device.objects.filter(id=device_id))

        poweroutlets = device.poweroutlets.all()
        poweroutlets_templates = PowerOutletTemplate.objects.filter(device_type=device.device_type)

        #se il template ha una power port che non ho nel device fisico stop
        device_pp = PowerPort.objects.filter(device_id=device.id)

        matching = {}
        mismatch = False
        for i in poweroutlets_templates:
            found = False
            if i.power_port_id is not None:
                ppt = PowerPortTemplate.objects.get(id=i.power_port_id)
                for pp in device_pp:
                    if pp.name == ppt.name:
                        matching[i.id] = pp.id
                        found = True
                
                if not found:
                    mismatch = True
                    break
        
        if not mismatch:
            # Manually validating interfaces and interface templates lists
            with open("/tmp/ciccio.log", "w") as f:
                f.write(str(request.POST.getlist("add_to_device")))
                
            add_to_device = filter(
                lambda i: i in poweroutlets_templates.values_list("id", flat=True),
                map(int, filter(lambda x: x.isdigit(), request.POST.getlist("add_to_device")))
            )
            remove_from_device = filter(
                lambda i: i in poweroutlets.values_list("id", flat=True),
                map(int, filter(lambda x: x.isdigit(), request.POST.getlist("remove_from_device")))
            )

            # Remove selected interfaces from the device and count them
            deleted = PowerOutlet.objects.filter(id__in=remove_from_device).delete()[0]

            # Add selected interfaces to the device and count them
            add_to_device_component = PowerOutletTemplate.objects.filter(id__in=add_to_device)

            bulk_create = []
            keys_to_avoid = ["id"]

            for i in add_to_device_component.values():
                tmp = PowerOutlet()
                tmp.device = device
                for k in i.keys():
                    if k not in keys_to_avoid:
                        setattr(tmp, k, i[k])
                tmp.power_port_id = matching.get(i["id"], None)
                bulk_create.append(tmp)

            created = len(PowerOutlet.objects.bulk_create(bulk_create))

            # Getting and validating a list of interfaces to rename
            fix_name_components = filter(lambda i: str(i.id) in request.POST.getlist("fix_name"), poweroutlets)

            # Casting interface templates into UnifiedInterface objects for proper comparison with interfaces for renaming
            unified_component_templates = [
                ComparisonPowerOutlet(i.id, i.name, i.type, i.get_type_display(), is_template=True, power_port_name=PowerPortTemplate.objects.get(id=i.power_port_id).name if i.power_port_id is not None else "") for i in poweroutlets_templates]


            # Rename selected interfaces
            fixed = 0
            for component in fix_name_components:
                unified_component = [ComparisonPowerOutlet(i.id, i.name, i.type, i.get_type_display(), power_port_name=PowerPort.objects.get(id=i.power_port_id).name if i.power_port_id is not None else "") for i in poweroutlets]

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
        else:
            messages.error(request, "Fai prima le power ports")
            return redirect(request.path)

class FrontPortComparisonView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """Comparison of interfaces between a device and a device type and beautiful visualization"""
    permission_required = ("dcim.view_interface", "dcim.add_interface", "dcim.change_interface", "dcim.delete_interface")

    def get(self, request, device_id):
        device = get_object_or_404(Device.objects.filter(id=device_id))
        
        frontports = device.frontports.all()
        frontports_templates = FrontPortTemplate.objects.filter(device_type=device.device_type)

        return get_components(request, device, frontports, frontports_templates)

    def post(self, request, device_id):
        form = InterfaceComparisonForm(request.POST)
        if form.is_valid():
            device = get_object_or_404(Device.objects.filter(id=device_id))

        frontports = device.frontports.all()
        frontports_templates = FrontPortTemplate.objects.filter(device_type=device.device_type)
            
        return post_components(request, device, frontports, frontports_templates, FrontPort, FrontPortTemplate)

class RearPortComparisonView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """Comparison of interfaces between a device and a device type and beautiful visualization"""
    permission_required = ("dcim.view_interface", "dcim.add_interface", "dcim.change_interface", "dcim.delete_interface")

    def get(self, request, device_id):
        device = get_object_or_404(Device.objects.filter(id=device_id))
        
        rearports = device.rearports.all()
        rearports_templates = RearPortTemplate.objects.filter(device_type=device.device_type)

        return get_components(request, device, rearports, rearports_templates)

    def post(self, request, device_id):
        form = InterfaceComparisonForm(request.POST)
        if form.is_valid():
            device = get_object_or_404(Device.objects.filter(id=device_id))

        rearports = device.rearports.all()
        rearports_templates = RearPortTemplate.objects.filter(device_type=device.device_type)
            
        return post_components(request, device, rearports, rearports_templates, RearPort, RearPortTemplate)

class DeviceBayComparisonView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """Comparison of interfaces between a device and a device type and beautiful visualization"""
    permission_required = ("dcim.view_interface", "dcim.add_interface", "dcim.change_interface", "dcim.delete_interface")

    def get(self, request, device_id):
        device = get_object_or_404(Device.objects.filter(id=device_id))
        
        devicebays = device.devicebays.all()
        devicebays_templates = DeviceBayTemplate.objects.filter(device_type=device.device_type)

        return get_components(request, device, devicebays, devicebays_templates)

    def post(self, request, device_id):
        form = InterfaceComparisonForm(request.POST)
        if form.is_valid():
            device = get_object_or_404(Device.objects.filter(id=device_id))

        devicebays = device.devicebays.all()
        devicebays_templates = DeviceBayTemplate.objects.filter(device_type=device.device_type)
            
        return post_components(request, device, devicebays, devicebays_templates, DeviceBay, DeviceBayTemplate)
