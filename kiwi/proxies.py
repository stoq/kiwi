#
# Kiwi: a Framework and Enhanced Widgets for Python
#
# Copyright (C) 2002-2005 Async Open Source
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

import sys

from kiwi import _warn, ValueUnset
from kiwi.accessors import kgetattr, ksetattr, clear_attr_cache
from kiwi.interfaces import Mixin, MixinSupportValidation
from kiwi.log import Logger

class ProxyError(Exception):
    pass

log = Logger(category='proxy')

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
    
class Proxy:
    """ A Proxy is a class that 'attaches' an instance to an interface's
    widgets, and transparently manipulates that instance's attributes as
    the user alters the content of the widgets.

    The Proxy takes the widget list and detects what widgets are to be
    attached to the model by looking if it is a KiwiWidget and if it
    has the model-attribute set.
    """
    _setter_error_handler = None
    
    def __init__(self, view, model=None, widgets=[]):
        self.view = view
        self.model = model
        self._model_attributes = {}
        self._setup_widgets(widgets)
        self._initialize_widgets()

    def _initialize_widgets(self):
        """Update the contents of the widgets.

        This should be called after _setup_widgets.
        """
        for attribute, widget in self._model_attributes.items():

            if self.model is None:
                # if we have no model, leave value unset so we pick up
                # the widget default below.
                value = ValueUnset
            else:
                # if we have a model, grab its value to update the widgets
                self._register_proxy_in_model(attribute)
                value = kgetattr(self.model, attribute, ValueUnset)
                    
            tweak_function = getattr(self, "tweak_%s" % attribute, None)
            if tweak_function:
                tweak_function(attribute, value)
            else:
                self.update(attribute, value, block=True)

            # The initial value of the model is set, at this point
            # do a read, it'll trigger a validation for widgets who
            # supports it.
            if not isinstance(widget, MixinSupportValidation):
                continue

            widget.validate(force=True)
            
    def _setup_widgets(self, widgets):
        """
        Connect to the 'content-changed' signal of all the Kiwi widgets
        in the widgets list parameter.
        @param widgets: the widget names
        @type  widgets: list of strings
        """
        model_attributes = self._model_attributes
        for widget_name in widgets:
            widget = getattr(self.view, widget_name, None)
            if widget is None:
                raise AttributeError("The widget %s was not found in the "
                                     "view %s" % (
                    widget_name, self.view.__class__.__name__))
            
            if not isinstance(widget, Mixin):
                raise ProxyError("The widget %s (%r), in view %s is not "
                                 "a kiwi widget and cannot be added to a proxy"
                                 % (widget_name, widget,
                                    self.view.__class__.__name__))

            data_type = widget.get_property('data-type')
            if data_type is None:
                raise ProxyError("The kiwi widget %s (%r) in view %s should "
                                 "have a data type set" % (
                    widget_name, widget, self.view.__class__.__name__))
            
            attribute = widget.get_property('model-attribute')
            if not attribute:
                raise ProxyError(
                    "The widget %s (%s) in view %s is a kiwi widget but does "
                    "not have a model attribute set so it will not be "
                    "associated with the model" % (
                    widget_name, widget, self.view.__class__.__name__))
                continue
             
            connection_id = widget.connect('content-changed',
                                           self._on_widget__content_changed,
                                           attribute)
            widget.set_data('content-changed-id', connection_id)

            # save this widget in our map
            if attribute in model_attributes:
                old_widget = model_attributes[attribute]
                raise KeyError("The widget %s (%r) in view %s is already in "
                               "the proxy, defined by widget %s (%r)" % (
                    widget_name, widget, self.view.__class__.__name__,
                    old_widget.name, old_widget))
            
            model_attributes[attribute] = widget
            
            # here we define the view that owns the widget
            widget.owner = self.view

    def _on_widget__content_changed(self, widget, attribute):
        """This is called as soon as the content of one of the widget
        changes, the widgets tries fairly hard to not emit when it's not
        neccessary"""

        # skip updates for model if there is none, right?
        if self.model is None:
            return

        if isinstance(widget, MixinSupportValidation):
            value = widget.validate()
        else:
            value = widget.read()
        
        log('%s.%s = %r' % (self.model.__class__.__name__,
                            attribute, value)) 
        
        # only update the model if the data is correct
        if value is ValueUnset:
            return

        # XXX: one day we might want to queue and unique updates?
        self._block_proxy_in_model(True)
        try:
            ksetattr(self.model, attribute, value)
        except:
            if self._setter_error_handler:
                self._setter_error_handler(sys.exc_value, self.model, 
                                           attribute, value)
            else:
                raise

        self._block_proxy_in_model(False)

        # Call global update hook 
        self.proxy_updated(widget, value)

    def _block_proxy_in_model(self, state):
        model = self.model
        if not hasattr(model, "block_proxy"):
            return
        
        if state:
            model.block_proxy(self)
        else:
            model.unblock_proxy(self)

    def _register_proxy_in_model(self, attribute):
        model = self.model
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
                   "Persistent.__setstate__() of course) to reinitialize "
                   "things properly.)")
            raise TypeError(msg % (model, self))

    def _unregister_proxy_in_model(self):
        if self.model and hasattr(self.model, "unregister_proxy"):
            self.model.unregister_proxy(self)

    # Public API
    def proxy_updated(self, widgetproxy, value):
        """ This is a hook that is called whenever the proxy updates the
        model. Implement it in the inherited class to perform actions that
        should be done each time the user changes something in the interface.
        This hook by default does nothing.
        """
        pass

    def set_setter_error_handler(self, handler):
        """ Sets a method that will be called if an update to a model
        attribute raises an exception. The handler will receive the
        following arguments, in order:

            - Exception object
            - model
            - attribute name
            - value attempted
        """
        self._setter_error_handler = handler

    def update(self, attribute, value=ValueUnset, block=False):
        """ Generic frontend function to update the contentss of a widget based
        on its model attribute name using the internal update functions. 

            - attribute: the name of the attribute whose widget we wish to
              updated.  If accessing a radiobutton, specify its group
              name. 
            - value specifies the value to set in the widget. If
              unspecified, it defaults to the current model's value
              (through an accessor, if it exists, or getattr). 
            - block defines if we are to block cascading proxy updates
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
            if self.model is None:
                # We really want to avoid trying to update our UI if our
                # model doesn't exist yet and no value was provided.
                # update() is also called by user code, but it should be
                # safe to return here since you shouldn't need to code
                # around the lack of a model in your callbacks if you
                # can help it.
                return
            value = kgetattr(self.model, attribute, ValueUnset)

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
            data_type = widget.get_property('data-type')
            value_type = type(value)
            if not isinstance(value, data_type):
                raise TypeError(
                    "attribute %s of model %r requires a value of "
                    "type %s, not %s" % (
                    attribute, self.model,
                    data_type.__name__,
                    value_type.__name__))
        
        if block:
            block_widget(widget)
            self.view.handler_block(widget)
            widget.update(value)
            self.view.handler_unblock(widget)
            unblock_widget(widget)
        else:
            widget.update(value)
        return True


    def notify(self, attribute, value=ValueUnset):
        """  Notifies the proxy that the named attribute has changed. Calls
        tweak_foo by default if the attribute provided is "foo" and update_foo
        exists. This should *only* be called by the FrameWork Model, not by an
        end-user callback.

            - name: the name of the attribute being changed
            - value: what it was set to
        """
        func = getattr(self, "tweak_%s" % attribute, None)
        if func:
            # If value is unset, send in model value to tweak_%s
            if value is ValueUnset:
                value = kgetattr(self.model, attribute, ValueUnset)
                if value is ValueUnset:
                    raise ValueError("model value for %s was unset" % attribute)
            func(attribute, value)
        else:
            self.update(attribute, value, block=True)

    def new_model(self, new_model, relax_type=False):
        """ Reuses the same proxy with another instance as model. Allows a
        proxy interface to change model without the need to destroy and
        recreate the UI (which would cause flashing, at least)
        """
        # unregister previous proxy
        self._unregister_proxy_in_model()
        
        # the following isn't strictly necessary, but it currently works
        # around a bug with reused ids in the attribute cache and also
        # makes a lot of sense for most applications (don't want a huge
        # eternal cache pointing to models that you're not using anyway)
        clear_attr_cache()

        if self.model is not None:
            assert self.model.__class__
            if not relax_type and type(new_model) != type(self.model) and \
                not isinstance(new_model, self.model.__class__):
                raise TypeError("New model has wrong type %s, expected %s"
                                % (type(new_model), type(self.model)))

        self.model = new_model

        self._initialize_widgets()
    
