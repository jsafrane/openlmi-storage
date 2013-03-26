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
""" Module for LMI_DiskPartitionConfigurationSetting class."""

import pywbem
from openlmi.storage.SettingProvider import SettingProvider
from openlmi.storage.SettingManager import Setting

import parted
import openlmi.common.cmpi_logging as cmpi_logging
from openlmi.storage.util import storage

class LMI_DiskPartitionConfigurationSetting(SettingProvider):
    """
        Implementation of LMI_DiskPartitionConfigurationSetting
    """

    @cmpi_logging.trace_method
    def __init__(self, *args, **kwargs):
        supported_properties = {
            'Bootable': SettingProvider.string_to_bool,
            'Hidden': SettingProvider.string_to_bool,
            'PartitionType': pywbem.Uint16,
        }
        super(LMI_DiskPartitionConfigurationSetting, self).__init__(
                setting_classname="LMI_DiskPartitionConfigurationSetting",
                supported_properties=supported_properties,
                validate_properties=None,
                *args, **kwargs)

    @cmpi_logging.trace_method
    def get_configuration(self, device):
        """
            Return Setting with configuration of given device.
        """
        _id = self.create_setting_id(storage.get_persistent_name(device))
        setting = Setting(Setting.TYPE_CONFIGURATION, _id)
        setting['Bootable'] = str(device.bootable)
        flag = device.getFlag(parted.PARTITION_HIDDEN)
        if flag:
            setting['Hidden'] = "True"
        if device.isExtended:
            setting['PartitionType'] = str(self.Values.PartitionType.Extended)
        elif device.isLogical:
            setting['PartitionType'] = str(self.Values.PartitionType.Logical)
        elif device.isPrimary:
            setting['PartitionType'] = str(self.Values.PartitionType.Primary)
        else:
            setting['PartitionType'] = str(self.Values.PartitionType.Unknown)
        setting['ElementName'] = setting.the_id
        return setting

    @cmpi_logging.trace_method
    def enumerate_configurations(self):
        """
            Enumerate all instances attached to partitions.
        """
        for device in self.storage.partitions:
            yield self.get_configuration(device)

    @cmpi_logging.trace_method
    def get_configuration_for_id(self, instance_id):
        """
            Return Setting instance for given instance_id.
            Return None if no such Setting is found.
        """
        path = self.parse_setting_id(instance_id)
        if not path:
            return None

        device = storage.get_device_for_persistent_name(self.storage, path)
        if not device:
            return None
        return self.get_configuration(device)

    @cmpi_logging.trace_method
    def get_associated_element_name(self, instance_id):
        """
            Return CIMInstanceName for ElementSettingData association.
            Return None if no such element exist. 
        """
        path = self.parse_setting_id(instance_id)
        if not path:
            return None

        device = storage.get_device_for_persistent_name(self.storage, path)
        if not device:
            return None

        return self.provider_manager.get_name_for_device(device)


    class Values(SettingProvider.Values):
        class PartitionType(object):
            Unknown = 0
            Primary = 1
            Extended = 2
            Logical = 3
