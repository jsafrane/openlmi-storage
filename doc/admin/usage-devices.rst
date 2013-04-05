Device management
=================

The API manages all block devices in machine's local /dev/ directory, i.e. also
remote disks (iSCSI, FcoE, ...), as long as there is appropriate device in
local /dev/.


Device hierarchy
----------------

Each block device is represented by instance of ``CIM_StorageExtent`` or its
subclasss.

.. figure:: generated/extent-inherit.svg

``LMI_StorageExtent`` represents all devices, which do not have any specific
``CIM_StorageExtent`` subclass.

Each volume group is represented by ``LMI_VGStoragePool``.

.. figure:: generated/pool-inherit.svg

Instances of ``LMI_VGStoragePool``, ``CIM_StorageExtent`` and its subclasses
compose an oriented graph of devices on the system. Devices are connected with
these associations or their subclasses:

- ``LMI_BasedOn`` and is subclasses associates a block device to all devices,
  on which it directly depends on, for example a partition is associated to a
  disk, on which it resides, and MD RAID is associated to all underlying
  devices, which compose the RAID.

- ``LMI_AssociatedComponentExtent`` associates volume groups with its physical
  extents.

- ``LMI_LVAllocatedFromStoragePool`` associates logical volumes to their
  volume groups.

.. figure:: pic/raid-lvm-simple.svg

  Example of two logical volumes allocated from volume group created on top of
  MD RAID with three devices.

Device manipulation
-------------------
Block devices cannot be directly manipulated using intrinsic or extrinsic
methods of ``CIM_StorageExtent`` or ``LMI_VGStoragePool``.

Please use appropriate ``ConfigurationService`` to create, modify or delete devices
or volume groups:

* :doc:`usage-partitioning`.

* :doc:`usage-raid`.

* :doc:`usage-lvm`.

* :doc:`usage-fs`.

 .. note::

   Previous releases allowed to use ``DeleteInstance`` intrinsic method to
   delete various ``LMI_StorageExtents``. This method is now deprecated and will
   be removed from future releases of OpenLMI-Storage.
   
   The reason is that  ``DeleteInstance`` cannot be asynchronous and could
   block the whole provider for long time.

