#!/usr/bin/python
# -*- Coding:utf-8 -*-
#
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

from test_base import StorageTestBase
import unittest
import pywbem

class TestCreatePartition(StorageTestBase):
    """
        Test LMI_DiskPartitionConfigurationService.LMI_CreateOrModifyPartition
        with different parameters.
        
        As consequence, it tests also:
        - LMI_DiskPartitionConfigurationCapabilities.CreateSetting.
        - Setting modify / delete.
        - DeleteInstance on partitions.
        - SetPartitionStyle.
    """

    MBR_CLASS = "LMI_DiskPartition"
    GPT_CLASS = "LMI_GenericDiskPartition"

    STYLE_EMBR = 4100
    STYLE_MBR = 2
    STYLE_GPT = 3

    def setUp(self):
        """ Prepare for test."""
        super(TestCreatePartition, self).setUp()
        self.service = self.wbemconnection.EnumerateInstanceNames(
                "LMI_DiskPartitionConfigurationService")[0]
        self.storage_service = self.wbemconnection.EnumerateInstanceNames(
                "LMI_StorageConfigurationService")[0]

    def _check_name(self, partname, classname):
        """ Check that CIMInstanceName represents a partition. """
        self.assertEqual(partname['SystemName'], self.SYSTEM_NAME)
        self.assertEqual(partname['SystemCreationClassName'], self.SYSTEM_CLASS_NAME)
        self.assertEqual(partname['CreationClassName'], classname)

    def _get_capabilities_name(self, style):
        """
            Return CIMInstanceName with partition capabilities representing
            given partition style.
        """
        if style == self.STYLE_EMBR:
            style_name = "EMBR"
        elif style == self.STYLE_MBR:
            style_name = "MBR"
        elif style == self.STYLE_GPT:
            style_name = "GPT"

        return pywbem.CIMInstanceName(
                classname="LMI_DiskPartitionConfigurationCapabilities",
                keybindings={
                        'InstanceID': "LMI:LMI_DiskPartitionConfigurationCapabilities:" + style_name
                })

    def _create_setting(self, style):
        """
            Create new partition configuration setting instance of given
            PartitionStyle and return its CIMInstance.
        """
        capabilities = self._get_capabilities_name(style)
        if not capabilities:
            return None
        (retval, outparams) = self.wbemconnection.InvokeMethod(
                "CreateSetting", capabilities)
        self.assertEqual(retval, 0)
        self.assertEqual(len(outparams), 1)
        return self.wbemconnection.GetInstance(outparams['setting'])

    def _delete_setting(self, setting):
        """ Delete Setting with given CIMInstanceName."""
        self.wbemconnection.DeleteInstance(setting)


    def _set_partition_style(self, disk_name, style):
        """ Create partition table on self.disk_name with given style."""
        caps = self._get_capabilities_name(style)
        (retval, outparams) = self.wbemconnection.InvokeMethod(
                "SetPartitionStyle",
                self.service,
                Extent=disk_name,
                PartitionStyle=caps)
        self.assertEqual(retval, 0)
        self.assertDictEqual(outparams, {})

    def _find_extended_partition(self, diskname):
        """
            Return CIMInstanceName of extended partition on the device.
        """
        partitions = self.wbemconnection.Associators(
                diskname,
                AssocClass="LMI_PartitionBasedOn")
        for p in partitions:
            if p['PartitionType'] == 2:  # extended
                return p.path
        return None


    def test_err_no_params(self):
        """ Try LMI_CreateOrModifyPartition with no parameters -> error."""
        self.assertRaises(pywbem.CIMError, self.wbemconnection.InvokeMethod,
                "LMI_CreateOrModifyPartition",
                self.service)

    def test_err_wrong_goal(self):
        """ Try LMI_CreateOrModifyPartition with unknown goal InstanceId -> error."""
        goal = pywbem.CIMInstanceName(
                classname="LMI_DiskPartitionConfigurationSetting",
                keybindings={'InstanceID':'not_existing'})
        self.assertRaises(pywbem.CIMError, self.wbemconnection.InvokeMethod,
                "LMI_CreateOrModifyPartition",
                self.service,
                extent=self.disk_name,
                Goal=goal)

    def test_err_wrong_extent(self):
        """ Try LMI_CreateOrModifyPartition with unknown extent DeviceID -> error."""
        disk_name = pywbem.CIMInstanceName(
                classname=self.DISK_CLASS,
                keybindings={
                        'DeviceID': '/dev/does/not/exist',
                        'SystemCreationClassName': self.SYSTEM_CLASS_NAME,
                        'SystemName': self.SYSTEM_NAME,
                        'CreationClassName': self.DISK_CLASS})
        self.assertRaises(pywbem.CIMError, self.wbemconnection.InvokeMethod,
                "LMI_CreateOrModifyPartition",
                self.service,
                extent=disk_name)

    def test_err_wrong_goal_style_gpt(self):
        """
            Try LMI_CreateOrModifyPartition with goal not corresponding to
            GPT partition table style.-> error.
        """
        # create GPT partition table
        self._set_partition_style(self.disk_name, self.STYLE_GPT)

        # try Hidden
        goal = self._create_setting(self.STYLE_GPT)
        goal['Hidden'] = True
        self.wbemconnection.ModifyInstance(goal)
        self.assertRaises(pywbem.CIMError, self.invoke_async_method,
                "LMI_CreateOrModifyPartition",
                self.service,
                int, 'partition',
                extent=self.disk_name,
                Goal=goal.path)
        self._delete_setting(goal.path)

        # try Extended partition
        goal = self._create_setting(self.STYLE_GPT)
        goal['PartitionType'] = pywbem.Uint16(2)
        self.wbemconnection.ModifyInstance(goal)
        self.assertRaises(pywbem.CIMError, self.invoke_async_method,
                "LMI_CreateOrModifyPartition",
                self.service,
                int, 'partition',
                extent=self.disk_name,
                Goal=goal.path)

        # try logical partition
        goal['PartitionType'] = pywbem.Uint16(3)
        self.wbemconnection.ModifyInstance(goal)
        self.assertRaises(pywbem.CIMError, self.invoke_async_method,
                "LMI_CreateOrModifyPartition",
                self.service,
                int, 'partition',
                extent=self.disk_name,
                Goal=goal.path)

        self._delete_setting(goal.path)

    def test_gpt_maximum(self):
        """
            Try LMI_CreateOrModifyPartition on GPT partition table without
            any size on a disk.
        """
        self._test_gpt_maximum(self.disk_name)


    # TODO: don't skip when #927219 is fixed                )
    @unittest.skip("Cannot create partitions on RAID because of bug #927219")
    def test_gpt_maximum_mdraid(self):
        """
            Try LMI_CreateOrModifyPartition on GPT partition table without
            any size on a MD RAID.
        """
        raidname = self._create_mdraid(self.partition_names[:3], 0)
        self._test_gpt_maximum(raidname)
        self._delete_mdraid(raidname)

    def _test_gpt_maximum(self, disk_name):
        """
            Try LMI_CreateOrModifyPartition on GPT partition table without
            any size on given device.
        """
        # create GPT partition table
        self._set_partition_style(disk_name, self.STYLE_GPT)
        goal = self._create_setting(self.STYLE_GPT)
        (retval, outparams) = self.invoke_async_method(
                "LMI_CreateOrModifyPartition",
                self.service,
                int, 'partition',
                extent=disk_name,
                # TODO: uncomment when #891861 is fixed
                # Goal=goal.path,
                )
        self.assertEqual(retval, 0)
        self.assertIn("partition", outparams)

        partition = outparams['partition']
        disk_instance = self.wbemconnection.GetInstance(disk_name)
        partition_instance = self.wbemconnection.GetInstance(partition)
        self.assertEqual(partition_instance['Primordial'], False)

        self.assertAlmostEqual(
                disk_instance['NumberOfBlocks'],
                partition_instance['NumberOfBlocks'],
                delta=2 * 1024 * 10)  # 10 megabytes

        # second call must fail
        self.assertRaises(pywbem.CIMError, self.invoke_async_method,
                "LMI_CreateOrModifyPartition",
                self.service,
                int, 'partition',
                extent=disk_name,
                # TODO: uncomment when #891861 is fixed
                # Goal=goal.path,
                )

        # check based on
        basedons = self.wbemconnection.References(
                partition,
                ResultClass="LMI_PartitionBasedOn")
        self.assertEqual(len(basedons), 1)
        basedon = basedons[0]
        self.assertCIMNameEquals(basedon['Antecedent'], disk_name)
        self.assertCIMNameEquals(basedon['Dependent'], partition)
        self.assertAlmostEqual(
                basedon['StartingAddress'], 0, delta=2 * 1024 * 2)  # 2 megabytes
        self.assertAlmostEqual(
                basedon['EndingAddress'],
                disk_instance['NumberOfBlocks'],
                delta=4 * 1024 * 2)  # 4 megabytes

        self._delete_setting(goal.path)
        (ret, outparams) = self.invoke_async_method(
                "LMI_DeletePartition",
                self.service,
                int, None,
                Partition=partition)
        self.assertEquals(ret, 0)

    def test_mbr_maximum(self):
        """
            Try LMI_CreateOrModifyPartition on MBR partition table without
            any size on a disk.
        """
        self._test_mbr_maximum(self.disk_name)

    # TODO: don't skip when #927219 is fixed                )
    @unittest.skip("Cannot create partitions on RAID because of bug #927219")
    def test_mbr_maximum_mdraid(self):
        """
            Try LMI_CreateOrModifyPartition on MBR partition table without
            any size on a MD RAID.
        """
        raidname = self._create_mdraid(self.partition_names[:3], 0)
        self._test_mbr_maximum(raidname)
        self._delete_mdraid(raidname)

    def _test_mbr_maximum(self, disk_name):
        """
            Try LMI_CreateOrModifyPartition on MBR partition table without
            any size.
        """
        # create MBR partition table
        self._set_partition_style(disk_name, self.STYLE_MBR)
        goal = self._create_setting(self.STYLE_MBR)
        (retval, outparams) = self.invoke_async_method(
                "LMI_CreateOrModifyPartition",
                self.service,
                int, 'partition',
                extent=disk_name,
                # TODO: uncomment when #891861 is fixed
                # Goal=goal.path,
                )
        self.assertEqual(retval, 0)
        self.assertIn("partition", outparams)

        partition = outparams['partition']
        disk_instance = self.wbemconnection.GetInstance(disk_name)
        partition_instance = self.wbemconnection.GetInstance(partition)
        self.assertEqual(partition_instance['Primordial'], False)

        self.assertAlmostEqual(
                disk_instance['NumberOfBlocks'],
                partition_instance['NumberOfBlocks'],
                delta=2 * 1024 * 10)  # 10 megabytes

        # check based on
        basedons = self.wbemconnection.References(
                partition,
                ResultClass="LMI_PartitionBasedOn")
        self.assertEqual(len(basedons), 1)
        basedon = basedons[0]
        self.assertCIMNameEquals(basedon['Antecedent'], disk_name)
        self.assertCIMNameEquals(basedon['Dependent'], partition)
        self.assertAlmostEqual(
                basedon['StartingAddress'], 0, delta=2 * 1024 * 2)  # 2 megabytes
        self.assertAlmostEqual(
                basedon['EndingAddress'],
                disk_instance['NumberOfBlocks'],
                delta=4 * 1024 * 2)  # 4 megabytes

        # second call must fail
        self.assertRaises(pywbem.CIMError, self.invoke_async_method,
                "LMI_CreateOrModifyPartition",
                self.service,
                int, 'partition',
                extent=disk_name,
                # TODO: uncomment when #891861 is fixed
                # Goal=goal.path,
                )

        self._delete_setting(goal.path)
        (ret, outparams) = self.invoke_async_method(
                "LMI_DeletePartition",
                self.service,
                int, None,
                Partition=partition)
        self.assertEquals(ret, 0)

    def test_gpt_sizes(self):
        """
            Try LMI_CreateOrModifyPartition on GPT partition table with
            sizes on a disk.
        """
        self._test_gpt_sizes(self.disk_name)

    def _test_gpt_sizes(self, disk_name):
        """
            Try LMI_CreateOrModifyPartition on GPT partition table with
            sizes on given device.
        """
        partition_size = 10 * 1024 * 1024  # 10 MB
        partition_count = 10
        partitions = []
        # create GPT partition table
        self._set_partition_style(disk_name, self.STYLE_GPT)
        goal = self._create_setting(self.STYLE_GPT)

        for _ in xrange(partition_count):
            (retval, outparams) = self.invoke_async_method(
                    "LMI_CreateOrModifyPartition",
                    self.service,
                    int, 'partition',
                    extent=disk_name,
                    size=pywbem.Uint64(partition_size),
                    # TODO: uncomment when #891861 is fixed
                    # Goal=goal.path,
                    )
            self.assertEqual(retval, 0)
            self.assertIn("partition", outparams)

            partition = outparams['partition']
            partitions.append(partition)

            partition_instance = self.wbemconnection.GetInstance(partition)
            self.assertEqual(
                    partition_size / 512,
                    partition_instance['NumberOfBlocks'])

            # check based on
            basedons = self.wbemconnection.References(
                    partition,
                    ResultClass="LMI_PartitionBasedOn")
            self.assertEqual(len(basedons), 1)
            basedon = basedons[0]
            self.assertCIMNameEquals(basedon['Antecedent'], disk_name)
            self.assertCIMNameEquals(basedon['Dependent'], partition)

        self._delete_setting(goal.path)

        for partition in partitions:
            (ret, outparams) = self.invoke_async_method(
                    "LMI_DeletePartition",
                    self.service,
                    int, None,
                    Partition=partition)
            self.assertEquals(ret, 0)

    def test_mbr_sizes(self):
        """
            Try LMI_CreateOrModifyPartition on MBR partition table with
            sizes on a disk.
        """
        self._test_mbr_sizes(self.disk_name)

    def _test_mbr_sizes(self, disk_name):
        """
            Try CreateOrModifyPartition on MBR partition table with
            sizes. It should automatically create an extended partition!
        """
        partition_size = 1024 * 1024 * 10  # 10 MB
        partition_count = 10
        partitions = []
        # create MBR partition table
        self._set_partition_style(disk_name, self.STYLE_MBR)

        for i in xrange(partition_count):
            (retval, outparams) = self.invoke_async_method(
                    "LMI_CreateOrModifyPartition",
                    self.service,
                    int, 'partition',
                    extent=disk_name,
                    size=pywbem.Uint64(partition_size),
                    )
            self.assertEqual(retval, 0)
            self.assertIn("partition", outparams)

            partition = outparams['partition']
            partitions.append(partition)

            partition_instance = self.wbemconnection.GetInstance(partition)
            self.assertEqual(
                    partition_size / 512,
                    partition_instance['NumberOfBlocks'])

            # check based on
            basedons = self.wbemconnection.References(
                    partition,
                    ResultClass="LMI_PartitionBasedOn")
            self.assertEqual(len(basedons), 1)
            basedon = basedons[0]
            if i < 3:
                self.assertCIMNameEquals(basedon['Antecedent'], disk_name)
            else:
                if i == 3:
                    # find the extended partition
                    extended_partition = self._find_extended_partition(disk_name)
                # it's based on the extended partition!
                self.assertNotEqual(basedon['Antecedent'], extended_partition)
            self.assertCIMNameEquals(basedon['Dependent'], partition)

        partitions.reverse()
        for partition in partitions:
            (ret, outparams) = self.invoke_async_method(
                    "LMI_DeletePartition",
                    self.service,
                    int, None,
                    Partition=partition)
            self.assertEquals(ret, 0)
        (ret, outparams) = self.invoke_async_method(
                "LMI_DeletePartition",
                self.service,
                int, None,
                Partition=extended_partition)
        self.assertEquals(ret, 0)

        # remove the extended partition, created automatically

    # TODO: don't skip when #891861 is fixed                )
    @unittest.skip("Cannot create extended partitions because of bug #891861")
    def test_logical_sizes(self):
        """
            Try LMI_CreateOrModifyPartition on MBR partition table with
            start/end addresses and logical partitions.
        """
        partition_size = 1024 * 1024 * 10  # 10 MB
        partition_count = 10
        partitions = []

        # create MBR partition table and one huge Extended partition
        self._set_partition_style(self.disk_name, self.STYLE_MBR)
        goal = self._create_setting(self.STYLE_MBR)
        goal['PartitionType'] = pywbem.Uint16(2)  # Extended
        self.wbemconnection.ModifyInstance(goal)
        (retval, outparams) = self.wbemconnection.InvokeMethod(
                "LMI_CreateOrModifyPartition",
                self.service,
                extent=self.disk_name,
                Goal=goal.path)
        self.assertEqual(retval, 0)
        self.assertIn("partition", outparams)
        extended_partition = outparams['partition']

        # create partition_count logical partitions on it
        goal['PartitionType'] = pywbem.Uint16(3)  # Logical
        self.wbemconnection.ModifyInstance(goal)
        for _ in xrange(partition_count):
            (retval, outparams) = self.wbemconnection.InvokeMethod(
                    "LMI_CreateOrModifyPartition",
                    self.service,
                    extent=extended_partition,
                    Size=pywbem.Uint64(partition_size),
                    Goal=goal.path)
            self.assertEqual(retval, 0)
            self.assertIn("partition", outparams)

            partition = outparams['partition']
            partitions.append(partition)

            partition_instance = self.wbemconnection.GetInstance(partition)
            self.assertEqual(
                    partition_size / 512,
                    partition_instance['NumberOfBlocks'])

            # check based on
            basedons = self.wbemconnection.References(
                    partition,
                    ResultClass="LMI_PartitionBasedOn")
            self.assertEqual(len(basedons), 1)
            basedon = basedons[0]
            self.assertNotEqual(basedon['Antecedent'], extended_partition)
            self.assertEqual(basedon['Dependent'], partition)

        self._delete_setting(goal.path)

        partitions.reverse()
        for partition in partitions:
            (ret, outparams) = self.invoke_async_method(
                    "LMI_DeletePartition",
                    self.service,
                    int, None,
                    Partition=partition)
            self.assertEquals(ret, 0)
        (ret, outparams) = self.invoke_async_method(
                "LMI_DeletePartition",
                self.service,
                int, None,
                Partition=extended_partition)
        self.assertEquals(ret, 0)

    # TODO: test partition modification

if __name__ == '__main__':
    unittest.main()
