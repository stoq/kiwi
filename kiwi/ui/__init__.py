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

"""User interface: Framework and Widget support"""


try:
    import gi
    # This will raise ValueError if the required version was not found
    gi.require_version('Gtk', '3.0')
except (ImportError, ValueError) as e:
    raise SystemExit(
        "GTK+ 3.0.0 or higher is required by kiwi.ui\n"
        "Error was: {}".format(e))

from gi.repository import Gtk, Gdk

from kiwi.environ import environ


style_provider = Gtk.CssProvider()
style_provider.load_from_path(
    environ.get_resource_filename('kiwi', 'css', 'kiwi.css'))
screen = Gdk.Screen.get_default()
if screen is not None:
    Gtk.StyleContext.add_provider_for_screen(
        screen,
        style_provider,
        Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
