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
""" Module for LMI_LVStorageExtent class."""

from openlmi.storage.ExtentProvider import ExtentProvider
import blivet
import openlmi.common.cmpi_logging as cmpi_logging
from openlmi.storage.SettingHelper import SettingHelper
from openlmi.storage.SettingManager import StorageSetting
import pywbem
import openlmi.storage.util.storage as storage
from openlmi.storage.SettingProvider import SettingProvider

class LMI_LVStorageExtent(ExtentProvider, SettingHelper):
    """
        Provider of LMI_LVStorageExtent class.
    """

    @cmpi_logging.trace_method
    def __init__(self, *args, **kwargs):
        super(LMI_LVStorageExtent, self).__init__(
                classname='LMI_LVStorageExtent',
                setting_classname='LMI_LVStorageSetting',
                *args, **kwargs)

    @cmpi_logging.trace_method
    def provides_device(self, device):
        """
            Returns True, if this class is provider for given Anaconda
            StorageDevice class.
        """
        if  isinstance(device,
                    blivet.devices.LVMLogicalVolumeDevice):
            return True
        return False

    @cmpi_logging.trace_method
    def enumerate_devices(self):
        """
            Enumerate all StorageDevices, that this provider provides.
        """
        for device in self.storage.lvs:
            yield device

    @cmpi_logging.trace_method
    def get_element_name(self, device):
        return device.lvname

    @cmpi_logging.trace_method
    def get_instance(self, env, model, device=None):
        """
            Add LV-specific properties.
        """
        model = super(LMI_LVStorageExtent, self).get_instance(
                env, model, device)
        if not device:
            device = self._get_device(model)

        model['UUID'] = device.uuid

        return model

    @cmpi_logging.trace_method
    def _get_setting_for_device(self, device, setting_provider):
        """ Return setting for given device """
        setting = StorageSetting(
                StorageSetting.TYPE_CONFIGURATION,
                setting_provider.create_setting_id(device.path))
        setting.set_setting(self.get_redundancy(device))
        setting['ElementName'] = device.path
        return setting

    @cmpi_logging.trace_method
    def enumerate_settings(self, setting_provider):
        """
            This method returns iterable with all instances of LMI_*Setting
            as Setting instances.
        """
        for lv in self.storage.lvs:
            yield self._get_setting_for_device(lv, setting_provider)

    @cmpi_logging.trace_method
    def get_setting_for_id(self, setting_provider, instance_id):
        """
            Return Setting instance, which corresponds to LMI_*Setting with
            given InstanceID.
            Return None if there is no such instance.
            
            Subclasses must override this method.
        """
        path = setting_provider.parse_setting_id(instance_id)
        if not path:
            return None
        device = self.storage.devicetree.getDeviceByPath(path)
        if not path:
            return None
        if not isinstance(device,
                blivet.devices.LVMLogicalVolumeDevice):
            cmpi_logging.logger.trace_warn(
                    "InstanceID %s is not LVMLogicalVolumeDevice" % instance_id)
            return None
        return self._get_setting_for_device(device, setting_provider)

    @cmpi_logging.trace_method
    def get_associated_element_name(self, setting_provider, instance_id):
        """
            Return CIMInstanceName of ManagedElement for ElementSettingData
            association for setting with given ID.
            Return None if no such ManagedElement exists.
        """
        path = setting_provider.parse_setting_id(instance_id)
        if not path:
            return None
        device = self.storage.devicetree.getDeviceByPath(path)
        if not path:
            return None
        if not isinstance(device,
                blivet.devices.LVMLogicalVolumeDevice):
            cmpi_logging.logger.trace_warn(
                    "InstanceID %s is not LVMLogicalVolumeDevice" % instance_id)
            return None
        return self.get_name_for_device(device)

    @cmpi_logging.trace_method
    def get_supported_setting_properties(self, setting_provider):
        """
            Return hash property_name -> constructor.
                constructor is a function which takes string argument
                and returns CIM value. (i.e. pywbem.Uint16
                or bool or string etc).
            This hash will be passed to SettingProvider.__init__ 
        """
        return {
                'DataRedundancyGoal': pywbem.Uint16,
                'DataRedundancyMax': pywbem.Uint16,
                'DataRedundancyMin': pywbem.Uint16,
                'ExtentStripeLength' : pywbem.Uint16,
                'ExtentStripeLengthMax' : pywbem.Uint16,
                'ExtentStripeLengthMin' : pywbem.Uint16,
                'NoSinglePointOfFailure' : SettingProvider.string_to_bool,
                'PackageRedundancyGoal' : pywbem.Uint16,
                'PackageRedundancyMax' : pywbem.Uint16,
                'PackageRedundancyMin' : pywbem.Uint16,
                'ParityLayout' : pywbem.Uint16,
        }

    @cmpi_logging.trace_method
    def get_setting_ignore(self, setting_provider):
        return {
                'CompressedElement': False,
                'CompressionRate': 1,
                'InitialSynchronization': 0,
                'SpaceLimit': 0,
                'ThinProvisionedInitialReserve': 0,
                'UseReplicationBuffer': 0,
        }

    @cmpi_logging.trace_method
    def get_setting_validators(self, setting_provider):
        return None


    @cmpi_logging.trace_method
    def do_delete_instance(self, device):
        cmpi_logging.logger.info("DELETE LV: %s" % (device.path))
        action = blivet.deviceaction.ActionDestroyDevice(device)
        storage.do_storage_action(self.storage, [action])
