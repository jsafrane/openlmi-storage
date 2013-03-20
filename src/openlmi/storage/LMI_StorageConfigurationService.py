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
""" Module for LMI_StorageConfigurationService class."""

from openlmi.storage.ServiceProvider import ServiceProvider
import pywbem
import blivet.formats
import openlmi.common.cmpi_logging as cmpi_logging
import openlmi.storage.util.units as units
import openlmi.storage.util.storage as storage
from openlmi.storage.DeviceProvider import DeviceProvider
from openlmi.storage.SettingProvider import SettingProvider
from openlmi.storage.JobManager import Job

class LMI_StorageConfigurationService(ServiceProvider):
    """ Provider of LMI_StorageConfigurationService. """

    @cmpi_logging.trace_method
    def __init__(self, *args, **kwargs):
        super(LMI_StorageConfigurationService, self).__init__(
                classname="LMI_StorageConfigurationService",
                *args, **kwargs)

    @cmpi_logging.trace_method
    def _check_redundancy_setting(self, redundancy, setting):
        """
            Check that DeviceProvider.Redundancy matches Setting.
            Return None if so or string with error message if it does
            not match.
        """
        # Too many return statements, but it has a purpose.
        # pylint: disable-msg=R0911

        drmax = setting.get('DataRedundancyMax', None)
        drmin = setting.get('DataRedundancyMin', None)
        drgoal = setting.get('DataRedundancyGoal', None)

        if drmax is not None and int(drmax) < redundancy.data_redundancy:
            return "DataRedundancyMax is too low."
        if drmin is not None and int(drmin) > redundancy.data_redundancy:
            return "DataRedundancyMin is too high."
        if (drmax is None and drmin is None and drgoal is not None
                and int(drgoal) != redundancy.data_redundancy):
            # only goal is set - it must match
            return "DataRedundancyGoal does not match."

        esmax = setting.get('ExtentStripeLengthMax', None)
        esmin = setting.get('ExtentStripeLengthMin', None)
        esgoal = setting.get('ExtentStripeLength', None)
        if esmax is not None and int(esmax) < redundancy.stripe_length:
            return "ExtentStripeLengthMax is too low."
        if esmin is not None and int(esmin) > redundancy.stripe_length:
            return "ExtentStripeLengthMin is too high."
        if (esmax is None and esmin is None and esgoal is not None
                and int(esgoal) != redundancy.stripe_length):
            # only goal is set - it must match
            return "ExtentStripeLength does not match."

        prmax = setting.get('PackageRedundancyMax', None)
        prmin = setting.get('PackageRedundancyMin', None)
        prgoal = setting.get('PackageRedundancyGoal', None)
        if prmax is not None and int(prmax) < redundancy.package_redundancy:
            return "PackageRedundancyMax is too low."
        if prmin is not None and int(prmin) > redundancy.package_redundancy:
            return "PackageRedundancyMin is too high."
        if (prmax is None and prmin is None and prgoal is not None
                and prgoal != redundancy.package_redundancy):
            # only goal is set - it must match
            return "PackageRedundancyGoal does not match."

        nspof = setting.get('NoSinglePointOfFailure', None)
        if (nspof is not None
                and SettingProvider.string_to_bool(nspof)
                    != redundancy.no_single_point_of_failure):
            return "NoSinglePointOfFailure does not match."

        parity = setting.get('ParityLayout', None)
        if (parity is not None
                and int(parity) != redundancy.parity_layout):
            return "ParityLayout does not match."

        return None

    @cmpi_logging.trace_method
    def _check_redundancy_goal_setting(self, redundancy, setting):
        """
            Check that DeviceProvider.Redundancy matches Setting['*Goal'].
            Return None if so or string with error message if it does
            not match.
            
            If any of the *Goal property is missing, the min/max is checked
            if it fits.
        """
        drgoal = setting.get('DataRedundancyGoal', None)
        if (drgoal is not None
                and int(drgoal) != redundancy.data_redundancy):
            return "DataRedundancyGoal does not match."

        esgoal = setting.get('ExtentStripeLength', None)
        if (esgoal is not None
                and int(esgoal) != redundancy.stripe_length):
            return "ExtentStripeLength does not match."

        prgoal = setting.get('PackageRedundancyGoal', None)
        if (prgoal is not None
                and prgoal != redundancy.package_redundancy):
            return "PackageRedundancyGoal does not match."

        nspof = setting.get('NoSinglePointOfFailure', None)
        if (nspof is not None
                and SettingProvider.string_to_bool(nspof)
                    != redundancy.no_single_point_of_failure):
            return "NoSinglePointOfFailure does not match."

        parity = setting.get('ParityLayout', None)
        if (parity is not None
                and int(parity) != redundancy.parity_layout):
            return "ParityLayout does not match."

        return self._check_redundancy_setting(redundancy, setting)

    @cmpi_logging.trace_method
    def _modify_lv(self, device, name, size):
        """
            Really modify the logical volume, all parameters were checked.
        """
        outparams = []
        if name is not None:
            # rename
            raise pywbem.CIMError(pywbem.CIM_ERR_NOT_SUPPORTED,
                    "Rename of logical volume is not yet supported.")

        if size is not None:
            # resize

            # check PE size
            newsize = device.vg.align(float(size) / units.MEGABYTE, True)
            oldsize = device.vg.align(device.size, False)
            if newsize != oldsize:
                action = blivet.deviceaction.ActionResizeDevice(
                        device, newsize)
                storage.do_storage_action(self.storage, [action])
                self.storage.devicetree.processActions(dryRun=False)
                self.storage.reset()

        newsize = device.size * units.MEGABYTE
        outparams.append(pywbem.CIMParameter(
                name="Size",
                type="uint64",
                value=pywbem.Uint64(newsize)))

        outparams.append(pywbem.CIMParameter(
                name='theelement',
                type='reference',
                value=self.provider_manager.get_name_for_device(device)))
        ret = self.Values.CreateOrModifyElementFromStoragePool \
                .Job_Completed_with_No_Error
        return (ret, outparams)


    @cmpi_logging.trace_method
    def _create_lv(self, pool, name, size):
        """
            Really create the logical volume, all parameters were checked.
        """
        args = {}
        args['parents'] = [pool]
        args['size'] = pool.align(float(size) / units.MEGABYTE, True)
        if name:
            args['name'] = name

        storage.log_storage_call("CREATE LV", args)

        lv = self.storage.newLV(**args)
        action = blivet.deviceaction.ActionCreateDevice(lv)
        storage.do_storage_action(self.storage, [action])

        newsize = lv.size * units.MEGABYTE
        outparams = [
                pywbem.CIMParameter(
                        name='theelement',
                        type='reference',
                        value=self.provider_manager.get_name_for_device(lv)),
                pywbem.CIMParameter(
                    name="Size",
                    type="uint64",
                    value=pywbem.Uint64(newsize))
        ]
        ret = self.Values.CreateOrModifyElementFromStoragePool \
                .Job_Completed_with_No_Error
        return (ret, outparams)

    @cmpi_logging.trace_method
    def _parse_goal(self, param_goal, classname):
        """
            Find Setting for given CIMInstanceName and check, that it is
            of given CIM class. 
            Return None, if no Goal was given.
            Raise CIMError, if the Goal cannot be found.
        """
        if param_goal:
            instance_id = param_goal['InstanceID']
            goal = self.provider_manager.get_setting_for_id(
                instance_id, classname)
            if not goal:
                raise pywbem.CIMError(pywbem.CIM_ERR_INVALID_PARAMETER,
                    classname + " Goal does not found.")
        else:
            goal = None
        return goal

    @cmpi_logging.trace_method
    def _parse_element(self, param_theelement, classname, blivet_class):
        """
            Find StorageDevice for given CIMInstanceName.
            Return None if no CIMInstanceName was given.
            Raise CIMError if the device does not exist or is not of given
            class.
        """
        if not param_theelement:
            return None
        if param_theelement.classname != classname:
            raise pywbem.CIMError(pywbem.CIM_ERR_FAILED,
                    "Expected %s as TheElement.", (classname))

        device = self.provider_manager.get_device_for_name(param_theelement)
        if not device:
            raise pywbem.CIMError(pywbem.CIM_ERR_FAILED,
                    "Cannot find the TheElement device.")
        if not isinstance(device, blivet_class):
            raise pywbem.CIMError(pywbem.CIM_ERR_FAILED,
                "The TheElement parameter is not %s." % (classname,))
        return device


    @cmpi_logging.trace_method
    def _parse_pool(self, param_inpool):
        """
            Find LVMVolumeGroupDevice for given CIMInstanceName.
            Return None if no CIMInstanceName was given.
            Raise CIMError if the device does not exist or is not VG.
        """
        if not param_inpool:
            return None

        pool = self.provider_manager.get_device_for_name(param_inpool)
        if not pool:
            raise pywbem.CIMError(pywbem.CIM_ERR_FAILED,
                    "Cannot find the InPool device.")
        if not isinstance(pool,
            blivet.devices.LVMVolumeGroupDevice):
            raise pywbem.CIMError(pywbem.CIM_ERR_FAILED,
                    "The InPool parameter is not LMI_VGStoragePool.")
        return pool

    @cmpi_logging.trace_method
    def cim_method_createormodifylv(self, env, object_name,
                                    param_elementname=None,
                                    param_goal=None,
                                    param_theelement=None,
                                    param_inpool=None,
                                    param_size=None):
        """
            Implements LMI_StorageConfigurationService.CreateOrModifyLV()

            Create or modify Logical Volume. This method is shortcut to
            CreateOrModifyElementFromStoragePool with the right Goal. Lazy
            applications can use this method to create or modify LVs, without
            calculation of the Goal setting.
        """
        self.check_instance(object_name)

        # check parameters
        goal = self._parse_goal(param_goal, "LMI_LVStorageSetting")
        device = self._parse_element(param_theelement, "LMI_LVStorageExtent",
                blivet.devices.LVMLogicalVolumeDevice)
        pool = self._parse_pool(param_inpool)

        # check if resize is needed
        if param_size and device:
            oldsize = device.vg.align(device.size, False) * units.MEGABYTE
            if param_size < oldsize:
                raise pywbem.CIMError(pywbem.CIM_ERR_NOT_SUPPORTED,
                        "Shrinking of logical volumes is not supported.")
            if oldsize == param_size:
                # don't need to change the size
                param_size = None

        # check if rename is needed
        if device and device.name == param_elementname:
            # don't need to change the name
            param_elementname = None

        # pool vs goal
        if goal and pool:
            pool_provider = self.provider_manager.get_provider_for_device(pool)
            redundancy = pool_provider.get_redundancy(pool)
            error = self._check_redundancy_setting(redundancy, goal)
            if error:
                raise pywbem.CIMError(pywbem.CIM_ERR_FAILED,
                        "The Goal does not match InPool's capabilities: "
                            + error)

        # pool vs theelement
        if pool and device and device.vg != pool:
                raise pywbem.CIMError(pywbem.CIM_ERR_NOT_SUPPORTED,
                        "InPool does not match TheElement's pool, modification"\
                        " of a pool is not supported.")

        if not device and not pool:
            raise pywbem.CIMError(pywbem.CIM_ERR_NOT_SUPPORTED,
                    "Either InPool or TheElement must be specified.")

        if not device and not param_size:
            raise pywbem.CIMError(pywbem.CIM_ERR_INVALID_PARAMETER,
                    "Parameter Size must be set when creating a logical"\
                    " volume.")

        if device:
            return self._modify_lv(device, param_elementname, param_size)
        else:
            return self._create_lv(pool, param_elementname, param_size)


    @cmpi_logging.trace_method
    # Too many aruments of generated method: pylint: disable-msg=R0913
    def cim_method_createormodifyelementfromstoragepool(self, env, object_name,
                                                        param_elementname=None,
                                                        param_goal=None,
                                                        param_inpool=None,
                                                        param_theelement=None,
                                                        param_elementtype=None,
                                                        param_size=None):
        """
            Implements LMI_StorageConfigurationService
                            .CreateOrModifyElementFromStoragePool()

            Start a job to create (or modify) a Logical Volume from a
            LMI_StoragePool. One of the parameters for this method is Size. As
            an input parameter, Size specifies the desired size of the
            element. As an output parameter, it specifies the size achieved.
            The Size is rounded to extent size of the Volume Group. Space is
            taken from the input StoragePool. The desired settings for the
            element are specified by the Goal parameter. If the requested size
            cannot be created, no action will be taken, and the Return Value
            will be 4097/0x1001. Also, the output value of Size is set to the
            nearest possible size.  This method supports renaming or resizing
            of a Logical Volume.  If 0 is returned, the function completed
            successfully and no ConcreteJob instance was required. If
            4096/0x1000 is returned, a ConcreteJob will be started to create
            the element. The Job's reference will be returned in the output
            parameter Job.
        """
        if param_elementtype is not None:
            etype = self.Values.CreateOrModifyElementFromStoragePool.ElementType
            if param_elementtype != etype.StorageExtent:
                raise pywbem.CIMError(pywbem.CIM_ERR_INVALID_PARAMETER,
                        "The only ElementType is StorageExtent (3).")
        # create LV
        return self.cim_method_createormodifylv(env, object_name,
                param_elementname,
                param_goal,
                param_theelement,
                param_inpool,
                param_size)


    @cmpi_logging.trace_method
    def _modify_vg(self, job, poolname, goal, devnames, name):
        """
            Modify existing Volume Group. The parameters were already checked.
            This method is called in context of JobManager worker thread.
        """
        devices = []
        for devname in devnames:
            device = self.storage.devicetree.getDeviceByPath(devname)
            if device is None:
                raise pywbem.CIMError(pywbem.CIM_ERR_FAILED,
                        "Device %s disappeared." % (devname,))
            devices.append(device)

        pool = self.storage.devicetree.getDeviceByPath(poolname)
        if not pool:
            raise pywbem.CIMError(pywbem.CIM_ERR_FAILED,
                    "Pool %s disappeared." % (poolname,))

        if name is not None:
            # rename
            raise pywbem.CIMError(pywbem.CIM_ERR_NOT_SUPPORTED,
                    "Rename of volume group is not yet supported.")

        # check extent size
        if goal and goal['ExtentSize'] != pool.peSize:
            raise pywbem.CIMError(pywbem.CIM_ERR_NOT_SUPPORTED,
                    "Changing ExtentSize is not supported.")

        # check for added and removed devices:
        add_devices = []
        for device in devices:
            if device not in pool.pvs:
                add_devices.append(device)

        rm_devices = []
        for device in pool.pvs:
            if device not in devices:
                rm_devices.append(device)

        # now do it
        if add_devices:
            raise pywbem.CIMError(pywbem.CIM_ERR_NOT_SUPPORTED,
                    "Adding new devices to volume group is not yet supported.")
        if rm_devices:
            raise pywbem.CIMError(pywbem.CIM_ERR_NOT_SUPPORTED,
                    "Removing devices from volume group is not yet supported.")

        outparams = {}
        retval = self.Values.CreateOrModifyVG.Job_Completed_with_No_Error
        job.finish_method(
                Job.STATE_FINISHED_OK,
                return_value=retval,
                return_type=Job.ReturnValueType.Uint32,
                output_arguments=outparams,
                affected_elements=[poolname],
                error=None)

    @cmpi_logging.trace_method
    def _create_vg(self, job, goal, devnames, name):
        """
            Create new  Volume Group. The parameters were already checked.
            This method is called in context of JobManager worker thread.
        """
        devices = []
        for devname in devnames:
            device = self.storage.devicetree.getDeviceByPath(devname)
            if device is None:
                raise pywbem.CIMError(pywbem.CIM_ERR_FAILED,
                        "Device %s disappeared." % (devname,))
            devices.append(device)

        actions = []
        for device in devices:
            # TODO: check if it is unused!
            if not (device.format
                    and isinstance(device.format,
                        blivet.formats.lvmpv.LVMPhysicalVolume)):
                # create the pv format there
                pv = blivet.formats.getFormat('lvmpv')
                actions.append(blivet.ActionCreateFormat(device, pv))

        args = {}
        args['parents'] = devices
        if goal and goal['ExtentSize']:
            args['peSize'] = float(goal['ExtentSize']) / units.MEGABYTE
        if name:
            args['name'] = name

        storage.log_storage_call("CREATE VG", args)

        vg = self.storage.newVG(**args)
        actions.append(blivet.ActionCreateDevice(vg))
        storage.do_storage_action(self.storage, actions)

        poolname = self.provider_manager.get_name_for_device(vg)
        newsize = vg.size * units.MEGABYTE
        outparams = {
                'pool': poolname,
                'size':pywbem.Uint64(newsize),
        }
        retval = self.Values.CreateOrModifyVG.Job_Completed_with_No_Error
        job.finish_method(
                Job.STATE_FINISHED_OK,
                return_value=retval,
                return_type=Job.ReturnValueType.Uint32,
                output_arguments=outparams,
                affected_elements=[poolname],
                error=None)

    @cmpi_logging.trace_method
    def _parse_inextents(self, param_inextents):
        """
            Find StorageDevices for given array of CIMInstanceNames and
            return couple (devices, redundancies), where devices
            is array of StorageDevices and redundancies is array
            of Redundancy of the devices.
            Return (None, None), if no InExtents were given.
            Raise CIMError, if any of the extents cannot be found.
        """
        if not param_inextents:
            return (None, None)
        devices = []
        redundancies = []
        for extent_name in param_inextents:
            provider = self.provider_manager.get_device_provider_for_name(
                    extent_name)
            if not provider:
                raise pywbem.CIMError(pywbem.CIM_ERR_INVALID_PARAMETER,
                    "Cannot find provider for InExtent " + str(extent_name))
            device = provider.get_device_for_name(extent_name)
            if not provider:
                raise pywbem.CIMError(pywbem.CIM_ERR_INVALID_PARAMETER,
                    "Cannot find device for InExtent " + str(extent_name))
            devices.append(device)
            redundancies.append(provider.get_redundancy(device))

        return (devices, redundancies)

    @cmpi_logging.trace_method
    def cim_method_createormodifyvg(self, env, object_name,
                                    param_elementname=None,
                                    param_goal=None,
                                    param_inextents=None,
                                    param_pool=None,
                                    input_arguments=None,
                                    method_name=None):
        """
            Implements LMI_StorageConfigurationService.CreateOrModifyVG()

            Create or modify Volume Group. This method is shortcut to
            CreateOrModifyStoragePool with the right Goal. Lazy applications
            can use this method to create or modify VGs, without calculation
            of the Goal setting.
            
            On implementation side, this method is called by
            CreateOrModifyStoragePool. If so, input_arguments and method_name
            parameters are set, so we can create proper Job here.
        """
        # check parameters
        self.check_instance(object_name)

        # remember input parameters for job
        if not input_arguments:
            input_arguments = {
                'ElementName' : pywbem.CIMProperty(name='ElementName',
                        type='string',
                        value=param_elementname),
                'Goal' : pywbem.CIMProperty(name='Goal',
                        type='reference',
                        value=param_goal),
                'InExtents': pywbem.CIMProperty(name='InExtents',
                        type='reference',
                        is_array=True,
                        value=param_inextents),
                'Pool': pywbem.CIMProperty(name='Pool',
                        type='reference',
                        value=param_pool),
            }
        if not method_name:
            method_name = 'CreateOrModifyVG'

        goal = self._parse_goal(param_goal, "LMI_VGStorageSetting")
        pool = self._parse_pool(param_pool)
        (devices, redundancies) = self._parse_inextents(param_inextents)

        # extents vs goal:
        if devices and goal:
            final_redundancy = DeviceProvider.Redundancy \
                    .get_common_redundancy_list(redundancies)
            error = self._check_redundancy_setting(final_redundancy, goal)
            if error:
                raise pywbem.CIMError(pywbem.CIM_ERR_FAILED,
                        "The Goal does not match InExtents' capabilities: "
                            + error)

        # elementname
        name = param_elementname
        if pool and param_elementname == pool.name:
            # no rename is needed
            name = None

        if not pool and not devices:
            raise pywbem.CIMError(pywbem.CIM_ERR_INVALID_PARAMETER,
                    "Either Pool or InExtents must be specified")

        # Schedule a job
        devnames = [device.path for device in devices]
        devpaths = [self.provider_manager.get_name_for_device(device)
                        for device in devices]
        if pool:
            jobname = "MODIFY VG %s" % (name)
            poolname = self.provider_manager.get_name_for_device(pool)
        else:
            jobname = "CREATE VG %s FROM %s" % (name, ",".join(devnames))

        job = Job(
                job_manager=self.job_manager,
                job_name=jobname,
                input_arguments=input_arguments,
                method_name=method_name,
                affected_elements=devpaths,
                owning_element=self._get_instance_name())
        if pool:
            job.set_execute_action(self._modify_vg,
                    job, poolname, goal, devnames, name)
        else:
            job.set_execute_action(self._create_vg,
                    job, goal, devnames, name)

        # enqueue the job
        self.job_manager.add_job(job)

        outparams = [ pywbem.CIMParameter(
                name='job',
                type='reference',
                value=job.get_name())]
        return (self.Values.CreateOrModifyVG\
                .Method_Parameters_Checked___Job_Started, outparams)


    @cmpi_logging.trace_method
    # Too many aruments of generated method: pylint: disable-msg=R0913
    def cim_method_createormodifystoragepool(self, env, object_name,
                                             param_elementname=None,
                                             param_goal=None,
                                             param_inpools=None,
                                             param_inextents=None,
                                             param_pool=None,
                                             param_size=None):
        """
            Implements LMI_StorageConfigurationService.CreateOrModifyStoragePool()

            Starts a job to create (or modify) a StoragePool.Only Volume Groups
            can be created or modified using this method.\nLMI supports only
            creation of pools from whole StorageExtents, it is not possible to
            allocate only part of an StorageExtent.\nOne of the parameters for
            this method is Size. As an input parameter, Size specifies the
            desired size of the pool. It must match sum of all input extent
            sizes. Error will be returned if not, with correct Size output
            parameter value. \nAny InPools as parameter will result in
            error.\nThe capability requirements that the Pool must support are
            defined using the Goal parameter. \n This method supports renaming
            of a Volume Group and adding and removing StorageExtents to/from a
            Volume Group. \nIf 0 is returned, then the task completed
            successfully and the use of ConcreteJob was not required. If the
            task will take some time to complete, a ConcreteJob will be
            created and its reference returned in the output parameter Job. \n
            This method automatically formats the StorageExtents added to a
            Volume Group as Physical Volumes.
        """
        # check parameters
        if param_size:
            raise pywbem.CIMError(pywbem.CIM_ERR_NOT_SUPPORTED,
                    "Parameter Size is not supported.")
        if param_inpools:
            raise pywbem.CIMError(pywbem.CIM_ERR_NOT_SUPPORTED,
                    "Parameter InPools is not supported.")

        input_arguments = {
            'ElementName' : pywbem.CIMProperty(name='ElementName',
                    type='string',
                    value=param_elementname),
            'Goal' : pywbem.CIMProperty(name='Goal',
                    type='reference',
                    value=param_goal),
            'InExtents': pywbem.CIMProperty(name='InExtents',
                    type='reference',
                    is_array=True,
                    value=param_inextents),
            'InPools': pywbem.CIMProperty(name='InPools',
                    type='reference',
                    is_array=True,
                    value=param_inpools),
            'Pool': pywbem.CIMProperty(name='Pool',
                    type='reference',
                    value=param_pool),
            'Size': pywbem.CIMProperty(name='Size',
                    type='uint64',
                    value=param_size),
        }

        return self.cim_method_createormodifyvg(env, object_name,
                param_elementname, param_goal, param_inextents, param_pool,
                input_arguments, 'CreateOrModifyStoragePool')

    @cmpi_logging.trace_method
    # Too many aruments of generated method: pylint: disable-msg=R0913
    def cim_method_createormodifyelementfromelements(self, env, object_name,
                                                     param_inelements,
                                                     param_elementtype,
                                                     param_elementname=None,
                                                     param_goal=None,
                                                     param_theelement=None,
                                                     param_size=None):
        """
            Implements LMI_StorageConfigurationService.CreateOrModifyElementFromElements()

            Start a job to create (or modify) a MD RAID from specified input
            StorageExtents. Only whole StorageExtents can be added to a
            RAID.\nAs an input parameter, Size specifies the desired size of
            the element and must match size of all input StorageVolumes
            combined in the RAID. Use null to avoid this calculation. As an
            output parameter, it specifies the size achieved. \n The desired
            Settings for the element are specified by the Goal parameter. \n
            If 0 is returned, the function completed successfully and no
            ConcreteJob instance was required. If 4096/0x1000 is returned, a
            ConcreteJob will be started to create the element. The Job\'s
            reference will be returned in the output parameter Job.\n This
            method does not support MD RAID modification for now.
        """
        # check parameters
        if param_size is not None:
            raise pywbem.CIMError(pywbem.CIM_ERR_NOT_SUPPORTED,
                    "Parameter Size is not supported.")

        if param_elementtype is not None:
            etypes = self.Values.CreateOrModifyElementFromElements.ElementType
            if param_elementtype != etypes.Storage_Extent:
                raise pywbem.CIMError(pywbem.CIM_ERR_NOT_SUPPORTED,
                        "Parameter ElementType must have value" \
                        " '3 - StorageExtent'.")
        input_arguments = {
                'InElements': pywbem.CIMProperty(name='InElements',
                        type='reference',
                        is_array=True,
                        value=param_inelements),
                'ElementType': pywbem.CIMProperty(name='ElementType',
                        type='int16',
                        value=param_elementtype),
                'ElementName' : pywbem.CIMProperty(name='ElementName',
                        type='string',
                        value=param_elementname),
                'TheElement': pywbem.CIMProperty(name='TheElement',
                        type='reference',
                        value=param_theelement),
                'Goal' : pywbem.CIMProperty(name='Goal',
                        type='reference',
                        value=param_goal),
                'Size' : pywbem.CIMProperty(name='Size',
                        type='uint64',
                        value=param_size),
        }

        return self.cim_method_createormodifymdraid(env, object_name,
                param_elementname=param_elementname,
                param_theelement=param_theelement,
                param_goal=param_goal,
                param_level=None,
                param_inextents=param_inelements,
                input_arguments=input_arguments,
                method_name='CreateOrModifyElementFromElements')

    @cmpi_logging.trace_method
    def _find_raid_level(self, redundancies, goal):
        """
           Find and return RAID level corresponding to given Goal and set of
           redundancies of input devices.
        """
        # find redundancies of the devices
        # try all possible RAID levels and take the best one
        # hash level -> redundancy of the RAID with given level
        levels = {
                0: DeviceProvider.Redundancy.get_common_redundancy_list(
                        redundancies, 0),
                1: DeviceProvider.Redundancy.get_common_redundancy_list(
                        redundancies, 1),
                4: DeviceProvider.Redundancy.get_common_redundancy_list(
                        redundancies, 4),
                5: DeviceProvider.Redundancy.get_common_redundancy_list(
                        redundancies, 5),
                6: DeviceProvider.Redundancy.get_common_redundancy_list(
                        redundancies, 6),
                10: DeviceProvider.Redundancy.get_common_redundancy_list(
                        redundancies, 10),
        }

        # hash RAID level number -> priority of the level
        # if more RAID levels matches the goal, the lowest priority is selected
        level_priorities = {
                1: 1,
                5: 2,
                6: 3,
                4: 4,
                10: 5,
                0: 6
        }

        # first, check the goal[*Goal] properties
        best_level = None
        for (level, redundancy) in levels.iteritems():
            err = self._check_redundancy_goal_setting(redundancy, goal)
            if err is None:
                # we have match which either completely satisfied goal[*Goal]
                # or the redundancy matches goal[*Min/Max] properties
                if not best_level:
                    best_level = level
                else:
                    if level_priorities[level] < level_priorities[best_level]:
                        best_level = level
                cmpi_logging.logger.trace_info(
                        "Goal check: matching RAID%d, best level so far: %d"
                        % (level, best_level))
            else:
                cmpi_logging.logger.trace_info(
                        "Goal check: skipping goal RAID%d: %s"
                            % (level, err))

        if best_level is not None:
            return best_level

        # then, find any that matches
        for (level, redundancy) in levels.iteritems():
            err = self._check_redundancy_setting(redundancy, goal)
            if err is None:
                if not best_level:
                    best_level = level
                else:
                    if level_priorities[level] < level_priorities[best_level]:
                        best_level = level
                cmpi_logging.logger.trace_info(
                        "Any check: matching RAID%d, best level so far: %d"
                        % (level, best_level))
            else:
                cmpi_logging.logger.trace_info(
                        "Any check: skipping RAID%d: %s"
                            % (level, err))
        return best_level

    @cmpi_logging.trace_method
    def _schedule_create_mdraid(self, level, goal, devices, name,
            input_arguments, method_name):
        """
        Create the job to create a MD RAID.
        """
        devnames = [device.path for device in devices]
        devpaths = [self.provider_manager.get_name_for_device(device)
                        for device in devices]
        job = Job(
                job_manager=self.job_manager,
                job_name="CREATE MDRAID ON " + "+".join(devnames),
                input_arguments=input_arguments,
                method_name=method_name,
                affected_elements=devpaths,
                owning_element=self._get_instance_name())
        job.set_execute_action(self._create_mdraid,
                job, level, goal, devnames, name)

        # enqueue the job
        self.job_manager.add_job(job)

        outparams = [ pywbem.CIMParameter(
                name='job',
                type='reference',
                value=job.get_name())]
        return (self.Values.CreateOrModifyMDRAID\
                .Method_Parameters_Checked___Job_Started, outparams)

    @cmpi_logging.trace_method
    # pylint: disable-msg=W0613
    def _create_mdraid(self, job, level, goal, devicnames, name):
        """
            Create new  MD RAID. The parameters were already checked.
        """
        # covert devices from strings to real devices
        devices = []
        for devname in devicnames:
            device = self.storage.devicetree.getDeviceByPath(devname)
            if device is None:
                raise pywbem.CIMError(pywbem.CIM_ERR_FAILED,
                        "Device %s disappeared." % (devname,))
            # TODO: check if devices are unused!
            devices.append(device)

        args = {}
        args['parents'] = devices
        if name:
            args['name'] = name
        args['level'] = str(level)
        args['memberDevices'] = len(devices)

        storage.log_storage_call("CREATE MDRAID", args)

        raid = self.storage.newMDArray(**args)
        action = blivet.ActionCreateDevice(raid)
        storage.do_storage_action(self.storage, [action])

        newsize = raid.size * units.MEGABYTE
        raidname = self.provider_manager.get_name_for_device(raid)
        outparams = {
            'theelement': raidname,
            'size' : pywbem.Uint64(newsize)
        }
        retval = self.Values.CreateOrModifyMDRAID.Completed_with_No_Error
        job.finish_method(
                Job.STATE_FINISHED_OK,
                return_value=retval,
                return_type=Job.ReturnValueType.Uint32,
                output_arguments=outparams,
                affected_elements=[raidname, ],
                error=None)

    @cmpi_logging.trace_method
    # pylint: disable-msg=W0613
    def _schedule_modify_mdraid(self, raid, level, goal, devices, name,
            input_parameters, method_name):
        """
            Modify existing MD RAID. The parameters were already checked.
        """
        raise pywbem.CIMError(pywbem.CIM_ERR_NOT_SUPPORTED,
                "MD RAID modification is not supported yet.")

    @cmpi_logging.trace_method
    def cim_method_createormodifymdraid(self, env, object_name,
                                        param_elementname=None,
                                        param_theelement=None,
                                        param_goal=None,
                                        param_level=None,
                                        param_inextents=None,
                                        input_arguments=None,
                                        method_name=None):
        """
            Implements LMI_StorageConfigurationService.CreateOrModifyMDRAID()

            Create or modify MD RAID array. This method is shortcut to
            CreateOrModifyElementFromElements with the right Goal. Lazy
            applications can use this method to create or modify MD RAID with
            the right level, without calculation of the Goal setting.\n Either
            Level or Goal must be specified. If both are specified, they must
            match.\n RAID modification is not yet supported.
        """
        # check parameters
        self.check_instance(object_name)

        # remember input parameters for job
        if not input_arguments:
            input_arguments = {
                    'ElementName' : pywbem.CIMProperty(name='ElementName',
                            type='string',
                            value=param_elementname),
                    'TheElement': pywbem.CIMProperty(name='TheElement',
                            type='reference',
                            value=param_theelement),
                    'Goal' : pywbem.CIMProperty(name='Goal',
                            type='reference',
                            value=param_goal),
                    'Level' : pywbem.CIMProperty(name='Level',
                            type='uint16',
                            value=param_level),
                    'InExtents': pywbem.CIMProperty(name='InExtents',
                            type='reference',
                            is_array=True,
                            value=param_inextents),
            }
        if not method_name:
            method_name = "CreateOrModifyMDRAID"

        # check the parameters
        goal = self._parse_goal(param_goal, "LMI_MDRAIDStorageSetting")
        raid = self._parse_element(param_theelement, "LMI_MDRAIDStorageExtent",
                blivet.devices.MDRaidArrayDevice)
        (devices, redundancies) = self._parse_inextents(param_inextents)

        # level
        if param_level is not None and param_level not in (
                self.Values.CreateOrModifyMDRAID.Level.RAID0,
                self.Values.CreateOrModifyMDRAID.Level.RAID1,
                self.Values.CreateOrModifyMDRAID.Level.RAID4,
                self.Values.CreateOrModifyMDRAID.Level.RAID5,
                self.Values.CreateOrModifyMDRAID.Level.RAID6,
                self.Values.CreateOrModifyMDRAID.Level.RAID10):
            raise pywbem.CIMError(pywbem.CIM_ERR_INVALID_PARAMETER,
                    "Invalid value of parameter Level.")

        # goal vs level
        if goal and param_level is not None:
            raise pywbem.CIMError(pywbem.CIM_ERR_INVALID_PARAMETER,
                    "Only one of Level and Goal parameters may be used.")

        # extents vs goal:
        if devices and goal:
            # guess RAID level
            param_level = self._find_raid_level(redundancies, goal)
            if param_level is None:
                raise pywbem.CIMError(pywbem.CIM_ERR_FAILED,
                        "The Goal does not match any RAID level for InExtents.")

        # nr. of devices vs level
        if ((param_level == 0
                or param_level == 1)
                    and len(devices) < 2):
            raise pywbem.CIMError(pywbem.CIM_ERR_FAILED,
                    "At least two devices are required for RAID level %d."
                    % (param_level))

        if (param_level == 5 or param_level == 4) and len(devices) < 3:
            raise pywbem.CIMError(pywbem.CIM_ERR_FAILED,
                    "At least three devices are required for RAID level" \
                    " 4 or 5.")
        if param_level == 6 and len(devices) < 4:
            raise pywbem.CIMError(pywbem.CIM_ERR_FAILED,
                    "At least four devices are required for RAID level 6.")
        if param_level == 10 and len(devices) < 2:
            raise pywbem.CIMError(pywbem.CIM_ERR_FAILED,
                    "At least two devices are required for RAID level 10.")

        name = param_elementname
        if raid and param_elementname == raid.name:
            # no rename is needed
            name = None

        if not raid and not devices:
            raise pywbem.CIMError(pywbem.CIM_ERR_INVALID_PARAMETER,
                    "Either TheElement or InExtents must be specified")

        if raid:
            return self._schedule_modify_mdraid(
                    raid, param_level, goal, devices, name, input_arguments,
                    method_name)
        else:
            return self._schedule_create_mdraid(
                    param_level, goal, devices, name, input_arguments,
                    method_name)

    @cmpi_logging.trace_method
    def _delete_mdraid(self, job, devicepath):
        """
        Really delete a MD RAID array. This method is called in context of
        JobManager worker thread.
        """
        device = self.storage.devicetree.getDeviceByPath(devicepath)
        if not device:
            raise pywbem.CIMError(pywbem.CIM_ERR_FAILED,
                    "Cannot find device %s" % (devicepath,))
        if not isinstance(device, blivet.devices.MDRaidArrayDevice):
            raise pywbem.CIMError(pywbem.CIM_ERR_FAILED,
                    "Device %s is not LMI_MDRAIDStorageExtent" % (devicepath,))

        # finally delete it
        actions = []
        actions.append(blivet.ActionDestroyDevice(device))
        # Destroy also all formats on member devices.
        # TODO: remove when Blivet does this automatically.
        for parent in device.parents:
            actions.append(blivet.deviceaction.ActionDestroyFormat(parent))
        storage.do_storage_action(self.storage, actions)

        ret = self.Values.DeleteMDRAID.Completed_with_No_Error
        job.finish_method(
                Job.STATE_FINISHED_OK,
                return_value=ret,
                return_type=Job.ReturnValueType.Uint32,
                output_arguments={},
                affected_elements=[],
                error=None)

    @cmpi_logging.trace_method
    def cim_method_deletemdraid(self, env, object_name,
                                param_theelement=None):
        """Implements LMI_StorageConfigurationService.DeleteMDRAID()

        Delete MD RAID array. All members are detached from the array and
        all RAID metadata are erased.
        
        Keyword arguments:
        env -- Provider Environment (pycimmb.ProviderEnvironment)
        object_name -- A pywbem.CIMInstanceName or pywbem.CIMCLassName 
            specifying the object on which the method DeleteMDRAID() 
            should be invoked.
        param_theelement --  The input parameter TheElement (type REF (pywbem.CIMInstanceName(classname='LMI_MDRAIDStorageExtent', ...)) 
            The MD RAID device to destroy.
            

        Returns a two-tuple containing the return value (type pywbem.Uint32 self.Values.DeleteMDRAID)
        and a list of CIMParameter objects representing the output parameters

        Output parameters:
        Job -- (type REF (pywbem.CIMInstanceName(classname='CIM_ConcreteJob', ...)) 
            Reference to the job (may be null if job completed).
            

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
        # check parameters
        self.check_instance(object_name)

        # remember input parameters for job
        input_arguments = {
                'TheElement': pywbem.CIMProperty(name='TheElement',
                        type='reference',
                        value=param_theelement),
        }

        # check the parameters
        raid = self._parse_element(param_theelement, "LMI_MDRAIDStorageExtent",
                blivet.devices.MDRaidArrayDevice)
        if not raid:
            raise pywbem.CIMError(pywbem.CIM_ERR_INVALID_PARAMETER,
                    "Parameter TheElement must be specified an must be "
                    "reference to LMI_MDRAIDStorageExtent")
        # Schedule the job
        job = Job(
                job_manager=self.job_manager,
                job_name="DELETE MDRAID " + raid.path,
                input_arguments=input_arguments,
                method_name='DeleteMDRAID',
                affected_elements=[param_theelement],
                owning_element=self._get_instance_name())
        job.set_execute_action(self._delete_mdraid,
                job, raid.path)

        # enqueue the job
        self.job_manager.add_job(job)

        outparams = [ pywbem.CIMParameter(
                name='job',
                type='reference',
                value=job.get_name())]
        return (self.Values.CreateOrModifyMDRAID\
                .Method_Parameters_Checked___Job_Started, outparams)


    @cmpi_logging.trace_method
    def _delete_vg(self, job, poolpath):
        """
        Delete VG. This method is called in context of
        JobManager worker thread.
        """
        pool = self.storage.devicetree.getDeviceByPath(poolpath)
        if not pool:
            raise pywbem.CIMError(pywbem.CIM_ERR_FAILED,
                    "Cannot find VG %s" % (poolpath,))
        if not isinstance(pool, blivet.devices.LVMVolumeGroupDevice):
            raise pywbem.CIMError(pywbem.CIM_ERR_FAILED,
                    "Device %s is not LMI_VGStoragePool" % (poolpath,))

        # finally delete it
        action = blivet.ActionDestroyDevice(pool)
        storage.do_storage_action(self.storage, [action])

        ret = self.Values.DeleteVG.Job_Completed_with_No_Error
        job.finish_method(
                Job.STATE_FINISHED_OK,
                return_value=ret,
                return_type=Job.ReturnValueType.Uint32,
                output_arguments={},
                affected_elements=[],
                error=None)

    @cmpi_logging.trace_method
    def cim_method_deletevg(self, env, object_name,
                            param_pool=None, input_arguments=None,
                            method_name=None):
        """Implements LMI_StorageConfigurationService.DeleteVG()

        Start a job to delete a Volume Group. If 0 is returned, the
        function completed successfully, and no ConcreteJob was required.
        If 4096/0x1000 is returned, a ConcreteJob will be started to
        delete the StoragePool. A reference to the Job is returned in the
        Job parameter.
        """
        self.check_instance(object_name)
        # remember input parameters for job
        if not input_arguments:
            input_arguments = {
                    'Pool': pywbem.CIMProperty(name='Pool',
                            type='reference',
                            value=param_pool),
            }
        if not method_name:
            method_name = "DeleteVG"

        # check the parameters
        pool = self._parse_pool(param_pool)
        if not pool:
            raise pywbem.CIMError(pywbem.CIM_ERR_FAILED,
                    "Parameter Pool is mandatory and must be"
                    " LMI_VGStoragePool.")

        # Schedule the job
        job = Job(
                job_manager=self.job_manager,
                job_name="DELETE VG " + pool.path,
                input_arguments=input_arguments,
                method_name=method_name,
                affected_elements=[param_pool],
                owning_element=self._get_instance_name())
        job.set_execute_action(self._delete_vg,
                job, pool.path)

        # enqueue the job
        self.job_manager.add_job(job)

        outparams = [ pywbem.CIMParameter(
                name='job',
                type='reference',
                value=job.get_name())]
        return (self.Values.DeleteVG\
                .Method_Parameters_Checked___Job_Started, outparams)

    @cmpi_logging.trace_method
    def cim_method_deletestoragepool(self, env, object_name,
                                     param_pool=None):
        """Implements LMI_StorageConfigurationService.DeleteStoragePool()

        Start a job to delete a StoragePool. The freed space is returned
        source StoragePools (indicated by AllocatedFrom StoragePool) or
        back to underlying storage extents. If 0 is returned, the function
        completed successfully, and no ConcreteJob was required. If
        4096/0x1000 is returned, a ConcreteJob will be started to delete
        the StoragePool. A reference to the Job is returned in the Job
        parameter.
        
        Implementation just calls DeleteVG with the same arguments.
        """
        input_arguments = {
                'Pool': pywbem.CIMProperty(name='Pool',
                        type='reference',
                        value=param_pool),
        }
        return self.cim_method_deletevg(env, object_name, param_pool,
                input_arguments, "DeleteStoragePool")

    class Values(ServiceProvider.Values):
        class CreateOrModifyElementFromStoragePool(object):
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
            class ElementType(object):
                Unknown = pywbem.Uint16(0)
                Reserved = pywbem.Uint16(1)
                StorageVolume = pywbem.Uint16(2)
                StorageExtent = pywbem.Uint16(3)
                LogicalDisk = pywbem.Uint16(4)
                ThinlyProvisionedStorageVolume = pywbem.Uint16(5)
                ThinlyProvisionedLogicalDisk = pywbem.Uint16(6)
                # DMTF_Reserved = ..
                # Vendor_Specific = 32768..65535

        class CreateOrModifyLV(object):
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

        class CreateOrModifyVG(object):
            Job_Completed_with_No_Error = pywbem.Uint32(0)
            Not_Supported = pywbem.Uint32(1)
            Unknown = pywbem.Uint32(2)
            Timeout = pywbem.Uint32(3)
            Failed = pywbem.Uint32(4)
            Invalid_Parameter = pywbem.Uint32(5)
            In_Use = pywbem.Uint32(6)
            Method_Parameters_Checked___Job_Started = pywbem.Uint32(4096)
            Size_Not_Supported = pywbem.Uint32(4097)

        class CreateOrModifyStoragePool(object):
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

        class CreateOrModifyElementFromElements(object):
            Completed_with_No_Error = pywbem.Uint32(0)
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
            class ElementType(object):
                Unknown = pywbem.Uint16(0)
                Reserved = pywbem.Uint16(1)
                Storage_Volume = pywbem.Uint16(2)
                Storage_Extent = pywbem.Uint16(3)
                Storage_Pool = pywbem.Uint16(4)
                Logical_Disk = pywbem.Uint16(5)
                ThinlyProvisionedStorageVolume = pywbem.Uint16(6)
                ThinlyProvisionedLogicalDisk = pywbem.Uint16(7)
                # DMTF_Reserved = ..
                # Vendor_Specific = 32768..65535

        class CreateOrModifyMDRAID(object):
            Completed_with_No_Error = pywbem.Uint32(0)
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
            class Level(object):
                RAID0 = pywbem.Uint16(0)
                RAID1 = pywbem.Uint16(1)
                RAID4 = pywbem.Uint16(4)
                RAID5 = pywbem.Uint16(5)
                RAID6 = pywbem.Uint16(6)
                RAID10 = pywbem.Uint16(10)
        class DeleteMDRAID(object):
            Completed_with_No_Error = pywbem.Uint32(0)
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
        class DeleteVG(object):
            Job_Completed_with_No_Error = pywbem.Uint32(0)
            Not_Supported = pywbem.Uint32(1)
            Unknown = pywbem.Uint32(2)
            Timeout = pywbem.Uint32(3)
            Failed = pywbem.Uint32(4)
            Invalid_Parameter = pywbem.Uint32(5)
            In_Use = pywbem.Uint32(6)
            # DMTF_Reserved = ..
            Method_Parameters_Checked___Job_Started = pywbem.Uint32(4096)
            # Method_Reserved = 4097..32767
            # Vendor_Specific = 32768..65535
