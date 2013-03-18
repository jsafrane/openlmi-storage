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
""" Module for ProviderManager class."""

import openlmi.common.cmpi_logging as cmpi_logging

class ProviderManager(object):
    """
        Simple class containing references to various providers to simplify
        various tasks.
        
        The manager holds reference to all device providers of Anaconda
        StorageDevice subclasses and all LMI_*Setting providers.        
        The manager can then find a CIM provider for a
        StorageDevice instance and find provider or StorageDevice instance
        for CIM InstanceName.
        The major benefit of this manager is to convert Anaconda StorageDevice
        instance to CIM InstanceName and back. Therefore various associations
        can easily get their Antecendent/Dependent InstanceNames.

        The device providers must be registered by add_device_provider().
        The device providers must be subclasses of DeviceProvider class.
        
        The manager holds references to LMI_*Setting providers. For example
        LMI_*Service providers need access to settings, so they can use this
        manager to get them.
        The setting providers must be registered by add_setting_provider().
        The setting providers must be subclasses of SettingProvider class.
        
        The manager holds references to LMI_*Service providers, so
        the LMI_HostedService can easily enumerate all services.
        The service providers must be registered by add_service_provider().
        The service providers must be subclasses of ServiceProvider class.
    """

    @cmpi_logging.trace_method
    def __init__(self):
        self.device_providers = []
        self.setting_providers = []
        self.service_providers = []
        self.capabilities_providers = []
        self.format_providers = []

    @cmpi_logging.trace_method
    def add_device_provider(self, provider):
        """
            Add new device provider to the manager.
        """
        self.device_providers.append(provider)

    @cmpi_logging.trace_method
    def add_setting_provider(self, provider):
        """
            Add new setting provider to the manager.
        """
        self.setting_providers.append(provider)

    @cmpi_logging.trace_method
    def add_service_provider(self, provider):
        """
            Add new service provider to the manager.
        """
        self.service_providers.append(provider)

    @cmpi_logging.trace_method
    def add_capabilities_provider(self, provider):
        """
            Add new service provider to the manager.
        """
        self.capabilities_providers.append(provider)

    @cmpi_logging.trace_method
    def add_format_provider(self, provider):
        """
            Add new service provider to the manager.
        """
        self.format_providers.append(provider)

    @cmpi_logging.trace_method
    def get_device_provider_for_name(self, object_name):
        """
            Return provider for given CIM InstanceName.
            Return None if no such provider is registered.
        """
        for provider in self.device_providers:
            if provider.provides_name(object_name):
                return provider
        return None

    @cmpi_logging.trace_method
    def get_device_for_name(self, object_name):
        """
            Return Anaconda StorageDevice for given CIM InstanceName.
            Return None if no device exist.
        """
        provider = self.get_device_provider_for_name(object_name)
        if provider:
            return provider.get_device_for_name(object_name)
        return None

    @cmpi_logging.trace_method
    def get_provider_for_device(self, device):
        """
            Return provider for given Anaconda StorageDevice.
            Return None if no such provider is registered.
        """
        for provider in self.device_providers:
            if provider.provides_device(device):
                return provider
        return None

    @cmpi_logging.trace_method
    def get_name_for_device(self, device):
        """
            Return CIM InstanceName for given Anaconda StorageDevice.
            Return None if no device exist.
        """
        provider = self.get_provider_for_device(device)
        if provider:
            return provider.get_name_for_device(device)
        return None

    @cmpi_logging.trace_method
    def get_provider_for_format(self, device, fmt):
        """
            Return FormatProvider for given DeviceFormat subclass
        """
        for prov in self.format_providers:
            if prov.provides_format(device, fmt):
                return prov
        return None

    @cmpi_logging.trace_method
    def get_provider_for_format_name(self, object_name):
        """
            Return provider for given CIM InstanceName of LMI_FileSystemFormat
            subclass.
            Return None if no such provider is registered.
        """
        for provider in self.format_providers:
            if provider.classname == object_name.classname:
                return provider
        return None


    @cmpi_logging.trace_method
    def get_setting_for_id(self, instance_id, setting_classname=None):
        """
            Return Setting instance for given InstanceID.
            If setting_classname is not None, it also checks that the
            setting classname equals setting_classname.
            
            Return None if there is no such instance.
        """
        # parse the instance id
        parts = instance_id.split(":")
        if len(parts) != 3:
            return None
        if parts[0] != "LMI":
            return None
        classname = parts[1]
        if setting_classname and setting_classname != classname:
            return None
        for provider in self.setting_providers:
            if provider.setting_classname == classname:
                return provider.find_instance(instance_id)

    @cmpi_logging.trace_method
    def get_service_providers(self):
        """ Return list of registered service providers."""
        return self.service_providers

    @cmpi_logging.trace_method
    def get_capabilities_provider_for_class(self, classname):
        """ Return list of registered capabilities providers."""
        for provider in self.capabilities_providers:
            if provider.classname == classname:
                return provider
        return None
