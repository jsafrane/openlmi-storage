# OpenLMI Storage Provider
#
# Copyright (C) 2012 Red Hat, Inc.  All rights reserved.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""
    Support functions for Blivet.
"""

import subprocess
import os
import parted
import pywbem
import blivet
import openlmi.common.cmpi_logging as cmpi_logging

GPT_TABLE_SIZE = 34 * 2  # there are two copies
MBR_TABLE_SIZE = 1

def _align_up(address, alignment):
    """ Align address to nearest higher address divisible by alignment."""
    return (address / alignment + 1) * alignment

def _align_down(address, alignment):
    """ Align address to nearest lower address divisible by alignment."""
    return (address / alignment) * alignment

@cmpi_logging.trace_function
def get_logical_partition_start(partition):
    """
        Return starting sector of logical partition metadata, relative to
        extended partition start.
    """
    disk = partition.disk
    ext = disk.format.partedDisk.getExtendedPartition()
    if not ext:
        raise pywbem.CIMError(pywbem.CIM_ERR_FAILED,
                'Cannot find extended partition.')

    metadata = None
    part = ext.nextPartition()
    while part is not None:
        if (part.type & parted.PARTITION_LOGICAL
                and part.type & parted.PARTITION_METADATA):
            metadata = part
        if part.path == partition.path:
            break
        part = part.nextPartition()

    print 'partition', part, 'metadata', metadata
    if not part:
        raise pywbem.CIMError(pywbem.CIM_ERR_FAILED,
                'Cannot find the partition on the disk.')
    if not metadata:
        raise pywbem.CIMError(pywbem.CIM_ERR_FAILED,
                'Cannot find metadata for the partition.')

    return metadata.geometry.start

@cmpi_logging.trace_function
def get_partition_table_size(device):
    """
        Return size of partition table (in blocks) for given Anaconda
        StorageDevice instance.
    """
    if device.format:
        fmt = device.format
        if fmt.labelType == "gpt":
            return GPT_TABLE_SIZE * 2
        if fmt.labelType == "msdos":
            return MBR_TABLE_SIZE
    return 0

@cmpi_logging.trace_function
def get_available_sectors(device):
    """
        Return (start, end), where start is the first usable sector after
        partition table and end is the last usable sector before any
        partition table copy 
    """
    size = device.partedDevice.length
    if device.format:
        fmt = device.format
        alignment = device.partedDevice.optimumAlignment.grainSize
        if fmt.labelType == "gpt":
            return (
                    _align_up(GPT_TABLE_SIZE, alignment),
                    _align_down(size - GPT_TABLE_SIZE - 1, alignment))
        if fmt.labelType == "msdos":
            return(
                    _align_up(MBR_TABLE_SIZE, alignment),
                    _align_down(size - 1, alignment))

    if isinstance(device, blivet.devices.PartitionDevice):
        if device.isExtended:
            return(
                    _align_up(0, alignment),
                    _align_down(size - 1, alignment))

    return (0, size - 1)

@cmpi_logging.trace_function
def remove_partition(storage, device):
    """
        Remove PartitionDevice from system, i.e. delete a partition.
    """
    action = blivet.deviceaction.ActionDestroyDevice(device)
    do_storage_action(storage, [action])

@cmpi_logging.trace_function
def do_storage_action(storage, actions):
    """
        Perform array Anaconda DeviceActions on given Storage instance.
    """
    do_partitioning = False

    for action in actions:
        cmpi_logging.logger.trace_info("Running action " + str(action))
        cmpi_logging.logger.trace_info("    on device " + repr(action.device))

        if (isinstance(action.device, blivet.devices.PartitionDevice)
                and isinstance(action,
                        blivet.deviceaction.ActionCreateDevice)):
            do_partitioning = True

        storage.devicetree.registerAction(action)
    try:
        if do_partitioning:
            # this must be called when creating a partition
            cmpi_logging.logger.trace_verbose("Running doPartitioning()")
            blivet.partitioning.doPartitioning(storage=storage)

        storage.devicetree.processActions(dryRun=False)

        for action in actions:
            if not isinstance(action,
                    blivet.deviceaction.ActionDestroyDevice):
                cmpi_logging.logger.trace_verbose(
                        "Result: " + repr(action.device))

    finally:
        os.system('udevadm trigger --subsystem-match block')
        os.system('udevadm settle')
        storage.reset()

def log_storage_call(msg, args):
    """
        Log a storage action to log.
        logger.info will be used. The message should have format
        'CREATE <type>' or 'DELETE <type>', where <type> is type of device
        (PARTITION, MDRAID, VG, LV, ...). The arguments will be printed
        after it in no special orded, only StorageDevice instances
        will be replaced with device.path.
    """
    print_args = {}
    for (key, value) in args.iteritems():
        if isinstance(value, blivet.devices.StorageDevice):
            value = value.path
        if key == 'parents':
            value = [d.path for d in value]
        print_args[key] = value

    logger = cmpi_logging.logger
    if logger:
        logger.info(msg + ": " + str(print_args))
