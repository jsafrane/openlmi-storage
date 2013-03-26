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
""" Module for LMI_LVStorageCapabilities class."""

from openlmi.storage.CapabilitiesProvider import CapabilitiesProvider
import openlmi.common.cmpi_logging as cmpi_logging
from openlmi.storage.SettingManager import StorageSetting
import pywbem
import blivet.devices
from openlmi.storage.BaseProvider import BaseProvider
from openlmi.storage.util import storage

class LMI_LVStorageCapabilities(CapabilitiesProvider):
    """ Provider of LMI_LVStorageCapabilities class."""
    @cmpi_logging.trace_method
    def __init__(self, *args, **kwargs):
        super(LMI_LVStorageCapabilities, self).__init__(
                classname='LMI_LVStorageCapabilities', *args, **kwargs)
        self.pool_provider = None

    @cmpi_logging.trace_method
    def get_pool_name_for_capabilities(self, instance_id):
        """
            Return CIMInstanceName of storage pool associated with capabilities
            with given id.
        """
        path = self.parse_instance_id(instance_id)
        if not path:
            return None
        device = storage.get_device_for_persistent_name(self.storage, path)
        if not device:
            return None
        if not isinstance(device,
                blivet.devices.LVMVolumeGroupDevice):
            cmpi_logging.logger.trace_warn(
                    "InstanceID %s is not LVMVolumeGroupDevice" % instance_id)
            return None

        if not self.pool_provider:
            self.pool_provider = self.provider_manager.get_provider_for_device(
                    device)
        return self.pool_provider.get_name_for_device(device)


    @cmpi_logging.trace_method
    def _get_capabilities_for_device(self, device):
        """ Return capabilities fir given device. """
        if not self.pool_provider:
            self.pool_provider = self.provider_manager.get_provider_for_device(
                    device)

        redundancy = self.pool_provider.get_redundancy(device)
        caps = {}
        _id = storage.get_persistent_name(device)
        caps['InstanceID'] = self.create_capabilities_id(_id)
        caps['ElementName'] = device.path
        caps['DataRedundancyDefault'] = \
                pywbem.Uint16(redundancy.data_redundancy)
        caps['DataRedundancyMax'] = pywbem.Uint16(redundancy.data_redundancy)
        caps['DataRedundancyMin'] = pywbem.Uint16(redundancy.data_redundancy)
        caps['NoSinglePointOfFailure'] = redundancy.no_single_point_of_failure
        caps['NoSinglePointOfFailureDefault'] = \
                redundancy.no_single_point_of_failure
        caps['ExtentStripeLengthDefault'] = \
                pywbem.Uint16(redundancy.stripe_length)
        caps['PackageRedundancyDefault'] = \
                pywbem.Uint16(redundancy.package_redundancy)
        caps['PackageRedundancyMax'] = pywbem.Uint16(
                redundancy.package_redundancy)
        caps['PackageRedundancyMin'] = pywbem.Uint16(
                redundancy.package_redundancy)
        if redundancy.parity_layout:
            caps['ParityLayoutDefault'] = pywbem.Uint16(
                    redundancy.parity_layout + 1)
        else:
            caps['ParityLayoutDefault'] = None
        return caps


    @cmpi_logging.trace_method
    def enumerate_capabilities(self):
        """
            Return an iterable with all capabilities instances, i.e.
            dictionaries property_name -> value.
            If the capabilities are the default ones, it must have
            '_default' as a property name.
            
            Subclasses must override this method.
        """
        for vg in self.storage.vgs:
            yield self._get_capabilities_for_device(vg)

    @cmpi_logging.trace_method
    def create_setting_for_capabilities(self, capabilities):
        """
            Create LMI_*Setting for given capabilities.
            Return CIMInstanceName of the setting or raise CIMError on error. 
       """
        setting_id = self.setting_manager.allocate_id(
                'LMI_LVStorageSetting')
        if not setting_id:
            raise pywbem.CIMError(pywbem.CIM_ERR_FAILED,
                    "Failed to allocate setting InstanceID")

        setting = StorageSetting(StorageSetting.TYPE_TRANSIENT, setting_id)
        setting['DataRedundancyGoal'] = capabilities['DataRedundancyDefault']
        setting['DataRedundancyMax'] = capabilities['DataRedundancyDefault']
        setting['DataRedundancyMin'] = capabilities['DataRedundancyDefault']
        setting['ExtentStripeLength'] = \
                capabilities['ExtentStripeLengthDefault']
        setting['ExtentStripeLengthMax'] = \
                capabilities['ExtentStripeLengthDefault']
        setting['ExtentStripeLengthMin'] = \
                capabilities['ExtentStripeLengthDefault']
        setting['NoSinglePointOfFailure'] = \
                capabilities['NoSinglePointOfFailure']
        setting['PackageRedundancyGoal'] = \
                capabilities['PackageRedundancyDefault']
        setting['PackageRedundancyMax'] = \
                capabilities['PackageRedundancyDefault']
        setting['PackageRedundancyMin'] = \
                capabilities['PackageRedundancyDefault']
        setting['ElementName'] = 'CreatedFrom' + capabilities['InstanceID']
        if capabilities['ParityLayoutDefault']:
            setting['ParityLayout'] = capabilities['ParityLayoutDefault'] - 1
        else:
            setting['ParityLayout'] = None

        self.setting_manager.set_setting('LMI_LVStorageSetting', setting)
        return pywbem.CIMInstanceName(
                classname='LMI_LVStorageSetting',
                namespace=self.config.namespace,
                keybindings={'InstanceID': setting_id})

    @cmpi_logging.trace_method
    def get_capabilities_for_id(self, instance_id):
        """
            Return dictionary property_name -> value.
            If the capabilities are the default ones, it must have
            '_default' as a property name.
            Return None if there is no such Capabilities instance.
            
            Subclasses can override this method.
        """
        path = self.parse_instance_id(instance_id)
        if not path:
            return None
        device = storage.get_device_for_persistent_name(self.storage, path)
        if not device:
            return None
        if not isinstance(device,
                blivet.devices.LVMVolumeGroupDevice):
            cmpi_logging.logger.trace_warn(
                    "InstanceID %s is not LVMVolumeGroupDevice" % instance_id)
            return None

        return self._get_capabilities_for_device(device)

    @cmpi_logging.trace_method
    # pylint: disable-msg=W0221
    def cim_method_createsetting(self, env, object_name,
            param_settingtype=None):
        """
            Implements LMI_LVStorageCapabilities.CreateSetting()

            Create LMI_LVStorageSetting applicable to this VG
            All properties its will have default values.
            
        """
        # just check param_settingtype
        if param_settingtype:
            setting_type = self.Values.CreateSetting.SettingType
            if (param_settingtype != setting_type.Default
                    and param_settingtype != setting_type.Goal):
                raise pywbem.CIMError(pywbem.CIM_ERR_FAILED,
                    "Wrong value of SettingType parameter.")

        (retval, outvars) = super(LMI_LVStorageCapabilities, self)\
                .cim_method_createsetting(env, object_name)

        # rename output param from 'setting' to 'newsetting'
        if outvars and outvars[0].name == "setting":
            outvars = [pywbem.CIMParameter('newsetting', type='reference',
                    value=outvars[0].value)]
        return (retval, outvars)


    @cmpi_logging.trace_method
    def cim_method_createlvstoragesetting(self, env, object_name):
        """
           Implements LMI_LVStorageCapabilities.CreateLVStorageSetting()

            This method creates new instance of LMI_LVStorageSetting.
            Applications then do not need to calculate DataRedundancy,
            PackageRedundancy and ExtentStripeLength. Because only basic
            Logical Volumes without any additional stripping or mirroring are
            supported, this method basically clones LMI_VGStorageSetting to
            LMI_LVStorageSetting.
        """
        return super(LMI_LVStorageCapabilities, self).cim_method_createsetting(
                env, object_name)


    class Values(CapabilitiesProvider.Values):
        class CreateSetting(object):
            Success = pywbem.Uint32(0)
            Not_Supported = pywbem.Uint32(1)
            Unspecified_Error = pywbem.Uint32(2)
            Timeout = pywbem.Uint32(3)
            Failed = pywbem.Uint32(4)
            Invalid_Parameter = pywbem.Uint32(5)
            # DMTF_Reserved = ..
            # Vendor_Specific = 32768..65535
            class SettingType(object):
                Default = pywbem.Uint16(2)
                Goal = pywbem.Uint16(3)

class LMI_LVElementCapabilities(BaseProvider):
    """
        Base class for LMI_*ElementCapabilities providers.
        
        If all capabilities instances are associated only with appropriate
        LMI_*Service, this class does not need to be subclasses.
        
        Otherwise, subclasses can associate capabilities to other managed
        elements.
    """
    @cmpi_logging.trace_method
    def __init__(self, classname, capabilities_provider, device_provider,
            *args, **kwargs):
        self.classname = classname
        self.capabilities_provider = capabilities_provider
        self.device_provider = device_provider
        super(LMI_LVElementCapabilities, self).__init__(*args, **kwargs)

    @cmpi_logging.trace_method
    def enumerate_capabilities(self):
        """
            Return iterable with (managed_element_name, capabilities_name),
            where managed_element_name and capabilities_name
            are CIMInstanceName.
            
            By default, all capabilities provided by capabilities_provider
            are associated to service_provider.
            
            Subclasses can override this method if different behavior is
            requested.
        """
        for capabilities in self.capabilities_provider.enumerate_capabilities():

            provider = self.capabilities_provider
            managed_element_name = provider.get_pool_name_for_capabilities(
                    capabilities['InstanceID'])

            capabilities_name = pywbem.CIMInstanceName(
                    classname=self.capabilities_provider.classname,
                    namespace=self.config.namespace,
                    keybindings={'InstanceID' : capabilities['InstanceID']})
            yield (managed_element_name, capabilities_name)

    @cmpi_logging.trace_method
    def enum_instances(self, env, model, keys_only):
        """
            Provider implementation of EnumerateInstances intrinsic method.
        """
        model.path.update({'Capabilities': None, 'ManagedElement': None})
        for (managed_element, capabilities) in self.enumerate_capabilities():
            model['Capabilities'] = capabilities
            model['ManagedElement'] = managed_element
            if keys_only:
                yield model
            else:
                yield self.get_instance(env, model, capabilities)

    @cmpi_logging.trace_method
    # pylint: disable-msg=W0221
    def get_instance(self, env, model, capabilities_name=None):
        """
            Provider implementation of GetInstance intrinsic method.
        """
        # find the capabilities instance
        instance_id = None
        if not capabilities_name:
            capabilities = self.capabilities_provider.get_capabilities_for_id(
                    model['Capabilities']['InstanceID'])
            if not capabilities:
                raise pywbem.CIMError(pywbem.CIM_ERR_NOT_FOUND,
                        "Capabilities not found.")
            instance_id = capabilities['InstanceID']
        else:
            instance_id = capabilities_name['InstanceID']

        name = self.capabilities_provider.get_pool_name_for_capabilities(
                instance_id)
        if not name:
            raise pywbem.CIMError(pywbem.CIM_ERR_NOT_FOUND,
                    "Cannot find StoragePool for Capabilities.")

        if name['InstanceID'] != model['ManagedElement']['InstanceID']:
            raise pywbem.CIMError(pywbem.CIM_ERR_NOT_FOUND,
                    "ManagedElement is not associated to Capabilities.")

        return model

    @cmpi_logging.trace_method
    def references(self, env, object_name, model, result_class_name, role,
                   result_role, keys_only):
        """Instrument Associations. """
        return self.simple_references(env, object_name, model,
                result_class_name, role, result_role, keys_only,
                "CIM_Capabilities",
                "CIM_ManagedElement")


    class Values(object):
        class Characteristics(object):
            Default = pywbem.Uint16(2)
            Current = pywbem.Uint16(3)
            # DMTF_Reserved = ..
            # Vendor_Specific = 32768..65535
