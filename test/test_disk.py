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

class TestDisk(StorageTestBase):
    """
        Test basic features of hard disks.
         - it can be enumerated
         - it can be get
         - it cannot be removed
         - it cannot be modified
    """

    DISK_CLASS = "LMI_StorageExtent"

    def _check_name(self, diskname):
        """ Check that CIMInstanceName represents a disk. """
        self.assertEqual(diskname['SystemName'], self.SYSTEM_NAME)
        self.assertEqual(diskname['SystemCreationClassName'], self.SYSTEM_CLASS_NAME)
        self.assertEqual(diskname['CreationClassName'], self.DISK_CLASS)

    def test_enumerate_instances(self):
        """ Test EnumerateInstances on disks and their properties. """
        disks = self.wbemconnection.EnumerateInstances(self.DISK_CLASS)
        disknames = [disk.path for disk in disks]
        self.assertGreater(len(disks), 1)

        # check that all disks were returned
        self.assertCIMNameIn(self.disk_name, disknames)

        # now, check common properties
        for disk in disks:
            if disk['DeviceID'] != self.disk_name['DeviceID']:
                continue

            self.assertEqual(disk['ExtentStripeLength'], 1)
            self.assertEqual(disk['DataRedundancy'], 1)
            self.assertEqual(disk['PackageRedundancy'], 0)
            self.assertEqual(disk['NoSinglePointOfFailure'], False)
            self.assertEqual(disk['IsComposite'], False)
            self.assertEqual(disk['Primordial'], True)

            # TODO: check exact values
            self.assertGreater(disk['NumberOfBlocks'], 0)
            self.assertGreater(disk['ConsumableBlocks'], 0)
            self.assertGreater(disk['BlockSize'], 0)


    def test_enumerate_names(self):
        """ Test EnumerateInstanceNames on disks. """
        disknames = self.wbemconnection.EnumerateInstanceNames(self.DISK_CLASS)
        self.assertGreater(len(disknames), 1)

        self.assertCIMNameIn(self.disk_name, disknames)

        # check that every disk can be get
        for diskname in disknames:
            disk = self.wbemconnection.GetInstance(diskname)
            self.assertIsNotNone(disk)
            if diskname['DeviceID'] == self.disk_name['DeviceID']:
                self._check_name(disk.path)

    def _create_disk_name(self, device_id):
        """ Return CIMInstanceName for given DeviceID."""
        name = pywbem.CIMInstanceName(
                classname=self.DISK_CLASS,
                keybindings={
                        'DeviceID': device_id,
                        'SystemCreationClassName': self.SYSTEM_CLASS_NAME,
                        'SystemName': self.SYSTEM_NAME,
                        'CreationClassName': self.DISK_CLASS})
        return name

    def test_get(self):
        name = self._create_disk_name(self.disk_name['DeviceID'])
        disk = self.wbemconnection.GetInstance(name)
        self.assertIsNotNone(disk)

    def test_remove(self):
        name = self._create_disk_name(self.disk_name['DeviceID'])
        self.assertRaises(pywbem.CIMError,
                self.wbemconnection.DeleteInstance, name)

    def test_modify(self):
        name = self._create_disk_name(self.disk_name['DeviceID'])
        disk = self.wbemconnection.GetInstance(name)
        self.assertRaises(pywbem.CIMError,
                self.wbemconnection.ModifyInstance, disk)

if __name__ == '__main__':
    unittest.main()
