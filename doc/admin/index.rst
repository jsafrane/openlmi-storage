OpenLMI Storage Provider documentation
======================================

OpenLMI-Storage is CIM provider which manages local block devices, i.e. block
devices which are present in ``/dev/`` directory. This includes also attached
iSCSI, FC and FCoE devices, as long as appropriate block device is present.

Application developers who are familiar with SMI-S should start read at
:ref:`SMI-S profiles <smis-profiles>` chapter.

Application developers and/or sysadmins should skip whole SMI-S and start
reading :ref:`OpenLMI-Storage usage <openlmi-usage>`.

Content:

.. toctree::
   :maxdepth: 2

   smis-profiles
   usage
   admin
   todo

OpenLMI Storage CIM classes:

.. toctree::
   :maxdepth: 1

   mof/tree
   mof/index

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

