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
import subprocess
import tempfile
import os

EXT2 = 11  # LMI_FileSystemSetting.ActualFileSystemType

class TestOverwriteUnused(StorageTestBase):
    """
        Test that 'unused' devices can be overwritten in various ways.  
    """

    def setUp(self):
        super(TestOverwriteUnused, self).setUp()
        self.service = self.wbemconnection.EnumerateInstanceNames(
                "LMI_FileSystemConfigurationService")[0]
        self.storage_service = self.wbemconnection.EnumerateInstanceNames(
                "LMI_StorageConfigurationService")[0]
        # create a directory to mount stuff
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        os.rmdir(self.tmpdir)


    def _prepare_nonfs_partitions(self):
        """
        Prepare some metadata on partitions.
        :returns: tuple (array of integers, array of integers).
        Both arrays are indexes into self.partition_names, indicating
        used partitions (=the first array) and unused
        partitions(=the second array).
        The used partitions are not allowed to be deleted or overwritten.
        """
        # partition 0+1: stopped RAID = unused
        subprocess.check_call(['mdadm', '-C', '-l', '0', '-n', '2',
                '/dev/md/second', self.partitions[0], self.partitions[1]])
        subprocess.check_call(['mdadm', '-S', '/dev/md/second'])

        # partition 2+3: running RAID = used
        subprocess.check_call(['mdadm', '-C', '-l', '0', '-n', '2',
                '/dev/md/first', self.partitions[2], self.partitions[3]])

        # partition 4: unused PV = unused
        subprocess.check_call(['pvcreate', self.partitions[4]])
        # partition 5: used PV = used
        subprocess.check_call(['pvcreate', self.partitions[5]])
        subprocess.check_call(['vgcreate', 'tstVG', self.partitions[5]])

        # TODO: add LUKS
        self.restart_cim()
        return ([2, 3, 5], [0, 1, 4])


    def _clear_nonfs_partitions(self):
        """
        Clear all data created by _prepare_nonfs.
        """
        subprocess.call(['mdadm', '-S', '/dev/md/first'])
        subprocess.call(['pvremove', self.partitions[4]])
        subprocess.call(['vgremove', 'tstVG'])
        subprocess.call(['pvremove', self.partitions[5]])
        for part in self.partitions:
            subprocess.call(['wipefs', '-a', '--force', part])

        self.restart_cim()

    def _prepare_fs_partitions(self, for_delete):
        """
        Prepare some filesystems on partitions.
        :param for_delete: ``boolean`` True, if the filesystems will be deleted.
        I.e. btrfs on two devices deletes formats on both devices, while
        formatting one device as different format leaves the other formatted
        as btrfs.
        
        :returns: tuple (array of integers, array of integers).
        Both arrays are indexes into self.partition_names, indicating
        used partitions (=the first array) and unused
        partitions(=the second array).
        The used partitions are not allowed to be deleted or overwritten.
        """
        # create a directory to mount stuff
        os.mkdir(self.tmpdir + '/1')
        os.mkdir(self.tmpdir + '/2')

        # partition 0+1: unmounted BTRFS = unused
        # This does not work because of bug #948302
        # TODO: uncomment when 948302 is fixed
        # subprocess.check_call(['mkfs.btrfs', '-f',
        #        self.partitions[0], self.partitions[1]])

        # partition 2+3: mounted BTRFS = used
        subprocess.check_call(['mkfs.btrfs', '-f',
                self.partitions[2], self.partitions[3]])
        subprocess.check_call(['mount', self.partitions[2], self.tmpdir + '/1'])

        # partition 4: unmounted ext3 = unused
        subprocess.check_call(['mkfs.ext3', self.partitions[4]])
        # partition 5: mounted ext3 = used
        subprocess.check_call(['mkfs.ext3', self.partitions[5]])
        subprocess.check_call(['mount', self.partitions[5], self.tmpdir + '/2'])
        # partition 6: unmounted btrfs = unused
        subprocess.check_call(['mkfs.btrfs', '-f', self.partitions[6]])

        self.restart_cim()

        if for_delete:
            # partition[1] was erased by removing format from partitions[0],
            # there is no format on it
            return ([2, 3, 5], [4, 6])
        else:
            return ([2, 3, 5], [4, 6])


    def _clear_fs_partitions(self):
        """
        Clear all data created by _prepare_fs.
        """
        subprocess.call(['umount', self.tmpdir + '/2'])
        subprocess.call(['umount', self.tmpdir + '/1'])
        for part in self.partitions:
            subprocess.call(['wipefs', '-a', '--force', part])
        os.rmdir(self.tmpdir + '/2')
        os.rmdir(self.tmpdir + '/1')
        self.restart_cim()

    def _test_create_fs(self, used, unused):
        """ Test LMI_CreateFileSystem both on used and unused devices."""
        for i in unused + used:
            device_name = self.partition_names[i]

            try:
                # Try to reformat the partition and see what happens
                (ret, _outparams) = self.invoke_async_method(
                        "LMI_CreateFileSystem",
                        self.service,
                        int, None,
                        InExtents=[device_name, ],
                        FileSystemType=pywbem.Uint16(EXT2))
            except pywbem.CIMError, err:
                if i not in unused:
                    pass  # we expected the error
                else:
                    print "Got unexpected exception:", err
                ret = 1

            if i in unused:
                # LMI_CreateFileSystem must have succeeded
                self.assertEquals(ret, 0)
            else:
                # LMI_CreateFileSystem must have failed
                self.assertNotEquals(ret, 0)


    def _test_delete_fs(self, used, unused):
        """ Test DeleteFileSystem both on used and unused devices."""
        for i in unused + used:
            device_name = self.partition_names[i]
            # find associated format
            formats = self.wbemconnection.AssociatorNames(device_name,
                    AssocClass='LMI_ResidesOnExtent')
            self.assertEquals(len(formats), 1)
            fmt = formats[0]
            try:
                # Try to delete the format
                (ret, _outparams) = self.invoke_async_method(
                        "DeleteFileSystem",
                        self.service,
                        int, None,
                        TheFileSystem=fmt)
            except pywbem.CIMError, err:
                if i not in unused:
                    pass  # we expected the error
                else:
                    print "Got unexpected exception:", err
                ret = 1

            if i in unused:
                # DeleteFileSystem must have succeeded
                self.assertEquals(ret, 0)
            else:
                # DeleteFileSystem must have failed
                self.assertNotEquals(ret, 0)

    def _test_create_vg(self, used, unused):
        """ Test CreateOrModifyVG both on used and unused devices."""
        for i in unused + used:
            device_name = self.partition_names[i]
            try:
                # Try to create a VG on the device
                (ret, outparams) = self.invoke_async_method(
                        "CreateOrModifyVG",
                        self.storage_service,
                        int, 'pool',
                        InExtents=[device_name, ],
                        ElementName='tst')
            except pywbem.CIMError, err:
                if i not in unused:
                    pass  # we expected the error
                else:
                    print "Got unexpected exception:", err

                ret = 1

            if i in unused:
                # CreateOrModifyVG must have succeeded
                self.assertEquals(ret, 0)
                # delete the VG
                poolname = outparams['pool']
                (ret, _outparams) = self.invoke_async_method(
                        "DeleteVG",
                        self.storage_service,
                        int, None,
                        Pool=poolname)
                self.assertEquals(ret, 0)
            else:
                # CreateOrModifyVG must have failed
                self.assertNotEquals(ret, 0)

    def _test_create_raid(self, used, unused):
        """ Test CreateOrModifyMDRAID both on used and unused devices."""
        for i in unused + used:
            # We need at least two devices for MD RAID, take some unused
            # as the second and make sure it's not the tested one.
            second = unused[0]
            if second == i:
                second = unused[1]

            device_name = self.partition_names[i]
            second_name = self.partition_names[second]
            try:
                # Try to create a RAID on the device
                (ret, outparams) = self.invoke_async_method(
                        "CreateOrModifyMDRAID",
                        self.storage_service,
                        int, 'theelement',
                        InExtents=[second_name, device_name, ],
                        Level=pywbem.Uint16(0),
                        ElementName='tst')
            except pywbem.CIMError, err:
                if i not in unused:
                    pass  # we expected the error
                else:
                    print "Got unexpected exception:", err

                ret = 1

            if i in unused:
                # CreateOrModifyMDRAID must have succeeded
                self.assertEquals(ret, 0)
                # delete the raid
                raidname = outparams['theelement']
                (ret, _outparams) = self.invoke_async_method(
                        "DeleteMDRAID",
                        self.storage_service,
                        int, None,
                        TheElement=raidname)
                self.assertEquals(ret, 0)
            else:
                # CreateOrModifyMDRAID must have failed
                self.assertNotEquals(ret, 0)

    def _test_nonfs(self, test_function):
        """
        Prepare various non-fs formats on devices and call test_function on
        them.
        """
        try:
            (used, unused) = self._prepare_nonfs_partitions()
            test_function(used, unused)
        finally:
            self._clear_nonfs_partitions()

    def _test_fs(self, test_function, for_delete):
        """
        Prepare various fs formats on devices and call test_function on
        them.
        """
        try:
            (used, unused) = self._prepare_fs_partitions(for_delete)
            test_function(used, unused)
        finally:
            self._clear_fs_partitions()

    def test_create_fs_nonfs(self):
        """Test LMI_CreateFileSystem on non-fs formats."""
        self._test_nonfs(self._test_create_fs)

    def test_delete_fs_nonfs(self):
        """Test DeleteFileSystem on non-fs formats."""
        self._test_nonfs(self._test_delete_fs)

    def test_create_vg_nonfs(self):
        """Test CreateOrModifyVG on non-fs formats."""
        self._test_nonfs(self._test_create_vg)

    def test_create_raid_nonfs(self):
        """Test CreateOrModifyMDRAID on non-fs formats."""
        self._test_nonfs(self._test_create_raid)

    def test_create_fs_fs(self):
        """Test LMI_CreateFileSystem on fs formats."""
        self._test_fs(self._test_create_fs, False)

    def test_delete_fs_fs(self):
        """Test DeleteFileSystem on fs formats."""
        self._test_fs(self._test_delete_fs, True)

    def test_create_vg_fs(self):
        """Test CreateOrModifyVG on fs formats."""
        self._test_fs(self._test_create_vg, False)

    def test_create_raid_fs(self):
        """Test CreateOrModifyMDRAID on fs formats."""
        self._test_fs(self._test_create_raid, False)

    def test_delete_raid(self):
        """ Test DeleteMDRAID on used and unused MD RAID device."""
        try:
            os.mkdir(self.tmpdir + "/second")

            # first: unused
            subprocess.check_call(['mdadm', '-C', '-l', '0', '-n', '2',
                    '/dev/md/first', self.partitions[0], self.partitions[1]])

            # second: with mounted fs = used
            subprocess.check_call(['mdadm', '-C', '-l', '0', '-n', '2',
                    '/dev/md/second', self.partitions[2], self.partitions[3]])
            subprocess.check_call(['mkfs.ext3', '/dev/md/second'])
            subprocess.check_call(['mount', '/dev/md/second',
                    self.tmpdir + "/second"])

            # third: part of VG = used
            subprocess.check_call(['mdadm', '-C', '-l', '0', '-n', '2',
                    '/dev/md/third', self.partitions[4], self.partitions[5]])
            subprocess.check_call(['pvcreate', '/dev/md/third'])
            subprocess.check_call(['vgcreate', 'thirdVG', '/dev/md/third'])
            self.restart_cim()

            used = ['/dev/md/third', '/dev/md/second']
            unused = ['/dev/md/first']

            for devname in unused + used:
                device = self.wbemconnection.ExecQuery("WQL",
                        'SELECT * FROM LMI_StorageExtent WHERE Name="%s"'
                        % (devname,))[0]
                try:
                    # Try to create a VG on the device
                    (ret, _outparams) = self.invoke_async_method(
                            "DeleteMDRAID",
                            self.storage_service,
                            int, None,
                            TheElement=device.path)
                except pywbem.CIMError, err:
                    if devname not in unused:
                        pass  # we expected the error
                    else:
                        print "Got unexpected exception:", err
                    ret = 1

                if devname in unused:
                    # DeleteMDRAID must have succeeded
                    self.assertEquals(ret, 0)
                else:
                    # DeleteMDRAID must have failed
                    self.assertNotEquals(ret, 0)
        finally:
            subprocess.call(['vgremove', 'thirdVG'])
            subprocess.call(['umount', '/dev/md/second'])
            subprocess.call(['mdadm', '-S', '/dev/md/first'])
            subprocess.call(['mdadm', '-S', '/dev/md/second'])
            subprocess.call(['mdadm', '-S', '/dev/md/third'])
            os.rmdir(self.tmpdir + "/second")
            for part in self.partitions:
                subprocess.call(['wipefs', '-a', '--force', part])
            self.restart_cim()


    def test_delete_vg(self):
        """ Test DeleteVG on used and unused MD RAID device."""
        try:
            os.mkdir(self.tmpdir + "/second")

            for part in self.partitions:
                subprocess.check_call(['pvcreate', part])

            # VGfirst: unused
            subprocess.check_call(['vgcreate', 'VGfirst',
                    self.partitions[0], self.partitions[1]])

            # VGsecond: mounted = used
            subprocess.check_call(['vgcreate', 'VGsecond',
                    self.partitions[2], self.partitions[3]])
            subprocess.check_call(['lvcreate', '-n', 'LVsecond', '-l',
                    '100%VG', 'VGsecond'])
            subprocess.check_call(['mkfs.ext3', '/dev/VGsecond/LVsecond'])
            subprocess.check_call(['mount', '/dev/VGsecond/LVsecond',
                    self.tmpdir + "/second"])

            # VGthird: has LV = used
            subprocess.check_call(['vgcreate', 'VGthird',
                    self.partitions[4], self.partitions[5]])
            subprocess.check_call(['lvcreate', '-n', 'LVthird', '-l',
                    '100%VG', 'VGthird'])
            self.restart_cim()

            used = ['VGsecond', 'VGthird']
            unused = ['VGfirst']

            for poolname in unused + used:
                pool = self.wbemconnection.ExecQuery("WQL",
                        'SELECT * FROM LMI_VGStoragePool WHERE ElementName="%s"'
                        % (poolname,))[0]
                try:
                    # Try to create a VG on the device
                    (ret, _outparams) = self.invoke_async_method(
                            "DeleteVG",
                            self.storage_service,
                            int, None,
                            Pool=pool.path)
                except pywbem.CIMError, err:
                    if poolname not in unused:
                        pass  # we expected the error
                    else:
                        print "Got unexpected exception:", err
                    ret = 1

                if poolname in unused:
                    # DeleteVG must have succeeded
                    self.assertEquals(ret, 0)
                else:
                    # DeleteVG must have failed
                    self.assertNotEquals(ret, 0)
        finally:
            subprocess.call(['lvremove', '-f', '/dev/VGthird/LVthird'])
            subprocess.call(['vgremove', 'VGthird'])
            subprocess.call(['umount', '/dev/VGsecond/LVsecond'])
            subprocess.call(['lvremove', '-f', '/dev/VGsecond/LVsecond'])
            subprocess.call(['vgremove', 'VGsecond'])
            subprocess.call(['vgremove', 'VGfirst'])
            os.rmdir(self.tmpdir + "/second")
            for part in self.partitions:
                subprocess.call(['wipefs', '-a', '--force', part])
            self.restart_cim()

    def test_delete_lv(self):
        """ Test LV on used and unused MD RAID device."""
        try:
            os.mkdir(self.tmpdir + "/second")

            for part in self.partitions:
                subprocess.check_call(['pvcreate', part])

            subprocess.check_call(['vgcreate', 'VG',
                    self.partitions[0], self.partitions[1]])

            # LVfirst - unused
            subprocess.check_call(['lvcreate', '-n', 'LVfirst', '-l',
                    '50%VG', 'VG'])

            # LVsecond - mounted = used
            subprocess.check_call(['lvcreate', '-n', 'LVsecond', '-l',
                    '50%VG', 'VG'])
            subprocess.check_call(['mkfs.ext3', '/dev/VG/LVsecond'])
            subprocess.check_call(['mount', '/dev/VG/LVsecond',
                    self.tmpdir + "/second"])
            self.restart_cim()

            used = ['LVsecond']
            unused = ['LVfirst']

            for devname in unused + used:
                device = self.wbemconnection.ExecQuery("WQL",
                        'SELECT * FROM LMI_LVStorageExtent WHERE ElementName="%s"'
                        % (devname,))[0]
                try:
                    # Try to create a VG on the device
                    (ret, _outparams) = self.invoke_async_method(
                            "DeleteLV",
                            self.storage_service,
                            int, None,
                            TheElement=device.path)
                except pywbem.CIMError, err:
                    if devname not in unused:
                        pass  # we expected the error
                    else:
                        print "Got unexpected exception:", err
                    ret = 1

                if devname in unused:
                    # DeleteLV must have succeeded
                    self.assertEquals(ret, 0)
                else:
                    # DeleteLV must have failed
                    self.assertNotEquals(ret, 0)
        finally:
            subprocess.call(['umount', '/dev/VG/LVsecond'])
            subprocess.call(['lvremove', '-f', '/dev/VG/LVsecond'])
            subprocess.call(['lvremove', '-f', '/dev/VG/LVfirst'])
            subprocess.call(['vgremove', 'VG'])
            os.rmdir(self.tmpdir + "/second")
            for part in self.partitions:
                subprocess.call(['wipefs', '-a', '--force', part])
            self.restart_cim()

if __name__ == '__main__':
    unittest.main()
