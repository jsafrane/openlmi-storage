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
""" Module for LMI_LocalFilesystem."""

from openlmi.storage.LocalFileSystemProvider import LocalFileSystemProvider
import openlmi.common.cmpi_logging as cmpi_logging
import blivet.formats

class LMI_LocalFileSystem(LocalFileSystemProvider):
    """
        Generic file system provider for filesystems which do not have
        it's own provider.
    """
    @cmpi_logging.trace_method
    def __init__(self, *args, **kwargs):
        super(LMI_LocalFileSystem, self).__init__(
                classname="LMI_LocalFileSystem",
                device_type=None,
                setting_classname="LMI_FileSystemSetting",
                *args, **kwargs)

    @cmpi_logging.trace_method
    def provides_format(self, device, fmt):
        if fmt is None:
            return False
        # skip all non-filesystems
        if not isinstance(fmt, blivet.formats.fs.FS):
            return False

        # TODO: implement btrfs subvolumes
        if isinstance(device, blivet.devices.BTRFSSubVolumeDevice):
            return False

        # For BTRFS, we show LMI_LocalFileSystem for each BTRFSVolumeDevice
        if (isinstance(fmt, blivet.formats.fs.BTRFS)
                and not isinstance(device, blivet.devices.BTRFSVolumeDevice)):
            # This is not BTRFSVolumeDevice
            return False

        # TODO: skip formats with its own classes (currently none)

        # skip 'Unknown' format
        if fmt.type is None:
            return False
        return True

    def get_devices(self, device, fmt):
        if isinstance(fmt, blivet.formats.fs.BTRFS):
            if isinstance(device, blivet.devices.BTRFSSubVolumeDevice):
                # TODO: implement subvolumes
                return []
            if not isinstance(device, blivet.devices.BTRFSVolumeDevice):
                # We have real block device. Find the BTRFSVolume device for
                # it - it must be its only child.
                children = self.storage.devicetree.getChildren(device)
                if len(children) != 1:
                    cmpi_logging.logger.trace_warn("Failed to find btrfs volume"
                            " device on %s: %s" % (str(device), str(children)))
                    return []
                device = children[0]
            if isinstance(device, blivet.devices.BTRFSVolumeDevice):
                return device.parents
            else:
                cmpi_logging.logger.trace_warn("Failed to find btrfs volume"
                        " device on %s" % (str(device)))
                return []
        return [device]

    @cmpi_logging.trace_method
    def get_uuid(self, device, fmt):
        # We need to override it for BTRFS, it's uuid is in BTRFSVolumeDevice,
        # not it format
        if (isinstance(fmt, blivet.formats.fs.BTRFS)
            and isinstance(device, blivet.devices.BTRFSVolumeDevice)):
            uuid = device.uuid
            if uuid:
                return uuid
        return super(LMI_LocalFileSystem, self).get_uuid(device, fmt)
