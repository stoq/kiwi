#
# Kiwi: a Framework and Enhanced Widgets for Python
#
# Copyright (C) 2005 Async Open Source
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
#            Johan Dahlin <jdahlin@async.com.br>
#

import sys

import gobject

class Mixin(object):
    # gsignal('content-changed')
    # gproperty('data-type')
    # gproperty('model-attribute')
    # gproperty('default-value')
    # gproperty('validation-changed')
    
    def read(self):
        pass
    
    def update(self, value):
        pass
    
class MixinSupportValidation(object):
    # gproperty('mandatory')
    def is_valid(self):
        pass

    # These two are mainly used by subclasses
    def validate_data(self, data):
        pass
    
    def before_validate(self, data):
        pass

class AbstractGladeAdaptor(object):
    """Abstract class that define the functionality an class that handle
    glade files should provide."""

    def get_widget(self, widget_name):
        """Return the widget in the glade file that has that name"""

    def get_widgets(self):
        """Return a tuple with all the widgets in the glade file"""

    def attach_slave(self, name, slave):
        """Attaches a slaveview to the view this adaptor belongs to,
        substituting the widget specified by name.
        The widget specified *must* be a eventbox; its child widget will be
        removed and substituted for the specified slaveview's toplevel widget
        """

    def signal_autoconnect(self, dic):
        """Connect the signals in the keys of dict with the objects in the
        values of dic
        """

def implementsIProxy():
    """Add a content-changed signal and a data-type, default-value, 
    model-attribute properties to the class where this 
    functions is called.
    """
    frame = sys._getframe(1)
    try:
        local_namespace = frame.f_locals
    finally:
        del frame

    if not '__gsignals__' in local_namespace:
        dic = local_namespace['__gsignals__'] = {}
    else:
        dic = local_namespace['__gsignals__']

    dic['content-changed'] = (gobject.SIGNAL_RUN_LAST, None, ())
    dic['validation-changed'] = (gobject.SIGNAL_RUN_LAST, None, (bool,))
    
    # the line below is used for triggering custom validation.
    # if you want a custom validation on a widget make a method on the
    # view class for each widget that you want to validate.
    # the method signature is:
    # def on_widgetname__validate(self, widget, data)
    dic['validate'] = (gobject.SIGNAL_RUN_LAST, object, (object,))

    if not '__gproperties__' in local_namespace:
        dic = local_namespace['__gproperties__'] = {}
    else:
        dic = local_namespace['__gproperties__']

    dic['data-type'] = (object, 'data-type', 'Data Type',
                        gobject.PARAM_READWRITE)
    dic['model-attribute'] = (str, 'model-attribute', 'Model Attribute', '',
                              gobject.PARAM_READWRITE)
    dic['default-value'] = (object, 'default-value', 'Default Value',
                            gobject.PARAM_READABLE)

def implementsIMandatoryProxy():
    frame = sys._getframe(1)
    try:
        local_namespace = frame.f_locals
    finally:
        del frame

    dic = local_namespace['__gproperties__']
    dic['mandatory'] = (bool, 'mandatory', 'Mandatory', False,
                        gobject.PARAM_READWRITE)
