#
# Kiwi: a Framework and Enhanced Widgets for Python
#
# Copyright (C) 2005-2006 Async Open Source
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
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307
# USA
#
# Author(s): Johan Dahlin     <jdahlin@async.com.br>
#

"""
Extension to the logging module

This module defines a couple of extensions to the logging module included
in the python standard distribution.

It creates an additional logging handler that print log records on the
standard output. This handler is only showing records which has a level
set to logging.WARNING or higher by default.
The messages printed by this handler can be modified by using the environment
variable called KIWI_LOG.

The syntax for the string which KIWI_LOG points to is the following::

    domain ':' level [, domain ':', level]

domain can contain wildcards such as * and ?
level is an integer 1-5 which defines the minimal level:

  - B{5}: DEBUG
  - B{4}: INFO
  - B{3}: WARNING
  - B{2}: ERROR
  - B{1}: CRITICAL

Examples::

    KIWI_LOG="stoq*:5"

will print all the messages in a domain starting with stoq with DEBUG or higher::

    KIWI_LOG="kiwi*:4,stoq.*:5"

will print all the messages with INFO or higher in all domains starting with kiwi,
and all the messages in the stoq.* domains which are DEBUG or higher

Inspiration for the syntax is taken from the U{debugging facilities<http://gstreamer.freedesktop.org/data/doc/gstreamer/head/gstreamer/html/gstreamer-GstInfo.html#id2857358>} of the
U{GStreamer<http://www.gstreamer.net>} multimedia framework.
"""

import fnmatch
import logging
import os

# Globals

_console = None
_filter = None

class LogError(Exception):
    pass

class Logger(object):
    # Backwards compatibility, we should probably replace the callsites
    # with import logging; logging.getLogger(name)
    def __new__(self, name):
        return logging.getLogger(name)

class _Logger(logging.Logger):
    def __call__(self, message, *args, **kwargs):
        self.info(message, *args, **kwargs)

logging.setLoggerClass(_Logger)

class ReversedGlobalFilter(logging.Filter):
    """
    It's like a reversed filter, the default behavior
    is to not show the message, you need to add custom filters for all
    the records you wish to see
    """
    def __init__(self):
        logging.Filter.__init__(self)
        self.filters = []

    def add_filter(self, f, level=logging.DEBUG):
        self.filters.append((f, level))

    def filter(self, record):
        for f, level in self.filters:
            if (record.levelno >= level and
                fnmatch.fnmatch(record.name, f)):
                return True

        return False

def set_log_file(filename, mask=None):
    """
    Set the filename used for logging.

    @param filename:
    @param mask: optional
    """
    file_handler = logging.FileHandler(filename, 'w')
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(name)-18s %(levelname)-8s %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'))
    root = logging.getLogger()
    root.addHandler(file_handler)

    if mask:
        file_filter = ReversedGlobalFilter()
        file_filter.add_filter(mask, logging.DEBUG)
        file_handler.addFilter(file_filter)

    return file_handler.stream

def set_log_level(name, level):
    """
    Set the log level.

    @param name: logging category
    @param level: level
    """
    global _filter
    _filter.add_filter(name, level)

def _read_log_levels(console_filter):
    log_levels = {}
    # bootstrap issue, cannot depend on kiwi.environ
    log_level = os.environ.get('KIWI_LOG')
    if not log_level:
        return log_levels

    for part in log_level.split(','):
        if not ':' in part:
            continue

        if part.count(':') > 1:
            raise LogError("too many : in part %s" % part)
        name, level = part.split(':')
        try:
            level = int(level)
        except ValueError:
            raise LogError("invalid level: %s" % level)

        if level < 0 or level > 5:
            raise LogError("level must be between 0 and 5")

        level = 50 - (level * 10)

        console_filter.add_filter(name, level)

def _create_console():
    global _filter, _console

    console = logging.StreamHandler()
    console.setFormatter(logging.Formatter(
        "%(asctime)s %(name)-20s %(message)s", datefmt='%T'))
    root = logging.getLogger()
    root.addHandler(console)
    root.setLevel(logging.DEBUG)

    console_filter = ReversedGlobalFilter()
    # Always display warnings or higher on the console
    console_filter.add_filter('*', logging.WARNING)
    console.addFilter(console_filter)

    _read_log_levels(console_filter)

    # Set globals
    _filter = console_filter
    _console = console

def update_logger():
    _create_console()

_create_console()

kiwi_log = Logger('kiwi')
