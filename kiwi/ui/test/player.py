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
# Author(s): Johan Dahlin <jdahlin@async.com.br
#

import sys
import threading
import time

import gobject
gobject.threads_init()
import gtk
from gtk import gdk
#gdk.threads_init()

from kiwi.ui.test.common import Base

class TimeOutError(Exception):
    pass

class ThreadSafeFunction:
    """
    A function which is safe thread in the mainloop context
    """
    
    def __init__(self, func):
        self._func = func
        
    def __call__(self, *args, **kwargs):
        gobject.idle_add(self._func, *args, **kwargs)

        # dialog.run locks us out
        #gdk.threads_enter()
        #rv = self._func(*args, **kwargs)
        #gdk.threads_leave()
        #return rv
        
class ThreadSafeObject:
    """
    A wrapper around a gobject which replaces all callable
    objects which wraps all callable objects uses L{ThreadSafeFunction}.
    """
    def __init__(self, gobj):
        """
        @param gobj:
        """
        self._gobj = gobj

    def __getattr__(self, name):
        attr = getattr(self._gobj, name, None)
        if attr is None:
            raise KeyError(name)
        if callable(attr):
            return ThreadSafeFunction(attr)
        return attr
            
class DictWrapper(object):
    def __init__(self, dict, name):
        self._dict = dict
        self._name = name

    def __getattr__(self, attr):
        if not attr in self._dict:
            raise KeyError("no %s called %s" % (self._name, attr))
        
        return ThreadSafeObject(self._dict[attr])

class App(DictWrapper):
    def __getattr__(self, attr):
        return DictWrapper(self._dict[attr], 'widget')
    
class ApplicationThread(threading.Thread):
    """
    A separate thread in which the application will be executed in.
    It's necessary to use threads since we want to allow applications
    to run gtk.main and dialog.run without needing any modifications
    """
    def __init__(self, args):
        threading.Thread.__init__(self)
        self._args = args

    def run(self):
        sys.argv = self._args[:]
        execfile(sys.argv[0])

class Player(Base):
    """
    Event playback object
    """
    def __init__(self, args):
        """
        @param args:
        """
        Base.__init__(self)

        self._appthread = ApplicationThread(args)
        self._appthread.start()

        self._app = App(self._objects, name='window')
        
    def get_app(self):
        """
        Returns a virtual application object, which is a special object
        where you can access the windows as attributes and widget in the
        windows as attributes on the window, examples:

        >>> app = player.get_app()
        >>> app.WindowName.WidgetName.method()
        
        @returns: virtual application object
        """
        return self._app
    
    def wait_for_window(self, name, timeout=10):
        """
        @param name:
        """

        start_time = time.time()
        # XXX: No polling!
        #print 'waiting for', name
        while True:
            if name in self._objects:
                window = self._objects[name]
                time.sleep(0.5)
                return window

            if time.time() - start_time > timeout:
                raise TimeOutError("could not find window %s" % name)
            time.sleep(0.05)

    def delete_window(self, window_name):
        """
        Deletes a window, creates a delete-event and sends it to the window
        """
        if not window_name in self._windows:
            raise KeyError(window_name)
        
        window = self._windows[window_name]
        # If the window is already removed, skip
        if window.window is None:
            return
        
        event = gdk.Event(gdk.DELETE)
        event.window = window.window
        event.put()
        
    def finish(self):
        gobject.idle_add(gtk.main_quit)
        self._appthread.join()
        raise SystemExit
