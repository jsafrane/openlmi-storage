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

MEGABYTE = 1024 * 1024

class TestCreateMDRAID(StorageTestBase):
    """
        Test LMI_StorageConfigurationService.TestCreateMDRAID
        (create only).
    """

    STYLE_GPT = 3
    PARTITION_CLASS = "LMI_GenericDiskPartition"


    def setUp(self):
        """ Find storage service. """
        super(TestCreateMDRAID, self).setUp()
        self.service = self.wbemconnection.EnumerateInstanceNames(
                "LMI_StorageConfigurationService")[0]
        self.part_service = self.wbemconnection.EnumerateInstanceNames(
                "LMI_DiskPartitionConfigurationService")[0]
        self.capabilities = self.wbemconnection.EnumerateInstanceNames(
                "LMI_MDRAIDStorageCapabilities")[0]

    def _create_setting(self, level=None, devices=None):
        """ Create a MDRAIDStorageSetting and return CIMInstance of it."""
        if level is None:
            (retval, outparams) = self.wbemconnection.InvokeMethod(
                    "CreateSetting",
                    self.capabilities)
            self.assertEqual(retval, 0)
            self.assertEqual(len(outparams), 1)

            setting_name = outparams['newsetting']
            setting = self.wbemconnection.GetInstance(setting_name)
            return setting

        # create settign for given RAID level with given devices
        (retval, outparams) = self.wbemconnection.InvokeMethod(
                "CreateMDRAIDStorageSetting",
                self.capabilities,
                Level=pywbem.Uint16(level),
                InExtents=devices)
        self.assertEqual(retval, 0)
        self.assertEqual(len(outparams), 1)

        setting_name = outparams['setting']
        setting = self.wbemconnection.GetInstance(setting_name)
        return setting

    def _create_empty_setting(self):
        """ Create a MDRAIDStorageSetting, remove all redundancy properties
            from it and return it
        ."""
        setting = self._create_setting()

        setting['DataRedundancyGoal'] = pywbem.CIMProperty(
                name='DataRedundancyGoal',
                value=None,
                type='uint16')
        setting['DataRedundancyMax'] = pywbem.CIMProperty(
                name='DataRedundancyMax',
                value=None,
                type='uint16')
        setting['DataRedundancyMin'] = pywbem.CIMProperty(
                name='DataRedundancyMin',
                value=None,
                type='uint16')
        setting['PackageRedundancyGoal'] = pywbem.CIMProperty(
                name='PackageRedundancyGoal',
                value=None,
                type='uint16')
        setting['PackageRedundancyMin'] = pywbem.CIMProperty(
                name='PackageRedundancyMin',
                value=None,
                type='uint16')
        setting['PackageRedundancyMax'] = pywbem.CIMProperty(
                name='PackageRedundancyMax',
                value=None,
                type='uint16')
        setting['ExtentStripeLength'] = pywbem.CIMProperty(
                name='ExtentStripeLength',
                value=None,
                type='uint16')
        setting['ExtentStripeLengthMin'] = pywbem.CIMProperty(
                name='ExtentStripeLengthMin',
                value=None,
                type='uint16')
        setting['ExtentStripeLengthMax'] = pywbem.CIMProperty(
                name='ExtentStripeLengthMax',
                value=None,
                type='uint16')
        setting['NoSinglePointOfFailure'] = pywbem.CIMProperty(
                name='NoSinglePointOfFailure',
                value=None,
                type='boolean')
        setting['ParityLayout'] = pywbem.CIMProperty(
                name='ParityLayout',
                value=None,
                type='uint16')
        self.wbemconnection.ModifyInstance(setting)
        return setting

    def _delete_setting(self, setting_name):
        """ Delete given setting. """
        self.wbemconnection.DeleteInstance(setting_name)

    def _get_extent_size(self, extent_name):
        """ Return size of given disk, in bytes."""
        disk = self.wbemconnection.GetInstance(extent_name)
        return disk['NumberOfBlocks'] * disk['BlockSize']

    def _test_raid_n(self, devices, level,
            data_redundancy, stripe_length, package_redundancy, parity_layout,
            nspof, expected_size, goal=None):
        """
            Create RAID<level> with given devices.
            Then check that it has specified redundancy properties.
            Destroy everything.
        """
        if goal:
            (ret, outparams) = self.invoke_async_method(
                    "CreateOrModifyMDRAID",
                    self.service,
                    int, "theelement",
                    InExtents=devices,
                    Goal=goal)
        else:
            (ret, outparams) = self.invoke_async_method(
                    "CreateOrModifyMDRAID",
                    self.service,
                    int, "theelement",
                    InExtents=devices,
                    Level=pywbem.Uint16(level))
        if len(outparams) == 1:
            # there is no Size returned, Pegasus does not support it yet
            # TODO: remove when pegasus supports embedded objects of unknown
            # types, rhbz#920763
            if outparams.has_key('theelement'):
                raid = self.wbemconnection.GetInstance(outparams['theelement'])
                outparams['size'] = raid['NumberOfBlocks'] * raid['BlockSize']

        self.assertEqual(ret, 0)
        self.assertEqual(len(outparams), 2)
        self.assertAlmostEqual(
                outparams['size'],
                expected_size,
                delta=2 * MEGABYTE)
        raidname = outparams['theelement']
        raid = self.wbemconnection.GetInstance(raidname)
        self.assertNotEqual(raid['UUID'], '')
        self.assertEqual(raid['Level'], level)
        self.assertNotEqual(raid['UUID'], None)
        self.assertEqual(raid['Primordial'], False)

        # check based-on
        basedons = self.wbemconnection.References(
                raidname,
                ResultClass="LMI_MDRAIDBasedOn")
        self.assertEqual(len(basedons), len(devices))
        for basedon in basedons:
            self.assertCIMNameIn(basedon['Antecedent'], devices)
            self.assertCIMNameEquals(basedon['Dependent'], raidname)

        # check setting
        settings = self.wbemconnection.Associators(
                raidname,
                AssocClass="LMI_MDRAIDElementSettingData")
        self.assertEqual(len(settings), 1)
        setting = settings[0]

        self._check_redundancy(raid, setting,
                data_redundancy=data_redundancy,
                stripe_legtht=stripe_length,
                package_redundancy=package_redundancy,
                parity_layout=parity_layout,
                check_parity_layout=True,
                nspof=nspof)

        # delete the raid
        (ret, outparams) = self.invoke_async_method(
                "DeleteMDRAID",
                self.service,
                int,
                TheElement=raidname)
        self.assertEquals(ret, 0)

    def test_create_raid0_level(self):
        """ Test CreateOrModifyMDRAID level 0."""
        partition_size = self._get_extent_size(self.partition_names[0])
        # two devices
        self._test_raid_n(self.partition_names[:2], level=0,
                data_redundancy=1,
                stripe_length=2,
                package_redundancy=0,
                parity_layout=None,
                nspof=False,
                expected_size=partition_size * 2)
        # three devices
        self._test_raid_n(self.partition_names[:3], level=0,
                data_redundancy=1,
                stripe_length=3,
                package_redundancy=0,
                parity_layout=None,
                nspof=False,
                expected_size=partition_size * 3)

    def test_create_raid0_goal(self):
        """ Test CreateOrModifyMDRAID level 0 with Goal."""
        partition_size = self._get_extent_size(self.partition_names[0])
        # two devices
        setting = self._create_setting(0, self.partition_names[:2])
        self._test_raid_n(self.partition_names[:2], level=0,
                data_redundancy=1,
                stripe_length=2,
                package_redundancy=0,
                parity_layout=None,
                nspof=False,
                expected_size=partition_size * 2,
                goal=setting.path)
        self._delete_setting(setting.path)
        # three devices
        setting = self._create_setting(0, self.partition_names[:3])
        self._test_raid_n(self.partition_names[:3], level=0,
                data_redundancy=1,
                stripe_length=3,
                package_redundancy=0,
                parity_layout=None,
                nspof=False,
                expected_size=partition_size * 3,
                goal=setting.path)
        self._delete_setting(setting.path)

    def test_create_raid1_level(self):
        """ Test CreateOrModifyMDRAID level 1."""
        partition_size = self._get_extent_size(self.partition_names[0])

        # two devices
        self._test_raid_n(self.partition_names[:2], level=1,
                data_redundancy=2,
                stripe_length=1,
                package_redundancy=1,
                parity_layout=None,
                nspof=True,
                expected_size=partition_size)
        # three devices
        self._test_raid_n(self.partition_names[:4], level=1,
                data_redundancy=4,
                stripe_length=1,
                package_redundancy=3,
                parity_layout=None,
                nspof=True,
                expected_size=partition_size)

    def test_create_raid1_goal(self):
        """ Test CreateOrModifyMDRAID level 1 with Goal."""
        partition_size = self._get_extent_size(self.partition_names[0])

        # two devices
        setting = self._create_setting(1, self.partition_names[:2])
        self._test_raid_n(self.partition_names[:2], level=1,
                data_redundancy=2,
                stripe_length=1,
                package_redundancy=1,
                parity_layout=None,
                nspof=True,
                expected_size=partition_size,
                goal=setting.path)
        self._delete_setting(setting.path)
        # three devices
        setting = self._create_setting(1, self.partition_names[:4])
        self._test_raid_n(self.partition_names[:4], level=1,
                data_redundancy=4,
                stripe_length=1,
                package_redundancy=3,
                parity_layout=None,
                nspof=True,
                expected_size=partition_size,
                goal=setting.path)
        self._delete_setting(setting.path)

    def test_create_raid4_level(self):
        """ Test CreateOrModifyMDRAID level 4."""
        partition_size = self._get_extent_size(self.partition_names[0])

        # 3 devices
        self._test_raid_n(self.partition_names[:3], level=4,
                data_redundancy=1,
                stripe_length=3,
                package_redundancy=1,
                parity_layout=1,  # non-rotated parity
                nspof=True,
                expected_size=partition_size * 2)
        # 4 devices
        self._test_raid_n(self.partition_names[:4], level=4,
                data_redundancy=1,
                stripe_length=4,
                package_redundancy=1,
                parity_layout=1,  # non-rotated parity
                nspof=True,
                expected_size=partition_size * 3)

    def test_create_raid4_goal(self):
        """ Test CreateOrModifyMDRAID level 4 with Goal."""
        partition_size = self._get_extent_size(self.partition_names[0])

        # 3 devices
        setting = self._create_setting(4, self.partition_names[:3])
        self._test_raid_n(self.partition_names[:3], level=4,
                data_redundancy=1,
                stripe_length=3,
                package_redundancy=1,
                parity_layout=1,  # non-rotated parity
                nspof=True,
                expected_size=partition_size * 2,
                goal=setting.path)
        self._delete_setting(setting.path)
        # 4 devices
        setting = self._create_setting(4, self.partition_names[:4])
        self._test_raid_n(self.partition_names[:4], level=4,
                data_redundancy=1,
                stripe_length=4,
                package_redundancy=1,
                parity_layout=1,  # non-rotated parity
                nspof=True,
                expected_size=partition_size * 3,
                goal=setting.path)
        self._delete_setting(setting.path)

    def test_create_raid5_level(self):
        """ Test CreateOrModifyMDRAID level 5."""
        partition_size = self._get_extent_size(self.partition_names[0])

        # 3 devices
        self._test_raid_n(self.partition_names[:3], level=5,
                data_redundancy=1,
                stripe_length=3,
                package_redundancy=1,
                parity_layout=2,  # rotated parity
                nspof=True,
                expected_size=partition_size * 2)
        # 5 devices
        self._test_raid_n(self.partition_names[:5], level=5,
                data_redundancy=1,
                stripe_length=5,
                package_redundancy=1,
                parity_layout=2,  # rotated parity
                nspof=True,
                expected_size=partition_size * 4)

    def test_create_raid5_goal(self):
        """ Test CreateOrModifyMDRAID level 5 with Goal."""
        partition_size = self._get_extent_size(self.partition_names[0])

        # 3 devices
        setting = self._create_setting(5, self.partition_names[:3])
        self._test_raid_n(self.partition_names[:3], level=5,
                data_redundancy=1,
                stripe_length=3,
                package_redundancy=1,
                parity_layout=2,  # rotated parity
                nspof=True,
                expected_size=partition_size * 2,
                goal=setting.path)
        self._delete_setting(setting.path)
        # 5 devices
        setting = self._create_setting(5, self.partition_names[:5])
        self._test_raid_n(self.partition_names[:5], level=5,
                data_redundancy=1,
                stripe_length=5,
                package_redundancy=1,
                parity_layout=2,  # rotated parity
                nspof=True,
                expected_size=partition_size * 4,
                goal=setting.path)
        self._delete_setting(setting.path)

    def test_create_raid6_level(self):
        """ Test CreateOrModifyMDRAID level 6."""
        partition_size = self._get_extent_size(self.partition_names[0])

        # 4 devices
        self._test_raid_n(self.partition_names[:4], level=6,
                data_redundancy=1,
                stripe_length=4,
                package_redundancy=2,
                parity_layout=2,  # rotated parity
                nspof=True,
                expected_size=partition_size * 2)
        # 5 devices
        self._test_raid_n(self.partition_names[:5], level=6,
                data_redundancy=1,
                stripe_length=5,
                package_redundancy=2,
                parity_layout=2,  # rotated parity
                nspof=True,
                expected_size=partition_size * 3)

    def test_create_raid6_goal(self):
        """ Test CreateOrModifyMDRAID level 6 with Goal."""
        partition_size = self._get_extent_size(self.partition_names[0])

        # 4 devices
        setting = self._create_setting(6, self.partition_names[:4])
        self._test_raid_n(self.partition_names[:4], level=6,
                data_redundancy=1,
                stripe_length=4,
                package_redundancy=2,
                parity_layout=2,  # rotated parity
                nspof=True,
                expected_size=partition_size * 2,
                goal=setting.path)
        self._delete_setting(setting.path)

        # 5 devices
        setting = self._create_setting(6, self.partition_names[:5])
        self._test_raid_n(self.partition_names[:5], level=6,
                data_redundancy=1,
                stripe_length=5,
                package_redundancy=2,
                parity_layout=2,  # rotated parity
                nspof=True,
                expected_size=partition_size * 3,
                goal=setting.path)
        self._delete_setting(setting.path)

    def test_create_raid10_level(self):
        """ Test CreateOrModifyMDRAID level 10."""
        partition_size = self._get_extent_size(self.partition_names[0])

        # two devices
        self._test_raid_n(self.partition_names[:2], level=10,
                data_redundancy=2,
                stripe_length=1,
                package_redundancy=1,
                parity_layout=None,
                nspof=True,
                expected_size=partition_size)
        # 3 devices
        self._test_raid_n(self.partition_names[:3], level=10,
                data_redundancy=2,
                stripe_length=2,
                package_redundancy=1,
                parity_layout=None,
                nspof=True,
                expected_size=partition_size * 1.5)
        # 4 devices
        self._test_raid_n(self.partition_names[:4], level=10,
                data_redundancy=2,
                stripe_length=2,
                package_redundancy=1,
                parity_layout=None,
                nspof=True,
                expected_size=partition_size * 2)
        # 5 devices
        self._test_raid_n(self.partition_names[:5], level=10,
                data_redundancy=2,
                stripe_length=3,
                package_redundancy=1,
                parity_layout=None,
                nspof=True,
                expected_size=partition_size * 2.5)
        # 6 devices
        self._test_raid_n(self.partition_names[:6], level=10,
                data_redundancy=2,
                stripe_length=3,
                package_redundancy=1,
                parity_layout=None,
                nspof=True,
                expected_size=partition_size * 3)

    def test_create_raid10_goal(self):
        """ Test CreateOrModifyMDRAID level 10 with a valid Goal."""
        partition_size = self._get_extent_size(self.partition_names[0])

        # don't test two devices - that's RAID1

        # 3 devices
        setting = self._create_setting(10, self.partition_names[:3])
        self._test_raid_n(self.partition_names[:3], level=10,
                data_redundancy=2,
                stripe_length=2,
                package_redundancy=1,
                parity_layout=None,
                nspof=True,
                expected_size=partition_size * 1.5,
                goal=setting.path)
        self._delete_setting(setting.path)

        # 4 devices
        setting = self._create_setting(10, self.partition_names[:4])
        self._test_raid_n(self.partition_names[:4], level=10,
                data_redundancy=2,
                stripe_length=2,
                package_redundancy=1,
                parity_layout=None,
                nspof=True,
                expected_size=partition_size * 2,
                goal=setting.path)
        self._delete_setting(setting.path)

        # 5 devices
        setting = self._create_setting(10, self.partition_names[:5])
        self._test_raid_n(self.partition_names[:5], level=10,
                data_redundancy=2,
                stripe_length=3,
                package_redundancy=1,
                parity_layout=None,
                nspof=True,
                expected_size=partition_size * 2.5,
                goal=setting.path)
        self._delete_setting(setting.path)

        # 6 devices
        setting = self._create_setting(10, self.partition_names[:6])
        self._test_raid_n(self.partition_names[:6], level=10,
                data_redundancy=2,
                stripe_length=3,
                package_redundancy=1,
                parity_layout=None,
                nspof=True,
                expected_size=partition_size * 3,
                goal=setting.path)
        self._delete_setting(setting.path)

    def test_create_wrong_device_numbers(self):
        """
            Test CreateOrModifyMDRAID with various levels and bad nr. of
            devices.
        """
        # raid 0 with 1 device
        self.assertRaises(pywbem.CIMError, self.wbemconnection.InvokeMethod,
                "CreateOrModifyMDRAID",
                self.service,
                InExtents=self.partition_names[:1],
                Level=pywbem.Uint16(0))

        # raid 1 with 1 device
        self.assertRaises(pywbem.CIMError, self.wbemconnection.InvokeMethod,
                "CreateOrModifyMDRAID",
                self.service,
                InExtents=self.partition_names[:1],
                Level=pywbem.Uint16(1))

        # raid 4 with 1 device
        self.assertRaises(pywbem.CIMError, self.wbemconnection.InvokeMethod,
                "CreateOrModifyMDRAID",
                self.service,
                InExtents=self.partition_names[:1],
                Level=pywbem.Uint16(4))

        # raid 4 with 2 devices
        self.assertRaises(pywbem.CIMError, self.wbemconnection.InvokeMethod,
                "CreateOrModifyMDRAID",
                self.service,
                InExtents=self.partition_names[:2],
                Level=pywbem.Uint16(4))

        # raid 5 with 1 device
        self.assertRaises(pywbem.CIMError, self.wbemconnection.InvokeMethod,
                "CreateOrModifyMDRAID",
                self.service,
                InExtents=self.partition_names[:1],
                Level=pywbem.Uint16(5))

        # raid 5 with 2 devices
        self.assertRaises(pywbem.CIMError, self.wbemconnection.InvokeMethod,
                "CreateOrModifyMDRAID",
                self.service,
                InExtents=self.partition_names[:2],
                Level=pywbem.Uint16(5))

        # raid 6 with 1 device
        self.assertRaises(pywbem.CIMError, self.wbemconnection.InvokeMethod,
                "CreateOrModifyMDRAID",
                self.service,
                InExtents=self.partition_names[:1],
                Level=pywbem.Uint16(6))

        # raid 6 with 2 devices
        self.assertRaises(pywbem.CIMError, self.wbemconnection.InvokeMethod,
                "CreateOrModifyMDRAID",
                self.service,
                InExtents=self.partition_names[:2],
                Level=pywbem.Uint16(6))

        # raid 6 with 3 devices
        self.assertRaises(pywbem.CIMError, self.wbemconnection.InvokeMethod,
                "CreateOrModifyMDRAID",
                self.service,
                InExtents=self.partition_names[:3],
                Level=pywbem.Uint16(6))

        # raid 10 with 1 device
        self.assertRaises(pywbem.CIMError, self.wbemconnection.InvokeMethod,
                "CreateOrModifyMDRAID",
                self.service,
                InExtents=self.partition_names[:1],
                Level=pywbem.Uint16(10))



    def test_create_wrong_goals(self):
        """
            Test CreateOrModifyMDRAID with various wrong goals.
        """
        # unknown goal
        goal = pywbem.CIMInstanceName(
                classname=" LMI_MDRAIDStorageSetting",
                keybindings={
                        'InstanceID' : 'LMI:LMI_MDRAIDStorageSetting:not-existing'
        })
        self.assertRaises(pywbem.CIMError, self.wbemconnection.InvokeMethod,
                "CreateOrModifyMDRAID",
                self.service,
                InExtents=self.partition_names[:2],
                Level=pywbem.Uint16(0),
                Goal=goal)

        # raid1 with wrong data redundancy
        setting = self._create_setting(1, self.partition_names[:2])
        setting['DataRedundancyGoal'] = pywbem.Uint16(3)
        setting['DataRedundancyMin'] = pywbem.Uint16(3)
        setting['DataRedundancyMax'] = pywbem.Uint16(3)
        self.wbemconnection.ModifyInstance(setting)
        self.assertRaises(pywbem.CIMError, self.wbemconnection.InvokeMethod,
                "CreateOrModifyMDRAID",
                self.service,
                InExtents=self.partition_names[:2],
                Goal=setting.path)
        self._delete_setting(setting.path)

        # raid1 with wrong package redundancy
        setting = self._create_setting(1, self.partition_names[:2])
        setting['PackageRedundancyGoal'] = pywbem.Uint16(2)
        setting['PackageRedundancyMin'] = pywbem.Uint16(2)
        setting['PackageRedundancyMax'] = pywbem.Uint16(2)
        self.wbemconnection.ModifyInstance(setting)
        self.assertRaises(pywbem.CIMError, self.wbemconnection.InvokeMethod,
                "CreateOrModifyMDRAID",
                self.service,
                InExtents=self.partition_names[:2],
                Goal=setting.path)
        self._delete_setting(setting.path)

    def test_create_calculate_goals(self):
        """
            Test CreateOrModifyMDRAID with Goal settings, where not all
            properties are set and the implementation must choose the
            best RAID level.
        """
        partition_size = self._get_extent_size(self.partition_names[0])

        # raid1 is selected as default if no properties are set
        setting = self._create_empty_setting()
        self._test_raid_n(self.partition_names[:4], level=1,
                data_redundancy=4,
                stripe_length=1,
                package_redundancy=3,
                parity_layout=None,
                nspof=True,
                expected_size=partition_size * 1,
                goal=setting.path)
        self._delete_setting(setting.path)

        #  ParityLayout set -> use RAID5 (and not RAID6)
        setting = self._create_empty_setting()
        setting['ParityLayout'] = pywbem.Uint16(2)  # Rotated parity
        self.wbemconnection.ModifyInstance(setting)
        self._test_raid_n(self.partition_names[:4], level=5,
                data_redundancy=1,
                stripe_length=4,
                package_redundancy=1,
                parity_layout=2,
                nspof=True,
                expected_size=partition_size * 3,
                goal=setting.path)
        self._delete_setting(setting.path)

        #  ParityLayout set and higher redundancy -> use RAID6
        setting = self._create_empty_setting()
        setting['ParityLayout'] = pywbem.Uint16(2)  # Rotated parity
        setting['PackageRedundancyMin'] = pywbem.Uint16(2)
        self.wbemconnection.ModifyInstance(setting)
        self._test_raid_n(self.partition_names[:4], level=6,
                data_redundancy=1,
                stripe_length=4,
                package_redundancy=2,
                parity_layout=2,
                nspof=True,
                expected_size=partition_size * 2,
                goal=setting.path)
        self._delete_setting(setting.path)

        #  ParityLayout set  -> use RAID4
        setting = self._create_empty_setting()
        setting['ParityLayout'] = pywbem.Uint16(1)  # Non-Rotated parity
        self.wbemconnection.ModifyInstance(setting)
        self._test_raid_n(self.partition_names[:4], level=4,
                data_redundancy=1,
                stripe_length=4,
                package_redundancy=1,
                parity_layout=1,
                nspof=True,
                expected_size=partition_size * 3,
                goal=setting.path)
        self._delete_setting(setting.path)

        #  request higher redundancy -> RAID1 (instead of RAID 4, 5, 6, 10)
        setting = self._create_empty_setting()
        setting['PackageRedundancyMin'] = pywbem.Uint16(1)
        self.wbemconnection.ModifyInstance(setting)
        self._test_raid_n(self.partition_names[:4], level=1,
                data_redundancy=4,
                stripe_length=1,
                package_redundancy=3,
                parity_layout=None,
                nspof=True,
                expected_size=partition_size * 1,
                goal=setting.path)
        self._delete_setting(setting.path)

        #  request higher data and pkg. redundancy -> RAID1 (instead of RAID10)
        setting = self._create_empty_setting()
        setting['PackageRedundancyMin'] = pywbem.Uint16(1)
        setting['DataRedundancyMin'] = pywbem.Uint16(2)
        self.wbemconnection.ModifyInstance(setting)
        self._test_raid_n(self.partition_names[:4], level=1,
                data_redundancy=4,
                stripe_length=1,
                package_redundancy=3,
                parity_layout=None,
                nspof=True,
                expected_size=partition_size * 1,
                goal=setting.path)
        self._delete_setting(setting.path)

        #  request higher data and pkg. redundancy with upper limit -> RAID10 only
        setting = self._create_empty_setting()
        setting['PackageRedundancyMin'] = pywbem.Uint16(1)
        setting['DataRedundancyMin'] = pywbem.Uint16(2)
        setting['DataRedundancyMax'] = pywbem.Uint16(3)
        self.wbemconnection.ModifyInstance(setting)
        self._test_raid_n(self.partition_names[:4], level=10,
                data_redundancy=2,
                stripe_length=2,
                package_redundancy=1,
                parity_layout=None,
                nspof=True,
                expected_size=partition_size * 2,
                goal=setting.path)
        self._delete_setting(setting.path)

        #  request higher redundancy with upper limit -> RAID5 (instead of 6 and 4)
        setting = self._create_empty_setting()
        setting['PackageRedundancyMin'] = pywbem.Uint16(1)
        setting['PackageRedundancyMax'] = pywbem.Uint16(2)
        self.wbemconnection.ModifyInstance(setting)
        self._test_raid_n(self.partition_names[:4], level=5,
                data_redundancy=1,
                stripe_length=4,
                package_redundancy=1,
                parity_layout=2,
                nspof=True,
                expected_size=partition_size * 3,
                goal=setting.path)
        self._delete_setting(setting.path)


if __name__ == '__main__':
    unittest.main()
