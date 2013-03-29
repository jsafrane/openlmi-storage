# Copyright (C) 2012 Red Hat, Inc.  All rights reserved.
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
""" Module for StorageConfiguration class."""

import ConfigParser
import socket
import openlmi.common.cmpi_logging as cmpi_logging

class StorageConfiguration(object):
    """
        OpenLMI configuration file. By default, it resides in
        /etc/openlmi/storage/storage.conf.
        
        There should be only one instance of this class.
    """

    CONFIG_PATH = '/etc/openlmi/storage/'
    CONFIG_FILE = CONFIG_PATH + 'storage.conf'

    PERSISTENT_PATH = '/var/lib/openlmi-storage/'
    SETTINGS_DIR = 'settings/'

    defaults = {
        'Namespace' : 'root/cimv2',
        'SystemClassName' : 'Linux_ComputerSystem',
        'Debug': 'false',
        'DebugBlivet': 'false',
        'Stderr': 'false',
    }

    @cmpi_logging.trace_method
    def __init__(self):
        """ Initialize and load a configuration file."""
        self._listeners = set()
        self.config = ConfigParser.SafeConfigParser(defaults=self.defaults)
        self.load()

    @cmpi_logging.trace_method
    def add_listener(self, callback):
        """ 
            Add a callback, which will be called when configuration is updated.
            The callback will be called with StorageConfiguration as parameter:
              callback(config)
        """
        self._listeners.add(callback)

    @cmpi_logging.trace_method
    def remove_listener(self, callback):
        """ 
            Remove previously registered callback.
        """

        self._listeners.remove(callback)

    @cmpi_logging.trace_method
    def _call_listeners(self):
        """
            Call all listeners that configuration has updated.
        """
        for callback in self._listeners:
            callback(self)

    @cmpi_logging.trace_method
    def load(self):
        """
            Load configuration from CONFIG_FILE. The file does not need to
            exist.
        """
        self.config.read(self.CONFIG_FILE)
        if not self.config.has_section('CIM'):
            self.config.add_section('CIM')
        if not self.config.has_section('Log'):
            self.config.add_section('Log')
        self._call_listeners()

    @property
    def namespace(self):
        """ Return namespace of OpenLMI storage provider."""
        return self.config.get('CIM', 'Namespace')

    @property
    def system_class_name(self):
        """ Return SystemClassName of OpenLMI storage provider."""
        return self.config.get('CIM', 'SystemClassName')

    @property
    def system_name(self):
        """ Return SystemName of OpenLMI storage provider."""
        return socket.getfqdn()

    @property
    def tracing(self):
        """ Return True if tracing is enabled."""
        return self.config.getboolean('Log', 'Debug')

    @property
    def blivet_tracing(self):
        """ Return True if blivet tracing is enabled."""
        return self.config.getboolean('Log', 'DebugBlivet')

    @property
    def stderr(self):
        """ Return True if logging to stderr is enabled."""
        return self.config.getboolean('Log', 'Stderr')

