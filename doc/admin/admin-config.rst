.. _openlmi-config:

Configuration
=============

Configuration file is stored in ``/etc/openlmi/storage/storage.conf``. This file
has simple .ini syntax, with ``#`` or ``;`` used for comments.


Default configuration::

     [CIM]
     Namespace=root/cimv2
     SystemClassName=Linux_ComputerSystem
     
     [Log]
     Debug=false
     Stderr=false
     DebugBlivet=false

======= =================== ==================== ===========
Section Option name         Default value        Desciption
======= =================== ==================== ===========
``CIM`` ``Namespace``       root/cimv2           Namespace where OpenLMI-Storage providers are registered.
``CIM`` ``SystemClassName`` Linux_ComputerSystem Name of CIM_ComputerSystem class, which is used to represent the computer system. It will be used as ``SystemClassName`` property value of various classes.
``Log`` ``Debug``           false                Toggles logging of detailed debug messages in providers.
``Log`` ``Stderr``          false                Toggles sending of log messages to standard error output of the CIMOM.
``Log`` ``DebugBlivet``     false                Toggles logging of detailed debug messages in Blivet.
======= =================== ==================== ===========

Persistent setting
------------------

OpenLMI-Storage stores persistent data in ``/var/lib/openlmi-storage/``.
Typically, various :ref:`CIM_SettingData <CIM-SettingData>` instances with
:ref:`ChangeableType <CIM-SettingData-ChangeableType>`
``Changeable - Persistent`` are stored here.

Logging
=======

By default, all log messages with level INFO and above are sent to CIMOM using
standard CMPI ``CMLogMessage`` function. Consult documentation of your CIMOM
how to enable output of these messages into CIMOM logs.

With ``Stderr`` configuration option enabled, all logs are sent both to CIMOM
and to the standard error output of the CIMOM.

With ``Debug`` and ``DebugBlivet`` options enabled, all messages with level
DEBUG and above are sent to CIMOM and (if enabled) also to stderr.
