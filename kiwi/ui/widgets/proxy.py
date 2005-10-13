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

import gettext

import gobject
import gtk
from gtk import gdk

from kiwi import ValueUnset
from kiwi.datatypes import ValidationError, converter
from kiwi.decorators import delayed
from kiwi.interfaces import Mixin, MixinSupportValidation
from kiwi.ui.tooltip import Tooltip

_ = gettext.gettext

class WidgetMixin(Mixin):
    """This class is a mixin that provide a common interface for KiwiWidgets.

    Usually the Proxy class need to set and get data from the widgets. It also
    need a validation framework.
    """

    def __init__(self, data_type=str, model_attribute=None,
                 default_value=None):
        self._default_value = default_value
        self._data_type = data_type
        self._model_attribute = model_attribute
        self._data_format = None

    def set_data_format(self, format):
        self._data_format = format
        
    def update(self, data):
        """Set the content of the widget with @data.

        The type of @data should match the data-type property. The two
        exceptions to this rule is ValueUnset and None. When the proxy
        call ourselves with these values we just do nothing. This probably
        means that the model is not initialized.
        """
        if data is ValueUnset or data is None:
            return
        elif not isinstance(data, self._data_type):
            raise TypeError(
                "attribute %s must be of type %s, but got %r of type %s" 
                % (self.name, self._data_type.__name__,
                   data, type(data).__name__))

    def read(self):
        """Get the content of the widget.

        The type of the return value matches the data-type property.

        This returns None if the user input a invalid value
        """
        
    def do_get_property(self, pspec):
        prop_name = pspec.name.replace("-", "_")
        func = getattr(self, "prop_get_%s" % prop_name, None)
        if not func:
            raise AttributeError("Invalid property name: %s" % pspec.name)
        return func()

    def do_set_property(self, pspec, value):
        prop_name = pspec.name.replace("-", "_")
        func = getattr(self, "prop_set_%s" % prop_name)
        if not func:
            raise AttributeError("Invalid property name: %s" % pspec.name)
        return func(value)
    
    def prop_get_data_type(self):
        return self._data_type

    def prop_set_data_type(self, data_type):
        """Set the data type for the widget
        
        data_type can be None, a type object or a string with the name of the
        type object, so None, "<type 'str'>" or 'str'
        """

        if data_type is None:
            self._data_type = None
            return

        value = None
        for t in converter.get_list():
            if t.type == data_type or t.type.__name__ == data_type:
                value = t.type
                break

        assert not isinstance(value, str), value
        
        if not value:
            type_names = converter.get_supported_types_names()
            raise TypeError("%s is not supported. Supported types are: %s"
                            % (data_type, ', '.join(type_names)))

        self._data_type = value

    def prop_get_model_attribute(self):
        return self._model_attribute

    def prop_set_model_attribute(self, attribute):
        self._model_attribute = attribute

    def prop_get_default_value(self):
        return self._default_value

    def prop_set_default_value(self, value):
        if isinstance(value, basestring):
            value = self.str2type(value)
            
        self._default_value = value
    
    def str2type(self, data):
        """Convert a string to our data type.

        This may raise exceptions if we can't do the conversion
        """
        if self._data_type is None:
            msg = "You must set the data type before converting a string"
            raise TypeError(msg)
        if data is None:
            return
        assert isinstance(data, basestring)
        # if the user clear the widget we should not raise a conversion error
        if data == '':
            return self._default_value
        return converter.from_string(self._data_type, data)

    def type2str(self, data):
        """Convert a value to a string"""
        if self._data_type is None:
            msg = "You must set the data type before converting a type"
            raise TypeError(msg)

        assert isinstance(data, self._data_type)

        kwargs = {}
        if self._data_format:
            kwargs['format'] = self._data_format

        return converter.as_string(self._data_type, data, **kwargs)

COMPLAIN_DELAY = 500

class FadeOut:
    """I am a helper class to draw the fading effect of the background
    Call my methods start() and stop() to control the fading.
    """
    MERGE_COLORS_DELAY = 100

    ERROR_COLOR = "#ffd5d5"
    # XXX: Fetch the default value from the widget instead of hard coding it.
    GOOD_COLOR = "white"

    def __init__(self, widget):
        self._widget = widget
        self._background_timeout_id = -1
        
    def _merge_colors(self, src_color, dst_color, steps=10):
        """
        Change the background of widget from src_color to dst_color
        in the number of steps specified
        """
        gdk_src = gdk.color_parse(src_color)
        gdk_dst = gdk.color_parse(dst_color)
        rs, gs, bs = gdk_src.red, gdk_src.green, gdk_src.blue
        rd, gd, bd = gdk_dst.red, gdk_dst.green, gdk_dst.blue
        rinc = (rd - rs) / float(steps)
        ginc = (gd - gs) / float(steps)
        binc = (bd - bs) / float(steps)
        for dummy in xrange(steps):
            rs += rinc
            gs += ginc
            bs += binc
            col = gtk.gdk.color_parse("#%02X%02X%02X" % (int(rs) >> 8,
                                                         int(gs) >> 8,
                                                         int(bs) >> 8))
            self._widget.update_background(col)
            yield True

        # When the fading animation is finished, set the error icon
        # We don't need to check if the state is valid, since stop()
        # (which removes this timeout) is called as soon as the user
        # types valid data.
        self._widget._draw_stock_icon(ERROR_ICON)
        yield False

    # FIXME: When we can depend on 2.4
    #@delayed(COMPLAIN_DELAY)
    def start(self):
        # If we changed during the delay
        if self._widget.is_valid():
            self.stop()
            return
        if self._background_timeout_id != -1:
            return 
        func = self._merge_colors(FadeOut.GOOD_COLOR,
                                  FadeOut.ERROR_COLOR).next
        self._background_timeout_id = (
            gobject.timeout_add(FadeOut.MERGE_COLORS_DELAY, func))
        
    start = delayed(COMPLAIN_DELAY)(start)
    
    def stop(self):
        if self._background_timeout_id != -1:
            gobject.source_remove(self._background_timeout_id)
            self._background_timeout_id = -1
        self._widget.update_background(gdk.color_parse(FadeOut.GOOD_COLOR))

MANDATORY_ICON = gtk.STOCK_EDIT
ERROR_ICON = gtk.STOCK_DIALOG_INFO

class WidgetMixinSupportValidation(WidgetMixin, MixinSupportValidation):
    """Class used by some Kiwi Widgets that need to support mandatory 
    input and validation features such as custom validation and data-type
    validation.
    
    Mandatory support provides a way to warn the user when input is necessary.
    The validatation feature provides a way to check the data entered and to
    display information about what is wrong.
    """

    def __init__(self, data_type=str, model_attribute=None,
                 default_value=None, widget=None):
        WidgetMixin.__init__(self, data_type, model_attribute, default_value)

        self._tooltip = Tooltip(self)
        self._fade = FadeOut(self)
        
        # state variables
        self._valid = True
        self._mandatory = False
        
    # Properties
    
    def prop_get_mandatory(self):
        """Checks if the Kiwi Widget is set to mandatory"""
        return self._mandatory
    
    def prop_set_mandatory(self, mandatory):
        """Sets the Kiwi Widget as mandatory, in other words, 
        the user needs to provide data to the widget 
        """
        self._mandatory = mandatory

    # Override in subclass
    
    def update_background(self, color):
        "Implement in subclass"
        
    def set_pixbuf(self, pixbuf):
        "Implement in subclass"

    def before_validate(self, data):
        "Implement in subclass"

    def get_icon_window(self):
        "Implement in subclass"
        
    # Public API

    def is_valid(self):
        return self._valid
    
    def show_tooltip(self, widget):
        self._tooltip.display(widget)

    def hide_tooltip(self):
        self._tooltip.hide()
    
    def validate_data(self, data, force=False):
        """Checks if the data is valid.
        
        Validates data-type and custom validation.
        data - the data to validate
        returns the widget data-type
        """

        old_state = self.is_valid()
        
        # check if we should draw the mandatory icon
        # this need to be done before any data conversion because we
        # we don't want to end drawing two icons
        if data is None or data == '':
            self._set_blank()
        else:
            try:
                if isinstance(data, basestring):
                    data = self.str2type(data)

                # Callbacks, this is a rather complex process

                # Step 1: A WidgetProxy subclass can implement a
                #         before_validate callback which is called before
                #         user functions.
                #         For example, check if the value is in the combo
                if self.before_validate:
                    self.before_validate(data)

                # Step 2: The widgets themselves have now valid the data
                #         Next step is to call the application specificed
                #         checks, which are found in the view.
                if data is not None:
                    # this signal calls the on_widgetname__validate method
                    # of the view class and gets the exception (if any).
                    error = self.emit("validate", data)
                    if error:
                        raise error

            except ValidationError, e:
                self._set_invalid(str(e))
                data = ValueUnset
            else:
                self._set_valid()

        # Step 3, if validation changed, emit a signal
        #         unless force is used, then we're always emitting
        new_state = self.is_valid()
        if old_state == new_state and force == False:
            return data
        
        self.emit('validation-changed', new_state)

    def _set_valid(self):
        "Valid state, Remove icons"
        self._fade.stop()
        self.set_pixbuf(None)
        self._valid = True
        
    def _set_invalid(self, text):
        "Invalid state, when the input is invalid"
        self._fade.start()
        self._tooltip.set_text(text)
        self._valid = False
        
    def _set_blank(self):
        "Blank state, for mandatory, draw an icon"
        if self._mandatory:
            self._draw_stock_icon(MANDATORY_ICON)
            self._tooltip.set_text(_('This field is mandatory'))
            valid = False
        else:
            valid = True
        self._valid = valid

    def _draw_stock_icon(self, stock_id):
        icon = self.render_icon(stock_id, gtk.ICON_SIZE_MENU)
        self.set_pixbuf(icon)
        self.queue_draw()
