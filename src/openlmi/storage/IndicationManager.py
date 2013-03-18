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
# -*- coding: utf-8 -*-
"""    
    .. autoclass:: IndicationManager
        :members:
"""

import pywbem
import openlmi.common.cmpi_logging as cmpi_logging
import socket
import threading
from Queue import Queue

class IndicationManager(object):
    """
    Using ``IndicationManager`` class
    providers can send indications without bothering with handling of
    indication subscriptions.
    
    Usage:

    1. Subclass CIM_InstCreation and CIM_InstModification.
    
    2. In your initialization routine, create one ``IndicationManager``
    instance. E.g. one for whole ``LMI_Storage`` may be is enough.
     
    3. Call ``indication_manager.add_filters()`` with all filters your providers
    support. This method can be called multiple times. For example::
      
          filters = {
              "JobPercentUpdated": {
                  "Query" : "SELECT * FROM CIM_InstModification WHERE SourceInstance ISA CIM_ConcreteJob AND SourceInstance.CIM_ConcreteJob::PercentComplete <> PreviousInstance.CIM_ConcreteJob::PercentComplete",
                  "Description" : "Modification of Percentage Complete for a Concrete Job.",
              },
              "JobSucceeded": {
                  "Query" : "SELECT * FROM CIM_InstModification WHERE SourceInstance ISA CIM_ConcreteJob AND ANY SourceInstance.CIM_ConcreteJob::OperationalStatus[*] = 17 AND ANY SourceInstance.CIM_ConcreteJob::OperationalStatus[*] = 2",
                  "Description": "Modification of Operational Status for a Concrete Job to 'Complete' and 'OK'.",
              },
              #... other indications
          }
          instance_manager.add_filters(filters)
      
    4. In your provider module, implement indication functions like this::
    
        def authorize_filter(env, fltr, ns, classes, owner):
            indication_manager.authorize_filter(env, fltr, ns, classes, owner)

        def activate_filter (env, fltr, ns, classes, first_activation):
            indication_manager.activate_filter(env, fltr, ns, classes, first_activation)
        
        def deactivate_filter(env, fltr, ns, classes, last_activation):
            indication_manager.deactivate_filter(env, fltr, ns, classes, last_activation)
        
        def enable_indications(env):
            indication_manager.enable_indications(env)
        
        def disable_indications(env):
            indication_manager.disable_indications(env)
                    
    From now on, the ``IndicationManager`` will track all subscribed filters.
    You can query the ``indication_manager.is_subscribed()`` before you create
    and send an indication. Use ``indication_manager.send_indication()`` to send
    your indications.
     
    Only static (=preconfigured, read-only) indication filters are
    supported.
        
    The supported filters must be passed to add_filters method. The filters
    are passed as dictionary
    ``'filter_id' -> {dictionary 'IndicationFilter property' -> 'value'}``.
    There must be at least ``Query`` property in each filter, CQL is assumed.
    
    This helper automatically tracks which filters are subscribed. Provider
    can query ``is_subscribed()`` to check, if filter with given ``filter_id``
    is subscribed before generating indications.
    
    The CMPI interface to send indications is complicated -
    when an indication is send from CIMOM callback (e.g. ``get_instance``), it
    must use current ``env`` parameter of the callback and it would be
    tedious to pass it to ``IndicationManager`` each time.
    Therefore ``IndicationManager`` creates its own thread, registers it at
    CIMOM using ``PrepareAttachThread``/``AttachThread``.
      
    As side-effect, indication can be sent from any thread, there is no need
    to call ``PrepareAttachThread``/``AttachThread``.
    """
    SEVERITY_INFO = pywbem.Uint16(2)  # CIM_Indication.PerceivedSeverity

    @cmpi_logging.trace_method
    def __init__(self, env, nameprefix, namespace):
        """
        Create new ``IndicationManager``. Usually only one instance
        is necessary for one provider process.
        
        :param env: (``ProviderEnvironment``) Provider enviroment, taken from 
            CIMOM callback (e.g. ``get_providers()``).
        :param nameprefix: (``string``) Prefix of your ``CIM_InstCreation`` and
            ``CIM_InstModification`` subclasses, e.g. 'Storage' for
            ``LMI_StorageInstCreation``.
        :param namespace: (``string``) Namespace, which will be set to outgoing
            indications instances.
        """

        self.filters = {}
        self.enabled = False
        self.subscribed_filters = set()
        self.nameprefix = nameprefix
        self.instcreation_classname = "LMI_" + nameprefix + "InstCreation"
        self.instmodification_classname = ("LMI_" + nameprefix
                + "InstModification")
        self.instdeletion_classname = "LMI_" + nameprefix + "InstDeletion"
        self.namespace = namespace

        self.queue = Queue()
        # prepare indication thread
        ch = env.get_cimom_handle()
        new_broker = ch.PrepareAttachThread()
        self.indication_sender = threading.Thread(
                target=self._send_indications_loop, args=(new_broker,))
        self.indication_sender.daemon=True
        self.indication_sender.start()

    @cmpi_logging.trace_method
    def add_filters(self, filters):
        """
        Add new filters to the helper. These filters will be allowed for
        subscription.
        
        :param filters: (``dictionary filter_id -> filter properties``)
            The filters. ``filter properties`` is dictionary 
            ``property_name -> value``, where at least ``Query`` property
            must be set. ``Name`` property will be automatically created
            as 'LMI:CIM_IndicationFilter:<filter_id>'.
        """
        self.filters.update(filters)

    @cmpi_logging.trace_method
    def authorize_filter(self, _env, fltr, _ns, _classes, _owner):
        """
        AuthorizeFilter callback from CIMOM. Call this method from appropriate
        CIMOM callback.
        """
        for (_id, _fltr) in self.filters.iteritems():
            if _fltr['Query'] == fltr:
                cmpi_logging.logger.info("InstanceFilter %s: %s authorized"
                        % (_id, fltr))
                return True
        cmpi_logging.logger.info("InstanceFilter %s denied" % (fltr,))
        return False

    @cmpi_logging.trace_method
    def activate_filter(self, _env, fltr, _ns, _classes, first_activation):
        """
        ActivateFilter callback from CIMOM. Call this method from appropriate
        CIMOM callback.
        """
        if first_activation:
            for (_id, _fltr) in self.filters.iteritems():
                if _fltr['Query'] == fltr:
                    self.subscribed_filters.add(_id)
                    cmpi_logging.logger.info("InstanceFilter %s: %s "
                            "started" % (id, fltr))

    @cmpi_logging.trace_method
    def deactivate_filter(self, _env, fltr, _ns, _classes, last_activation):
        """
        DeactivateFilter callback from CIMOM. Call this method from appropriate
        CIMOM callback.
        """
        if last_activation:
            for (_id, _fltr) in self.filters.iteritems():
                if _fltr['Query'] == fltr:
                    self.subscribed_filters.remove(_id)
                    cmpi_logging.logger.info("InstanceFilter %s: %s "
                            "stopped" % (_id, fltr))

    @cmpi_logging.trace_method
    def enable_indications(self, _env):
        """
        EnableIndications callback from CIMOM. Call this method from appropriate
        CIMOM callback.
        """
        self.enabled = True
        cmpi_logging.logger.info("Indications enabled")

    @cmpi_logging.trace_method
    def disable_indications(self, _env):
        """
        EnableIndications callback from CIMOM. Call this method from appropriate
        CIMOM callback.
        """
        self.enabled = False
        cmpi_logging.logger.info("Indications disabled")

    @cmpi_logging.trace_method
    def send_indication(self, indication):
        """
        Send indication to all subscribers. Call this method from appropriate
        CIMOM callback.
        """
        self.queue.put(indication)

    @cmpi_logging.trace_method
    def send_instcreation(self, instance, filter_id):
        """
        Send ``LMI_<nameprefix>InstCreation`` indication with given instance.
        
        :param instance: (``CIMInstance``) The created instance.
        :param filter_id: (``string``) The ID of registered filter which
            corresponds to this indication.
        """
        if not self.is_subscribed(filter_id):
            return
        path = pywbem.CIMInstanceName(
                classname=self.instcreation_classname,
                namespace=self.namespace)
        ind = pywbem.CIMInstance(
                self.instcreation_classname,
                path=path)
        ind['SourceInstance'] = instance
        ind['SourceInstanceHost'] = socket.gethostname()
        ind['SourceInstanceModelPath'] = str(instance.path)
        ind['IndicationFilterName'] = "LMI:CIM_IndicationFilter:" + filter_id
        ind['PerceivedSeverity'] = self.SEVERITY_INFO

        cmpi_logging.logger.info("Sending indication %s for %s" %
                (filter_id, str(path)))
        self.send_indication(ind)

    @cmpi_logging.trace_method
    def send_instmodification(self, old_instance, new_instance, filter_id):
        """
        Send ``LMI_<nameprefix>InstModification`` indication with given
        instance.
        
        :param old_instance: (``CIMInstance``) The instance before modification.
        :param new_instance: (``CIMInstance``) The instance after modification.
        :param filter_id: (``string``) The ID of registered filter which
            corresponds to this indication.
        """
        if not self.is_subscribed(filter_id):
            return
        path = pywbem.CIMInstanceName(
                classname=self.instmodification_classname,
                namespace=self.namespace)
        ind = pywbem.CIMInstance(
                self.instcreation_classname,
                path=path)
        ind['SourceInstance'] = new_instance
        ind['PreviousInstance'] = old_instance
        ind['SourceInstanceHost'] = socket.gethostname()
        ind['SourceInstanceModelPath'] = str(new_instance.path)
        ind['IndicationFilterName'] = "LMI:CIM_IndicationFiler:" + filter_id
        ind['PerceivedSeverity'] = self.SEVERITY_INFO

        cmpi_logging.logger.info("Sending indication %s for %s" %
                (filter_id, str(path)))
        self.send_indication(ind)

    @cmpi_logging.trace_method
    def is_subscribed(self, fltr_id):
        """
        Return True, if there is someone subscribed for given filter.
        
        :param fltr_id: (``string``) ID of the filter to check.
        """
        if not self.enabled:
            return False
        if fltr_id in self.subscribed_filters:
            return True
        return False

    @cmpi_logging.trace_method
    def _send_indications_loop(self, broker):
        """
        This method runs in its own thread. It just sends all enqueued
        indications.
        
        :param broker: (``BrokerCIMOMHandle``) Handle of the CIMOM.
        """
        broker.AttachThread()
        while True:
            indication = self.queue.get()
            cmpi_logging.logger.trace_info("Delivering indication %s" %
                (str(indication.path)))
            broker.DeliverIndication(self.namespace, indication)
            self.queue.task_done()
