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

import gettext
import logging
from logging import DEBUG, INFO, WARNING, ERROR, CRITICAL
import os
import sys

from kiwi.environ import environ

_ = gettext.gettext


_log_level = INFO

class Log(logging.Logger):
    def __init__(self, file=sys.stdout, level=INFO,
                 category='fiscal_printer'):
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
        global _log_level
        logging.Logger.__init__(self, category, _log_level)
        self._category = category
        
        # Tries to open the given file. If IOerror occour, send log to stdout
        file_obj = None
        
        if type(file) == type(sys.stdout):
            # If file is already a file object, just set it to file_obj var
            if 'w' in file.mode or 'a' in file.mode or '+' in file.mode:
                file_obj = file
            else:
                # Without write permission to the given file object,
                # write to stdout
                print _(">>> Given file object in read-only mode! Using "
                        "standard output to write logs!")
                file_obj = sys.stdout
        else:
            try:
                file_obj = open(file, 'a')
            except:
                print _(">>> Couldn't access specified file! Using standard "
                        "output to write logs!")
                file_obj = sys.stdout
                
        stream_handler = logging.StreamHandler(file_obj)
            
        # Formater class define a format for the log messages been
        # logged with this handler
        # The following format string
        #   ("%(asctime)s (%(levelname)s) - %(message)s") will result
        # in a log message like this:
        #   2005-09-07 18:15:12,636 (WARNING) - (message!)
        format_string = ("%(asctime)s %(message)s")
        stream_handler.setFormatter(logging.Formatter(format_string,
                                                      datefmt='%T'))
        self.addHandler(stream_handler)

    def log(self, message, level=INFO):
        """This method logs messages with default log_level.
        
        If it's desired another level, user is able to define it using
        the level argument.        
        """        
        logging.Logger.log(self, level, message)

class Logger(object):
    log_domain = 'default'
    def __init__(self, category=None):
        category = (category or self.log_domain)
        self._log = Log(category=category)
        self._category = category

    def __call__(self, message):
        self.info(message)
        
    def log(self, level, message):
        global _log_level
        if _log_level <= level:
            frame = sys._getframe(2)
            filename = os.path.basename(frame.f_code.co_filename)
            message = '%s %s:%d %s' % (self._category, filename,
                                       frame.f_lineno, message)
            self._log.log(level=level, message=message)
        
    def debug(self, message):
        self.log(DEBUG, message)

    def info(self, message):
        self.log(INFO, message)

    def warning(self, message):
        self.log(WARNING, message)

    def error(self, message):
        self.log(ERROR, message)

    def critical(self, message):
        self.log(CRITICAL, message)

def set_log_level(level):
    global _log_level
    _log_level = level

log_level = environ.get_log_level()
if log_level is None:
    # Default is to show only warnings and higher
    log_level = WARNING
else:
    log_level = int(log_level)
set_log_level(log_level)
