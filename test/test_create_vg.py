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

from test_base import StorageTestBase, short_tests_only
import unittest
import pywbem


MEGABYTE = 1024 * 1024

class TestCreateVG(StorageTestBase):
    """
        Test LMI_StorageConfigurationService.CreateOrModifyVG
        (create only).
    """

    VG_CLASS = "LMI_VGStoragePool"
    STYLE_EMBR = 4100
    STYLE_MBR = 2
    STYLE_GPT = 3
    PARTITION_CLASS = "LMI_GenericDiskPartition"


    def setUp(self):
        """ Find storage service. """
        super(TestCreateVG, self).setUp()
        self.service = self.wbemconnection.EnumerateInstanceNames(
                "LMI_StorageConfigurationService")[0]
        self.part_service = self.wbemconnection.EnumerateInstanceNames(
                "LMI_DiskPartitionConfigurationService")[0]
        self.capabilities = self.wbemconnection.EnumerateInstanceNames(
                "LMI_VGStorageCapabilities")[0]

    def _get_disk_size(self, devicename):
        """ Return size of given device, in bytes."""
        disk = self.wbemconnection.GetInstance(devicename)
        return disk['NumberOfBlocks'] * disk['BlockSize']

    def test_create_1pv(self):
        """ Test CreateOrModifyVG with one PV."""
        (ret, outparams) = self.invoke_async_method(
                "CreateOrModifyVG",
                self.service,
                int, "pool",
                InExtents=self.partition_names[:1],
                ElementName='tstName')
        if len(outparams) == 1:
            # there is no Size returned, Pegasus does not support it yet
            # TODO: remove when pegasus supports embedded objects of unknown
            # types, rhbz#920763
            if outparams.has_key('pool'):
                vg = self.wbemconnection.GetInstance(outparams['pool'])
                outparams['size'] = vg['TotalExtents'] * vg['ExtentSize']

        self.assertEqual(ret, 0)
        self.assertEqual(len(outparams), 2)
        self.assertAlmostEqual(
                outparams['size'],
                self._get_disk_size(self.partition_names[0]),
                delta=4 * MEGABYTE)
        vgname = outparams['pool']
        vg = self.wbemconnection.GetInstance(vgname)
        self.assertEqual(vg['TotalManagedSpace'], outparams['size'])
        self.assertEqual(vg['PoolID'], 'tstName')
        self.assertEqual(vg['ElementName'], 'tstName')
        self.assertNotEqual(vg['UUID'], '')
        self.assertNotEqual(vg['UUID'], None)
        self.assertEqual(vg['ExtentSize'], 4 * MEGABYTE)
        self.assertEqual(
                vg['ExtentSize'] * vg['TotalExtents'],
                vg['TotalManagedSpace'])
        self.assertEqual(
                vg['ExtentSize'] * vg['RemainingExtents'],
                vg['RemainingManagedSpace'])

        (ret, outparams) = self.invoke_async_method(
                'DeleteVG',
                self.service,
                int, None,
                Pool=vgname)
        self.assertEquals(ret, 0)

    @unittest.skipIf(short_tests_only(), "Running short tests only.")
    def test_create_10pv(self):
        """ Test CreateOrModifyVG with 10 PVs."""
        (ret, outparams) = self.invoke_async_method(
                "CreateOrModifyVG",
                self.service,
                int, "pool",
                InExtents=self.partition_names[:10])
        if len(outparams) == 1:
            # there is no Size returned, Pegasus does not support it yet
            # TODO: remove when pegasus supports embedded objects of unknown
            # types, rhbz#920763
            if outparams.has_key('pool'):
                vg = self.wbemconnection.GetInstance(outparams['pool'])
                outparams['size'] = vg['TotalExtents'] * vg['ExtentSize']

        self.assertEqual(ret, 0)
        self.assertEqual(len(outparams), 2)
        self.assertAlmostEqual(
                outparams['size'],
                self._get_disk_size(self.partition_names[0]) * 10,
                delta=30 * MEGABYTE)
        vg = outparams['pool']

        (ret, outparams) = self.invoke_async_method(
                'DeleteVG',
                self.service,
                int, None,
                Pool=vg)
        self.assertEquals(ret, 0)

    @unittest.skipIf(short_tests_only(), "Running short tests only.")
    def test_create_10vg(self):
        """ Test CreateOrModifyVG with 10 VGs."""
        vgs = []
        for part in self.partition_names[:10]:
            (ret, outparams) = self.invoke_async_method(
                    "CreateOrModifyVG",
                    self.service,
                    int, "pool",
                    InExtents=[part])
            if len(outparams) == 1:
                # there is no Size returned, Pegasus does not support it yet
                # TODO: remove when pegasus supports embedded objects of unknown
                # types, rhbz#920763
                if outparams.has_key('pool'):
                    vg = self.wbemconnection.GetInstance(outparams['pool'])
                    outparams['size'] = vg['TotalExtents'] * vg['ExtentSize']
            self.assertEqual(ret, 0)
            self.assertEqual(len(outparams), 2)
            vg = outparams['pool']
            vgs.append(vg)

        for vg in vgs:
            (ret, outparams) = self.invoke_async_method(
                    'DeleteVG',
                    self.service,
                    int, None,
                    Pool=vg)
            self.assertEquals(ret, 0)

    def test_create_unknown_setting(self):
        """ Test CreateOrModifyVG with non-existing setting."""
        goal = pywbem.CIMInstanceName(
                classname=" LMI_VGStorageSetting",
                keybindings={
                        'InstanceID' : 'LMI:LMI_VGStorageSetting:not-existing'
                })
        self.assertRaises(pywbem.CIMError, self.wbemconnection.InvokeMethod,
                    "CreateOrModifyVG",
                    self.service,
                    InExtents=self.partition_names[:1],
                    Goal=goal
                    )

    def test_create_wrong_setting_class(self):
        """ Test CreateOrModifyVG with non-existing setting."""
        goal = pywbem.CIMInstanceName(
                classname=" LMI_LVStorageSetting",
                keybindings={
                        'InstanceID' : 'LMI:LMI_LVStorageSetting:not-existing'
                })
        self.assertRaises(pywbem.CIMError, self.wbemconnection.InvokeMethod,
                    "CreateOrModifyVG",
                    self.service,
                    InExtents=self.partition_names[:1],
                    Goal=goal
                    )

    def _create_setting(self):
        """ Create a VGStorageSetting and return CIMInstance of it."""
        (retval, outparams) = self.wbemconnection.InvokeMethod(
                "CreateSetting",
                self.capabilities)
        self.assertEqual(retval, 0)
        self.assertEqual(len(outparams), 1)

        setting_name = outparams['newsetting']
        setting = self.wbemconnection.GetInstance(setting_name)
        return setting

    def _delete_setting(self, setting_name):
        """ Delete given setting. """
        self.wbemconnection.DeleteInstance(setting_name)

    def test_create_default_setting(self):
        """
            Test CreateOrModifyVG with default setting from 
            VGStroageCapabilities.CreateSetting.
        """
        goal = self._create_setting()

        (ret, outparams) = self.invoke_async_method(
                "CreateOrModifyVG",
                self.service,
                int, "pool",
                InExtents=self.partition_names[:1],
                Goal=goal.path)
        if len(outparams) == 1:
            # there is no Size returned, Pegasus does not support it yet
            # TODO: remove when pegasus supports embedded objects of unknown
            # types, rhbz#920763
            if outparams.has_key('pool'):
                vg = self.wbemconnection.GetInstance(outparams['pool'])
                outparams['size'] = vg['TotalExtents'] * vg['ExtentSize']

        self.assertEqual(ret, 0)
        self.assertEqual(len(outparams), 2)
        self.assertAlmostEqual(
                outparams['size'],
                self._get_disk_size(self.partition_names[0]),
                delta=4 * MEGABYTE)
        vgname = outparams['pool']
        vg = self.wbemconnection.GetInstance(vgname)
        self.assertEqual(vg['TotalManagedSpace'], outparams['size'])
        self.assertNotEqual(vg['ElementName'], '')
        self.assertNotEqual(vg['ElementName'], None)
        self.assertNotEqual(vg['UUID'], '')
        self.assertNotEqual(vg['UUID'], None)
        self.assertEqual(vg['ExtentSize'], 4 * MEGABYTE)
        self.assertEqual(
                vg['ExtentSize'] * vg['TotalExtents'],
                vg['TotalManagedSpace'])
        self.assertEqual(
                vg['ExtentSize'] * vg['RemainingExtents'],
                vg['RemainingManagedSpace'])

        # check it has a setting associated
        settings = self.wbemconnection.Associators(
                vgname,
                AssocClass="LMI_VGElementSettingData")
        self.assertEqual(len(settings), 1)
        setting = settings[0]
        self.assertEqual(setting['ExtentSize'], goal['ExtentSize'])
        self.assertEqual(setting['DataRedundancyGoal'], goal['DataRedundancyGoal'])
        self.assertLessEqual(setting['DataRedundancyMax'], goal['DataRedundancyMax'])
        self.assertGreaterEqual(setting['DataRedundancyMin'], goal['DataRedundancyMin'])
        self.assertEqual(setting['ExtentStripeLength'], goal['ExtentStripeLength'])
        self.assertLessEqual(setting['ExtentStripeLengthMax'], goal['ExtentStripeLengthMax'])
        self.assertGreaterEqual(setting['ExtentStripeLengthMin'], goal['ExtentStripeLengthMin'])
        self.assertEqual(setting['NoSinglePointOfFailure'], goal['NoSinglePointOfFailure'])
        self.assertEqual(setting['PackageRedundancyGoal'], goal['PackageRedundancyGoal'])
        self.assertLessEqual(setting['PackageRedundancyMax'], goal['PackageRedundancyMax'])
        self.assertGreaterEqual(setting['PackageRedundancyMin'], goal['PackageRedundancyMin'])

        (ret, outparams) = self.invoke_async_method(
                'DeleteVG',
                self.service,
                int, None,
                Pool=vgname)
        self.assertEquals(ret, 0)
        self._delete_setting(goal.path)

    def test_create_setting_1m(self):
        """
            Test CreateOrModifyVG with 2MiB ExtentSize.
        """
        goal = self._create_setting()
        goal['ExtentSize'] = pywbem.Uint64(MEGABYTE)
        self.wbemconnection.ModifyInstance(goal)

        (ret, outparams) = self.invoke_async_method(
                "CreateOrModifyVG",
                self.service,
                int, "pool",
                InExtents=self.partition_names[:1],
                Goal=goal.path)
        if len(outparams) == 1:
            # there is no Size returned, Pegasus does not support it yet
            # TODO: remove when pegasus supports embedded objects of unknown
            # types, rhbz#920763
            if outparams.has_key('pool'):
                vg = self.wbemconnection.GetInstance(outparams['pool'])
                outparams['size'] = vg['TotalExtents'] * vg['ExtentSize']

        self.assertEqual(ret, 0)
        self.assertEqual(len(outparams), 2)
        self.assertAlmostEqual(
                outparams['size'],
                self._get_disk_size(self.partition_names[0]),
                delta=4 * MEGABYTE)
        vgname = outparams['pool']
        vg = self.wbemconnection.GetInstance(vgname)
        self.assertEqual(vg['TotalManagedSpace'], outparams['size'])
        self.assertNotEqual(vg['ElementName'], '')
        self.assertNotEqual(vg['ElementName'], None)
        self.assertNotEqual(vg['UUID'], '')
        self.assertNotEqual(vg['UUID'], None)
        self.assertEqual(vg['ExtentSize'], MEGABYTE)
        self.assertEqual(
                vg['ExtentSize'] * vg['TotalExtents'],
                vg['TotalManagedSpace'])
        self.assertEqual(
                vg['ExtentSize'] * vg['RemainingExtents'],
                vg['RemainingManagedSpace'])

        # check it has a setting associated
        settings = self.wbemconnection.Associators(
                vgname,
                AssocClass="LMI_VGElementSettingData")
        self.assertEqual(len(settings), 1)
        setting = settings[0]
        self.assertEqual(setting['ExtentSize'], goal['ExtentSize'])
        self.assertEqual(setting['DataRedundancyGoal'], goal['DataRedundancyGoal'])
        self.assertLessEqual(setting['DataRedundancyMax'], goal['DataRedundancyMax'])
        self.assertGreaterEqual(setting['DataRedundancyMin'], goal['DataRedundancyMin'])
        self.assertEqual(setting['ExtentStripeLength'], goal['ExtentStripeLength'])
        self.assertLessEqual(setting['ExtentStripeLengthMax'], goal['ExtentStripeLengthMax'])
        self.assertGreaterEqual(setting['ExtentStripeLengthMin'], goal['ExtentStripeLengthMin'])
        self.assertEqual(setting['NoSinglePointOfFailure'], goal['NoSinglePointOfFailure'])
        self.assertEqual(setting['PackageRedundancyGoal'], goal['PackageRedundancyGoal'])
        self.assertLessEqual(setting['PackageRedundancyMax'], goal['PackageRedundancyMax'])
        self.assertGreaterEqual(setting['PackageRedundancyMin'], goal['PackageRedundancyMin'])

        (ret, outparams) = self.invoke_async_method(
                'DeleteVG',
                self.service,
                int, None,
                Pool=vgname)
        self.assertEquals(ret, 0)
        self._delete_setting(goal.path)

    def test_create_setting_64k(self):
        """
            Test CreateOrModifyVG with 64k ExtentSize.
        """
        goal = self._create_setting()
        goal['ExtentSize'] = pywbem.Uint64(64 * 1024)
        self.assertRaises(pywbem.CIMError, self.wbemconnection.ModifyInstance,
                goal)
        self._delete_setting(goal.path)

if __name__ == '__main__':
    unittest.main()
