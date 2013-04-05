Partitioning
============

Disks or any other block devices with partition tables have their
:ref:`LMI_StorageExtent <LMI-StorageExtent>` or its subclass associated to
:ref:`LMI_DiskPartitionConfigurationCapabilities <LMI-DiskPartitionConfigurationCapabilities>`
using :ref:`LMI_InstalledPartitionTable <LMI-InstalledPartitionTable>`.

A GPT partition present on a block device are represented as
:ref:`LMI_GenericDiskPartition <LMI-GenericDiskPartition>`.

A MS-DOS partition present on a block device are represented as
:ref:`LMI_DiskPartition <LMI-DiskPartition>`.

Both MS-DOS and GPT partitions are associated to the parent device using
:ref:`LMI_PartitionBasedOn <LMI-PartitionBasedOn>`. This BasedOn association
contains also start and end sectors of the partitions. Note that logical
partitions are associated with the extended partition where they are located,
see the diagram below.

.. _diagram:

Following instance diagram shows ``/dev/sda`` disk with MS-DOS partition table
and:

* 3 primary partitions

* 1 extended partition

  * 2 logical partitions

.. figure:: pic/partition-instance.svg

Especially note that the extended partition ``/dev/sda4`` *contains* an extended
partition table and all logical partitions are based on this extended
partition. This is for compatibility with SMI-S and also it better illustrates
physical composition of the partitions on the disk.


However, to create a partition on the device, applications can use both
``/dev/sda`` or ``/dev/sda4`` as value of ``Extent`` parameter in
:ref:`LMI_CreateOrModifyPartition <LMI-DiskPartitionConfigurationService-LMI-CreateOrModifyPartition>`,
call.


Useful methods
--------------

:ref:`LMI_CreateOrModifyPartition <LMI-DiskPartitionConfigurationService-LMI-CreateOrModifyPartition>`
  Creates a partition on a device with GPT or MS-DOS partition table.
  Currently no special setting can be set and the method automatically creates
  extended and logical partitions when the primary partition table is getting
  full.

:ref:`SetPartitionStyle <LMI-DiskPartitionConfigurationService-SetPartitionStyle>`
  Creates partition table on a device of requested size. If the size is not
  specified, the largest possible partition is created.

:ref:`FindPartitionLocation <LMI-DiskPartitionConfigurationCapabilities-FindPartitionLocation>`
  Finds start and end sector where a partition would be created and returns
  size of the partition.

:ref:`LMI_DeletePartition <LMI-DiskPartitionConfigurationService-LMI-DeletePartition>`
  Destroys a partition.

The partitioning support is basic and has several limitations. Currently it is
not possible to explicitly set partition position. OpenLMI chooses the best
available free space for requested partitions. Typically, on empty disks, the
partitions are created one after another.

Currently it is not possible to explicitly create extended or logical
partitions, these are created automatically when there are too much primary
partitions:

* If there are less than 3 primary partitions on the device, *primary*
  partition is created.

* If there are exactly 3 primary partitions on the device and one of them
  extended, *primary* partition is created.

* If there are exactly 3 primary partitions on the device and none of them
  extended, one *extended* partition is created over the largest continuous
  unpartitioned space on the device. Then, requested *logical* partition is
  created on it. Therefore, single call to
  :ref:`LMI_CreateOrModifyPartition <LMI-DiskPartitionConfigurationService-LMI-CreateOrModifyPartition>`
  can create one extended and one logical partition.

* If there is extended partition present on the device and there are 4 primary
  partitions, a *logical* partition is created.

Use cases
---------


List supported partition table types
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Currently GPT and MS-DOS partition tables are supported. More types can be added
later. Enumerate instances of
:ref:`LMI_DiskPartitionConfigurationCapabilities <LMI-DiskPartitionConfigurationCapabilities>`
class to get list of all of them, together with their basic properties like
partition table size and maximum number of partitions::
    
    part_styles = root.LMI_DiskPartitionConfigurationCapabilities.instances()
    for style in part_styles:
        print style.Caption
        print "Partition table size:", style.PartitionTableSize, "block(s)"

Create partition table
^^^^^^^^^^^^^^^^^^^^^^

Use
:ref:`SetPartitionStyle <LMI-DiskPartitionConfigurationService-SetPartitionStyle>`
method.

Sample code to create GPT partition table on ``/dev/sda``::

    # Find the disk
    sda = root.LMI_StorageExtent.first_instance(
            Key="DeviceID",
            Value="/dev/sda")
    # Find the partition table style we want to create there
    gpt_caps = root.LMI_DiskPartitionConfigurationCapabilities.first_instance(
            Key="InstanceID",
            Value="LMI:LMI_DiskPartitionConfigurationCapabilities:GPT")
    # Create the partition table
    partitioning_service.SetPartitionStyle(
            Extent=sda,
            PartitionStyle = gpt_caps)

MS-DOS partition tables are created with the same code, just using different
:ref:`LMI_DiskPartitionConfigurationCapabilities <LMI-DiskPartitionConfigurationCapabilities>`
instance.

Create partition
^^^^^^^^^^^^^^^^

Use
:ref:`LMI_CreateOrModifyPartition <LMI-DiskPartitionConfigurationService-LMI-CreateOrModifyPartition>`
method.

Following code creates several partitions on ``/dev/sda``. The code is the same
for GPT and MS-DOS partitions:: 

    # Define helper function
    def print_partition(partition_name):
        partition = partition_name.to_instance()
        print("Created partition", partition.DeviceID,
                "with", partition.NumberOfBlocks * partition.BlockSize, "bytes.")
    
    # Find the disk
    sda = root.LMI_StorageExtent.first_instance(
            Key="DeviceID",
            Value="/dev/sda")
    
    # create 4 partitions with 100 MB each
    for i in range(4):
        (ret, outparams, err) = partitioning_service.LMI_CreateOrModifyPartition(
                Extent=sda,
                Size = 100 * MEGABYTE)
    print_partition(outparams['partition'])
    
    # Create partition with the whole remaining space - just omit 'Size' parameter
    (ret, outparams, err) = partitioning_service.LMI_CreateOrModifyPartition(
            Extent=sda)
    print_partition(outparams['partition'])

On an empty disk with GPT partition table this code creates:

* 4 partitions with 100 MB each.

* One partition with the largest continuous unpartitioned space on the disk.

On an empty disk with MS-DOS partition table, the code creates:

* 3 primary partitions, 100 MB each.

* One extended partition with the largest continuous unpartitioned space.

* One 100 MB logical partitions.

* One logical partition with the largest continuous free space on the extended
  partition.

The resulting partitions can be seen in the diagram_ above.

List all partitions on a disk
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Enumerate :ref:`LMI_PartitionBasedOn <LMI-PartitionBasedOn>` associations of the
disk.

Following code lists all partitions on ``/dev/sda``, together with their
location::

    # Find the disk
    sda = root.LMI_StorageExtent.first_instance(
            Key="DeviceID",
            Value="/dev/sda")
    
    based_ons = sda.references(ResultClass="LMI_PartitionBasedOn")
    for based_on in based_ons:
    print "Found partition", based_on.Dependent['DeviceID'], \
            "at sectors", based_on.StartingAddress, based_on.EndingAddress
    # TODO: check extended partition
    
Find the largest continuous unpartitioned space on a disk
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Using side-effect of
:ref:`FindPartitionLocation <LMI-DiskPartitionConfigurationCapabilities-FindPartitionLocation>`,
we can find size of the largest partition that can be created on ``/dev/sda``::

    # Find the disk
    sda = root.LMI_StorageExtent.first_instance(
            Key="DeviceID",
            Value="/dev/sda")
    # Find LMI_DiskPartitionConfigurationCapabilities associated to the disk
    sda_partition_capabilities = sda.associators(
            AssocClass='LMI_InstalledPartitionTable') [0]
    # Call its FindPartitionLocation without 'Size' parameter
    # - the largest available space is returned.
    (ret, outparams, err) = sda_partition_capabilities.FindPartitionLocation(
            Extent = sda)
    print "Largest space for a partition:", outparams['size']

Delete partition
^^^^^^^^^^^^^^^^

Call
:ref:`LMI_DeletePartition <LMI-DiskPartitionConfigurationService-LMI-DeletePartition>`::

    sda1 = root.CIM_StorageExtent.first_instance(
            Key="DeviceID",
            Value="/dev/sda1")
    (ret, outparams, err) = partitioning_service.LMI_DeletePartition(
            Partition = sda1.path)

Future direction
----------------

In future, we might implement:

* :ref:`CreateOrModifyPartition <LMI-DiskPartitionConfigurationService-CreateOrModifyPartition>`
  method to meet SMI-S requirements. Then it will be possible to set partition
  exact start/end address.

* :ref:`LMI_CreateOrModifyPartition <LMI-DiskPartitionConfigurationService-LMI-CreateOrModifyPartition>`
  would also modify existing partitions, for example resize them.

* Using
  :ref:`LMI_CreateOrModifyPartition <LMI-DiskPartitionConfigurationService-LMI-CreateOrModifyPartition>`
  it should be possible to set exact type of partition to create
  (primary/logical/extended).
