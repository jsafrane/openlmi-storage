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
""" Module for LocalFileSystemProvider."""

import pywbem
from openlmi.storage.FormatProvider import FormatProvider
from openlmi.storage.SettingHelper import SettingHelper
from openlmi.storage.SettingManager import Setting
from openlmi.storage.SettingProvider import SettingProvider
import openlmi.common.cmpi_logging as cmpi_logging

class LocalFileSystemProvider(FormatProvider, SettingHelper):
    """
        Abstract provider for local filesystems.
        Each provider must have .device_type property, which represents
        blivet.formats.<DeviceFormat child>.type of format it
        represents.
    """


    @cmpi_logging.trace_method
    def __init__(self, *args, **kwargs):
        super(LocalFileSystemProvider, self).__init__(*args, **kwargs)

        vals = LocalFileSystemProvider.Values
        self.fs_settings = {
            'ext2' : {
                'ActualFileSystemType':
                    vals.ActualFileSystemType.EXT2,
                'DataExtentsSharing':
                    vals.DataExtentsSharing.No_Sharing,
                'FilenameCaseAttributes':
                    vals.FilenameCaseAttributes.Case_sensitive,
                'ObjectTypes': [
                        vals.ObjectTypes.inodes,
                        vals.ObjectTypes.files,
                        vals.ObjectTypes.files_directories,
                ],
                'NumberOfObjectsMin': [
                        pywbem.Uint64(0),
                        pywbem.Uint64(0),
                        pywbem.Uint64(0),
                ],
                'NumberOfObjectsMax': [
                        pywbem.Uint64(2 ** 32 - 1),  # nr. of inodes
                        pywbem.Uint64(10 ** 18),  # nr. of files
                        pywbem.Uint64(0),  # nr. of files in dir.
                ],
                'NumberOfObjects': [
                        pywbem.Uint64(0),
                        pywbem.Uint64(0),
                        pywbem.Uint64(0),
                ],
                'ObjectSize':  [
                        pywbem.Uint64(256),  # inode size
                        pywbem.Uint64(0),  # file size
                        pywbem.Uint64(0),  # file size in directory
                ],
                'ObjectSizeMin':  [
                        pywbem.Uint64(128),  # inode size
                        pywbem.Uint64(0),  # file size
                        pywbem.Uint64(0),  # file size in directory
                ],
                'ObjectSizeMax':  [
                        pywbem.Uint64(4096),  # inode size
                        pywbem.Uint64(0),  # file size
                        pywbem.Uint64(0),  # file size in directory
                ],
                'FilenameFormats': [
                    vals.FilenameFormats.Unix
                ],
                'FilenameLengthMax':  [
                        pywbem.Uint64(255),
                ],
                'PersistenceTypes': [
                        vals.PersistenceTypes.Persistent]
            },
            'ext3' : {
                'ActualFileSystemType':
                    vals.ActualFileSystemType.EXT3,
                'DataExtentsSharing':
                    vals.DataExtentsSharing.No_Sharing,
                'FilenameCaseAttributes':
                    vals.FilenameCaseAttributes.Case_sensitive,
                'ObjectTypes': [
                        vals.ObjectTypes.inodes,
                        vals.ObjectTypes.files,
                        vals.ObjectTypes.files_directories,
                ],
                'NumberOfObjectsMin': [
                        pywbem.Uint64(0),
                        pywbem.Uint64(0),
                        pywbem.Uint64(0),
                ],
                'NumberOfObjectsMax': [
                        pywbem.Uint64(2 ** 32 - 1),  # nr.of inodes
                        pywbem.Uint64(2 ** 32 - 1),  # nr. of files
                        pywbem.Uint64(0),
                ],
                'NumberOfObjects': [
                        pywbem.Uint64(0),  # nr.of inodes
                        pywbem.Uint64(0),  # nr. of files
                        pywbem.Uint64(0),
                ],
                'ObjectSize':  [
                        pywbem.Uint64(256),  # inode size
                        pywbem.Uint64(0),  # file size
                        pywbem.Uint64(0),
                ],
                'ObjectSizeMin':  [
                        pywbem.Uint64(128),  # inode size
                        pywbem.Uint64(0),  # file size
                        pywbem.Uint64(0),
                ],
                'ObjectSizeMax':  [
                        pywbem.Uint64(4096),  # inode size
                        pywbem.Uint64(0),  # file size
                        pywbem.Uint64(0),
                ],
                'FilenameFormats': [
                    vals.FilenameFormats.Unix
                ],
                'FilenameLengthMax':  [
                        pywbem.Uint64(255),
                ],
                'PersistenceTypes': [
                        vals.PersistenceTypes.Persistent]
            },
            'ext4' : {
                'ActualFileSystemType':
                    vals.ActualFileSystemType.EXT4,
                'DataExtentsSharing':
                    vals.DataExtentsSharing.No_Sharing,
                'FilenameCaseAttributes':
                    vals.FilenameCaseAttributes.Case_sensitive,
                'ObjectTypes': [
                        vals.ObjectTypes.inodes,
                        vals.ObjectTypes.files,
                        vals.ObjectTypes.files_directories,
                ],
                'NumberOfObjectsMin': [
                        pywbem.Uint64(0),
                        pywbem.Uint64(0),
                        pywbem.Uint64(0),
                ],
                'NumberOfObjectsMax': [
                        pywbem.Uint64(2 ** 32 - 1),  # nr.of inodes
                        pywbem.Uint64(2 ** 32 - 1),  # nr. of files
                        pywbem.Uint64(0),
                ],
                'NumberOfObjects': [
                        pywbem.Uint64(0),
                        pywbem.Uint64(0),
                        pywbem.Uint64(0),
                ],
                'ObjectSize':  [
                        pywbem.Uint64(256),  # inode size
                        pywbem.Uint64(0),  # file size
                        pywbem.Uint64(0),
                ],
                'ObjectSizeMin':  [
                        pywbem.Uint64(128),  # inode size
                        pywbem.Uint64(0),  # file size
                        pywbem.Uint64(0),
                ],
                'ObjectSizeMax':  [
                        pywbem.Uint64(4096),  # inode size
                        pywbem.Uint64(0),  # file size
                        pywbem.Uint64(0),
                ],
                'FilenameFormats': [
                    vals.FilenameFormats.Unix
                ],
                'FilenameLengthMax':  [
                        pywbem.Uint64(255),
                ],
                'PersistenceTypes': [
                        vals.PersistenceTypes.Persistent]
            },
            'btrfs' : {
                'ActualFileSystemType':
                    vals.ActualFileSystemType.BTRFS,
                'DataExtentsSharing':
                    vals.DataExtentsSharing.No_Sharing,
                'FilenameCaseAttributes':
                    vals.FilenameCaseAttributes.Case_sensitive,
                'ObjectTypes': [
                        vals.ObjectTypes.inodes,
                        vals.ObjectTypes.files,
                        vals.ObjectTypes.files_directories,
                ],
                'NumberOfObjectsMin': [
                        pywbem.Uint64(0),
                        pywbem.Uint64(0),
                        pywbem.Uint64(0),
                ],
                'NumberOfObjectsMax': [
                        pywbem.Uint64(2 ** 64 - 1),  # nr.of inodes
                        pywbem.Uint64(2 ** 64 - 1),  # nr. of files
                        pywbem.Uint64(0),
                ],
                'NumberOfObjects': [
                        pywbem.Uint64(0),
                        pywbem.Uint64(0),
                        pywbem.Uint64(0),
                ],
                'ObjectSize':  [
                        pywbem.Uint64(0),  # inode size
                        pywbem.Uint64(0),  # file size
                        pywbem.Uint64(0),
                ],
                'ObjectSizeMin':  [
                        pywbem.Uint64(128),  # inode size
                        pywbem.Uint64(0),  # file size
                        pywbem.Uint64(0),
                ],
                'ObjectSizeMax':  [
                        pywbem.Uint64(4096),  # inode size
                        pywbem.Uint64(8 * (2 ** 60)),  # file size 8 EiB
                        pywbem.Uint64(0),
                ],
                'FilenameFormats': [
                    vals.FilenameFormats.Unix
                ],
                'FilenameLengthMax':  [
                        pywbem.Uint64(255),
                ],
                'PersistenceTypes': [
                        vals.PersistenceTypes.Persistent]
            },
            'xfs' : {
                'ActualFileSystemType':
                    vals.ActualFileSystemType.XFS,
                'DataExtentsSharing':
                    vals.DataExtentsSharing.No_Sharing,
                'FilenameCaseAttributes':
                    vals.FilenameCaseAttributes.Case_sensitive,
                'ObjectTypes': [
                        vals.ObjectTypes.inodes,
                        vals.ObjectTypes.files,
                        vals.ObjectTypes.files_directories,
                ],
                'NumberOfObjectsMin': [
                        pywbem.Uint64(0),
                        pywbem.Uint64(0),
                        pywbem.Uint64(0),
                ],
                'NumberOfObjectsMax': [
                        pywbem.Uint64(2 ** 64 - 1),  # nr.of inodes
                        pywbem.Uint64(2 ** 64 - 1),  # nr of files
                        pywbem.Uint64(0),
                ],
                'NumberOfObjects': [
                        pywbem.Uint64(0),
                        pywbem.Uint64(0),
                        pywbem.Uint64(0),
                ],
                'ObjectSize':  [
                        pywbem.Uint64(0),  # inode size
                        pywbem.Uint64(0),  # file size
                        pywbem.Uint64(0),
                ],
                'ObjectSizeMin':  [
                        pywbem.Uint64(128),  # inode size
                        pywbem.Uint64(0),  # file size
                        pywbem.Uint64(0),
                ],
                'ObjectSizeMax':  [
                        pywbem.Uint64(4096),  # inode size
                        pywbem.Uint64(8 * (2 ** 60) - 1),  # file size 8 EiB-1
                        pywbem.Uint64(0),
                ],
                'FilenameFormats': [
                    vals.FilenameFormats.Unix
                ],
                'FilenameLengthMax':  [
                        pywbem.Uint64(255),
                ],
                'PersistenceTypes': [
                        vals.PersistenceTypes.Persistent]
            },
        }


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

        model['FileSystemType'] = fmt.name
        model['CaseSensitive'] = True
        model['CasePreserved'] = True
        model['PersistenceType'] = self.Values.PersistenceType.Persistent
        model['ElementName'] = fmt.device
        uuid = self.get_uuid(device, fmt)
        if uuid:
            model['UUID'] = uuid
        if fmt.label:
            model['ElementName'] = fmt.label
        return model

    @cmpi_logging.trace_method
    def _get_setting_for_format(self, setting_provider, fmt):
        """
            Return Setting for given format.
        """
        # Table of filesystems with Setting
        values = self.fs_settings.get(fmt.type, None)
        if values:
            # yes, we should create Setting for this FS
            setting = Setting(Setting.TYPE_CONFIGURATION,
                    setting_provider.create_setting_id(fmt.device))
            for (key, value) in values.iteritems():
                setting[key] = str(value)

            # TODO: add current block size, nr. of inodes, nr. of
            return setting
        return None

    @cmpi_logging.trace_method
    def enumerate_settings(self, setting_provider):
        """
            This method returns iterable with all instances of LMI_*Setting
            as Setting instances.
        """
        for device in self.storage.devices:
            if self.provides_format(device, device.format):
                setting = self._get_setting_for_format(
                        setting_provider, device.format)
                if setting:
                    yield setting


    @cmpi_logging.trace_method
    def get_setting_for_id(self, setting_provider, instance_id):
        """
            Return Setting instance, which corresponds to LMI_*Setting with
            given InstanceID.
            Return None if there is no such instance.
        """
        # TODO: use something more stable than device path
        path = setting_provider.parse_setting_id(instance_id)
        if not path:
            return None
        device = self.storage.devicetree.getDeviceByPath(path)
        if not device:
            return None
        if not device.format:
            return None
        return self._get_setting_for_format(setting_provider, device.format)

    @cmpi_logging.trace_method
    def get_associated_element_name(self, setting_provider, instance_id):
        """
            Return CIMInstanceName of ManagedElement for ElementSettingData
            association for setting with given ID.
            Return None if no such ManagedElement exists.
        """
        # TODO: use something more stable than device path
        path = setting_provider.parse_setting_id(instance_id)
        if not path:
            return None
        device = self.storage.devicetree.getDeviceByPath(path)
        if not device:
            return None
        fmt = device.format
        provider = self.provider_manager.get_provider_for_format(device, fmt)
        return provider.get_name_for_format(device, fmt)

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
                'ActualFileSystemType': pywbem.Uint16,
                'DataExtentsSharing': pywbem.Uint16,
                'FilenameCaseAttributes': pywbem.Uint16,
                'ObjectTypes' : SettingProvider.string_to_uint16_array,
                'NumberOfObjectsMin' : SettingProvider.string_to_uint64_array,
                'NumberOfObjectsMax' : SettingProvider.string_to_uint64_array,
                'NumberOfObjects' : SettingProvider.string_to_uint64_array,
                'ObjectSize' : SettingProvider.string_to_uint64_array,
                'ObjectSizeMin' : SettingProvider.string_to_uint64_array,
                'ObjectSizeMax' : SettingProvider.string_to_uint64_array,
                'PersistenceTypes' : SettingProvider.string_to_uint16_array,
                'FilenameFormats' : SettingProvider.string_to_uint16_array,
                'FilenameLengthMax' : SettingProvider.string_to_uint16_array,
        }

    @cmpi_logging.trace_method
    def get_setting_ignore(self, setting_provider):
        return {
                'CopyTagret': 0,
        }

    class Values(FormatProvider.Values):
        class PersistenceType(object):
            Unknown = pywbem.Uint16(0)
            Other = pywbem.Uint16(1)
            Persistent = pywbem.Uint16(2)
            Temporary = pywbem.Uint16(3)
            External = pywbem.Uint16(4)

        class ActualFileSystemType(object):
            Unknown = pywbem.Uint16(0)
            UFS = pywbem.Uint16(2)
            HFS = pywbem.Uint16(3)
            FAT = pywbem.Uint16(4)
            FAT16 = pywbem.Uint16(5)
            FAT32 = pywbem.Uint16(6)
            NTFS4 = pywbem.Uint16(7)
            NTFS5 = pywbem.Uint16(8)
            XFS = pywbem.Uint16(9)
            AFS = pywbem.Uint16(10)
            EXT2 = pywbem.Uint16(11)
            EXT3 = pywbem.Uint16(12)
            REISERFS = pywbem.Uint16(13)
            # DMTF_Reserved = ..
            EXT4 = pywbem.Uint16(0x8001)
            BTRFS = pywbem.Uint16(0x8002)
            JFS = pywbem.Uint16(0x8003)
            TMPFS = pywbem.Uint16(0x8004)
            VFAT = pywbem.Uint16(0x8005)

        class FilenameCaseAttributes(object):
            Unknown = pywbem.Uint16(0)
            Case_sensitive = pywbem.Uint16(1)
            Case_forced_to_upper_case = pywbem.Uint16(2)
            Case_forced_to_lower_case = pywbem.Uint16(3)
            Case_indifferent_but_lost = pywbem.Uint16(4)
            Case_indifferent_but_preserved = pywbem.Uint16(5)
            # DMTF_Reserved = ..
            # Vendor_Defined = 0x8000..

        class ObjectTypes(object):
            inodes = pywbem.Uint16(2)
            files = pywbem.Uint16(3)
            directories = pywbem.Uint16(4)
            links = pywbem.Uint16(5)
            devices = pywbem.Uint16(6)
            files_directories = pywbem.Uint16(7)
            Blocks = pywbem.Uint16(8)
            # DMTF_Reserved = ..
            # Vendor_Defined = 0x8000..

        class PersistenceTypes(object):
            Unknown = pywbem.Uint16(0)
            Other = pywbem.Uint16(1)
            Persistent = pywbem.Uint16(2)
            Temporary = pywbem.Uint16(3)
            External = pywbem.Uint16(4)
            # DMTF_Reserved = 5..

        class DataExtentsSharing(object):
            Unknown = pywbem.Uint16(0)
            No_Sharing = pywbem.Uint16(1)
            Sharing_Possible_Optional = pywbem.Uint16(2)
            Sharing_Enforced = pywbem.Uint16(3)
            # DMTF_Reserved = ..
            # Vendor_Defined = 0x8000..

        class FilenameFormats(object):
            DOS8_3 = pywbem.Uint16(1)
            Unix = pywbem.Uint16(2)
            VMS = pywbem.Uint16(3)
            Windows_LongNames = pywbem.Uint16(4)
            # DMTF_Reserved = ..
            # Vendor_Defined = 0x8000..
