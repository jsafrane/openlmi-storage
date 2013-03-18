# Copyright (C) 2013 Red Hat, Inc.  All rights reserved.
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA
#
# Authors: Jan Safranek <jsafrane@redhat.com>
# -*- coding: utf-8 -*-
""" Module for FormatProvider."""

import pywbem
from openlmi.storage.BaseProvider import BaseProvider
import openlmi.common.cmpi_logging as cmpi_logging

class FormatProvider(BaseProvider):
    """
        Abstract provider for data formats and filesystems.
        Each provider must have .device_type property, which represents
        blivet.formats.<DeviceFormat child>.type of format it
        represents.
    """
    @cmpi_logging.trace_method
    def __init__(self, classname, device_type, *args, **kwargs):
        self.classname = classname
        self.device_type = device_type
        super(FormatProvider, self).__init__(*args, **kwargs)

    @cmpi_logging.trace_method
    # pylint: disable-msg=W0613
    def provides_name(self, name):
        """
            Returns True, if this class is provider for given CIMInstanceName.
            Subclasses do not need to override this method as long as
            self.classname is correct CIM class name.
        """
        if not (name.has_key("CSCreationClassName")
                and name.has_key("CSName")
                and name.has_key("CreationClassName")
                and name.has_key("Name")):
            return False
        if name['CreationClassName'] != self.classname:
            return False
        if name['CSCreationClassName'] != self.config.system_class_name:
            return False
        if name['CSName'] != self.config.system_name:
            return False
        return True

    @cmpi_logging.trace_method
    # pylint: disable-msg=W0613
    def provides_format(self, device, fmt):
        """
            Returns True, if this class is provider for given Anaconda
            DeviceFormat class.
            Subclasses must override this method.
        """
        return False

    @cmpi_logging.trace_method
    def get_uuid(self, device, fmt):
        """
        Return UUID of the format or None when it does not exist.
        """
        try:
            return fmt.uuid
        except AttributeError:
            return None

    @cmpi_logging.trace_method
    def get_format_id(self, device, fmt):
        """
            Return LMI_DataFormat.Name. The name should be unique and stable
            across reboots or reconfigurations. UUID is used, subclasses
            do not need to override this method.
        """
        uuid = self.get_uuid(device, fmt)
        if uuid:
            return "UUID=" + uuid

        return "DEVICE=" + device.path

    @cmpi_logging.trace_method
    def get_format_for_id(self, name):
        """
            Return tuple (StorageDevice, DeviceFormat) for given Name property
            of CIMInstance. Return None if no such format exist.
            This is reverse function to get_format_id().
            Subclasses do not need to override this method if they do not
            override get_format_id().
        """

        if name.startswith("DEVICE="):
            (_unused, devname) = name.split("=")
            device = self.storage.devicetree.getDeviceByPath(devname)
        elif name.startswith("UUID="):
            (_unused, uuid) = name.split("=")
            device = self.storage.devicetree.getDeviceByUuid(uuid)
        else:
            return None
        if not device:
            return None
        return (device, device.format)

    @cmpi_logging.trace_method
    def get_name_for_format(self, device, fmt):
        """ Return CIMInstanceName for given DeviceFormat subclass."""
        name = pywbem.CIMInstanceName(self.classname,
                namespace=self.config.namespace,
                keybindings={
                        "CSCreationClassName": self.config.system_class_name,
                        "CSName": self.config.system_name,
                        "CreationClassName": self.classname,
                        "Name": self.get_format_id(device, fmt)})
        return name

    @cmpi_logging.trace_method
    def enum_instances(self, env, model, keys_only):
        """
            Enumerate instances. Subclasses do not need to override this method,
            as long as enumeration by self.provides_format is sufficient.
        """
        model.path.update({'CSName': None, 'CreationClassName': None,
            'CSCreationClassName': None, 'Name': None})

        for device in self.storage.devices:
            fmt = device.format
            if fmt and self.provides_format(device, fmt):
                name = self.get_name_for_format(device, fmt)
                model.update(name)
                if keys_only:
                    yield model
                else:
                    yield self.get_instance(env, model, fmt)

    @cmpi_logging.trace_method
    def get_format_for_name(self, instance_name):
        """
            Return tuple (StorageDevice, DeviceFormat) instance for given
            CIMInstanceName. Return None if no such instance_name exists.
        """
        if instance_name['CSName'] != self.config.system_name:
            return None
        if instance_name['CSCreationClassName'] != \
                    self.config.system_class_name:
            return None
        if instance_name['CreationClassName'] != self.classname:
            return None
        return self.get_format_for_id(instance_name['Name'])


    @cmpi_logging.trace_method
    # pylint: disable-msg=W0221
    def get_instance(self, env, model, fmt=None):
        """
            Get instance.
            Subclasses should override this method, the default implementation
            just check if the instance exists.
        """
        if not fmt:
            (device, fmt) = self.get_format_for_name(model)
        if not fmt:
            raise pywbem.CIMError(pywbem.CIM_ERR_NOT_FOUND,
                    "Cannot find the format.")
        model['FormatTypeDescription'] = fmt.name

        fmt_types = {
                "swap": self.Values.FormatType.Swap,
                "mdmember": self.Values.FormatType.MD_RAID_member,
                "lvmpv": self.Values.FormatType.Physical_Volume,
                "luks": self.Values.FormatType.LUKS,
                "biosboot": self.Values.FormatType.BIOS_Boot,
                "dmraidmember": self.Values.FormatType.DM_RAID_member,
                "multipath_member": self.Values.FormatType.Multipath_member,
                "prepboot": self.Values.FormatType.PPC_PReP_Boot,
        }
        fmt_type = fmt_types.get(fmt.type, self.Values.FormatType.Other)
        model['FormatType'] = fmt_type
        model['ElementName'] = fmt.device
        return model

    class Values(object):
        class FormatType(object):
            Swap = pywbem.Uint16(1)
            MD_RAID_member = pywbem.Uint16(2)
            Physical_Volume = pywbem.Uint16(3)
            LUKS = pywbem.Uint16(4)
            BIOS_Boot = pywbem.Uint16(5)
            DM_RAID_member = pywbem.Uint16(6)
            Multipath_member = pywbem.Uint16(7)
            PPC_PReP_Boot = pywbem.Uint16(8)
            Other = pywbem.Uint16(65535)


class LMI_ResidesOnExtent(BaseProvider):
    """ Implementation of LMI_ResidesOnExtent association."""
    def __init__(self, *args, **kwargs):
        super(LMI_ResidesOnExtent, self).__init__(*args, **kwargs)

    @cmpi_logging.trace_method
    def enum_instances(self, env, model, keys_only):
        """
            Enumerate instances.
        """
        model.path.update({'Dependent': None, 'Antecedent': None})

        for device in self.storage.devices:
            fmt = device.format
            if not fmt or not fmt.type:
                continue
            provider = self.provider_manager.get_provider_for_format(
                    device, fmt)
            if not provider:
                continue
            fmtname = provider.get_name_for_format(device, fmt)
            devname = self.provider_manager.get_name_for_device(device)
            if not devname:
                continue
            model['Dependent'] = fmtname
            model['Antecedent'] = devname
            yield model

    @cmpi_logging.trace_method
    def get_instance(self, env, model):
        """ Get instance. """
        fmtname = model['Dependent']
        devname = model['Antecedent']

        # just check that the device has the format
        device = self.provider_manager.get_device_for_name(devname)
        if not device:
            raise pywbem.CIMError(pywbem.CIM_ERR_NOT_FOUND,
                    "Cannot find Antecedent device.")

        fmt = device.format
        if not fmt:
            raise pywbem.CIMError(pywbem.CIM_ERR_NOT_FOUND,
                    "The Antecedent device has no format.")

        fmtprovider = self.provider_manager.get_provider_for_format(
                device, fmt)
        if not fmtprovider:
            raise pywbem.CIMError(pywbem.CIM_ERR_NOT_FOUND,
                    "The Antecedent device has unknown format.")

        real_fmtname = fmtprovider.get_name_for_format(device, fmt)
        if real_fmtname != fmtname:
            raise pywbem.CIMError(pywbem.CIM_ERR_NOT_FOUND,
                    "The Antecedent device has different format.")
        return model

    @cmpi_logging.trace_method
    def references(self, env, object_name, model, result_class_name, role,
                   result_role, keys_only):
        """Instrument Associations."""
        # don't forget to try both DataFormat and LocalFileSystem subclasses!
        refs = self.simple_references(
                    env, object_name, model,
                    result_class_name, role, result_role, keys_only,
                    "LMI_DataFormat",
                    "CIM_StorageExtent")
        if refs:
            return refs

        refs = self.simple_references(
                    env, object_name, model,
                    result_class_name, role, result_role, keys_only,
                    "LMI_LocalFileSystem",
                    "CIM_StorageExtent")
        return refs
