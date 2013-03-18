File System Management
======================

Local file systems, both supported and unsupported, are represented by
:ref:`LMI_LocalFileSystem <LMI-LocalFileSystem>` class and its subclasses.

Each :ref:`LMI_LocalFileSystem <LMI-LocalFileSystem>` instance of supported
filesystems have associated one instance of
:ref:`LMI_FileSystemSetting <LMI-FileSystemSetting>` representing its
configuration (e.g. inode size).

Supported filesystems are: ext2, ext3, ext4, xfs, btrfs. Only supported
filesystems can be created! Actual set of supported filesystems can be obtained
from
:ref:`LMI_FileSystemConfigurationCapabilities <LMI-FileSystemConfigurationCapabilities>`
instance associated to
:ref:`LMI_FileSystemConfigurationService <LMI-FileSystemConfigurationService>`.

.. _diagram:

Following instance diagram shows four block devices:

*  ``/dev/sda1`` and ``/dev/sda2`` with btrfs filesystem spanning both these
   devices.
*  ``/dev/sda3``with ext3 filesystem.
* ``/dev/sda4`` with msdos filesystems. The msdos filesystem is unsupported,
  therefore it has no :ref:`LMI_FileSystemSetting <LMI-FileSystemSetting>`
  associated.

.. figure:: pic/fs-instance.svg

.. Note::

   Currently the filesystem support is limited:

   * Filesystems can be only created and deleted, it is not possible to modify
     existing filesystem.
   * There is no way to set specific filesystem options
     when creating one. Simple ``mkfs.<filesystem type>`` is called, without any
     additional parameters.
   * btrfs filesystem can be only created or destroyed. There is currently no
     support for btrfs subvolumes, RAIDs, and dynamic addition or removal of
     block devices.
   * The :ref:`LMI_LocalFileSystem <LMI-LocalFileSystem>` instances do not
     report free and used space on the filesystems.
   
   These limitations will be addressed in future releases.   

Useful methods
--------------

:ref:`LMI_CreateFileSystem <LMI-FileSystemConfigurationService-LMI-CreateFileSystem>`
  Formats a StorageExtent with filesystem of given type. Currently the Goal
  parameter is not used, i.e. no filesystem options can be specified.

Use cases
---------

Create File System
^^^^^^^^^^^^^^^^^^

Use
:ref:`LMI_CreateFileSystem <LMI-FileSystemConfigurationService-LMI-CreateFileSystem>`
method. Following example formats ``/dev/sda3`` with ext3:: 
    
    # Find the /dev/sda3 device
    sda3 = root.CIM_StorageExtent.first_instance(
            Key="DeviceID", Value="/dev/sda3")
    
    # Format it
    (ret, outparams, err) = filesystem_service.LMI_CreateFileSystem(
            FileSystemType = 11, # 11 = EXT3
            InExtents= [sda3.path])

The resulting filesystem is the same as shown in diagram_ above.


Create btrfs File System with two devices
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Use the same
:ref:`LMI_CreateFileSystem <LMI-FileSystemConfigurationService-LMI-CreateFileSystem>`
method as above. Following example formats ``/dev/sda1`` and ``dev/sda2`` as
one btrfs volume::

    # Find the /dev/sda3 device 
   sda1 = root.CIM_StorageExtent.first_instance(
           Key="DeviceID", Value="/dev/sda1")
   sda2 = root.CIM_StorageExtent.first_instance(
           Key="DeviceID", Value="/dev/sda2")
   # Format them
   (ret, outparams, err) = filesystem_service.LMI_CreateFileSystem(
           FileSystemType = 11, # 11 = EXT3
           InExtents= [sda1.path, sda2.path])


The resulting filesystem is the same as shown in diagram_ above.

Delete filesystem
^^^^^^^^^^^^^^^^^

Use
:ref:`LMI_CreateFileSystem <LMI-FileSystemConfigurationService-LMI-CreateFileSystem>`
method::

    sda1 = root.CIM_StorageExtent.first_instance(
            Key="DeviceID", Value="/dev/sda1")
    fs = sda1.first_associator(ResultClass='LMI_LocalFileSystem')
    (ret, outparams, err) = filesystem_service.DeleteFileSystem(
            TheFileSystem = fs.path)

Note that with one btrfs on multiple block devices, the whole btrfs volume is
destroyed.

Future direction
----------------

In future, we might implement:

* Add advanced options to
  :ref:`LMI_CreateFileSystem <LMI-FileSystemConfigurationService-LMI-CreateFileSystem>`

* Allow (some) filesystem modification, e.g. amount of reserved space for root
  user.

* Indications of various events, like filesystem is getting full.

