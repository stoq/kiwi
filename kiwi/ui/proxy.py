#
# Kiwi: a Framework and Enhanced Widgets for Python
#
# Copyright (C) 2002-2007 Async Open Source
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
#

"""This module defines the Proxy class, which is a facility that can be used
to keep the state of a model object synchronized with a View.
"""

import gobject
import gtk

from kiwi import ValueUnset
from kiwi.accessor import kgetattr, ksetattr, clear_attr_cache
from kiwi.datatypes import converter
from kiwi.decorators import deprecated
from kiwi.interfaces import IProxyWidget, IValidatableProxyWidget
from kiwi.log import Logger

class ProxyError(Exception):
    pass

log = Logger('proxy')

def block_widget(widget):
    """Blocks the signal handler of the 'content-changed' signal on widget"""
    connection_id = widget.get_data('content-changed-id')
    if connection_id:
        widget.handler_block(connection_id)

def unblock_widget(widget):
    """Unblocks the signal handler of the 'content-changed' signal on widget"""
    connection_id = widget.get_data('content-changed-id')
    if connection_id:
        widget.handler_unblock(connection_id)

def _get_widget_data_type(widget):
    data_type = widget.get_property('data-type')
    c = converter.get_converter(data_type)
    return c.type

class Proxy:
    """ A Proxy is a class that 'attaches' an instance to an interface's
    widgets, and transparently manipulates that instance's attributes as
    the user alters the content of the widgets.

    The Proxy takes the widget list and detects what widgets are to be
    attached to the model by looking if it is a KiwiWidget and if it
    has the model-attribute set.
    """

    def __init__(self, view, model=None, widgets=()):
        """
        Create a new Proxy object.
        @param view:    view attched to the slave
        @type  view:    a L{kiwi.ui.views.BaseView} subclass
        @param model:   model attached to proxy
        @param widgets: the widget names
        @type  widgets: list of strings
        """
        self._view = view
        self._model = model
        self._model_attributes = {}

        for widget_name in widgets:
            widget = getattr(self._view, widget_name, None)
            if widget is None:
                raise AttributeError("The widget %s was not found in the "
                                     "view %s" % (
                    widget_name, self._view.__class__.__name__))

            self._setup_widget(widget_name, widget)

    # Private API

    def _reset_widget(self, attribute, widget):
        if self._model is None:
            # if we have no model, leave value unset so we pick up
            # the widget default below.
            value = ValueUnset
        else:
            # if we have a model, grab its value to update the widgets
            self._register_proxy_in_model(attribute)
            value = kgetattr(self._model, attribute, ValueUnset)

        self.update(attribute, value, block=True)

        # The initial value of the model is set, at this point
        # do a read, it'll trigger a validation for widgets who
        # supports it.
        if not IValidatableProxyWidget.providedBy(widget):
            return

        widget.validate(force=True)

    def _setup_widget(self, widget_name, widget):
        if not IProxyWidget.providedBy(widget):
            raise ProxyError("The widget %s (%r), in view %s is not "
                             "a kiwi widget and cannot be added to a proxy"
                             % (widget_name, widget,
                                self._view.__class__.__name__))

        data_type = _get_widget_data_type(widget)
        if data_type is None:
            raise ProxyError("The kiwi widget %s (%r) in view %s should "
                             "have a data type set" % (
                widget_name, widget, self._view.__class__.__name__))

        attribute = widget.get_property('model-attribute')
        if not attribute:
            attribute = widget_name
            widget.set_property('model-attribute', widget_name)

        # Do a isinstance here instead of in the callback,
        # as an optimization, it'll never change in runtime anyway
        connection_id = widget.connect(
            'content-changed',
            self._on_widget__content_changed,
            attribute,
            IValidatableProxyWidget.providedBy(widget))
        widget.set_data('content-changed-id', connection_id)

        if IValidatableProxyWidget.providedBy(widget):
            connection_id = widget.connect(
                'notify::visible',
                self._on_widget__notify)
            widget.set_data('notify-visible-id', connection_id)

            connection_id = widget.connect(
                'notify::sensitive',
                self._on_widget__notify)
            widget.set_data('notify-sensitive-id', connection_id)

        model_attributes = self._model_attributes
        # save this widget in our map
        if (attribute in model_attributes and
            # RadioButtons are allowed several times
            not gobject.type_is_a(widget, 'GtkRadioButton')):
            old_widget = model_attributes[attribute]
            raise KeyError("The widget %s (%r) in view %s is already in "
                           "the proxy, defined by widget %s (%r)" % (
                widget_name, widget, self._view.__class__.__name__,
                old_widget.name, old_widget))

        model_attributes[attribute] = widget
        self._reset_widget(attribute, widget)

    def _register_proxy_in_model(self, attribute):
        model = self._model
        if not hasattr(model, "register_proxy_for_attribute"):
            return
        try:
            model.register_proxy_for_attribute(attribute, self)
        except AttributeError:
            msg = ("Failed to run register_proxy() on Model %s "
                   "(that was supplied to  %s. \n"
                   "(Hint: if this model also inherits from ZODB's "
                   "Persistent class, this problem occurs if you haven't "
                   "set __setstate__() up correctly.  __setstate__() "
                   "should call Model.__init__() (and "
                   "Persistent.__setstate__() of course) to rereset "
                   "things properly.)")
            raise TypeError(msg % (model, self))

    def _unregister_proxy_in_model(self):
        if self._model and hasattr(self._model, "unregister_proxy"):
            self._model.unregister_proxy(self)

    # Callbacks

    def _on_widget__content_changed(self, widget, attribute, validate):
        """This is called as soon as the content of one of the widget
        changes, the widgets tries fairly hard to not emit when it's not
        neccessary"""

        # skip updates for model if there is none, right?
        if self._model is None:
            return

        if validate:
            value = widget.validate()
        else:
            value = widget.read()

        log('%s.%s = %r' % (self._model.__class__.__name__,
                            attribute, value))

        # only update the model if the data is correct
        if value is ValueUnset:
            return

        model = self._model
        # XXX: one day we might want to queue and unique updates?
        if hasattr(model, "block_proxy"):
            model.block_proxy(self)
            ksetattr(model, attribute, value)
            model.unblock_proxy(self)
        else:
            ksetattr(model, attribute, value)

        # Call global update hook
        self.proxy_updated(widget, attribute, value)

    # notify::sensitive and notify::visible are connected here
    def _on_widget__notify(self, widget, pspec):
        widget.emit('validation-changed', widget.is_valid())

    # Properties

    def _get_model(self):
        return self._model
    model = property(_get_model)

    # Public API

    def proxy_updated(self, widget, attribute, value):
        """ This is a hook that is called whenever the proxy updates the
        model. Implement it in the inherited class to perform actions that
        should be done each time the user changes something in the interface.
        This hook by default does nothing.
        @param widget:
        @param attribute:
        @param value:
        """

    def update_many(self, attributes, value=ValueUnset, block=False):
        """
        Like L{update} but takes a sequence of attributes

        @param attributes: sequence of attributes to update
        @param value: see L{update}
        @param block: see L{update}
        """

        for attribute in attributes:
            self.update(attribute, value, block)

    def update(self, attribute, value=ValueUnset, block=False):
        """ Generic frontend function to update the contentss of a widget based
        on its model attribute name using the internal update functions.

        @param attribute: the name of the attribute whose widget we wish to
          updated.  If accessing a radiobutton, specify its group
          name.
        @param value: specifies the value to set in the widget. If
          unspecified, it defaults to the current model's value
          (through an accessor, if it exists, or getattr).
        @param block: defines if we are to block cascading proxy updates
          triggered by this update. You should use block if you are
          calling update on *the same attribute that is currently
          being updated*.
          This means if you have hooked to a signal of the widget
          associated to that attribute, and you call update() for
          the *same attribute*, use block=True. And pray. 8). If
          block is set to False, the normal update mechanism will
          occur (the model being updated in the end, hopefully).
        """

        if value is ValueUnset:
        # We want to obtain a value from our model
            if self._model is None:
                # We really want to avoid trying to update our UI if our
                # model doesn't exist yet and no value was provided.
                # update() is also called by user code, but it should be
                # safe to return here since you shouldn't need to code
                # around the lack of a model in your callbacks if you
                # can help it.
                value = ValueUnset
            else:
                value = kgetattr(self._model, attribute, ValueUnset)

        widget = self._model_attributes.get(attribute, None)

        if widget is None:
            raise AttributeError("Called update for `%s', which isn't "
                                 "attached to the proxy %s. Valid "
                                 "attributes are: %s (you may have "
                                 "forgetten to add `:' to the name in "
                                 "the widgets list)"
                                 % (attribute, self,
                                    self._model_attributes.keys()))


        # The type of value should match the data-type property. The two
        # exceptions to this rule are ValueUnset and None
        if not (value is ValueUnset or value is None):
            data_type = _get_widget_data_type(widget)
            value_type = type(value)
            if not isinstance(value, data_type):
                raise TypeError(
                    "attribute %s of model %r requires a value of "
                    "type %s, not %s" % (
                    attribute, self._model,
                    data_type.__name__,
                    value_type.__name__))

        if block:
            block_widget(widget)
            self._view.handler_block(widget)
            widget.update(value)
            self._view.handler_unblock(widget)
            unblock_widget(widget)
        else:
            widget.update(value)
        return True

    def set_model(self, model, relax_type=False):
        """
        Updates the model instance of the proxy.
        Allows a proxy interface to change model without the need to destroy
        and recreate the UI (which would cause flashing, at least)

        @param model:
        @param relax_type:
        """
        if self._model is not None and model is not None:
            if (not relax_type and
                type(model) != type(self._model) and
                not isinstance(model, self._model.__class__)):
                raise TypeError("model has wrong type %s, expected %s"
                                % (type(model), type(self._model)))

        # the following isn't strictly necessary, but it currently works
        # around a bug with reused ids in the attribute cache and also
        # makes a lot of sense for most applications (don't want a huge
        # eternal cache pointing to models that you're not using anyway)
        clear_attr_cache()

        # unregister previous proxy
        self._unregister_proxy_in_model()

        self._model = model

        for attribute, widget in self._model_attributes.items():
            self._reset_widget(attribute, widget)

    def add_widget(self, name, widget):
        """
        Adds a new widget to the proxy

        @param name: name of the widget
        @param widget: widget, must be a gtk.Widget subclass
        """
        if name in self._model_attributes:
            raise TypeError("there is already a widget called %s" % name)

        if not isinstance(widget, gtk.Widget):
            raise TypeError("%r must be a gtk.Widget subclass" % widget)

        self._setup_widget(name, widget)

    def remove_widget(self, name):
        """
        Removes a widget from the proxy

        @param name: the name of the widget to remove
        """
        if not name in self._model_attributes:
            raise TypeError("there is no widget called %s" % name)

        widget = self._model_attributes.pop(name)
        widget.disconnect(widget.get_data('content-changed-id'))

        if IValidatableProxyWidget.providedBy(widget):
            for data_name in ('notify-visible-id',
                              'notify-sensitive-id'):
                widget.disconnect(widget.get_data(data_name))

    # Backwards compatibility

    def new_model(self, model, relax_type=False):
        self.set_model(model)
    new_model = deprecated('set_model', log)(new_model)

