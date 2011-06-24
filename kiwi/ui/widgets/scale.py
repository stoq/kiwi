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

import gobject
import gtk

from kiwi import ValueUnset
from kiwi.ui.proxywidget import ProxyWidgetMixin
from kiwi.utils import gsignal, type_register

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
        if data is None or data is ValueUnset:
            self.set_value(0.)
        else:
            self.set_value(data)


class ProxyHScale(_ProxyScale, ProxyWidgetMixin, gtk.HScale):
    __gtype_name__ = 'ProxyHScale'
    data_type = gobject.property(
        getter=ProxyWidgetMixin.get_data_type,
        setter=ProxyWidgetMixin.set_data_type,
        type=str, blurb='Data Type')
    model_attribute = gobject.property(type=str, blurb='Model attribute')
    gsignal('content-changed')
    gsignal('validation-changed', bool)
    gsignal('validate', object, retval=object)

    def __init__(self):
        gtk.HScale.__init__(self)
        ProxyWidgetMixin.__init__(self)
        self.props.data_type = float

type_register(ProxyHScale)


class ProxyVScale(_ProxyScale, ProxyWidgetMixin, gtk.VScale):
    __gtype_name__ = 'ProxyVScale'
    data_type = gobject.property(
        getter=ProxyWidgetMixin.get_data_type,
        setter=ProxyWidgetMixin.set_data_type,
        type=str, blurb='Data Type')
    model_attribute = gobject.property(type=str, blurb='Model attribute')
    gsignal('content-changed')
    gsignal('validation-changed', bool)
    gsignal('validate', object, retval=object)

    def __init__(self):
        gtk.VScale.__init__(self)
        ProxyWidgetMixin.__init__(self)
        self.props.data_type = float

type_register(ProxyVScale)
