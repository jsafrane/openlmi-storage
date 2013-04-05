Document conventions
====================

Throughout this document we use following conventions.

Examples
--------

All example scripts are for ``lmishell``. See it's documentation_ on OpenLMI_
page.

.. _documentation: https://fedorahosted.org/openlmi/wiki/shell

.. _OpenLMI: https://fedorahosted.org/openlmi/

We also assume that following script has been run to connecto to a CIMOM and
initialize basic variables::

    MEGABYTE = 1024*1024
    connection = connect("localhost", "root", "opensesame")
    root = connection.root.cimv2
    storage_service = root.LMI_StorageConfigurationService.first_instance()
    partitioning_service = root.LMI_DiskPartitionConfigurationService.first_instance()
