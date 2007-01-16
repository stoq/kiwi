#
# Kiwi: a Framework and Enhanced Widgets for Python
#
# Copyright (C) 2006 Async Open Source
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

"""
Runner - executes recorded scripts
"""

import doctest
import sys
import time

import gobject
from gtk import gdk

from kiwi.log import Logger
from kiwi.ui.test.common import WidgetIntrospecter

log = Logger('kiwi.ui.test.player')

class NotReadyYet(Exception):
    pass

class MissingWidget(KeyError):
    pass

class MagicWindowWrapper(object):
    def __init__(self, window, ns):
        self.window = window
        self.ns = ns

    def delete(self):
        self.window.emit('delete-event', gdk.Event(gdk.DELETE))

    def __getattr__(self, attr):
        if not attr in self.ns:
            raise MissingWidget(attr)
        return self.ns[attr]

class Runner(object):
    """
    @ivar parser:
    """
    def __init__(self, filename):
        self._filename = filename
        self._pos = 0
        self._windows = {}
        self._ns = {}
        self._source_id = -1

        self.parser = doctest.DocTestParser()
        self._stmts = self.parser.get_examples(open(filename).read())

        wi = WidgetIntrospecter()
        wi.register_event_handler()
        wi.connect('window-added', self._on_wi__window_added)
        wi.connect('window-removed', self._on_wi__window_removed)

    # Callbacks

    def _on_wi__window_added(self, wi, window, name, ns):
        log.info('Window added: %s' % (name,))
        self._windows[name] = MagicWindowWrapper(window, ns)

        self.iterate()

    def _on_wi__window_removed(self, wi, window, name):
        log.info('Window removed: %s' % (name,))
        del self._windows[name]

        self.iterate()

    # Public API

    def iterate(self):
        stmts = self._stmts
        while True:
            if self._pos == len(stmts):
                self.quit()
                break

            ex =  stmts[self._pos]
            self._pos += 1

            log.info('will now execute %r' % (ex.source[:-1],))
            try:
                exec compile(ex.source, self._filename,
                             'single', 0, 1) in self._ns
            except NotReadyYet:
                self._pos -= 1
                break
            except (SystemExit, KeyboardInterrupt):
                raise SystemExit
            except MissingWidget, e:
                raise SystemExit(
                    "ERROR: Could not find widget: %s" % str(e))
            except Exception, e:
                import traceback
                traceback.print_exc()
                raise SystemExit

            log.info('Executed %r' % (ex.source[:-1],))
            self._last = time.time()

    def quit(self):
        print '* Executed successfully'
        sys.exit(0)

    def start(self):
        self._last = time.time()

    def sleep(self, duration):
        """
        @param duration:
        """
        # We don't want to block the interface here which means that
        # we cannot use time.sleep.
        # Instead we schedule another execute iteration in the future
        # and raises NotReadyYet which stops the interpreter until
        # iterate is called again.

        def _iter():
            # Turn ourselves off and allow future calls to wait() to
            # queue new waits.
            self._source_id = -1

            # Iterate, which will call us again
            self.iterate()

            return False

        if self._source_id != -1:
            raise NotReadyYet

        # The delta is the last time we executed a statement minus
        delta = (self._last + duration) - time.time()
        if delta > 0:
            ms = int(delta * 1000)
            self._source_id = gobject.timeout_add(ms, _iter)
            raise NotReadyYet

        # Okay, we've waited enough, let's go back to business

    def waitopen(self, window_name):
        """
        @param window_name:
        """
        if not window_name in self._windows:
            raise NotReadyYet(window_name)
        return self._windows[window_name]

    def waitclose(self, window_name):
        """
        @param window_name:
        """
        if window_name in self._windows:
            raise NotReadyYet(window_name)

runner = None

def play_file(script, filename=None, args=None):
    """
    @param script:
    @param filename:
    @param args:
    """

    global runner

    log.info('Running script %s' % script)
    runner = Runner(script)

    if filename is None:
        fd = open(script)
        data = fd.readline()[:-1] + fd.readline()[:-1]

        # Check for run: lines in the doctests
        # run: ....
        pos = data.find('run:')
        if pos != -1:
            rest = data[pos+5:]
            # run: foo --arg
            if ' ' in rest:
                filename, args = rest.split(' ', 1)
                args = [args]
            # run: foo
            else:
                filename = rest
    else:
        if args is None:
            args = []

    sys.argv = [filename] + args[:]

    # Do one initial iteration so we can run some setup code before
    # creating/using the runner
    runner.iterate()

    execfile(sys.argv[0], globals(), globals())
