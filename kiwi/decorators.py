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
# Author(s): Johan Dahlin <jdahlin@async.com.br>
#

import gobject

from kiwi import _warn

class deprecated(object):
    """
    I am a decorator which prints a deprecation warning each
    time you call the decorated (and deprecated) function
    """
    def __init__(self, new):
        """
        @param new: the name of the new function replacing the old
          deprecated one
        @type new: string
        """
        self._new = new

    def __call__(self, func):
        def wrapper(*args, **kwargs):
            _warn("%s is deprecated, use %s instead" % (func.__name__,
                                                        self._new))
            return func(*args, **kwargs)
        return wrapper

class delayed(object):
    """
    I am a decorator which delays the function call using the gobject/gtk
    mainloop for a number of ms.
    """
    def __init__(self, delay):
        """
        @param delay: delay in ms
        @type delay:  integer
        """
        
        self._delay = delay
        self._timeout_id = -1
        
    def __call__(self, func):
        def real_call(args, kwargs):
            func(*args, **kwargs)
            self._timeout_id = -1
            return False
        
        def wrapper(*args, **kwargs):
            # Only one call at a time
            if self._timeout_id != -1:
                return
        
            self._timeout_id = gobject.timeout_add(self._delay,
                                                   real_call, args, kwargs)
        
        return wrapper

        
