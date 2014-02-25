#
# Kiwi: a Framework and Enhanced Widgets for Python
#
# Copyright (C) 2001-2013 Async Open Source
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
#            Johan Dahlin <jdahlin@async.com.br>
#

"""
Defines a set of objects to work with GObject signals within a view
"""

import inspect
import re

from kiwi.python import Settable

#
# Signal brokers
#

method_regex = re.compile(r'^(on|after)_(\w+)__(\w+)$')


class SignalProxyObject(object):
    """
    I am a descriptor that connects and disconnects signals
    for views containing GObjects.

    I'll connect methods such as on_button__clicked to and make them
    map to the clicked signal for view.button.

    The magic I do is that that you can replace view.button with another
    widget and it will replace the signal connections on the old object
    and reconnect on the new object
    """
    def __init__(self, name, signals):
        """
        :param name: name of this object in the view
        :param signals: list of signals (context, signal_name, method) to connect to,
           - context is either "on" or "after" depending on connect or connect_after
             should be used to connect the signal
           - signal_name is the name of the signal we should connect
           - method_name is the name of the method that should be our callback
        """
        self.object_name = name
        self.signals = signals

    def _connect_signals(self, state):
        for context, signal_name, method_name in self.signals:
            # We cannot pass in the callbacks from view in the constructor, since
            # the view will eventually change, so instead of passing the function
            # object we pass the name of the method and it will be fetched here.
            callback = getattr(state.view, method_name)

            # We catch TypeError and reraise it to get a nicer error message,
            # PyGObject should ideally not raise TypeError, because we cannot
            # know if TypeError comes from Python or PyGObject
            try:
                if context == 'on':
                    signal_id = state.obj.connect(signal_name, callback)
                elif context == 'after':
                    signal_id = state.obj.connect_after(signal_name, callback)
                else:
                    raise AssertionError(context)
            except TypeError:
                raise TypeError("%s.%s doesn't provide a signal %s" % (
                    state.view.__class__.__name__, self.object_name,
                    signal_name))

            # Save the name of the signal (for handler_block) and the
            # the signal_id for disconnection purposes
            state.connected_signals.append((signal_name, signal_id))

    def _disconnect_signals(self, state):
        # Don't even bother trying to disconnect signals if we don't have
        # an object set, which will happen the first time a SignalProxyObject
        # is instantiated
        if state.obj is not None:
            for signal_name, signal_id in state.connected_signals:
                state.obj.disconnect(signal_id)

        state.connected_signals = []

    def _get_state(self, view):
        # Since self is shared between different views we cannot
        # store any state in there, instead store state inside
        # the view. We currently use one dictionary per object
        view_state = view.__dict__.setdefault('_SignalProxy_state_', {})

        state = view_state.get(self.object_name)
        if state is None:
            # The state we need:
            # - connected_signals, the signals we use
            # - obj: used to connect/disconnect/block/unblock
            # - view: for displaying nice error messages
            view_state[self.object_name] = state = Settable(
                obj=None,
                view=view,
                connected_signals=[])
        return state

    # This is part of the python descriptor protocol, it will be called
    # when we do view.button = foo, which is usually done by the view for
    # all widgets constructed by a GtkBuilder, but it might also be triggered
    # manually for dynamic interfaces.
    def __set__(self, view, value):
        if view is None:
            raise AttributeError(
                "Can't set SignalProxyObject class attributes")

        # Fetch the current state from the view
        state = self._get_state(view)

        # There's no need to do the disconnect/connect dance
        # if the actual object didn't change, so skip out early
        # in that case
        if state.obj == value:
            return

        # First, we need to decouple the signal connections to
        # the previously connected object
        self._disconnect_signals(state)

        # We got a new object
        state.obj = value

        # Listen to the signals on the new object
        if value is not None:
            self._connect_signals(state)

    # This is also part of the python descriptor protocol and is called
    # whenever an attribute is fetched.
    def __get__(self, view, owner):
        # This happens when we try to access the class attribute,
        # for instance view.__class__.button, in that case we
        # return ourselves so we can call handler_[un]block
        if view is None:
            return self

        # Fetch the current state and return the object
        state = self._get_state(view)
        return state.obj

    #
    # Public API
    #

    def handler_block(self, instance, signal_name=None):
        state = self._get_state(instance)
        for signal, signal_id in state.connected_signals:
            if signal_name is None or signal == signal_name:
                state.obj.handler_block(signal_id)

    def handler_unblock(self, instance, signal_name=None):
        state = self._get_state(instance)
        for signal, signal_id in state.connected_signals:
            if signal_name is None or signal == signal_name:
                state.obj.handler_unblock(signal_id)


class SignalBroker(object):
    def __init__(self, view, controller=None):
        if controller is None:
            controller = view
        self.signal_proxies = []
        methods = self._get_all_methods(controller)
        self._do_connections(view, methods)

    def _get_all_methods(self, controller):
        methods = {}
        for cls in inspect.getmro(type(controller)):
            for attr, value in cls.__dict__.items():
                if value is not None:
                    methods[attr] = value
        return methods

    def _do_connections(self, view, methods):
        """This method allows subclasses to add more connection mechanism"""
        self._autoconnect_by_method_name(view, methods)

    def _autoconnect_by_method_name(self, view, methods):
        """
        Offers autoconnection of widget signals based on function names.
        You simply need to define your controller method in the format::

            def on_widget_name__signal_name(self, widget):

        In other words, start the method by "on_", followed by the
        widget name, followed by two underscores ("__"), followed by the
        signal name. Note: If more than one double underscore sequences
        are in the string, the last one is assumed to separate the
        signal name.
        """

        # First extract the callbacks to connect and group by the
        # object/attribute name
        objects = {}
        for method_name in methods:
            # `on_x__y' has 7 chars and is the smallest possible handler
            if len(method_name) < 7:
                continue
            match = method_regex.match(method_name)
            if match is not None:
                on_after, object_name, signal_name = match.groups()
                signal = [on_after, signal_name, method_name]
                objects.setdefault(object_name, []).append(signal)

        # For each object, replace the object with a SignalProxyObject
        for object_name in objects:
            # Extract the GObject from the view, before we replace it with
            # the descriptor
            obj = getattr(view, object_name, None)

            # Replace the attribute on the view with a magic descriptor,
            # note that this is done on the class and check if it's already
            # set before. We are not using hasattr/getattr here because, if a
            # parent class had a SignalProxyObject for object_name, it would
            # cause new signals on this subclass to be ignored
            if object_name not in view.__class__.__dict__:
                signal_proxy = SignalProxyObject(object_name,
                                                 objects[object_name])
                setattr(view.__class__, object_name, signal_proxy)
                # Store the signal_proxies so we can verify on view destruction
                # time that there are no unused connections
                self.signal_proxies.append(signal_proxy)

            # Make sure the descritor has the old widget value set
            setattr(view, object_name, obj)


class GladeSignalBroker(SignalBroker):
    def _do_connections(self, view, methods):
        super(GladeSignalBroker, self)._do_connections(view, methods)
        self._connect_glade_signals(view, methods)

    def _connect_glade_signals(self, view, methods):
        # mainly because the two classes cannot have a common base
        # class. studying the class layout carefully or using
        # composition may be necessary.

        # called by framework.basecontroller. takes a controller, and
        # creates the dictionary to attach to the signals in the tree.
        if not methods:
            raise AssertionError("controller must be provided")

        dict = {}
        for name, method in methods.items():
            if callable(method):
                dict[name] = method
        view._glade_adaptor.signal_autoconnect(dict)
