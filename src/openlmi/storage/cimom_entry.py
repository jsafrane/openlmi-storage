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
"""
    This module is the main entry from openlmi.storage.CIMOM.
    
    All initialization must be done here.
    
    This module instantiates all providers and registers them in CIMOM.
"""

from openlmi.storage.StorageConfiguration import StorageConfiguration
from openlmi.storage.ProviderManager import ProviderManager
from openlmi.storage.SettingManager import SettingManager

from openlmi.storage.LMI_StorageExtent import LMI_StorageExtent
from openlmi.storage.LMI_MDRAIDStorageExtent import LMI_MDRAIDStorageExtent
from openlmi.storage.LMI_DiskPartition import LMI_DiskPartition
from openlmi.storage.LMI_GenericDiskPartition import LMI_GenericDiskPartition
from openlmi.storage.LMI_LVStorageExtent import LMI_LVStorageExtent
from openlmi.storage.LMI_VGStoragePool import LMI_VGStoragePool
from openlmi.storage.LMI_PartitionBasedOn import LMI_PartitionBasedOn
from openlmi.storage.LMI_MDRAIDBasedOn import LMI_MDRAIDBasedOn
from openlmi.storage.LMI_LVBasedOn import LMI_LVBasedOn
from openlmi.storage.LMI_LVAllocatedFromStoragePool \
        import LMI_LVAllocatedFromStoragePool
from openlmi.storage.LMI_VGAssociatedComponentExtent \
        import LMI_VGAssociatedComponentExtent
from openlmi.storage.LMI_DiskPartitionConfigurationSetting \
        import LMI_DiskPartitionConfigurationSetting
from openlmi.storage.SettingProvider \
        import ElementSettingDataProvider, SettingHelperProvider
from openlmi.storage.LMI_DiskPartitioningConfigurationService \
        import LMI_DiskPartitionConfigurationService
from openlmi.storage.LMI_HostedStorageService \
        import LMI_HostedStorageService
from openlmi.storage.LMI_DiskPartitionConfigurationCapabilities \
        import LMI_DiskPartitionConfigurationCapabilities
from openlmi.storage.CapabilitiesProvider import ElementCapabilitiesProvider
from openlmi.storage.LMI_InstalledPartitionTable \
        import LMI_InstalledPartitionTable
from openlmi.storage.LMI_LVStorageCapabilities \
        import LMI_LVStorageCapabilities, LMI_LVElementCapabilities
from openlmi.storage.LMI_StorageConfigurationService \
        import LMI_StorageConfigurationService
from openlmi.storage.LMI_VGStorageCapabilities import LMI_VGStorageCapabilities
from openlmi.storage.LMI_MDRAIDStorageCapabilities \
        import LMI_MDRAIDStorageCapabilities
from openlmi.storage.LMI_SystemStorageDevice import LMI_SystemStorageDevice
from openlmi.storage.LMI_MDRAIDFormatProvider import LMI_MDRAIDFormatProvider
from openlmi.storage.LMI_PVFormatProvider import LMI_PVFormatProvider
from openlmi.storage.LMI_DataFormatProvider import LMI_DataFormatProvider
from openlmi.storage.FormatProvider import LMI_ResidesOnExtent
from openlmi.storage.LMI_LocalFileSystem import LMI_LocalFileSystem
from openlmi.storage.LMI_FileSystemConfigurationService \
        import LMI_FileSystemConfigurationService
from openlmi.storage.LMI_FileSystemConfigurationCapabilities \
        import LMI_FileSystemConfigurationCapabilities
from openlmi.storage.JobManager import JobManager
from openlmi.storage.IndicationManager import IndicationManager
from openlmi.storage.LMI_HostedFileSystem import LMI_HostedFileSystem

import openlmi.common.cmpi_logging as cmpi_logging
import blivet
import logging

indication_manager = None

def init_anaconda(log_manager, config):
    """ Initialize Anaconda storage module."""
    cmpi_logging.logger.info("Initializing Anaconda")

    # set up logging
    blivet_logger = logging.getLogger("blivet")
    blivet_logger.addHandler(log_manager.cmpi_handler)
    program_logger = logging.getLogger("program")
    program_logger.addHandler(log_manager.cmpi_handler)
    config.add_listener(change_anaconda_loglevel)
    blivet_logger.info("Hello")
    change_anaconda_loglevel(config)

    # set up storage class instance
    storage = blivet.Blivet()
    # identify the system's storage devices
    storage.reset()
    return storage

def change_anaconda_loglevel(config):
    """
    Callback called when configuration changes.
    Apply any new blivet loglevel.
    """
    blivet_logger = logging.getLogger("blivet")
    program_logger = logging.getLogger("program")
    if config.blivet_tracing:
        blivet_logger.setLevel(logging.DEBUG)
        program_logger.setLevel(logging.DEBUG)
    else:
        blivet_logger.setLevel(logging.WARN)
        program_logger.setLevel(logging.WARN)
    if config.stderr:
        # start sending to stderr
        if not change_anaconda_loglevel.stderr_handler:
            # create stderr handler
            formatter = logging.Formatter(cmpi_logging.LogManager.FORMAT_STDERR)
            stderr_handler = logging.StreamHandler()
            stderr_handler.setLevel(logging.DEBUG)
            stderr_handler.setFormatter(formatter)
            blivet_logger.addHandler(stderr_handler)
            program_logger.addHandler(stderr_handler)
            change_anaconda_loglevel.stderr_handler = stderr_handler
            blivet_logger.info("Started logging to stderr.")
    else:
        # stop sending to stderr
        if change_anaconda_loglevel.stderr_handler:
            blivet_logger.info("Stopped logging to stderr.")
            blivet_logger.removeHandler(change_anaconda_loglevel.stderr_handler)
            program_logger.removeHandler(
                    change_anaconda_loglevel.stderr_handler)
        change_anaconda_loglevel.stderr_handler = None
change_anaconda_loglevel.stderr_handler = None

def get_providers(env):
    """
        CIMOM callback. Initialize OpenLMI and return dictionary of all
        providers we implement.
    """
    # allow **magic here
    # pylint: disable-msg=W0142
    log_manager = cmpi_logging.LogManager(env)

    config = StorageConfiguration()
    config.load()
    log_manager.set_config(config)

    cmpi_logging.logger.info("Provider init.")

    global indication_manager
    indication_manager = IndicationManager(env, "Storage", config.namespace)

    manager = ProviderManager()
    setting_manager = SettingManager(config)
    setting_manager.load()
    storage = init_anaconda(log_manager, config)

    providers = {}

    job_manager = JobManager('Storage', config.namespace, indication_manager)

    # common construction options
    opts = {'storage': storage,
            'config': config,
            'provider_manager': manager,
            'setting_manager': setting_manager,
            'job_manager' : job_manager}

    # StorageDevice providers
    provider = LMI_StorageExtent(**opts)
    manager.add_device_provider(provider)
    providers['LMI_StorageExtent'] = provider

    provider = LMI_MDRAIDStorageExtent(**opts)
    manager.add_device_provider(provider)
    providers['LMI_MDRAIDStorageExtent'] = provider
    setting_provider = SettingHelperProvider(
            setting_helper=provider,
            setting_classname="LMI_MDRAIDStorageSetting",
            **opts)
    manager.add_setting_provider(setting_provider)
    providers['LMI_MDRAIDStorageSetting'] = setting_provider
    assoc_provider = ElementSettingDataProvider(
            setting_provider=setting_provider,
            managed_element_classname="LMI_MDRAIDStorageExtent",
            setting_data_classname="LMI_MDRAIDStorageSetting",
            **opts)
    providers['LMI_MDRAIDElementSettingData'] = assoc_provider

    provider = LMI_DiskPartition(**opts)
    manager.add_device_provider(provider)
    providers['LMI_DiskPartition'] = provider

    provider = LMI_GenericDiskPartition(**opts)
    manager.add_device_provider(provider)
    providers['LMI_GenericDiskPartition'] = provider

    provider = LMI_LVStorageExtent(**opts)
    manager.add_device_provider(provider)
    providers['LMI_LVStorageExtent'] = provider
    setting_provider = SettingHelperProvider(
            setting_helper=provider,
            setting_classname="LMI_LVStorageSetting",
            **opts)
    manager.add_setting_provider(setting_provider)
    providers['LMI_LVStorageSetting'] = setting_provider
    assoc_provider = ElementSettingDataProvider(
            setting_provider=setting_provider,
            managed_element_classname="LMI_LVStorageExtent",
            setting_data_classname="LMI_LVStorageSetting",
            **opts)
    providers['LMI_LVElementSettingData'] = assoc_provider

    provider = LMI_VGStoragePool(**opts)
    manager.add_device_provider(provider)
    providers['LMI_VGStoragePool'] = provider
    setting_provider = SettingHelperProvider(
            setting_helper=provider,
            setting_classname="LMI_VGStorageSetting",
            **opts)
    manager.add_setting_provider(setting_provider)
    providers['LMI_VGStorageSetting'] = setting_provider
    assoc_provider = ElementSettingDataProvider(
            setting_provider=setting_provider,
            managed_element_classname="LMI_VGStoragePool",
            setting_data_classname="LMI_VGStorageSetting",
            **opts)
    providers['LMI_VGElementSettingData'] = assoc_provider
    cap_provider = LMI_LVStorageCapabilities(**opts)
    manager.add_capabilities_provider(cap_provider)
    providers['LMI_LVStorageCapabilities'] = cap_provider
    assoc_provider = LMI_LVElementCapabilities(
            "LMI_LVElementCapabilities",
            cap_provider, provider, **opts)
    providers['LMI_LVElementCapabilities'] = assoc_provider

    # settings
    setting_provider = LMI_DiskPartitionConfigurationSetting(
            ** opts)
    manager.add_setting_provider(setting_provider)
    providers['LMI_DiskPartitionConfigurationSetting'] = setting_provider
    assoc_provider = ElementSettingDataProvider(
            setting_provider=setting_provider,
            managed_element_classname="CIM_DiskPartition",
            setting_data_classname="LMI_DiskPartitionConfigurationSetting",
            **opts)
    providers['LMI_DiskPartitionElementSettingData'] = assoc_provider


    # services & capabilities
    service_provider = LMI_StorageConfigurationService(**opts)
    manager.add_service_provider(service_provider)
    providers['LMI_StorageConfigurationService'] = service_provider
    cap_provider = LMI_VGStorageCapabilities(**opts)
    manager.add_capabilities_provider(cap_provider)
    providers['LMI_VGStorageCapabilities'] = cap_provider
    assoc_provider = ElementCapabilitiesProvider(
            "LMI_VGElementCapabilities",
            cap_provider, service_provider, **opts)
    providers['LMI_VGElementCapabilities'] = assoc_provider

    cap_provider = LMI_MDRAIDStorageCapabilities(**opts)
    manager.add_capabilities_provider(cap_provider)
    providers['LMI_MDRAIDStorageCapabilities'] = cap_provider
    assoc_provider = ElementCapabilitiesProvider(
            "LMI_MDRAIDElementCapabilities",
            cap_provider, service_provider, **opts)
    providers['LMI_MDRAIDElementCapabilities'] = assoc_provider


    service_provider = LMI_DiskPartitionConfigurationService(
            ** opts)

    manager.add_service_provider(service_provider)
    providers['LMI_DiskPartitionConfigurationService'] = service_provider

    cap_provider = LMI_DiskPartitionConfigurationCapabilities(
            ** opts)
    manager.add_capabilities_provider(cap_provider)
    providers['LMI_DiskPartitionConfigurationCapabilities'] = cap_provider
    assoc_provider = ElementCapabilitiesProvider(
            "LMI_DiskPartitionElementCapabilities",
            cap_provider, service_provider, **opts)
    providers['LMI_DiskPartitionElementCapabilities'] = assoc_provider


    # Associations
    provider = LMI_PartitionBasedOn(**opts)
    providers['LMI_PartitionBasedOn'] = provider

    provider = LMI_MDRAIDBasedOn(**opts)
    providers['LMI_MDRAIDBasedOn'] = provider

    provider = LMI_LVBasedOn(**opts)
    providers['LMI_LVBasedOn'] = provider

    provider = LMI_LVAllocatedFromStoragePool(**opts)
    providers['LMI_LVAllocatedFromStoragePool'] = provider

    provider = LMI_VGAssociatedComponentExtent(**opts)
    providers['LMI_VGAssociatedComponentExtent'] = provider

    provider = LMI_HostedStorageService(**opts)
    providers['LMI_HostedStorageService'] = provider

    provider = LMI_SystemStorageDevice(**opts)
    providers['LMI_SystemStorageDevice'] = provider

    provider = LMI_InstalledPartitionTable(**opts)
    providers['LMI_InstalledPartitionTable'] = provider

    fmt = LMI_DataFormatProvider(**opts)
    manager.add_format_provider(fmt)
    providers['LMI_DataFormat'] = fmt

    fmt = LMI_MDRAIDFormatProvider(**opts)
    manager.add_format_provider(fmt)
    providers['LMI_MDRAIDFormat'] = fmt

    fmt = LMI_PVFormatProvider(**opts)
    manager.add_format_provider(fmt)
    providers['LMI_PVFormat'] = fmt

    fmt = LMI_LocalFileSystem(**opts)
    manager.add_format_provider(fmt)
    providers['LMI_LocalFileSystem'] = fmt
    setting_provider = SettingHelperProvider(
            setting_helper=fmt,
            setting_classname="LMI_FileSystemSetting",
            **opts)
    manager.add_setting_provider(setting_provider)
    providers['LMI_FileSystemSetting'] = setting_provider
    assoc_provider = ElementSettingDataProvider(
            setting_provider=setting_provider,
            managed_element_classname="LMI_LocalFileSystem",
            setting_data_classname="LMI_FileSystemSetting",
            **opts)
    providers['LMI_FileSystemElementSettingData'] = assoc_provider

    service_provider = LMI_FileSystemConfigurationService(**opts)
    manager.add_service_provider(service_provider)
    providers['LMI_FileSystemConfigurationService'] = service_provider
    cap_provider = LMI_FileSystemConfigurationCapabilities(
            ** opts)
    manager.add_capabilities_provider(cap_provider)
    providers['LMI_FileSystemConfigurationCapabilities'] = cap_provider
    assoc_provider = ElementCapabilitiesProvider(
            "LMI_FileSystemConfigurationElementCapabilities",
            cap_provider, service_provider, **opts)
    providers['LMI_FileSystemConfigurationElementCapabilities'] = assoc_provider

    provider = LMI_ResidesOnExtent(**opts)
    providers['LMI_ResidesOnExtent'] = provider

    job_providers = job_manager.get_providers()
    providers.update(job_providers)

    provider = LMI_HostedFileSystem(**opts)
    providers['LMI_HostedFileSystem'] = provider

    print "providers:", providers
    return providers

def authorize_filter(env, fltr, ns, classes, owner):
    """ CIMOM callback."""
    indication_manager.authorize_filter(env, fltr, ns, classes, owner)

def activate_filter (env, fltr, ns, classes, first_activation):
    """ CIMOM callback."""
    indication_manager.activate_filter(env, fltr, ns, classes, first_activation)

def deactivate_filter(env, fltr, ns, classes, last_activation):
    """ CIMOM callback."""
    indication_manager.deactivate_filter(env, fltr, ns, classes,
            last_activation)

def enable_indications(env):
    """ CIMOM callback."""
    indication_manager.enable_indications(env)

def disable_indications(env):
    """ CIMOM callback."""
    indication_manager.disable_indications(env)

def can_unload(_env):
    """ CIMOM callback."""
    cmpi_logging.logger.trace_info("can_unload called")
    return True

def shutdown(_env):
    """ CIMOM callback."""
    cmpi_logging.logger.info("Provider shutdown.")
    return True
