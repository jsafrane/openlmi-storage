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
""" Module for LMI_DiskPartitionConfigurationService class."""

from openlmi.storage.ServiceProvider import ServiceProvider
from openlmi.storage.LMI_DiskPartitionConfigurationSetting \
        import LMI_DiskPartitionConfigurationSetting
import pywbem
import blivet.formats
import openlmi.storage.util.storage as storage
import openlmi.storage.util.units as units
import parted
import openlmi.common.cmpi_logging as cmpi_logging
from openlmi.storage.JobManager import Job

class LMI_DiskPartitionConfigurationService(ServiceProvider):
    """
        LMI_DiskPartitionConfigurationService provider implementation.
    """
    @cmpi_logging.trace_method
    def __init__(self, *args, **kwargs):
        super(LMI_DiskPartitionConfigurationService, self).__init__(
                "LMI_DiskPartitionConfigurationService", *args, **kwargs)

    @cmpi_logging.trace_method
    def get_instance(self, env, model):
        model = super(LMI_DiskPartitionConfigurationService, self).get_instance(
                env, model)
        schemes = self.Values.PartitioningSchemes
        model['PartitioningSchemes'] = \
                schemes.Volumes_may_be_partitioned_or_treated_as_whole
        return model

    @cmpi_logging.trace_method
    def cim_method_setpartitionstyle(self, env, object_name,
                                     param_extent=None,
                                     param_partitionstyle=None):
        """
            Implements LMI_DiskPartitionConfigurationService.SetPartitionStyle()

            This method installs a partition table on an extent of the
            specified partition style; creating an association between the
            extent and that capabilities instances referenced as method
            parameters. As a side effect, the consumable block size of the
            underlying extent is reduced by the block size of the metadata
            reserved by the partition table and associated metadata. This size
            is in the PartitionTableSize property of the associated
            DiskPartitionConfigurationCapabilities instance.
        """
        # check parameters here, the real work is done in _setpartitionstyle
        self.check_instance(object_name)

        if not param_extent:
            raise pywbem.CIMError(pywbem.CIM_ERR_INVALID_PARAMETER,
                    "Parameter Extent is mandatory.")

        # check the device
        device = self.provider_manager.get_device_for_name(param_extent)
        if not device:
            raise pywbem.CIMError(pywbem.CIM_ERR_FAILED,
                    "Cannot find the Extent.")
        if isinstance(device, blivet.devices.PartitionDevice):
            raise pywbem.CIMError(pywbem.CIM_ERR_NOT_SUPPORTED,
                    "Creation of extended partitions is not supported.")
        if self.storage.deviceDeps(device):
            raise pywbem.CIMError(pywbem.CIM_ERR_FAILED,
                    "The Extent is used.")

        # check the capabilities
        mgr = self.provider_manager
        capabilities_provider = mgr.get_capabilities_provider_for_class(
                'LMI_DiskPartitionConfigurationCapabilities')
        if not capabilities_provider:
            raise pywbem.CIMError(pywbem.CIM_ERR_FAILED,
                    "Cannot find capabilities provider.")
        if param_partitionstyle:
            capabilities = capabilities_provider.get_capabilities_for_id(
                    param_partitionstyle['InstanceID'])
            if not capabilities:
                raise pywbem.CIMError(pywbem.CIM_ERR_INVALID_PARAMETER,
                        "Cannot find capabilities for given PartitionStyle.")
        else:
            # find the default capabilities
            capabilities = capabilities_provider.get_default_capabilities()
            if not capabilities:
                raise pywbem.CIMError(pywbem.CIM_ERR_INVALID_PARAMETER,
                        "Parameter PartitionStyle is mandatory, there is no"\
                        " default PartitionStyle.")

        part_styles = capabilities_provider.Values.PartitionStyle
        if capabilities['PartitionStyle'] == part_styles.EMBR:
            raise pywbem.CIMError(pywbem.CIM_ERR_NOT_SUPPORTED,
                    "Creation of extended partitions is not supported.")

        retval = self._setpartitionstyle(
                device, capabilities, capabilities_provider)
        return (retval, [])

    @cmpi_logging.trace_method
    def _setpartitionstyle(self, device, capabilities, capabilities_provider):
        """
            Really set the partition style, all parameters were successfully
            checked.
        """
        part_styles = capabilities_provider.Values.PartitionStyle
        if capabilities['PartitionStyle'] == part_styles.MBR:
            label = "msdos"
        elif capabilities['PartitionStyle'] == part_styles.GPT:
            label = "gpt"
        else:
            raise pywbem.CIMError(pywbem.CIM_ERR_NOT_SUPPORTED,
                    "Unsupported PartitionStyle:"
                    + str(capabilities['PartitionStyle']) + ".")

        storage.log_storage_call("CREATE DISKLABEL",
                {'label': label, 'device': device.path})

        fmt = blivet.formats.getFormat('disklabel', labelType=label)
        action = blivet.deviceaction.ActionCreateFormat(device, fmt)
        storage.do_storage_action(self.storage, [action])

        return self.Values.SetPartitionStyle.Success


    @cmpi_logging.trace_method
    def _parse_goal(self, param_goal):
        """
            Check Goal parameter of a CIM method.
            It must be CIMInstanceName of LMI_DiskPartitionConfigurationSetting.
            Return Setting appropriate to the CIMInstanceName or None
            if no Goal was specified.
            Raise CIMError, if the goal does not exist. 

            param_goal = CIMInstanceName
        """
        if not param_goal:
            return None

        instance_id = param_goal['InstanceID']
        goal = self.provider_manager.get_setting_for_id(
            instance_id, "LMI_DiskPartitionConfigurationSetting")
        if not goal:
            raise pywbem.CIMError(pywbem.CIM_ERR_INVALID_PARAMETER,
                "LMI_DiskPartitionConfigurationSetting Goal does not"
                " found.")
        return goal

    @cmpi_logging.trace_method
    def _parse_partition(self, param_partition, device):
        """
            Check Partition parameter of a CIM method.
            It must be CIMInstanceName of a CIM_Partition.
            If a device was specified in the method, then check that the
            device contains the partition.
            Return PartitionDevice. Return None if no Partition parameter
            was set.
            Raise CIMError on any error like the partition does not exist
            or the partition is not on given device.
            
            param_partition = CIMInstanceName
            device = StorageDevice 
        """
        if not param_partition:
            return None

        partition = self.provider_manager.get_device_for_name(param_partition)
        if not partition:
            raise pywbem.CIMError(pywbem.CIM_ERR_FAILED,
                "Cannot find the Partition.")
        if not isinstance(device,
            blivet.devices.PartitionDevice):
            raise pywbem.CIMError(pywbem.CIM_ERR_INVALID_PARAMETER,
                "Parameter Partition does not refer to partition.")
        if device:
            # the partition must be on the device
            if device not in partition.parents:
                raise pywbem.CIMError(pywbem.CIM_ERR_INVALID_PARAMETER,
                    "The Partition does not reside on the Extent.")
        return partition

    @cmpi_logging.trace_method
    def _parse_extent(self, param_extent, goal):
        """
            Check Extent parameter of a CIM method.
            It must be CIMInstanceName of a CIM_StorageExtent and it must
            be possible to create partitions on it.
            If a Goal was specified in the method, then check that the
            partition with such goal can be created on the partition. 
            Return (StorageDevice, logical), where 'logical' is True, if
            a logical partition is requested. Return None if no Extent parameter
            was set.
            Raise CIMError on any error, like the device does not exist
            or there is no partition table on the device.
            
            param_extent = CIMInstanceName
            goal = Setting 
        """
        if not param_extent:
            return (None, None)

        logical = False
        device = self.provider_manager.get_device_for_name(param_extent)
        if not device:
            raise pywbem.CIMError(pywbem.CIM_ERR_FAILED,
                     "Cannot find the Extent.")
        if isinstance(device, blivet.devices.PartitionDevice):
            values = LMI_DiskPartitionConfigurationSetting.Values.PartitionType
            if goal and int(goal['PartitionType']) != values.Logical:
                raise pywbem.CIMError(pywbem.CIM_ERR_INVALID_PARAMETER,
                    "Only Goal with PartitionType == Logical can be"
                    " created on this device.")
            device = device.parents[0]
            logical = True
        return (device, logical)


    # Too many arguments, but this is generated function!
    # pylint: disable-msg=R0913
    def cim_method_createormodifypartition(self, env, object_name,
                                           param_goal=None,
                                           param_partition=None,
                                           param_devicefilename=None,
                                           param_extent=None,
                                           param_startingaddress=None,
                                           param_endingaddress=None):
        """
            Implements LMI_DiskPartitionConfigurationService.CreateOrModifyPartition()

            This method creates a new partition if the Partition parameter is
            null or modifies the partition specified. If the starting and
            ending address parameters are null, the resulting partition will
            occupy the entire underlying extent. If the starting address is
            non-null and the ending address is null, the resulting partition
            will extend to the end of the underlying extent. \n\nIn
            contradiction to SMI-S, no LogicalDisk will be created on the
            partition.\nIf logical partition is being created, it's start/end
            sector must include space for partition metadata and any alignment
            sectors. ConsumableSpace of the logical partition will be reduced
            by these metadata and alignment sectors.\nThe underlying extent
            MUST be associated to a capabilities class describing the
            installed partition style (partition table); this association is
            established using SetPartitionStyle().
        """
        # check parameters
        self.check_instance(object_name)

        if not param_partition and not param_extent:
            raise pywbem.CIMError(pywbem.CIM_ERR_INVALID_PARAMETER,
                    "Either Partition or extent parameter must be present.")
        if param_devicefilename:
            raise pywbem.CIMError(pywbem.CIM_ERR_NOT_SUPPORTED,
                    "Parameter DeviceFileName is not supported.")

        # check goal
        goal = self._parse_goal(param_goal)

        (device, logical) = self._parse_extent(param_extent, goal)
        if logical:
            # Recalculate start/end addresses from 'relative to extended
            # partition start' to 'relative to disk start'
            address_shift = partitioning.get_logical_partition_start(device)
            if param_startingaddress is not None:
                param_startingaddress = param_startingaddress + address_shift
            if param_endingaddress is not None:
                param_endingaddress = param_endingaddress + address_shift

        if device:
            (minstart, maxend) = partitioning.get_available_sectors(device)

        # check partition
        partition = self._parse_partition(param_partition, device)
        if partition:
            if param_startingaddress is None:
                start = 0
            if param_endingaddress is None:
                end = 0
            (retval, partition) = self._modify_partition(
                    partition, goal, start, end)
        else:
            if param_startingaddress is None:
                start = minstart
            if param_endingaddress is None:
                end = maxend
            (retval, partition) = self._create_partition(
                    device, goal, start, end)

        partition_name = self.provider_manager.get_name_for_device(partition)
        out_params = [pywbem.CIMParameter('partition', type='reference',
                           value=partition_name)]
        return (retval, out_params)

    @cmpi_logging.trace_method
    # pylint: disable-msg=W0613
    def _modify_partition(self, partition, goal, start, end):
        """
            Modify partition to given goal, start and end.
            Start and End can be 0, which means no change.
            Return (retval, partition).
        """
        raise pywbem.CIMError(pywbem.CIM_ERR_NOT_SUPPORTED,
                "Partition modification is not supported.")


    @cmpi_logging.trace_method
    # pylint: disable-msg=W0613
    def _lmi_modify_partition(self, partition, goal, size):
        """
            Modify partition to given goal and size.
            Size can be Null, which means no change.
            Return (retval, partition, size).
        """
        raise pywbem.CIMError(pywbem.CIM_ERR_NOT_SUPPORTED,
                "Partition modification is not supported.")

    @cmpi_logging.trace_method
    def _get_max_partition_size(self, device, partition_type):
        """
            Return maximum partition size on given device, in bytes.
            Partition_type must be parted constant or None
        """
        if partition_type is None:
            # Find the largest logical and normal and return the largest
            max_primary = self._get_max_partition_size(
                device, parted.PARTITION_NORMAL)
            max_logical = 0
            if device.format.extendedPartition is not None:
                max_logical = self._get_max_partition_size(
                    device, parted.PARTITION_LOGICAL)
            elif (device.format.labelType == 'msdos' and
                    len(device.format.partitions) > 3):
                # There is no extended partition and the new one
                # will be logical
                # -> reserve 2 MB for extended partition metadata
                max_primary = max_primary - 2 * units.MEGABYTE
            return max(max_primary, max_logical)
        else:
            parted_disk = device.format.partedDisk
            geom = blivet.partitioning.getBestFreeSpaceRegion(
                    parted_disk,
                    partition_type,
                    1,
                    grow=True)
            if geom is None:
                return 0
            return geom.getLength()



    @cmpi_logging.trace_method
    # pylint: disable-msg=W0613
    def _create_partition(self, device, goal, start, end):
        """
            Create partition on given device with  given goal, start and end.
            Return (retval, partition).
        """
        # TODO: wait for anaconda to implement start/end sectors
        raise pywbem.CIMError(pywbem.CIM_ERR_NOT_SUPPORTED,
                "CreateOrModifyPartition is not supported, use"\
                " LMI_CreateOrModifyPartition instead.")

    @cmpi_logging.trace_method
    def _calculate_partition_type(self, device, goal):
        """
            Calculate the right partition type for given goal and return
            pypaterd partition type.
        """
        part_type = None
        part_types = LMI_DiskPartitionConfigurationSetting.Values.PartitionType
        if int(goal['PartitionType']) == part_types.Extended:
            if device.format.labelType != "msdos":
                raise pywbem.CIMError(pywbem.CIM_ERR_INVALID_PARAMETER,
                    "Goal.PartitionType cannot be Extended for this"
                    " Extent.")
            part_type = parted.PARTITION_EXTENDED
        elif int(goal['PartitionType']) == part_types.Primary:
            part_type = parted.PARTITION_NORMAL
        elif int(goal['PartitionType']) == part_types.Logical:
            if device.format.labelType != "msdos":
                raise pywbem.CIMError(pywbem.CIM_ERR_INVALID_PARAMETER,
                         "Goal.PartitionType cannot be Logical for this"
                    " Extent.")
            part_type = parted.PARTITION_LOGICAL
        return part_type

    @cmpi_logging.trace_method
    def _lmi_create_partition(self, job, devicename, goal, size):
        """
            Create partition on given device with  given goal and size.
            Size can be null, which means the largest possible size.
            Return (retval, partition, size).
            This method is called from JobManager worker thread!
        """
        device = self.provider_manager.get_device_for_name(devicename)
        if not device:
            raise pywbem.CIMError(pywbem.CIM_ERR_FAILED,
                    "The devices disappeared: " + devicename)

        bootable = None
        part_type = None
        hidden = None
        primary = False

        if not isinstance(device.format,
                blivet.formats.disklabel.DiskLabel):
            raise pywbem.CIMError(pywbem.CIM_ERR_FAILED,
                    "Cannot find partition table on the extent.")

        # check goal and set appropriate partition parameters
        if goal:
            bootable = goal['Bootable']
            hidden = goal['Hidden']
            part_type = self._calculate_partition_type(device, goal)
            if part_type is not None:
                if part_type == parted.PARTITION_LOGICAL:
                    primary = False
                else:
                    primary = True

        # check size and grow it if necessary
        if size is None:
            grow = True
            size = 1
        else:
            # check maximum size
            max_partition = self._get_max_partition_size(device, part_type)
            max_partition = max_partition * device.partedDevice.sectorSize
            if max_partition < size:
                ret = self.Values.LMI_CreateOrModifyPartition.Size_Not_Supported
                return (ret, None, max_partition)
            # Ok, the partition will fit. Continue.
            grow = False
            size = size / units.MEGABYTE

        args = {
                'parents': [device],
                'size': size,
                'partType': part_type,
                'bootable': bootable,
                'grow': grow,
                'primary': primary
        }
        storage.log_storage_call("CREATE PARTITION", args)

        partition = self.storage.newPartition(**args)
        partition.disk = device

        if hidden is not None:
            if partition.flagAvailable(parted.PARTITION_HIDDEN):
                if hidden:
                    partition.setFlag(parted.PARTITION_HIDDEN)
            else:
                raise pywbem.CIMError(pywbem.CIM_ERR_INVALID_PARAMETER,
                        "Goal.Hidden cannot be set for this Extent.")

        # finally, do the dirty job
        action = blivet.deviceaction.ActionCreateDevice(partition)
        storage.do_storage_action(self.storage, [action])
        size = partition.size * units.MEGABYTE

        ret = self.Values.LMI_CreateOrModifyPartition\
                .Job_Completed_with_No_Error
        partition_name = self.provider_manager.get_name_for_device(partition)
        outparams = {
                'Size': pywbem.Uint64(size),
                'Partition': partition_name
        }
        job.finish_method(
                Job.STATE_FINISHED_OK,
                return_value=ret,
                return_type=Job.ReturnValueType.Uint32,
                output_arguments=outparams,
                affected_elements=[partition_name, ],
                error=None)


    @cmpi_logging.trace_method
    def cim_method_lmi_createormodifypartition(self, env, object_name,
                                               param_partition=None,
                                               param_goal=None,
                                               param_extent=None,
                                               param_size=None):
        """
            Implements LMI_DiskPartitionConfigurationService.LMI_CreateOrModifyPartition()

            Create new partition on given extent.Partition modification is not
            yet supported.The implementation will select the best space to fit
            the partition, with all alignment rules etc. \nIf no Size
            parameter is provided, the largest possible partition is
            created.\nIf no Goal is provided and GPT partition is requested,
            normal partition is created. If no Goal is provided and MS-DOS
            partition is requested and there is extended partition already on
            the device, a logical partition is created. If there is no
            extended partition on the device and there are at most two primary
            partitions on the device, primary partition is created. If there
            is no extended partition and three primary partitions already
            exist, new extended partition with all remaining space is created
            and a logical partition with requested size is created.
        
            Keyword arguments:
            env -- Provider Environment (pycimmb.ProviderEnvironment)
            object_name -- A pywbem.CIMInstanceName or pywbem.CIMCLassName 
                specifying the object on which the method LMI_CreateOrModifyPartition() 
                should be invoked.
            param_partition --  The input parameter Partition (type REF (pywbem.CIMInstanceName(classname='CIM_GenericDiskPartition', ...)) 
                A reference an existing partition instance to modify or null to
                request a new partition.
            
            param_goal --  The input parameter Goal (type REF (pywbem.CIMInstanceName(classname='LMI_DiskPartitionConfigurationSetting', ...)) 
                Setting to be applied to created/modified partition.
        
            param_extent --  The input parameter extent (type REF (pywbem.CIMInstanceName(classname='CIM_StorageExtent', ...)) 
                A reference to the underlying extent the partition is base on.
        
            param_size --  The input parameter Size (type pywbem.Uint64) 
                Requested size of the partition to create. If null when
                creating a partition, the larges possible partition is
                created.On output, the achieved size is returned.
        """
        self.check_instance(object_name)

        # remember input parameters for Job
        input_arguments = {
                'Partition' : pywbem.CIMProperty(name='Partition',
                        type='reference',
                        value=param_partition),
                'Goal' : pywbem.CIMProperty(name='Goal',
                        type='reference',
                        value=param_goal),
                'Extent': pywbem.CIMProperty(name='Extent',
                        type='reference',
                        value=param_extent),
                'Size': pywbem.CIMProperty(name='Size',
                        type='uint64',
                        value=param_size),
        }

        # check parameters
        if not param_partition and not param_extent:
            raise pywbem.CIMError(pywbem.CIM_ERR_INVALID_PARAMETER,
                    "Either Partition or extent parameter must be present.")

        goal = self._parse_goal(param_goal)
        (device, _unused) = self._parse_extent(param_extent, goal)
        partition = self._parse_partition(param_partition, device)

        if partition:
            # modify
            job_name = "MODIFY PARTITION %s" % (partition.path,)
            affected_elements = [param_partition]
        else:
            # create
            job_name = "CREATE PARTITION ON %s" % (device.path,)
            affected_elements = [param_extent]

        # prepare job
        job = Job(
                job_manager=self.job_manager,
                job_name=job_name,
                input_arguments=input_arguments,
                method_name='LMI_CreateOrModifyPartition',
                affected_elements=affected_elements,
                owning_element=self._get_instance_name())
        if partition:
            # modify
            job.set_execute_action(self._lmi_modify_partition,
                    job, param_partition, goal, param_size)

        else:
            # create
            job.set_execute_action(self._lmi_create_partition,
                    job, param_extent, goal, param_size)

        outparams = [ pywbem.CIMParameter(
                name='job',
                type='reference',
                value=job.get_name())]
        ret = self.Values.LMI_CreateOrModifyPartition\
                .Method_Parameters_Checked___Job_Started

        # enqueue the job
        self.job_manager.add_job(job)
        return (ret, outparams)



    class Values(ServiceProvider.Values):
        class PartitioningSchemes(object):
            No_partitions_allowed = pywbem.Uint16(2)
            Volumes_may_be_partitioned_or_treated_as_whole = pywbem.Uint16(3)
            Volumes_must_be_partitioned = pywbem.Uint16(4)

        class SetPartitionStyle(object):
            Success = pywbem.Uint32(0)
            Not_Supported = pywbem.Uint32(1)
            Unknown = pywbem.Uint32(2)
            Timeout = pywbem.Uint32(3)
            Failed = pywbem.Uint32(4)
            Invalid_Parameter = pywbem.Uint32(5)
            # DMTF_Reserved = ..
            # Extent_already_has_partition_table = 0x1000
            # Requested_Extent_too_large = 0x1001
            # Style_not_supported_by_Service = 0x1002
            # Method_Reserved = ..
            # Vendor_Specific = 0x8000..

        class CreateOrModifyPartition(object):
            Success = pywbem.Uint32(0)
            Not_Supported = pywbem.Uint32(1)
            Unknown = pywbem.Uint32(2)
            Timeout = pywbem.Uint32(3)
            Failed = pywbem.Uint32(4)
            Invalid_Parameter = pywbem.Uint32(5)
            # DMTF_Reserved = ..
            # Overlap_Not_Supported = 0x1000
            # No_Available_Partitions = 0x1001
            # Specified_partition_not_on_specified_extent = 0x1002
            # Device_File_Name_not_valid = 0x1003
            # LogicalDisk_with_different_DeviceFileName_exists = 0x1004
            # Method_Reserved = ..
            # Vendor_Specific = 0x8000..

        class LMI_CreateOrModifyPartition(object):
            Job_Completed_with_No_Error = pywbem.Uint32(0)
            Not_Supported = pywbem.Uint32(1)
            Unknown = pywbem.Uint32(2)
            Timeout = pywbem.Uint32(3)
            Failed = pywbem.Uint32(4)
            Invalid_Parameter = pywbem.Uint32(5)
            In_Use = pywbem.Uint32(6)
            # DMTF_Reserved = ..
            Method_Parameters_Checked___Job_Started = pywbem.Uint32(4096)
            Size_Not_Supported = pywbem.Uint32(4097)
            # Method_Reserved = 4098..32767
            # Vendor_Specific = 32768..65535
