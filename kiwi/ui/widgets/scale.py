#
# Kiwi: a Framework and Enhanced Widgets for Python
#
# Copyright (C) 2007 Async Open Source
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
#            Mauricio B. C. Vieira <mauricio.vieira@gmail.com>
#

"""GtkHScale and GtkVScale support for the Kiwi Framework"""

import gtk

from kiwi.ui.proxywidget import ProxyWidgetMixin
from kiwi.utils import PropertyObject, gsignal, type_register

class _ProxyScale:

    # changed allowed data types because scales can only
    # accept float values
    allowed_data_types = float,

    gsignal('value_changed', 'override')
    def do_value_changed(self):
        self.emit('content-changed')
        self.chain()

    def read(self):
        return self.get_value()

    def update(self, data):
        self.set_value(data)


class ProxyHScale(_ProxyScale, PropertyObject, ProxyWidgetMixin, gtk.HScale):
    __gtype_name__ = 'ProxyHScale'

    def __init__(self):
        ProxyWidgetMixin.__init__(self)
        PropertyObject.__init__(self, data_type=float)
        gtk.HScale.__init__(self)

type_register(ProxyHScale)


class ProxyVScale(_ProxyScale, PropertyObject, ProxyWidgetMixin, gtk.VScale):
    __gtype_name__ = 'ProxyVScale'

    def __init__(self, adjustment=None):
        ProxyWidgetMixin.__init__(self)
        PropertyObject.__init__(self, data_type=float)
        gtk.VScale.__init__(self)

type_register(ProxyVScale)
