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
    def __init__(self, filters=None):
        """
        @param filters: a list of tuples, (name, level),
          name can include wildcards: * or ?
        """
        logging.Filter.__init__(self)
        self.filters = filters or []

    def add_filter(self, f, level=logging.DEBUG):
        self.filters.append((f, level))

    def filter(self, record):
        for f, level in self.filters:
            if fnmatch.fnmatch(record.name, f):
                return True

        return False

def set_log_file(filename, mask=None):
    """
    @param filename:
    @param mask: optional
    """
    stoq = logging.FileHandler(filename, 'w')
    stoq.setFormatter(logging.Formatter(
        '%(asctime)s %(name)-18s %(levelname)-8s %(message)s',
        datefmt='%F %T'))
    root = logging.getLogger()
    root.addHandler(stoq)

    if mask:
        stoq.addFilter(ReversedGlobalFilter([(mask, logging.DEBUG)]))

def set_log_level(name, level):
    """
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
    console.setLevel(logging.DEBUG)
    console.setFormatter(logging.Formatter(
        "%(asctime)s %(message)s", datefmt='%T'))
    root = logging.getLogger()
    root.addHandler(console)
    root.setLevel(logging.DEBUG)

    console_filter = ReversedGlobalFilter()
    console.addFilter(console_filter)

    _read_log_levels(console_filter)

    # Set globals
    _filter = console_filter
    _console = console

_create_console()

kiwi_log = Logger('kiwi')
