#
# Kiwi: a Framework and Enhanced Widgets for Python
#
# Copyright (C) 2005,2006 Async Open Source
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

import logging

from gtk.glade import XML


log = logging.getLogger('libgladeloader')


class LibgladeWidgetTree(XML):
    def __init__(self, view, gladefile, domain=None):
        self._view = view
        self._gladefile = gladefile
        XML.__init__(self, gladefile, domain)
        self._widgets = [w.get_name() for w in self.get_widget_prefix('')]
        self._attach_widgets()

    def _attach_widgets(self):
        # Attach widgets in the widgetlist to the view specified, so
        # widgets = [label1, button1] -> view.label1, view.button1
        for w in self._widgets:
            widget = XML.get_widget(self, w)
            if widget is not None:
                setattr(self._view, w, widget)
            else:
                log.warn("Widget %s was not found in glade widget tree." % w)

    def get_widget(self, name):
        """Retrieves the named widget from the View (or glade tree)"""
        name = name.replace('.', '_')
        widget = XML.get_widget(self, name)

        if widget is None:
            raise AttributeError(
                "Widget %s not found in view %s" % (name, self._view))
        return widget

    def get_widgets(self):
        return self.get_widget_prefix('')

    def get_sizegroups(self):
        return []
