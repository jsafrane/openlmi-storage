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



class TestVGPoolMethods(StorageTestBase):
    """
        Test TestVGPoolMethods methods.
    """

    VG_CLASS = "LMI_VGStoragePool"
    STYLE_EMBR = 4100
    STYLE_MBR = 2
    STYLE_GPT = 3
    PARTITION_CLASS = "LMI_GenericDiskPartition"


    def setUp(self):
        """ Find storage service. """
        super(TestVGPoolMethods, self).setUp()
        self.service = self.wbemconnection.EnumerateInstanceNames(
                "LMI_StorageConfigurationService")[0]
        self.part_service = self.wbemconnection.EnumerateInstanceNames(
                "LMI_DiskPartitionConfigurationService")[0]

        vgname = self._create_vg()
        self.vg = self.wbemconnection.GetInstance(vgname)


    def tearDown(self):
        self._destroy_vg(self.vg.path)
        super(TestVGPoolMethods, self).tearDown()


    def _create_vg(self):
        """
            Create a partition and Volume Group on it and return its
            CIMInstanceName.
        """
        (ret, outparams) = self.invoke_async_method(
                "CreateOrModifyVG",
                self.service,
                int, 'Pool',
                InExtents=self.partition_names[:1],
                ElementName='tstName')
        self.assertEqual(ret, 0)
        return outparams['Pool']

    def _destroy_vg(self, vgname):
        """ Destroy VG and its partition. """
        self.invoke_async_method("DeleteVG", self.service, int, None,
                Pool=vgname)

    def test_supported_sizes(self):
        """ Test GetSupportedSizes() """
        (retval, _) = self.wbemconnection.InvokeMethod(
                "GetSupportedSizes",
                self.vg.path)
        self.assertEqual(retval, 2)

    def test_supported_range_noparam(self):
        """ Test GetSupportedSizeRange without any parameters. """
        (retval, outparams) = self.wbemconnection.InvokeMethod(
                "GetSupportedSizeRange",
                self.vg.path)
        self.assertEqual(retval, 0)
        self.assertEqual(len(outparams), 3)

        self.assertEqual(
                outparams['minimumvolumesize'], self.vg['ExtentSize'])
        self.assertEqual(
                outparams['maximumvolumesize'],
                self.vg['RemainingExtents'] * self.vg['ExtentSize'])
        self.assertEqual(
                outparams['volumesizedivisor'], self.vg['ExtentSize'])

    def test_supported_range_elementtype(self):
        """ Test GetSupportedSizeRange with ElementType parameter. """
        (retval, outparams) = self.wbemconnection.InvokeMethod(
                "GetSupportedSizeRange",
                self.vg.path,
                ElementType=pywbem.Uint16(4))  # logical disk - OK

        self.assertEqual(retval, 0)
        self.assertEqual(len(outparams), 3)

        self.assertEqual(
                outparams['minimumvolumesize'], self.vg['ExtentSize'])
        self.assertEqual(
                outparams['maximumvolumesize'],
                self.vg['RemainingExtents'] * self.vg['ExtentSize'])
        self.assertEqual(
                outparams['volumesizedivisor'], self.vg['ExtentSize'])


        (retval, outparams) = self.wbemconnection.InvokeMethod(
                "GetSupportedSizeRange",
                self.vg.path,
                ElementType=pywbem.Uint16(2))  # storage pool - fail
        self.assertEqual(retval, 3)  # invalid element type

        (retval, outparams) = self.wbemconnection.InvokeMethod(
                "GetSupportedSizeRange",
                self.vg.path,
                ElementType=pywbem.Uint16(3))  # storage volume - fail
        self.assertEqual(retval, 3)  # invalid element type

        (retval, outparams) = self.wbemconnection.InvokeMethod(
                "GetSupportedSizeRange",
                self.vg.path,
                ElementType=pywbem.Uint16(5))  # thin storage volume - fail
        self.assertEqual(retval, 3)  # invalid element type

        (retval, outparams) = self.wbemconnection.InvokeMethod(
                "GetSupportedSizeRange",
                self.vg.path,
                ElementType=pywbem.Uint16(6))  # thin logical disk - fail
        self.assertEqual(retval, 3)  # invalid element type

        # TODO: check goal

if __name__ == '__main__':
    unittest.main()
