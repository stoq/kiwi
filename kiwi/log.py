#
# Kiwi: a Framework and Enhanced Widgets for Python
#
# Copyright (C) 2005 Async Open Source
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
# Author(s): Adriano Monteiro <adriano@globalret.com.br>
#            Johan Dahlin     <jdahlin@async.com.br>
##

import logging
import os
import sys

from kiwi.environ import environ

class LogError(Exception):
    pass

class Formatter(logging.Formatter):
    def format(self, record):
        frame = sys._getframe(8)
        filename = os.path.basename(frame.f_code.co_filename)
        record.msg = '%s:%d %s' % (filename, frame.f_lineno, record.msg)
        return logging.Formatter.format(self, record)

class Logger(logging.Logger):
    log_domain = 'default'
    def __init__(self, name=None, level=logging.NOTSET):
        """Initializes Log module, creating log handler and defining log
        level. level attribute is not mandatory. It defines from which level
        messages should be logged. Logs with lower level are ignored.

        logging default levels table:

        Level
          - logging.NOTSET
          - logging.DEBUG
          - logging.INFO
          - logging.WARNING
          - logging.ERROR
          - logging.CRITICAL
        """
        if not name:
            name or Logger.log_name
        logging.Logger.__init__(self, name, get_log_level(name))

        stream_handler = logging.StreamHandler(sys.stdout)

        # Formater class define a format for the log messages been
        # logged with this handler
        # The following format string
        #   ("%(asctime)s (%(levelname)s) - %(message)s") will result
        # in a log message like this:
        #   2005-09-07 18:15:12,636 (WARNING) - (message!)
        format_string = ("%(asctime)s %(message)s")
        stream_handler.setFormatter(Formatter(format_string,
                                              datefmt='%T'))
        self.addHandler(stream_handler)

    def __call__(self, message, *args, **kwargs):
        self.info(message, *args, **kwargs)

_log_levels = {}

def set_log_level(name, level):
    """
    @param name: logging category
    @param level: level
    """
    _log_levels[name] = level

def get_log_level(name):
    """
    @param name: logging category
    @returns: the level
    """
    return _log_levels.get(name, logging.WARNING)

def _read_log_level():
    log_levels = {}
    log_level = environ.get_log_level()
    for part in log_level.split(','):
        if ':' in part:
            if part.count(':') > 1:
                raise LogError("too many : in part %s" % part)
            name, level = part.split(':')
            try:
                level = int(level)
            except ValueError:
                raise LogError("invalid level: %s" % level)

            if level < 0 or level > 5:
                raise LogError("level must be between 0 and 5")
        log_levels[name] = level

    return log_levels

_log_levels = _read_log_level()
