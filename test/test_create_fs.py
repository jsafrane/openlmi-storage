#!/usr/bin/python
# -*- Coding:utf-8 -*-
#
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

from test_base import StorageTestBase
import unittest
import pywbem

class TestCreateFS(StorageTestBase):
    """
        Test LMI_FileSystemConfigurationService.LMI_CreateFileSystem
        with different parameters.
    """

    def setUp(self):
        """ Find disk partition service. """
        super(TestCreateFS, self).setUp()
        self.service = self.wbemconnection.EnumerateInstanceNames(
                "LMI_FileSystemConfigurationService")[0]

    def test_no_params(self):
        """ Try LMI_CreateFileSystem with no parameters"""
        # InExtents = None -> error
        self.assertRaises(pywbem.CIMError, self.wbemconnection.InvokeMethod,
                "LMI_CreateFileSystem",
                self.service)

    def test_create_no_fstype(self):
        """ Test LMI_CreateFileSystem with no FileSystemType parameter."""
        # Goal = None -> error
        self.assertRaises(pywbem.CIMError, self.wbemconnection.InvokeMethod,
                "LMI_CreateFileSystem",
                self.service,
                InExtents=[self.partition_names[0], ])

    def _check_fs(self, fs_name, fs_type, fs_type_name):
        # check the LMI_LocalFileSystem properties
        fs = self.wbemconnection.GetInstance(fs_name)
        self.assertEquals(fs['FileSystemType'], fs_type_name)
        self.assertEquals(fs['PersistenceType'], 2)

        # check the LMI_FileSystemSetting properties
        fs_settings = self.wbemconnection.Associators(fs_name,
                AssocClass="LMI_FileSystemElementSettingData")
        self.assertEquals(len(fs_settings), 1)
        fs_setting = fs_settings[0]
        self.assertEquals(fs_setting['ActualFileSystemType'], fs_type)
        self.assertEquals(fs_setting['ChangeableType'], 3)  # transient
        # TODO: check NumberOfObjects property

    def test_create_ext2(self):
        """ Test LMI_CreateFileSystem with ext2."""
        EXT2 = 11  # LMI_FileSystemSetting.ActualFileSystemType
        (ret, outparams) = self.wbemconnection.InvokeMethod(
                "LMI_CreateFileSystem",
                self.service,
                InExtents=[self.partition_names[0], ],
                FileSystemType=pywbem.Uint16(EXT2))
        if ret == self.JOB_CREATED:
            (ret, outparams) = self.finish_job(
                    outparams['job'], int, "theelement")
        self.assertEquals(ret, 0)
        self.assertIn("theelement", outparams)
        self._check_fs(outparams['theelement'], EXT2, 'ext2')
        self._delete_fs(outparams['theelement'], [self.partition_names[0]])

    def test_create_ext3(self):
        """ Test LMI_CreateFileSystem with ext3."""
        EXT3 = 12  # LMI_FileSystemSetting.ActualFileSystemType
        (ret, outparams) = self.wbemconnection.InvokeMethod(
                "LMI_CreateFileSystem",
                self.service,
                InExtents=[self.partition_names[0], ],
                FileSystemType=pywbem.Uint16(EXT3))
        if ret == self.JOB_CREATED:
            (ret, outparams) = self.finish_job(
                    outparams['job'], int, "theelement")
        self.assertEquals(ret, 0)
        self.assertIn("theelement", outparams)
        self._check_fs(outparams['theelement'], EXT3, 'ext3')
        self._delete_fs(outparams['theelement'], [self.partition_names[0]])

    def test_create_ext4(self):
        """ Test LMI_CreateFileSystem with ext4."""
        EXT4 = 32769  # LMI_FileSystemSetting.ActualFileSystemType
        (ret, outparams) = self.wbemconnection.InvokeMethod(
                "LMI_CreateFileSystem",
                self.service,
                InExtents=[self.partition_names[0], ],
                FileSystemType=pywbem.Uint16(EXT4))
        if ret == self.JOB_CREATED:
            (ret, outparams) = self.finish_job(
                    outparams['job'], int, "theelement")
        self.assertEquals(ret, 0)
        self.assertIn("theelement", outparams)
        self._check_fs(outparams['theelement'], EXT4, 'ext4')
        self._delete_fs(outparams['theelement'], [self.partition_names[0]])

    def test_create_xfs(self):
        """ Test LMI_CreateFileSystem with xfs."""
        XFS = 9  # LMI_FileSystemSetting.ActualFileSystemType
        (ret, outparams) = self.wbemconnection.InvokeMethod(
                "LMI_CreateFileSystem",
                self.service,
                InExtents=[self.partition_names[0], ],
                FileSystemType=pywbem.Uint16(XFS))
        if ret == self.JOB_CREATED:
            (ret, outparams) = self.finish_job(
                    outparams['job'], int, "theelement")
        self.assertEquals(ret, 0)
        self.assertIn("theelement", outparams)
        self._check_fs(outparams['theelement'], XFS, 'xfs')
        self._delete_fs(outparams['theelement'], [self.partition_names[0]])

    def test_create_btrfs(self):
        """ Test LMI_CreateFileSystem with btrfs."""
        BTRFS = 32770  # LMI_FileSystemSetting.ActualFileSystemType
        (ret, outparams) = self.wbemconnection.InvokeMethod(
                "LMI_CreateFileSystem",
                self.service,
                InExtents=[self.partition_names[0], ],
                FileSystemType=pywbem.Uint16(BTRFS))
        if ret == self.JOB_CREATED:
            (ret, outparams) = self.finish_job(
                    outparams['job'], int, "theelement")
        self.assertEquals(ret, 0)
        self.assertIn("theelement", outparams)
        self._check_fs(outparams['theelement'], BTRFS, 'btrfs')
        self._delete_fs(outparams['theelement'], [self.partition_names[0]])

    def test_create_btrfs_2dev(self):
        """ Test LMI_CreateFileSystem with btrfs on 2 devices."""
        BTRFS = 32770  # LMI_FileSystemSetting.ActualFileSystemType
        (ret, outparams) = self.wbemconnection.InvokeMethod(
                "LMI_CreateFileSystem",
                self.service,
                InExtents=[self.partition_names[1], self.partition_names[2]],
                FileSystemType=pywbem.Uint16(BTRFS))
        if ret == self.JOB_CREATED:
            (ret, outparams) = self.finish_job(
                    outparams['job'], int, "theelement")
        self.assertEquals(ret, 0)
        self.assertIn("theelement", outparams)
        self._check_fs(outparams['theelement'], BTRFS, 'btrfs')
        self._delete_fs(outparams['theelement'],
                [self.partition_names[1], self.partition_names[2]])

    def _delete_fs(self, fsname, devicenames):
        """Delete given FS."""
        (ret, outparams) = self.wbemconnection.InvokeMethod(
                "DeleteFileSystem",
                self.service,
                TheFileSystem=fsname)
        if ret == self.JOB_CREATED:
            (ret, outparams) = self.finish_job(
                    outparams['job'], int)
        self.assertEquals(ret, 0)

        for devicename in devicenames:
            filesystems = self.wbemconnection.AssociatorNames(
                    devicename,
                    AssocClass="LMI_ResidesOnExtent")
            self.assertEquals(len(filesystems), 0)



if __name__ == '__main__':
    unittest.main()
