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
            
class ApplicationThread(threading.Thread):
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
        
    def get_object(self, window_name, widget_name):
        """
        @param window_name: name of the toplevel window
        @param name:        name of the widget
        @returns: a threadsafe wrapper around the widget
        """
        
        if not window_name in self._objects:
            raise KeyError(window_name)
        window_widgets = self._objects[window_name]
        if not widget_name in window_widgets:
            raise KeyError("No widget called %s in window %s" % (widget_name,
                                                                 window_name))
        
        return ThreadSafeObject(window_widgets[widget_name])
    
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
        if window.window is None:
            print 'Fixme %s is missing a GdkWindow', window_name
            return
        
        event = gdk.Event(gdk.DELETE)
        event.window = window.window
        event.put()
        
    def finish(self):
        gobject.idle_add(gtk.main_quit)
        self._appthread.join()
        raise SystemExit
