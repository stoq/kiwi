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

"""GtkButton support for the Kiwi Framework"""

import datetime

import gobject
import gtk
from gtk import gdk

from kiwi import ValueUnset
from kiwi.datatypes import number
from kiwi.ui.proxywidget import ProxyWidgetMixin
from kiwi.utils import gsignal

class ProxyButton(gtk.Button, ProxyWidgetMixin):
    """
    A ProxyButton is a Button subclass which is implementing the features
    required to be used inside the kiwi framework.

    It has a specific feature not found in other implementations. If
    the datatype is set to pixbuf a gtk.Image will be constructed from the
    pixbuf and be set as a child for the Button
    """

    allowed_data_types = (basestring, datetime.date, datetime.datetime,
                          datetime.time, gdk.Pixbuf) + number
    __gtype_name__ = 'ProxyButton'

    data_type = gobject.property(
        getter=ProxyWidgetMixin.get_data_type,
        setter=ProxyWidgetMixin.set_data_type,
        type=str, blurb='Data Type')
    model_attribute = gobject.property(type=str, blurb='Model attribute')
    gsignal('content-changed')
    gsignal('validation-changed', bool)
    gsignal('validate', object, retval=object)

    def __init__(self):
        gtk.Button.__init__(self)
        ProxyWidgetMixin.__init__(self)
        self.props.data_type = str

    def read(self):
        if self.data_type == 'Pixbuf':
            image = self.get_image()
            if not image:
                return

            storage_type = image.get_storage_type()
            if storage_type != gtk.IMAGE_PIXBUF:
                raise ValueError(
                    "the image of a ProxyButton must be loaded "
                    "from a pixbuf, not %s" % storage_type)
            return image.get_pixbuf()
        else:
            return self._from_string(self.get_label())

    def update(self, data):
        if self.data_type == 'Pixbuf':
            if data == ValueUnset:
                data = None

            if not data:
                image = None
            else:
                image = gtk.Image()
                image.set_from_pixbuf(data)
                image.show()

            self.set_property('image', image)
        else:
            if data is None:
                text = ""
            else:
                text = self._as_string(data)
            self.set_label(text)

        self.emit('content-changed')

