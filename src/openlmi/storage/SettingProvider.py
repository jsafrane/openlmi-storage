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
""" Module for SettingProvider class."""

import pywbem
from openlmi.storage.BaseProvider import BaseProvider
from openlmi.storage.SettingManager import Setting
import openlmi.common.cmpi_logging as cmpi_logging

class SettingProvider(BaseProvider):
    """
        Base of all LMI_*Setting providers.
        Every setting class can have:
            - number of fixed preconfigured instances
            - number of configurable persistent instances
            - number of configurable in-memory (transient) instances
            - instances associated to managed elements
        This class provides all four instance types.
        
        The setting itself is represented by dictionary of key -> value.
        
        Preconfigured instances are stored in /etc/openlmi/storage/settings/<setting_classname>.ini
        Persistent instances are stored in /var/lib/openlmi-storage/settings/<setting_classname>.ini
    """
    @cmpi_logging.trace_method
    def __init__(self,
            setting_classname,
            supported_properties,
            validate_properties=None,
            ignore_defaults=None,
            *args, **kwargs):
        """
            setting_classname = name of CIM class, which we provide
            supported_properties = hash property_name -> constructor
                constructor is a function which takes string argument
                and returns CIM value. (i.e. pywbem.Uint16
                or bool or string etc).
            validate_properties = hash property_name -> validator
                validator is a function which takes pywbem (Uint32, bool ...)
                value as parameter and returns True, if the value is correct for
                the property. Not all properties do need to have a validator.
            ignore_defaults = hash property_name -> default value.
                If this value of the property is set, the ModifyInstance
                won't complain, but it will silently ignore the value.
                This is useful when someone tries to set default value
                of a property and the provider does not implement it. 
        """
        self.setting_classname = setting_classname
        supported_properties['Caption'] = str
        supported_properties['ConfigurationName'] = str
        supported_properties['Description'] = str
        supported_properties['ChangeableType'] = pywbem.Uint16
        supported_properties['ElementName'] = str

        self.supported_properties = supported_properties
        self.validate_properties = validate_properties
        self.ignore_defaults = ignore_defaults

        super(SettingProvider, self).__init__(*args, **kwargs)

    @cmpi_logging.trace_method
    def enumerate_configurations(self):
        """
            Enumerate all instances of LMI_*Setting, which are attached 
            to managed elements, i.e. are not transient, persistent nor
            preconfigured.
            
            This method returns iterabe with Setting instances.
            
            Subclasses should override this method.
        """
        return []

    @cmpi_logging.trace_method
    def parse_setting_id(self, instance_id):
        """
            InstanceID should have format LMI:<classname>:<myid>.
            This method checks, that the format is OK and returns the myid.
            It returns None if the format is not OK.
            This method can be used in get_configuration_for_id.
        """
        # some devices (raid) have ':' in their /dev/disk/by-id, do not
        # include it in the split
        parts = instance_id.split(":", 2)
        if len(parts) != 3:
            return None
        if parts[0] != "LMI":
            return None
        if parts[1] != self.setting_classname:
            return None
        return parts[2]

    @cmpi_logging.trace_method
    def create_setting_id(self, myid):
        """
            InstanceID should have format LMI:<classname>:<ID>.
            This method returns string LMI:<classname>:<myid>
        """
        return "LMI:" + self.setting_classname + ":" + myid

    @cmpi_logging.trace_method
    # pylint: disable-msg=W0613
    def get_configuration_for_id(self, instance_id):
        """
            Return Setting instance for given instance_id.
            Return None if no such Setting is found. 
            
            Subclasses should override this method.
        """
        return None

    @cmpi_logging.trace_method
    # pylint: disable-msg=W0613
    def get_associated_element_name(self, instance_id):
        """
            Return CIMInstanceName for ElementSettingData association.
            Return None if no such element exist. 
            Subclasses should override this method.
        """
        return None

    @cmpi_logging.trace_method
    def enum_instances(self, env, model, keys_only):
        """
            Provider implementation of EnumerateInstances intrinsic method.
            Subclasses should not override this method, they should override
            enumerate_configurations only.
        """
        model.path.update({'InstanceID': None})

        # handle transient, persistent and preconfigured settings
        settings = self.setting_manager.get_settings(self.setting_classname)
        for setting in settings.values():
            model['InstanceID'] = setting.the_id
            if keys_only:
                yield model
            else:
                yield self.get_instance(env, model, setting)

        # handle configurations
        for setting in self.enumerate_configurations():
            model['InstanceID'] = setting.the_id
            if keys_only:
                yield model
            else:
                yield self.get_instance(env, model, setting)

    @cmpi_logging.trace_method
    def find_instance(self, instance_id):
        """
            Find an Setting instance with given InstanceID and return it.
            Return None if there is no such instance.
        """
        # find the setting in setting_manager
        settings = self.setting_manager.get_settings(self.setting_classname)
        if settings.has_key(instance_id):
            return settings[instance_id]

        # find the setting in configurations
        return self.get_configuration_for_id(instance_id)

    # pylint: disable-msg=W0221
    @cmpi_logging.trace_method
    def get_instance(self, env, model, setting=None):
        """
            Provider implementation of GetInstance intrinsic method.
        """
        if not setting:
            setting = self.find_instance(model['InstanceID'])

        if not setting:
            raise pywbem.CIMError(pywbem.CIM_ERR_NOT_FOUND,
                    "Cannot find setting.")

        # convert setting to model using supported_properties
        for (name, value) in setting.items():
            if value is not None:
                if self.supported_properties.has_key(name):
                    model[name] = self.supported_properties[name](value)

        types = self.Values.ChangeableType
        if setting.type == Setting.TYPE_CONFIGURATION:
            model['ChangeableType'] = types.Not_Changeable_Transient
        elif setting.type == Setting.TYPE_PERSISTENT:
            model['ChangeableType'] = types.Changeable_Persistent
        elif setting.type == Setting.TYPE_PRECONFIGURED:
            model['ChangeableType'] = types.Not_Changeable_Persistent
        elif setting.type == Setting.TYPE_TRANSIENT:
            model['ChangeableType'] = types.Changeable_Transient

        return model

    @staticmethod
    @cmpi_logging.trace_function
    def string_to_bool(value):
        """
            Convert a string to boolean value.
            '1', 'true' and 'True' are True, the rest is False.
        """
        if value == 1 or value == "true" or value == "True":
            return True
        elif value == 0 or value == "false" or value == "False":
            return False
        return bool(value)

    @staticmethod
    @cmpi_logging.trace_function
    def string_to_uint16_array(value):
        """
            Convert a string to array of integers.
            The string must be enclosed in [].
        """
        if not (value[0] == "[" and value[-1] == "]"):
            return None
        value = value[1:-1]
        values = value.split(",")
        return [pywbem.Uint16(i) for i in values]

    @staticmethod
    @cmpi_logging.trace_function
    def string_to_uint64_array(value):
        """
            Convert a string to array of integers.
            The string must be enclosed in [].
        """
        if not (value[0] == "[" and value[-1] == "]"):
            return None
        value = value[1:-1]
        values = value.split(",")
        return [pywbem.Uint64(i) for i in values]

    @cmpi_logging.trace_function
    def _check_changeable_type_modify(self, instance, setting):
        """
            Return True, if ModifInstance(instance) can modify ChangeableType
            property Setting instance.
            Return False, if the property should be skipped.
            Raise exception on error.
        """
        types = self.Values.ChangeableType
        if setting.type == Setting.TYPE_TRANSIENT:
            if instance['ChangeableType'] == types.Changeable_Persistent:
                # Can change only transient -> persistent
                # -> modify it now
                setting.type = Setting.TYPE_PERSISTENT
                return False
            if instance['ChangeableType'] == types.Changeable_Transient:
                # Ignore transient -> transient
                return False
        elif (setting.type == Setting.TYPE_PERSISTENT
                    and instance['ChangeableType']
                        == types.Changeable_Persistent):
            # Ignore persistent -> persistent
            return False
        raise pywbem.CIMError(pywbem.CIM_ERR_FAILED,
                "Cannot modify ChangeableType property to new value.")

    @cmpi_logging.trace_function
    def _check_property_modify(self, instance, setting, property_name):
        """
            Return True, if ModifInstance(instance) can modify property of
            this name in given Setting instance.
            Return False, if the property should be skipped.
            Raise exception on error.
        """
        if property_name == 'InstanceID':
            # Ignore InstanceID property
            return False

        if self.ignore_defaults and self.ignore_defaults.has_key(property_name):
            # Ignore properties in self. ignore_defaults
            if self.ignore_defaults[property_name] != instance[property_name]:
                # But only if they have the default value
                raise pywbem.CIMError(pywbem.CIM_ERR_FAILED,
                        "Property is not supported: " + property_name)
            return False

        if not self.supported_properties.has_key(property_name):
            # We do not support the property
            if instance[property_name]:
                raise pywbem.CIMError(pywbem.CIM_ERR_FAILED,
                        "Property is not supported: " + property_name)
            return False

        if property_name == 'ChangeableType':
            # ChangeableType has special treatment, only some changes are
            # allowed
            return self._check_changeable_type_modify(instance, setting)

        # Finally, allow the property to be set to new value.
        return True

    @cmpi_logging.trace_function
    def _do_modify_instance(self, instance, setting):
        """
            Modify instance of Setting with given CIMInstance.
        """
        for name in instance.iterkeys():
            if not self._check_property_modify(instance, setting, name):
                continue

            if instance[name] is not None:
                if (self.validate_properties
                        and self.validate_properties.has_key(name)):
                    # check validity of the property
                    validator = self.validate_properties[name]
                    if not validator(instance[name]):
                        raise pywbem.CIMError(pywbem.CIM_ERR_FAILED,
                                "The value of property %s is invalid." % (name))
                setting[name] = str(instance[name])
            else:
                setting[name] = None
        return setting

    @cmpi_logging.trace_function
    def set_instance(self, env, instance, modify_existing):
        """Return a newly created or modified instance.

        Keyword arguments:
        env -- Provider Environment (pycimmb.ProviderEnvironment)
        instance -- The new pywbem.CIMInstance.  If modifying an existing 
            instance, the properties on this instance have been filtered by 
            the PropertyList from the request.
        modify_existing -- True if ModifyInstance, False if CreateInstance

        Return the new instance.  The keys must be set on the new instance. 

        Possible Errors:
        CIM_ERR_ACCESS_DENIED
        CIM_ERR_NOT_SUPPORTED
        CIM_ERR_INVALID_PARAMETER (including missing, duplicate, unrecognized 
            or otherwise incorrect parameters)
        CIM_ERR_ALREADY_EXISTS (the CIM Instance already exists -- only 
            valid if modify_existing is False, indicating that the operation
            was CreateInstance)
        CIM_ERR_NOT_FOUND (the CIM Instance does not exist -- only valid 
            if modify_existing is True, indicating that the operation
            was ModifyInstance)
        CIM_ERR_FAILED (some other unspecified error occurred)

        """
        setting = self.find_instance(instance['InstanceID'])
        if not setting:
            raise pywbem.CIMError(pywbem.CIM_ERR_NOT_FOUND,
                    "Cannot find setting.")

        if not modify_existing:
            raise pywbem.CIMError(pywbem.CIM_ERR_NOT_SUPPORTED,
                    "CreateInstance is not supported.")

        if (setting.type == Setting.TYPE_CONFIGURATION
                or setting.type == Setting.TYPE_PRECONFIGURED):
            raise pywbem.CIMError(pywbem.CIM_ERR_FAILED,
                        "Cannot modify not-changeable setting.")

        setting = self._do_modify_instance(instance, setting)

        self.setting_manager.set_setting(self.setting_classname, setting)
        return instance

    @cmpi_logging.trace_method
    def delete_instance(self, env, instance_name):
        """Delete an instance.

        Keyword arguments:
        env -- Provider Environment (pycimmb.ProviderEnvironment)
        instance_name -- A pywbem.CIMInstanceName specifying the instance 
            to delete.

        Possible Errors:
        CIM_ERR_ACCESS_DENIED
        CIM_ERR_NOT_SUPPORTED
        CIM_ERR_INVALID_NAMESPACE
        CIM_ERR_INVALID_PARAMETER (including missing, duplicate, unrecognized 
            or otherwise incorrect parameters)
        CIM_ERR_INVALID_CLASS (the CIM Class does not exist in the specified 
            namespace)
        CIM_ERR_NOT_FOUND (the CIM Class does exist, but the requested CIM 
            Instance does not exist in the specified namespace)
        CIM_ERR_FAILED (some other unspecified error occurred)

        """
        setting = self.find_instance(instance_name['InstanceID'])
        if not setting:
            raise pywbem.CIMError(pywbem.CIM_ERR_NOT_FOUND,
                    "Cannot find setting.")

        if (setting.type == Setting.TYPE_CONFIGURATION
                or setting.type == Setting.TYPE_PRECONFIGURED):
            raise pywbem.CIMError(pywbem.CIM_ERR_FAILED,
                        "Cannot delete not-changeable setting.")

        self.setting_manager.delete_setting(self.setting_classname, setting)

    @cmpi_logging.trace_method
    def cim_method_clonesetting(self, env, object_name):
        """Implements LMI_DiskPartitionConfigurationSetting.CloneSetting()

        Create a copy of this instance. The resulting instance will have
        the same class and the same properties as the original instance
        except ChangeableType, which will be set to "Changeable -
        Transient" in the clone, and InstanceID.
        
        Keyword arguments:
        env -- Provider Environment (pycimmb.ProviderEnvironment)
        object_name -- A pywbem.CIMInstanceName or pywbem.CIMCLassName 
            specifying the object on which the method CloneSetting() 
            should be invoked.

        Returns a two-tuple containing the return value (type pywbem.Uint32)
        and a list of CIMParameter objects representing the output parameters

        Output parameters:
        Clone -- (type REF (pywbem.CIMInstanceName(setting_classname='CIM_StorageSetting', ...)) 
            Created copy.
            

        Possible Errors:
        CIM_ERR_ACCESS_DENIED
        CIM_ERR_INVALID_PARAMETER (including missing, duplicate, 
            unrecognized or otherwise incorrect parameters)
        CIM_ERR_NOT_FOUND (the target CIM Class or instance does not 
            exist in the specified namespace)
        CIM_ERR_METHOD_NOT_AVAILABLE (the CIM Server is unable to honor 
            the invocation request)
        CIM_ERR_FAILED (some other unspecified error occurred)

        """
        setting = self.find_instance(object_name['InstanceID'])
        if not setting:
            raise pywbem.CIMError(pywbem.CIM_ERR_NOT_FOUND,
                    "Cannot find setting.")

        instance_id = self.setting_manager.allocate_id(self.setting_classname)
        print "instanceid = ", instance_id
        new_setting = Setting(Setting.TYPE_TRANSIENT, instance_id)
        for (key, value) in setting.items():
            new_setting[key] = value
        self.setting_manager.set_setting(self.setting_classname, new_setting)

        out_params = []
        out_params += [pywbem.CIMParameter('Clone', type='reference',
                           value=pywbem.CIMInstanceName(
                                   classname=self.setting_classname,
                                   namespace=self.config.namespace,
                                   keybindings={'InstanceID' : instance_id}))]
        return (self.Values.CloneSetting.Success, out_params)


    class Values(object):
        class ChangeableType(object):
            Not_Changeable_Persistent = pywbem.Uint16(0)
            Changeable_Transient = pywbem.Uint16(1)
            Changeable_Persistent = pywbem.Uint16(2)
            Not_Changeable_Transient = pywbem.Uint16(3)

        class CloneSetting(object):
            Success = pywbem.Uint32(0)
            Not_Supported = pywbem.Uint32(1)
            Failed = pywbem.Uint32(4)


class ElementSettingDataProvider(BaseProvider):
    """
        Implementation of CIM_ElementSettingData.
        It uses functionality provided by SettingProvider.
    """
    @cmpi_logging.trace_method
    def __init__(self, setting_provider,
            managed_element_classname,
            setting_data_classname,
            *args, **kwargs):
        self.setting_provider = setting_provider
        self.managed_element_classname = managed_element_classname
        self.setting_data_classname = setting_data_classname
        super(ElementSettingDataProvider, self).__init__(*args, **kwargs)


    @cmpi_logging.trace_method
    def get_instance(self, env, model):
        """
            Provider implementation of GetInstance intrinsic method.
        """
        instance_id = model['SettingData']['InstanceID']
        element_name = self.setting_provider.get_associated_element_name(
                 instance_id)

        if not element_name:
            raise pywbem.CIMError(pywbem.CIM_ERR_NOT_FOUND,
                    "Cannot find the ManagedElement")

        if element_name != model['ManagedElement']:
            raise pywbem.CIMError(pywbem.CIM_ERR_NOT_FOUND,
                    "The ManagedElement is not associated to given SettingData")

        model['IsCurrent'] = pywbem.Uint16(1)  # current
        return model

    @cmpi_logging.trace_method
    def enum_instances(self, env, model, keys_only):
        """
            Provider implementation of EnumerateInstances intrinsic method.
        """
        model.path.update({'ManagedElement': None, 'SettingData': None})
        for setting in self.setting_provider.enumerate_configurations():
            instance_id = setting.the_id
            provider = self.setting_provider
            model['ManagedElement'] = provider.get_associated_element_name(
                    instance_id)
            model['SettingData'] = pywbem.CIMInstanceName(
                    classname=self.setting_data_classname,
                    namespace=self.config.namespace,
                    keybindings={'InstanceID' : instance_id})
            if keys_only:
                yield model
            else:
                yield self.get_instance(env, model)

    @cmpi_logging.trace_method
    def references(self, env, object_name, model, result_class_name, role,
                               result_role, keys_only):
        # If you want to get references for free, implemented in terms
        # of enum_instances, just leave the code below unaltered.
        return self.simple_references(env, object_name, model,
                result_class_name, role, result_role, keys_only,
                self.managed_element_classname,
                self.setting_data_classname)


class SettingHelperProvider(SettingProvider):
    """
        Provider of LMI_*Setting class for managed element classes which
        implement SettingHelper.
    """

    @cmpi_logging.trace_method
    def __init__(self, setting_helper, *args, **kwargs):
        self.setting_helper = setting_helper
        properties = setting_helper.get_supported_setting_properties(self)
        validators = setting_helper.get_setting_validators(self)
        ignore = setting_helper.get_setting_ignore(self)
        super(SettingHelperProvider, self).__init__(
                supported_properties=properties,
                validate_properties=validators,
                ignore_defaults=ignore,
                *args, **kwargs)

    @cmpi_logging.trace_method
    def enumerate_configurations(self):
        """
            Enumerate all instances of LMI_*Setting, which are attached 
            to managed elements, i.e. are not transient, persistent nor
            preconfigured.
            It returns setting_helper.enumerate_settings.
        """
        return self.setting_helper.enumerate_settings(self)

    @cmpi_logging.trace_method
    def get_configuration_for_id(self, instance_id):
        """
            Return Setting instance for given instance_id.
            Return None if no such Setting is found.
        """
        return self.setting_helper.get_setting_for_id(self, instance_id)

    @cmpi_logging.trace_method
    def get_associated_element_name(self, instance_id):
        """
            Return CIMInstanceName for ElementSettingData association.
            Return None if no such element exist.
        """
        return self.setting_helper.get_associated_element_name(
                self, instance_id)
