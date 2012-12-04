#!/usr/bin/python
# -*- Coding:utf-8 -*-
#
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


import logging

TRACE_WARNING = logging.INFO - 1
TRACE_INFO = logging.INFO - 2
TRACE_VERBOSE = logging.DEBUG

class CMPILogHandler(logging.Handler):
    """
        A handler class, which sends log messages to CMPI log.
    """

    def __init__(self, cmpi_logger, *args, **kwargs):
        self.cmpi_logger = cmpi_logger
        super(CMPILogHandler, self).__init__(*args, **kwargs)

    def emit(self, record):
        msg = self.format(record)
        if record.levelno >= logging.ERROR:
            self.cmpi_logger.log_error(msg)
        elif record.levelno >= logging.WARNING:
            self.cmpi_logger.log_warn(msg)
        elif record.levelno >= logging.INFO:
            self.cmpi_logger.log_info(msg)
        elif record.levelno >= TRACE_WARNING:
            self.cmpi_logger.trace_warn(msg)
        elif record.levelno >= TRACE_INFO:
            self.cmpi_logger.trace_info(msg)
        elif record.levelno >= logging.DEBUG:
            self.cmpi_logger.log_debug(msg)

class CMPILogger(logging.Logger):
    """
        A logger class, which adds trace level log methods.
    """
    def trace_warn(self, msg, *args, **kwargs):
        """ Log message with TRACE_WARNING severity. """
        self.log(TRACE_WARNING, msg, *args, **kwargs)

    def trace_info(self, msg, *args, **kwargs):
        """ Log message with TRACE_INFO severity. """
        self.log(TRACE_INFO, msg, *args, **kwargs)

    def trace_verbose(self, msg, *args, **kwargs):
        """ Log message with TRACE_VERBOSE severity. """
        self.log(TRACE_VERBOSE, msg, *args, **kwargs)

class CMPIFormatter(logging.Formatter):
    """
        Special formatter of CMPI log messages, trace messages
        include file name.
    """
    def __init__(self, *args, **kwargs):
        self.trace_formatter = logging.Formatter(
                '%(filename)s %(levelname)s: %(message)s')
        self.log_formatter = logging.Formatter('%(levelname)s: %(message)s')
        super(CMPIFormatter, self).__init__(*args, **kwargs)

    def format(self, record):
        if record.levelno >= logging.INFO:
            return self.log_formatter.format(record)
        else:
            return self.trace_formatter.format(record)

def init_logger(env):
    """
        Initialize logging.
    """
    cmpi_handler = CMPILogHandler(env.get_logger())
    cmpi_handler.setLevel(logging.INFO)
    formatter = CMPIFormatter()
    cmpi_handler.setFormatter(formatter)

    my_logger = logging.getLogger('openlmi.storage')
    my_logger.addHandler(cmpi_handler)

logger = logging.getLogger('openlmi.storage')