#
# Kiwi: a Framework and Enhanced Widgets for Python
#
# Copyright (C) 2001-2008 Async Open Source
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
# Author(s): Ronaldo Maia <romaia@async.com.br>
#

import gtk
import gobject

from kiwi.utils import gsignal


class ContextMenuItem(gtk.ImageMenuItem):
    gsignal('can-disable', retval=bool)

    def __init__(self, label, stock=None):
        """An menu item with an (option) icon.

        you can use this in three different ways:

        ContextMenuItem('foo')
        ContextMenuItem('foo', gtk.STOCK_PASTE)
        ContextMenuItem(gtk.STOCK_PASTE)

        The first will display an label 'foo'. The second will display the same label with the
        paste icon, and the last will display the paste icon with the default paste label
        """
        gtk.ImageMenuItem.__init__(self)

        if not stock:
            stock = label
            info = gtk.stock_lookup(label)
            if info:
                try:
                    label = info.label
                # For PyGTk
                except AttributeError:
                    label = info[1]

        lbl = gtk.AccelLabel(label)
        lbl.set_alignment(0, 0.5)
        lbl.set_use_underline(True)
        lbl.set_use_markup(True)
        self.add(lbl)

        image = gtk.Image()
        image.set_from_stock(stock, gtk.ICON_SIZE_MENU)
        self.set_image(image)


gobject.type_register(ContextMenuItem)


class ContextMenu(gtk.Menu):

    def append_separator(self):
        sep = gtk.SeparatorMenuItem()
        self.append(sep)

    def popup(self, button, time):
        self._filter_require_items()
        gtk.Menu.popup(self, None, None, None, button, time)

    def _filter_require_items(self):
        for menu_item in self.get_children():
            if not isinstance(menu_item, ContextMenuItem):
                continue

            can_select = not menu_item.emit('can-disable')
            menu_item.set_sensitive(can_select)


gobject.type_register(ContextMenu)
