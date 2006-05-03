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

import gtk
from gtk import gdk

from kiwi import ValueUnset
from kiwi.component import implements
from kiwi.datatypes import ValidationError, converter
from kiwi.environ import environ
from kiwi.interfaces import IProxyWidget, IValidatableProxyWidget
from kiwi.log import Logger
from kiwi.ui.gadgets import FadeOut
from kiwi.utils import gsignal, gproperty

log = Logger('widget proxy')

_ = gettext.gettext

class ProxyWidgetMixin(object):
    """This class is a mixin that provide a common interface for KiwiWidgets.

    Usually the Proxy class need to set and get data from the widgets. It also
    need a validation framework.

    @cvar allowed_data_types: A list of types which we are allowed to use
      in this class.
    """

    implements(IProxyWidget)

    gsignal('content-changed')
    gsignal('validation-changed', bool)
    gsignal('validate', object, retval=object)

    gproperty('data-type', object, blurb='Data Type')
    gproperty('model-attribute', str, blurb='Model attribute')

    allowed_data_types = object,

    # To be able to call the as/from_string without setting the data_type
    # property and still receiving a good warning.
    _converter = None

    def __init__(self):
        if not type(self.allowed_data_types) == tuple:
            raise TypeError("%s.allowed_data_types must be a tuple" % (
                self.allowed_data_types))
        self._data_format = None

    # Properties

    def prop_set_data_type(self, data_type):
        """Set the data type for the widget

        @param data_type: can be None, a type object or a string with the
                          name of the type object, so None, "<type 'str'>"
                          or 'str'
        """
        if data_type is None:
            return data_type

        # This may convert from string to type,
        # A type object will always be returned
        data_type = converter.check_supported(data_type)

        if not issubclass(data_type, self.allowed_data_types):
            raise TypeError(
                "%s only accept %s types, not %r"
                % (self,
                   ' or '.join([t.__name__ for t in self.allowed_data_types]),
                   data_type))

        self._converter = converter.get_converter(data_type)
        return data_type

    # Public API
    def set_data_format(self, format):
        self._data_format = format

    def read(self):
        """Get the content of the widget.
        The type of the return value
        @returns: None if the user input a invalid value
        @rtype: Must matche the data-type property.
        """
        raise NotImplementedError

    def update(self, value):
        """
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
            raise AssertionError(
                "You need to set a data type before calling _as_string")

        return conv.as_string(data, format=self._data_format)

    def _from_string(self, data):
        """Convert a string to the data type of the widget
        This may raise a L{kiwi.datatypes.ValidationError} if conversion
        failed
        @param data: data to convert
        """
        conv = self._converter
        if conv is None:
            raise AssertionError(
                "You need to set a data type before calling _from_string")

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

    gproperty('mandatory', bool, default=False)

    def __init__(self, widget=None):
        ProxyWidgetMixin.__init__(self)

        self._valid = True
        self._fade = FadeOut(self)
        self._fade.connect('color-changed', self._on_fadeout__color_changed)

    # Override in subclass

    def update_background(self, color):
        "Implement in subclass"

    def set_pixbuf(self, pixbuf):
        "Implement in subclass"

    def get_icon_window(self):
        "Implement in subclass"

    def set_tooltip(self, text):
        "Implement in subclass"

    # Public API

    def is_valid(self):
        """
        @returns: True if the widget is in validated state
        """
        return self._valid

    def validate(self, force=False):
        """Checks if the data is valid.
        Validates data-type and custom validation.

        @param force: if True, force validation
        @returns:     validated data or ValueUnset if it failed
        """

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

        if not fade:
            return

        # If there is no error text, set a generic one so the error icon
        # still have a tooltip
        if not text:
            text = _("'%s' is not a valid value for this field") % self.read()

        self.set_tooltip(text)

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

        if self._fade.start():
            self.set_pixbuf(None)

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
        """Updates the validation state and emits a signal iff it changed"""

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
