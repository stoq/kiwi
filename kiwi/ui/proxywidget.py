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
# Author(s): Christian Reis <kiko@async.com.br>
#            Lorenzo Gil Sanchez <lgs@sicem.biz>
#            Gustavo Rahal <gustavo@async.com.br>
#            Johan Dahlin <jdahlin@async.com.br>
#            Daniel Saran R. da Cunha <daniel@async.com.br>
#

"""Basic classes for widget support for the Kiwi Framework"""

import gettext

import gobject
import gtk
from gtk import gdk

from kiwi import ValueUnset
from kiwi.component import implements
from kiwi.datatypes import ValidationError, converter, BaseConverter
from kiwi.environ import environ
from kiwi.interfaces import IProxyWidget, IValidatableProxyWidget
from kiwi.log import Logger
from kiwi.ui.gadgets import FadeOut

log = Logger('widget proxy')

_ = lambda m: gettext.dgettext('kiwi', m)

class _PixbufConverter(BaseConverter):
    type = gdk.Pixbuf
    name = 'Pixbuf'

    def as_string(self, value, format='png'):
        if value is ValueUnset:
            return ''
        buffer = []
        value.save_to_callback(buffer.append, format)
        string = ''.join(buffer)
        return string

    def from_string(self, value, format='png'):
        loader = gdk.PixbufLoader(format)
        try:
            loader.write(value)
            loader.close()
        except gobject.GError, e:
            raise ValidationError(_("Could not load image: %s") % e)

        pixbuf = loader.get_pixbuf()
        return pixbuf

converter.add(_PixbufConverter)


class ProxyWidgetMixin(object):
    """This class is a mixin that provide a common interface for KiwiWidgets.

    Usually the Proxy class need to set and get data from the widgets. It also
    need a validation framework.

    @cvar allowed_data_types: A list of types which we are allowed to use
      in this class.
    """

    implements(IProxyWidget)

    allowed_data_types = ()

    # To be able to call the as/from_string without setting the data_type
    # property and still receiving a good warning.
    _converter = None

    def __init__(self):
        if not type(self.allowed_data_types) == tuple:
            raise TypeError("%s.allowed_data_types must be a tuple" % (
                self.allowed_data_types))
        self._data_format = None
        self._converter_options = {}
        self._data_type = None

    # Properties

    def get_data_type(self):
        return self._data_type

    def set_data_type(self, data_type):
        """Set the data type for the widget

        @param data_type: can be None, a type object or a string with the
                          name of the type object, so None, "<type 'str'>"
                          or 'str'
        """
        if data_type is None:
            return data_type
        elif data_type == '':
            return None

        # This may convert from string to type,
        # A type object will always be returned
        data_type = converter.check_supported(data_type)
        self._converter = converter.get_converter(data_type)
        self._data_type = self._converter.type.__name__
        return self._converter.type.__name__

    # Public API
    def set_data_format(self, format):
        self._data_format = format

    def set_options_for_datatype(self, datatype, **options):
        """Set some options to be passed to the datatype converter.
        Any additional parameter will be passed the the converter when
        converting an object to a string, for displaying in the widget. Note
        that the converter.as_string method should be able to handle such
        parameters.

        @param datatype: the datatype.
        """
        if not options:
            raise ValueError

        self._converter_options[datatype] = options

    def read(self):
        """Get the content of the widget.
        The type of the return value
        @returns: None if the user input a invalid value
        @rtype: Must matche the data-type property.
        """
        raise NotImplementedError

    def update(self, value):
        """
        Update the content value of the widget.
        @param value:
        """
        raise NotImplementedError

    # Private

    def _as_string(self, data):
        """Convert a value to a string
        @param data: data to convert
        """
        conv = self._converter
        if conv is None:
            conv = converter.get_converter(str)

        return conv.as_string(data, format=self._data_format,
                              **self._converter_options.get(conv.type,{}))

    def _from_string(self, data):
        """Convert a string to the data type of the widget
        This may raise a L{kiwi.datatypes.ValidationError} if conversion
        failed
        @param data: data to convert
        """
        conv = self._converter
        if conv is None:
            conv = converter.get_converter(str)

        return conv.from_string(data)

VALIDATION_ICON_WIDTH = 16
MANDATORY_ICON = gtk.STOCK_EDIT
ERROR_ICON = gdk.pixbuf_new_from_file(
    environ.find_resource('pixmap', 'validation-error-16.png'))

class ValidatableProxyWidgetMixin(ProxyWidgetMixin):
    """Class used by some Kiwi Widgets that need to support mandatory
    input and validation features such as custom validation and data-type
    validation.

    Mandatory support provides a way to warn the user when input is necessary.
    The validatation feature provides a way to check the data entered and to
    display information about what is wrong.
    """

    implements(IValidatableProxyWidget)

    def __init__(self, widget=None):
        ProxyWidgetMixin.__init__(self)

        self._valid = True
        self._fade = FadeOut(self)
        self._fade.connect('color-changed', self._on_fadeout__color_changed)
        self.connect('notify::mandatory', self._on_notify__mandatory)

    # Override in subclass

    def update_background(self, color):
        "Implement in subclass"

    def get_background(self):
        "Implement in subclass"

    def set_pixbuf(self, pixbuf):
        "Implement in subclass"

    def set_tooltip(self, text):
        "Implement in subclass"

    # Public API

    def is_valid(self):
        """
        Verify the widget state.
        @returns: True if the widget is in validated state
        """
        return self._valid

    def validate(self, force=False):
        """Checks if the data is valid.
        Validates data-type and custom validation.

        @param force: if True, force validation
        @returns:     validated data or ValueUnset if it failed
        """

        # If we're not visible or sensitive return a blank value, except
        # when forcing the validation
        if not force and (not self.get_property('visible') or
                          not self.get_property('sensitive')):
            return ValueUnset

        try:
            data = self.read()
            log.debug('Read %r for %s' %  (data, self.model_attribute))

            # check if we should draw the mandatory icon
            # this need to be done before any data conversion because we
            # we don't want to end drawing two icons
            if self.mandatory and (data == None or
                                   data == '' or
                                   data == ValueUnset):
                self.set_blank()
                return ValueUnset
            else:

                # The widgets themselves have now valid the data
                # Next step is to call the application specificed
                # checks, which are found in the view.
                if data is not None and data is not ValueUnset:
                    # this signal calls the on_widgetname__validate method
                    # of the view class and gets the exception (if any).
                    error = self.emit("validate", data)
                    if error:
                        raise error

            self.set_valid()
            return data
        except ValidationError, e:
            self.set_invalid(str(e))
            return ValueUnset

    def set_valid(self):
        """Changes the validation state to valid, which will remove icons and
        reset the background color
        """

        log.debug('Setting state for %s to VALID' % self.model_attribute)
        self._set_valid_state(True)

        self._fade.stop()
        self.set_pixbuf(None)

    def set_invalid(self, text=None, fade=True):
        """Changes the validation state to invalid.
        @param text: text of tooltip of None
        @param fade: if we should fade the background
        """
        log.debug('Setting state for %s to INVALID' % self.model_attribute)

        self._set_valid_state(False)

        # If there is no error text, set a generic one so the error icon
        # still have a tooltip
        if not text:
            text = _("'%s' is not a valid value for this field") % self.read()

        if not fade:
            self.set_pixbuf(ERROR_ICON)
            self.update_background(gtk.gdk.color_parse(self._fade.ERROR_COLOR))
            return

        # When the fading animation is finished, set the error icon
        # We don't need to check if the state is valid, since stop()
        # (which removes this timeout) is called as soon as the user
        # types valid data.
        def done(fadeout, c):
            self.set_pixbuf(ERROR_ICON)
            self.queue_draw()
            fadeout.disconnect(c.signal_id)

        class SignalContainer:
            pass
        c = SignalContainer()
        c.signal_id = self._fade.connect('done', done, c)

        if self._fade.start(self.get_background()):
            self.set_pixbuf(None)

        # If you try to set the tooltip before the icon in gtk.Entry, a
        # segfault happens.
        self.set_tooltip(text)

    def set_blank(self):
        """Changes the validation state to blank state, this only applies
        for mandatory widgets, draw an icon and set a tooltip"""

        log.debug('Setting state for %s to BLANK' % self.model_attribute)

        if self.mandatory:
            self._draw_stock_icon(MANDATORY_ICON)
            self.set_tooltip(_('This field is mandatory'))
            self._fade.stop()
            valid = False
        else:
            valid = True

        self._set_valid_state(valid)

    # Private

    def _set_valid_state(self, state):
        """Updates the validation state and emits a signal if it changed"""
        # FIXME: This should not happen, but somehow, model_attribute is being
        # set too late in some cases.
        if not self.model_attribute:
            return

        if self._valid == state:
            return

        self.emit('validation-changed', state)
        self._valid = state

    def _draw_stock_icon(self, stock_id):
        icon = self.render_icon(stock_id, gtk.ICON_SIZE_MENU)
        self.set_pixbuf(icon)
        self.queue_draw()

    # Callbacks

    def _on_fadeout__color_changed(self, fadeout, color):
        self.update_background(color)

    def _on_notify__mandatory(self, obj, pspec):
        self.validate()
