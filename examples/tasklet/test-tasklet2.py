"""
gtasklets demo program #2

needs patch at http://bugzilla.gnome.org/show_bug.cgi?id=139176
"""

from optparse import OptionParser
import os
import subprocess
import sys

from gi.repository import GObject
from gi.repository import Gtk, Gdk
from gi.repository import Pango

from kiwi import tasklet

try:
    import win32api

    def killproc(pid):
        """kill function for Win32"""
        handle = win32api.OpenProcess(1, 0, pid)
        return (0 != win32api.TerminateProcess(handle, 0))
except ImportError:
    import signal

    def killproc_(pid):
        """kill function for POSIX"""
        return os.kill(pid, signal.SIGTERM)

    killproc = killproc_  # pyflakes


def process_stdout_sink(chan, buffer, view):
    timeout = tasklet.WaitForTimeout(200)
    iowait = tasklet.WaitForIO(chan, priority=1000)
    msgwait = tasklet.WaitForMessages(accept='quit')
    while True:
        yield iowait, msgwait
        ev = tasklet.get_event()
        if isinstance(ev, tasklet.Message) and ev.name == 'quit':
            return
        assert ev is iowait
        text = chan.read()
        buffer.insert(buffer.get_end_iter(), text)
        view.scroll_to_mark(buffer.get_insert(), 0)
        ## Now wait for some time, don't let process output "drown"
        ## the TextView updates
        yield timeout, tasklet.WaitForMessages(defer='quit')
        ev = tasklet.get_event()
        assert ev is timeout


def main():
    parser = OptionParser(usage="usage: %prog command")
    (options, args) = parser.parse_args()
    if len(args) != 1:
        parser.print_help()
        sys.exit(1)

    win = Gtk.Window()
    textview = Gtk.TextView()
    textview.modify_font(Pango.FontDescription("Monospace"))
    textview.show()
    sw = Gtk.ScrolledWindow()
    sw.add(textview)
    sw.show()
    win.add(sw)
    win.set_default_size(Gdk.Screen.width() * 2 / 3,
                         Gdk.Screen.height() * 2 / 3)
    win.show()

    ## launch process
    proc = subprocess.Popen(args[0], shell=True, stdout=subprocess.PIPE,
                            bufsize=1, close_fds=True)
    win.set_title("%s (running)" % args[0])
    # print proc.stdout, type(proc.stdout), dir(proc.stdout)
    chan = GObject.IOChannel(filedes=proc.stdout.fileno())
    chan.set_flags(GObject.IO_FLAG_NONBLOCK)
    sink = tasklet.run(process_stdout_sink(chan, textview.get_buffer(),
                                           textview))

    ## child watch
    yield (tasklet.WaitForProcess(proc.pid),
           tasklet.WaitForSignal(win, "destroy"))

    if isinstance(tasklet.get_event(), tasklet.WaitForSignal):
        killproc(proc.pid)
        Gtk.main_quit()
    else:
        ## stop reader
        yield tasklet.Message("quit", dest=sink)
        win.set_title("%s (completed)" % args[0])
        yield tasklet.WaitForSignal(win, "destroy")
        tasklet.get_event()
        Gtk.main_quit()

if __name__ == '__main__':
    tasklet.run(main())
    Gtk.main()
