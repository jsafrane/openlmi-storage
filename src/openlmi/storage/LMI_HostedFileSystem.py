# Copyright (C) 2012 Red Hat, Inc.  All rights reserved.
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
""" Module for LMI_HostedFileSystem class."""

from openlmi.storage.BaseProvider import BaseProvider
import pywbem
import openlmi.common.cmpi_logging as cmpi_logging
from openlmi.storage.LocalFileSystemProvider import LocalFileSystemProvider

class LMI_HostedFileSystem(BaseProvider):
    """
        Implementation of LMI_HostedFileSystem provider.
    """

    @cmpi_logging.trace_method
    def __init__(self, *args, **kwargs):
        super(LMI_HostedFileSystem, self).__init__(*args, **kwargs)


    @cmpi_logging.trace_method
    def get_instance(self, env, model):
        """
            Provider implementation of GetInstance intrinsic method.
        """
        # just check keys
        system = model['GroupComponent']
        if (system['CreationClassName'] != self.config.system_class_name
                or system['Name'] != self.config.system_name):
            raise pywbem.CIMError(pywbem.CIM_ERR_NOT_FOUND,
                    "Wrong GroupComponent keys.")

        fmtname = model['PartComponent']
        fmtprovider = self.provider_manager.get_provider_for_format_name(
                fmtname)

        if not fmtprovider:
            raise pywbem.CIMError(pywbem.CIM_ERR_NOT_FOUND,
                    "The PartComponent device has unknown format.")

        if not isinstance(fmtprovider, LocalFileSystemProvider):
            raise pywbem.CIMError(pywbem.CIM_ERR_NOT_FOUND,
                    "The PartComponent is not a filesystem.")

        (device, fmt) = fmtprovider.get_format_for_name(fmtname)
        if not fmt or not device:
            raise pywbem.CIMError(pywbem.CIM_ERR_NOT_FOUND,
                    "The PartComponent not found.")

        return model

    @cmpi_logging.trace_method
    def enum_instances(self, env, model, keys_only):
        """
            Provider implementation of EnumerateInstances intrinsic method.
        """
        model.path.update({'GroupComponent': None, 'PartComponent': None})
        for device in self.storage.devices:
            fmt = device.format
            if not fmt or not fmt.type:
                continue
            provider = self.provider_manager.get_provider_for_format(
                    device, fmt)
            if not provider:
                continue
            # we're interested only in filesystems, not data formats
            if not isinstance(provider, LocalFileSystemProvider):
                continue

            model['GroupComponent'] = pywbem.CIMInstanceName(
                    classname=self.config.system_class_name,
                    namespace=self.config.namespace,
                    keybindings={
                            'CreationClassName' : self.config.system_class_name,
                            'Name' : self.config.system_name,
                    })
            model['PartComponent'] = provider.get_name_for_format(device, fmt)
            yield model

    @cmpi_logging.trace_method
    def references(self, env, object_name, model, result_class_name, role,
                   result_role, keys_only):
        """Instrument Associations."""
        return self.simple_references(env, object_name, model,
                result_class_name, role, result_role, keys_only,
                "LMI_LocalFileSystem",
                "CIM_System")
