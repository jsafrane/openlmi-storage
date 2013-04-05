OpenLMI-Storage usage
=====================

Block devices cannot be directly manipulated using intrinsic or extrinsic
methods of ``CIM_StorageExtent`` or ``LMI_VGStoragePool``.

Please use appropriate ``ConfigurationService`` to create, modify or delete devices
or volume groups:


.. toctree:: 
   :maxdepth: 2

   usage-partitioning
   usage-raid
   usage-lvm
   usage-fs


.. note::

   Previous releases allowed to use ``DeleteInstance`` intrinsic method to
   delete various ``LMI_StorageExtents``. This method is now deprecated and
   will be removed from future releases of OpenLMI-Storage. The reason is that
   ``DeleteInstance`` cannot be asynchronous and could block the whole provider
   for a long time.
