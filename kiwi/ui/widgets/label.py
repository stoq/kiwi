#
# Kiwi: a Framework and Enhanced Widgets for Python
#
# Copyright (C) 2003-2005 Async Open Source
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
# Author(s): Lorenzo Gil Sanchez <lgs@sicem.biz>
#            Gustavo Rahal <gustavo@async.com.br>
#

"""GtkLabel support for the Kiwi Framework

The :class:`Label` is also extended to support some basic markup like
:class:`Label.set_bold`"""

import datetime

import gobject
import gtk

from kiwi.datatypes import number, ValueUnset
from kiwi.ui.gadgets import set_foreground
from kiwi.ui.proxywidget import ProxyWidgetMixin
from kiwi.utils import gsignal, type_register


class ProxyLabel(gtk.Label, ProxyWidgetMixin):
    __gtype_name__ = 'ProxyLabel'
    model_attribute = gobject.property(type=str, blurb='Model attribute')
    # We wont emmit content-changed, but kiwi.proxy still relies on this.
    gsignal('content-changed')

    allowed_data_types = (basestring, datetime.date, datetime.datetime,
                          datetime.time) + number
    _label_replacements = {}

    def __init__(self, label='', data_type=None):
        """
        Create a new ProxyLabel object.
        :param label: initial text
        :param data_type: data type of label
        """
        gtk.Label.__init__(self, label)
        ProxyWidgetMixin.__init__(self)
        self.props.data_type = data_type
        self.set_use_markup(True)
        self._attr_dic = {"style": None,
                          "weight": None,
                          "size": None,
                          "underline": None}
        self._size_list = ('xx-small', 'x-small',
                           'small', 'medium',
                           'large', 'x-large',
                           'xx-large')

        self.connect("notify::label", self._on_label_changed)
        self._block_notify_label = False

    def _set_data_type(self, data_type):
        if not ProxyWidgetMixin.set_data_type(self, data_type):
            return

    data_type = gobject.property(
        getter=ProxyWidgetMixin.get_data_type,
        setter=_set_data_type,
        type=str, blurb='Data Type')

    @classmethod
    def replace(cls, markup, value):
        cls._label_replacements[markup] = value

    def _on_label_changed(self, label, param):
        if self._block_notify_label:
            self._block_notify_label = False
            return

        text = self.get_property('label')
        for rep in self._label_replacements.keys():
            if rep in text:
                text = text.replace(rep, self._label_replacements[rep])

        self._block_notify_label = True
        self.set_property('label', text)

    def read(self):
        return self._from_string(self.get_text())

    def update(self, data):
        if data is None or data is ValueUnset:
            text = ""
        else:
            text = self._as_string(data)
        self.set_text(text)

    def _apply_attributes(self):
        # sorting is been done so we can be sure of the order of the
        # attributes. Helps writing tests cases
        attrs = self._attr_dic
        keys = attrs.keys()
        keys.sort()

        attr_pairs = ['%s="%s"' % (key, attrs[key]) for key in keys
                      if attrs[key]]
        self.set_markup('<span %s>%s</span>' % (
            ' '.join(attr_pairs),
            self.get_text()))

    def _set_text_attribute(self, attribute_name, attr, value):
        if value:
            if self._attr_dic[attribute_name] is None:
                self._attr_dic[attribute_name] = attr
                self._apply_attributes()
        else:
            if self._attr_dic[attribute_name] is not None:
                self._attr_dic[attribute_name] = None
                self._apply_attributes()

    def set_bold(self, value):
        """ If True set the text to bold. False sets the text to normal """
        self._set_text_attribute("weight", "bold", value)

    def set_italic(self, value):
        """ Enable or disable italic text
        :param value: Allowed values:
          - True: enable Italic attribute
          - False: disable Italic attribute
        """
        self._set_text_attribute("style", "italic", value)

    def set_underline(self, value):
        """ Enable or disable underlined text
        :param value: Allowed values:
          - True: enable Underline attribute
          - Fase: disable Underline attribute
        """
        self._set_text_attribute("underline", "single", value)

    def set_size(self, size=None):
        """ Set the size of the label. If size is empty the label will be
        set to the default size.
        :param size: Allowed values:
          - xx-small
          - x-small
          - small
          - medium,
          - large
          - x-large
          - xx-large
        :type size: string
        """
        if (size is not None and
            size not in self._size_list):
            raise ValueError('Size of "%s" label is not valid' %
                             self.get_text())

        self._attr_dic["size"] = size
        self._apply_attributes()

    def set_text(self, text):
        """ Overrides gtk.Label set_text method. Sets the new text of
        the label but keeps the formating
        :param text: label
        :type text: string
        """
        gtk.Label.set_text(self, text)
        self._apply_attributes()

    def set_color(self, color):
        set_foreground(self, color)

type_register(ProxyLabel)
