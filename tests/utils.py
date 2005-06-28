import gtk

from kiwi.initgtk import gtk
from time import sleep
import sys

sys.path.insert(0, "..")

def refresh_gui(delay=0):
    while gtk.events_pending():
        gtk.main_iteration_do(block=False)
    sleep(delay)
