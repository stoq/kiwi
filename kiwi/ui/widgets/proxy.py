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

import time

import gobject
import gtk
from gtk import gdk

from kiwi import ValueUnset
from kiwi.datatypes import ValidationError, converter
from kiwi.interfaces import Mixin, MixinSupportValidation
from kiwi.ui.gadgets import set_background

MERGE_COLORS_DELAY = 100
CURSOR_POS_CHECKING_DELAY = 200

__pychecker__ = 'no-classattr'

def merge_colors(widget, src_color, dst_color, steps=10):
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
        set_background(widget, "#%02X%02X%02X" % (int(rs) >> 8,
                                                  int(gs) >> 8,
                                                  int(bs) >> 8))
        yield True

    yield False

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

    def prop_set_data_type(self, obj):
        """Set the data type for the widget
        
        data_type can be None, a type object or a string with the name of the
        type object, so None, "<type 'str'>" or 'str'
        """

        if obj is None:
            self._data_type = None
            return

        data_type = None
        for t in converter.get_list():
            if t.type == obj or t.type.__name__ == obj:
                data_type = t.type
                break

        assert not isinstance(data_type, str), data_type
        
        if not data_type:
            type_names = converter.get_supported_types_names()
            raise TypeError("%s is not supported. Supported types are: %s"
                            % (obj, ', '.join(type_names)))

        self._data_type = data_type

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
        
ERROR_COLOR = "#ffa5a5"
GOOD_COLOR = "white"

MANDATORY_ICON = gtk.STOCK_EDIT
INFO_ICON = gtk.STOCK_DIALOG_INFO

# amount of time until we complain if the data is wrong (seconds)
COMPLAIN_DELAY = 1

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
        
        self._error_tooltip = ErrorTooltip(self)
        
        # this flag means the data in the entry does not validate
        self._invalid_data = False
        # we also want to check if the widget is empty, which is an error
        # for mandatory widgets
        self._blank_data = True
        
        # this is the last time the user changed the widget
        self._last_change_time = None

        # id that paints the background red
        self._background_timeout_id = -1
        # id for idle that checks the cursor position
        self._get_cursor_position_id = -1
        # id for the idle that check if we should complain
        self._complaint_checker_id = -1

        # stores the position of the information icon
        self._info_icon_position = False

        # state variables
        self._mandatory = False
        self._draw_mandatory_icon = False
        
        self._draw_info_icon = False

        # this attribute stores the info on where to draw icons and paint
        # the background
        if widget is None:
            widget = self
        self._widget_to_draw = widget

    def prop_get_mandatory(self):
        """Checks if the Kiwi Widget is set to mandatory"""
        return self._mandatory
    
    def prop_set_mandatory(self, mandatory):
        """Sets the Kiwi Widget as mandatory, in other words, 
        the user needs to provide data to the widget 
        """
        self._mandatory = mandatory

    def before_validate(self, data):
        pass
    
    def validate_data(self, data, force=False):
        """Checks if the data is valid.
        
        Validates data-type and custom validation.
        data - the data to validate
        returns the widget data-type
        """
        
        old_state = self.is_correct()
        
        # check if we should draw the man a stringdatory icon
        # this need to be done before any data conversion because we
        # we don't want to end drawing two icons
        if data is None or data == '':
            self._blank_data = True
        else:
            self._blank_data = False

        self.draw_mandatory_icon_if_needed()            

        try:
            if isinstance(data, basestring):
                data = self.str2type(data)
                
            # Callbacks, this is a rather complex process
            
            # Step 1: A WidgetProxy subclass can implement a before_validate
            #         callback which is called before user functions.
            #         For example, check if the value is in the combo
            if self.before_validate:
                self.before_validate(data)

            # Step 2: The widgets themselves have now validated the data
            #         Next step is to call the application specificed
            #         checks, which are found in the view.
            if data is not None:
                # this signal calls the on_widgetname__validate method of the 
                # view class and gets the exception (if any).
                error = self.emit("validate", data)
                if error:
                    raise error
            
            # if the data is good we don't wait for the idle to inform
            # the user
            self._stop_complaining()

        except ValidationError, e:
            # Show the error icon
            self._validation_error(e)
            data = ValueUnset

        # Step 3, if validation changed, emit a signal
        #         unless force is used, then we're always emitting
        new_state = self.is_correct()
        if old_state == new_state and force == False:
            return data
        
        self.emit('validation-changed', new_state)

        return data
    
    def _validation_error(self, e):
        if self._invalid_data:
            self._blank_data = False
            
        self._invalid_data = True
        self._error_tooltip.set_error_text(str(e))
        if self._complaint_checker_id == -1:
            self._complaint_checker_id = \
                gobject.idle_add(self._check_for_complaints)
            self._get_cursor_position_id = \
                gobject.timeout_add(CURSOR_POS_CHECKING_DELAY,
                                    self._get_cursor_position)

    def _check_for_complaints(self):
        """Check for existing complaints and when to start complaining is case
        the input is wrong
        """
        if not self._last_change_time:
            # the user has not started to type
            return True
        
        elapsed_time = time.time() - self._last_change_time
        if elapsed_time < COMPLAIN_DELAY:
            return True
        
        if not self._invalid_data:
            return True

        return self._maybe_draw_icon()
    
    def _maybe_draw_icon(self):
        # if we are already complaining, don't complain again
        if self._background_timeout_id != -1:
            return True
        
        self._draw_info_icon = True
        self.queue_draw()
        func = merge_colors(self._widget_to_draw, 
                            GOOD_COLOR, ERROR_COLOR).next
        t_id = gobject.timeout_add(MERGE_COLORS_DELAY, func)
        self._background_timeout_id = t_id
        
        return False
        
    def _stop_complaining(self):
        """If the input is corrected this method stop some activits that
        where necessary while complaining"""
        self._invalid_data = False
        # if we are complaining
        if self._background_timeout_id != -1:
            gobject.source_remove(self._background_timeout_id)
            gobject.source_remove(self._complaint_checker_id)
            # before removing the get_cursor_position idle we need to be sure
            # that the tooltip is not been displayed
            self._error_tooltip.hide()
            gobject.source_remove(self._get_cursor_position_id)
            self._background_timeout_id = -1
            self._complaint_checker_id = -1
        set_background(self._widget_to_draw, GOOD_COLOR)
        self._draw_info_icon = False

    def _get_cursor_position(self):
        """If the input is wrong (as consequence the icon is been displayed),
        this method reads the mouse cursor position and checks if it's
        on top of the information icon
        """
        if not self._info_icon_position:
            self._error_tooltip.hide()
            return True
        
        icon_x, icon_x_range, icon_y, icon_y_range = self._info_icon_position
        
        toplevel = self.get_toplevel()
        pointer_x, pointer_y = toplevel.get_pointer()
        
        if pointer_x not in icon_x_range or pointer_y not in icon_y_range:
            self._error_tooltip.hide()
            return True
        
        if self._error_tooltip.flags() & gtk.VISIBLE:
            return True
            
        self._error_tooltip.display(toplevel, self)
                
        return True

    def _draw_icon(self, window):
        # if there is something wrong in the validation (draw_info_icon = True)
        # the widget should not be empty (draw_mandatory_icon = True)
        assert not (self._draw_mandatory_icon and self._draw_info_icon)
        
        if self._draw_mandatory_icon:
            icon = MANDATORY_ICON
        elif self._draw_info_icon:
            icon = INFO_ICON
        else:
            return
            
        (iconx, icony,
         pixw, pixh, pixbuf) = self._render_icon(icon, self._widget_to_draw)
        
        self._draw_pixbuf(window, iconx, icony, pixbuf, pixw, pixh)
        
        if self._draw_info_icon:
            iconx_range = range(iconx, iconx + pixw)
            icony_range = range(icony, icony + pixh)
            self._info_icon_position = (iconx, iconx_range,
                                        icony, icony_range)

    def _render_icon(self, icon, widget):
        widget_x, widget_y, widget_w, widget_h = widget.get_allocation()
        pixbuf = self.render_icon(icon, gtk.ICON_SIZE_MENU)
        pixw = pixbuf.get_width()
        pixh = pixbuf.get_height()
        
        return (widget_x + widget_w - pixw,
                widget_y + widget_h - pixh,
                pixw, pixh, pixbuf)

    def _draw_pixbuf(self, window, iconx, icony, pixbuf, pixw, pixh):
        area_window = window.get_children()[0]
        winw, winh = area_window.get_size()
            
        area_window.draw_pixbuf(None, pixbuf, 0, 0, 
                                winw - pixw, (winh - pixh)/2, pixw, pixh)

    def is_correct(self):
        if self._invalid_data:
            return False

        if self._blank_data and self._mandatory:
            return False

        return True

    def draw_mandatory_icon_if_needed(self):
        if self._blank_data and self._mandatory:
            self._draw_mandatory_icon = True
        else:
            self._draw_mandatory_icon = False
        self.queue_draw()
        
class ErrorTooltip(gtk.Window):
    """Small tooltip window that popup when the user click on top of the error
    (information) icon"""
    def __init__(self, widget):
        gtk.Window.__init__(self, gtk.WINDOW_POPUP)
        
        eventbox = gtk.EventBox()
        set_background(eventbox, "#fcffcd")

        alignment = gtk.Alignment()
        alignment.set_border_width(4)
        self._label = gtk.Label()
        alignment.add(self._label)
        eventbox.add(alignment)
        self.add(eventbox)

    def set_error_text(self, text):
        self._label.set_text(text)
    
    def display(self, window, widget):
        window_x, window_y = window.window.get_origin()
        entry_x, entry_y, entry_width, entry_height = widget.get_allocation()
        tooltip_width, tooltip_height = self.get_size()
        x = window_x + entry_x + entry_width - tooltip_width/2
        y = window_y + entry_y - entry_height
        
        self.move(x, y)
        self.show_all()
