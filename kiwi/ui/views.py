#
# Kiwi: a Framework and Enhanced Widgets for Python
#
# Copyright (C) 2001-2005 Async Open Source
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
#            Jon Nelson <jnelson@securepipe.com>
#            Lorenzo Gil Sanchez <lgs@sicem.biz>
#            Johan Dahlin <jdahlin@async.com.br>
#            Henrique Romano <henrique@async.com.br>
#

"""
Defines the View classes that are included in the Kiwi Framework, which
are the base of Delegates and Proxies.
"""

import string

import gobject
import gtk

from kiwi import _warn
from kiwi.environ import is_gazpacho_required
from kiwi.interfaces import MixinSupportValidation
from kiwi.proxies import Proxy
from kiwi.utils import gsignal
from kiwi.ui.gadgets import quit_if_last

try:
    from kiwi.ui.gazpacholoader import GazpachoWidgetTree as WidgetTree
except ImportError, e:
    if is_gazpacho_required():
        raise RuntimeError("Gazpacho is required, but could not be found: %s"
                           % e)
    else:
        try:
            from kiwi.ui.libgladeloader import LibgladeWidgetTree as WidgetTree
        except ImportError:
            raise RuntimeError("Could not find a glade parser library")
        
_non_interactive = [
    gtk.Label, 
    gtk.Alignment,
    gtk.AccelLabel,
    gtk.Arrow,
    gtk.EventBox,
    gtk.Fixed,
    gtk.Frame,
    gtk.HBox,
    gtk.HButtonBox,
    gtk.HPaned,
    gtk.HSeparator,
    gtk.Layout,
    gtk.Progress,
    gtk.ProgressBar,
    gtk.ScrolledWindow,
    gtk.Table,
    gtk.VBox,
    gtk.VButtonBox,
    gtk.VPaned,
    gtk.VSeparator,
    gtk.Window, 
]

_non_interactive = tuple(_non_interactive)

#
# Signal brokers
#

class SignalBroker(object):
    def __init__(self, view, controller):
        methods = controller._get_all_methods()
        self._do_connections(view, methods)

    def _do_connections(self, view, methods):
        """This method allows subclasses to add more connection mechanism"""
        self._autoconnect_by_method_name(view, methods)
        
    def _autoconnect_by_method_name(self, view, methods):
        """
        Offers autoconnection of widget signals based on function names.
        You simply need to define your controller method in the format::

            def on_widget_name__signal_name(self, widget, *args):

        In other words, start the method by "on_", followed by the
        widget name, followed by two underscores ("__"), followed by the
        signal name. Note: If more than one double underscore sequences
        are in the string, the last one is assumed to separate the
        signal name.
        """
        self._autoconnected = {}
        for fname in methods.keys():
            # `on_x__y' has 7 chars and is the smallest possible handler
            # (though illegal, of course, since the signal name x is bogus)
            if len(fname) < 7:
                continue
            if fname[:3] == "on_":
                after = 0
            elif fname[:6] == "after_":
                after = 1
            else:
                continue
            # cut out `on_' or `after'
            f = string.split(fname, "_", 1)
            if len(f) < 2:
                continue
            f = f[1]
            # separate widget from signal; for instance: 
            # "on_foo_bar__widget__clicked()" -> "foo_bar", "widget", "clicked"
            f = string.split(f, "__")
            if len(f) < 2:
                continue
            # signal is the last element
            signal = f[-1]
            # widget name is everything up to the last __
            # "foo_bar", "widget" -> "foo_bar__widget"
            w_name = string.join(f[:-1], "__")
            if not w_name:
                continue
            widget = getattr(view, w_name, None)
            if widget is None:
                raise AttributeError("couldn't find widget %s in %s"
                                     % (w_name, view))
            if not isinstance(widget, (gtk.Widget, gtk.Action)):
                raise AttributeError("%s (%s) is not a widget or an action "
                                     "and can't be connected to"
                                     % (w_name, widget))
            # Must use getattr; using the class method ends up with it
            # being called unbound and lacking, thus, "self".
            try:
                if after:
                   signal_id = widget.connect_after(signal, methods[fname])
                else:
                   signal_id = widget.connect(signal, methods[fname])
            except TypeError:
                _warn("Widget %s doesn't provide a signal %s"
                     % (widget.__class__, signal))
                continue
            if not self._autoconnected.has_key(widget):
                self._autoconnected[widget] = []
            self._autoconnected[widget].append((signal, signal_id))

    def handler_block(self, widget, signal_name):
        signals = self._autoconnected
        if not widget in signals:
            return
            
        for signal, signal_id in signals[widget]:
            if signal_name is None or signal == signal_name:
                widget.handler_block(signal_id)

    def handler_unblock(self, widget, signal_name):
        signals = self._autoconnected
        if not widget in signals:
            return
        
        for signal, signal_id in signals[widget]:
            if signal_name is None or signal == signal_name:
                widget.handler_unblock(signal_id)

    def disconnect_autoconnected(self):
        for widget, signals in self._autoconnected.items():
            for unused, signal_id in signals:
                widget.disconnect(signal_id)
        
class GladeSignalBroker(SignalBroker):
    def __init__(self, view, controller):
        SignalBroker.__init__(self, view, controller)

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
        view.glade_adaptor.signal_autoconnect(dict)
        

class SlaveView(gobject.GObject):
    """
    Base class for all View classes. Defines the essential class
    attributes (controller, toplevel, widgets) and handles
    initialization of toplevel and widgets.  Once
    AbstractView.__init__() has been called, you can be sure
    self.toplevel and self.widgets are sane and processed.

    When a controller is associated with a View (the view should be
    passed in to its constructor) it will try and call a hook in the
    View called _attach_callbacks. See AbstractGladeView for an example
    of this method.
    """
    controller = None
    toplevel = None
    widgets = []
    toplevel_name = None
    gladefile = None
    gladename = None
    domain = None
    
    # This signal is emited when the view wants to return a result value
    gsignal("result", object)
    
    # This is emitted when validation changed for a view
    # Used by parents views to know when child slaves changes
    gsignal('validation-changed', bool)
    
    def __init__(self, toplevel=None, widgets=None, gladefile=None,
                 gladename=None, toplevel_name=None, domain=None):
        """ Creates a new SlaveView. Sets up self.toplevel and self.widgets
        and checks for reserved names.
        """
        gobject.GObject.__init__(self)

        # setup the initial state with the value of the arguments or the
        # class variables
        klass = type(self)
        self.toplevel = toplevel or klass.toplevel
        self.widgets = widgets or klass.widgets
        self.gladefile = gladefile or klass.gladefile
        self.gladename = gladename or klass.gladename
        self.toplevel_name = toplevel_name or klass.toplevel_name
        self.domain = domain or klass.domain

        self.__broker = None
        
        for reserved in ["widgets", "toplevel", "gladefile",
                         "gladename", "tree", "model", "controller"]:
            # XXX: take into account widget constructor?
            if reserved in self.widgets:
                raise AttributeError("The widgets list for %s contains "
                                     "a widget named `%s', which is "
                                     "a reserved. name""" % (self, reserved))


        self.glade_adaptor = None
        if self.gladefile is not None:
            self._init_glade_adaptor()

        # Validation status
        self._valid = True

        # Dictionary slave/widget name -> validation status
        self._validation = {}
        
        # stores the function that will be called when widgets 
        # validity is checked
        self._validate_function = None

        if self.toplevel_name is not None and self.toplevel is None:
            self.toplevel = getattr(self, self.toplevel_name, None)
        
        if not self.toplevel:
            raise TypeError("A View requires an instance variable "
                            "called toplevel that specifies the "
                            "toplevel widget in it")


        self.proxies = []
        
        # grab the accel groups
        self._accel_groups = gtk.accel_groups_from_object(self.toplevel)

        self.slaves = {}

    def register_validate_function(self, function):
        """The signature of the validate function is:

        def function(is_valid):

        or, if it is a method:

        def function(self, is_valid):

        where the 'is_valid' parameter is True if all the widgets have
        valid data or False otherwise.
        """
        self._validate_function = function

    def _init_glade_adaptor(self):
        """Special init code that subclasses may want to override."""
        self.glade_adaptor = WidgetTree(self, self.gladefile,
                                        self.widgets, self.gladename,
                                        self.domain)

        container_name = self.toplevel_name or self.gladename or self.gladefile
            
        if container_name is None:
            msg = ("You provided a gladefile %s to grab the widgets from "
                   "but you didn't give me a toplevel/container name!")
            raise ValueError(msg % self.gladefile)

        # a SlaveView inside a glade file needs to come inside a toplevel
        # window, so we pull our slave out from it, grab its groups and
        # muerder it later
        shell = self.glade_adaptor.get_widget(container_name)
        if not isinstance(shell, gtk.Window):
            msg = "Container %s should be a Window, found %s"
            raise TypeError(msg % (container_name, type(shell)))

        if shell.get_property('visible'):
            _warn('Toplevel window %s in %s should not be visible' % (container_name,
                                                                      self.gladefile))
        # XXX grab the accel groups
        
        self.toplevel = shell.get_child()
        shell.remove(self.toplevel)
        shell.destroy()

    #
    # Hooks
    #

    def on_attach(self, parent):
        """ Hook function called when attach_slave is performed on slave views.
        """
        pass

    def on_startup(self):
        """
        This is a virtual method that can be customized by classes that
        want to perform additional initalization after a controller has
        been set for it.  If you need this, add this method to your View
        subclass and BaseController will call it when the controller is
        set to the proxy."""
        pass

    #
    # Accessors
    #

    def get_toplevel(self):
        """Returns the toplevel widget in the view"""
        return self.toplevel

    def get_widget(self, name):
        """Retrieves the named widget from the View"""
        name = string.replace(name,'.','_')
        widget = getattr(self, name, None)
        if widget is None:
            raise AttributeError("Widget %s not found in view %s"
                                 % (name, self))
        if not isinstance(widget, gtk.Widget):
            raise TypeError("%s in view %s is not a Widget"
                            % (name, self))
        return widget

    def set_controller(self, controller):
        """
        Sets the view's controller, checking to see if one has already
        been set before."""
        # Only one controller per view, please
        if self.controller:
            raise AssertionError("This view already has a controller: %s"
                                 % self.controller)
        self.controller = controller

    #
    # GTK+ proxies and convenience functions
    #

    def show(self, *args):
        """Shows the toplevel widget"""
        self.toplevel.show()

    def show_all(self, *args):
        """Shows all widgets attached to the toplevel widget"""
        if self.glade_adaptor is not None:
            raise AssertionError("You don't want to call show_all on a "
                                 "SlaveView. Use show() instead.")
        self.toplevel.show_all()

    def focus_toplevel(self):
        """Focuses the toplevel widget in the view"""
        # XXX: warn if there is no GdkWindow
        if self.toplevel and self.toplevel.window is not None:
            self.toplevel.grab_focus()

    def focus_topmost(self, widgets=None):
        """
        Looks through widgets specified (if no widgets are specified,
        look through all widgets attached to the view and sets focus to
        the widget that is rendered in the position closest to the view
        window's top and left

            - widgets: a list of widget names to be searched through
        """
        widget = self.get_topmost_widget(widgets, can_focus=True)
        if widget is not None: 
            widget.grab_focus()
        # So it can be idle_added safely
        return False

    def get_topmost_widget(self, widgets=None, can_focus=False):
        """
        A real hack; returns the widget that is most to the left and
        top of the window. 

            - widgets: a list of widget names.  If widgets is supplied,
              it only checks in the widgets in the list; otherwise, it
              looks at the widgets named in self.widgets, or, if
              self.widgets is None, looks through all widgets attached
              to the view.

            - can_focus: boolean, if set only searches through widget that can focus
        """
        # XXX: recurse through containers from toplevel widget, better
        # idea and will work.
        widgets = widgets or self.widgets or self.__dict__.keys()
        top_widget = None
        for widget_name in widgets:
            widget = getattr(self, widget_name)
            if not isinstance(widget, gtk.Widget):
                continue
            if not widget.flags() & gtk.REALIZED:
                # If widget isn't realized but we have a toplevel
                # window, it's safe to realize it. If this check isn't
                # performed, we get a crash as per
                # http://bugzilla.gnome.org/show_bug.cgi?id=107872
                if isinstance(widget.get_toplevel(), gtk.Window):
                    widget.realize()
                else:
                    _warn("get_topmost_widget: widget %s was unrealized"
                          % widget_name)
                    continue
            if can_focus:
                # Combos don't focus, but their entries do
                if isinstance(widget, gtk.Combo):
                    widget = widget.entry
                if not widget.flags() & gtk.CAN_FOCUS or \
                    isinstance(widget, (gtk.Label, gtk.HSeparator,
                                        gtk.VSeparator, gtk.Window)):
                    continue
                
            if top_widget:
                allocation = widget.allocation
                top_allocation = getattr(top_widget, 'allocation',  None)
                assert top_allocation != None
                if (top_allocation[0] + top_allocation[1] >
                    allocation[0] + allocation[1]):
                    top_widget = widget
            else:
                top_widget = widget
        return top_widget

    #
    # Callback handling
    #

    def _attach_callbacks(self, controller):
        if self.glade_adaptor is None:
            brokerclass = SignalBroker
        else:
            brokerclass = GladeSignalBroker
            
        self.__broker = brokerclass(self, controller)

#    def _setup_keypress_handler(self, keypress_handler):
#        # Only useful in BaseView and derived classes
#        # XXX: support slaveview correctly
#        _warn("Tried to setup a keypress handler for %s "
#              "but no toplevel window exists to attach to" % self)

    #
    # Slave handling
    #
    
    def attach_slave(self, name, slave):
        """Attaches a slaveview to the current view, substituting the
        widget specified by name.  the widget specified *must* be a
        eventbox; its child widget will be removed and substituted for
        the specified slaveview's toplevel widget::

         .-----------------------. the widget that is indicated in the diagram
         |window/view (self.view)| as placeholder will be substituted for the 
         |  .----------------.   | slaveview's toplevel.
         |  | eventbox (name)|   |  .-----------------.
         |  |.--------------.|      |slaveview (slave)| 
         |  || placeholder  <----.  |.---------------.|
         |  |'--------------'|    \___ toplevel      ||
         |  '----------------'   |  ''---------------'|
         '-----------------------'  '-----------------'

        the original way of attachment (naming the *child* widget
        instead of the eventbox) is still supported for compatibility
        reasons but will print a warning.
        """
        if name in self.slaves:
            # XXX: TypeError
            _warn("A slave with name %s is already attached to %r"  % (
                  name, self))
        self.slaves[name] = slave

        if not isinstance(slave, SlaveView):
            raise TypeError("slave must be a SlaveView, not a %s" % type(slave))

        shell = slave.get_toplevel()

        if isinstance(shell, gtk.Window): # view with toplevel window
            new_widget = shell.get_child()
            shell.remove(new_widget) # remove from window to allow reparent
        else: # slaveview
            new_widget = shell

        # if our widgets are in a glade file get the placeholder from them
        # or take it from the view itself otherwise
        if self.glade_adaptor:
            placeholder = self.glade_adaptor.get_widget(name)
        else:
            placeholder = getattr(self, name, None)
            
        if not placeholder:
            raise AttributeError(
                  "slave container widget `%s' not found" % name)
        parent = placeholder.get_parent()

        if slave._accel_groups:
            # take care of accelerator groups; attach to parent window if we
            # have one; if embedding a slave into another slave, store its
            # accel groups; otherwise complain if we're dropping the accelerators
            win = parent.get_toplevel()
            if isinstance(win, gtk.Window):
                # use idle_add to be sure we attach the groups as late
                # as possible and avoid reattaching groups -- see
                # comment in _attach_groups.
                gtk.idle_add(self._attach_groups, win, slave._accel_groups)
            elif isinstance(self, SlaveView):
                self._accel_groups.extend(slave._accel_groups)
            else:
                _warn("attached slave %s to parent %s, but parent lacked "
                      "a window and was not a slave view" % (slave, self))
            slave._accel_groups = []

        if isinstance(placeholder, gtk.EventBox):
            # standard mechanism
            child = placeholder.get_child()
            if child is not None:
                placeholder.remove(child)
            placeholder.add(new_widget)
        elif isinstance(parent, gtk.EventBox):
            # backwards compatibility
            _warn("attach_slave's api has changed: read docs, update code!")
            parent.remove(placeholder)
            parent.add(new_widget)
        else:
            raise TypeError(
                "widget to be replaced must be wrapped in eventbox")

        # when attaching a slave we usually want it visible
        parent.show()
        # call slave's callback
        slave.on_attach(self)
        
        slave.connect_object('validation-changed',
                             self._on_child__validation_changed,
                             name)
        # Fire of an initial notification
        slave.check_and_notify_validity(force=True)
        
        # return placeholder we just removed
        return placeholder

    def detach_slave(self, name):
        """
        Detatch a slave called name from view
        """
        if not name in self.slaves:
            raise LookupError("There is no slaved called %s attached to %r" %
                              (name, self))
        del self.slaves[name]
        
    def _attach_groups(self, win, accel_groups):
        # get groups currently attached to the window; we use them
        # to avoid reattaching an accelerator to the same window, which
        # generates messages like:
        #
        # gtk-critical **: file gtkaccelgroup.c: line 188
        # (gtk_accel_group_attach): assertion `g_slist_find
        # (accel_group->attach_objects, object) == null' failed.
        #
        # interestingly, this happens many times with notebook,
        # because libglade creates and attaches groups in runtime to
        # its toplevel window.
        current_groups = gtk.accel_groups_from_object(win)
        for group in accel_groups:
            if group in current_groups:
                # skip group already attached
                continue
            win.add_accel_group(group)

    def get_slave(self, holder):
        if self.slaves.has_key(holder):
            return self.slaves[holder]
        raise AttributeError, "Unknown slave for holder: %s" % holder


    #
    # Signal connection
    #

    def connect_multiple(self, widgets, signal, handler, after=False):
        """
        Connect the same handler to the specified signal for a number of
        widgets.
            - widgets: a list of GtkWidgets
            - signal: a string specifying the signals
            - handler: a callback method
            - after: a boolean; if TRUE, we use connect_after(), otherwise, connect()
        """
        if not isinstance(widgets, (list, tuple)):
            raise TypeError("widgets must be a list, found %s" % widgets)
        for widget in widgets:
            if not isinstance(widget, gtk.Widget):
                raise TypeError(
                "Only Gtk widgets may be passed in list, found\n%s" % widget)
            if after:
                widget.connect_after(signal, handler)
            else:
                widget.connect(signal, handler)

    def disconnect_autoconnected(self):
        """
        Disconnect handlers previously connected with 
        autoconnect_signals()"""
        self.__broker.disconnect_autoconnected()
        
    def handler_block(self, widget, signal_name=None):
        # XXX: Warning, or bail out?
        if not self.__broker:
            return
        self.__broker.handler_block(widget, signal_name)

    def handler_unblock(self, widget, signal_name=None):
        if not self.__broker:
            return
        self.__broker.handler_unblock(widget, signal_name)
        
    #
    # Proxies
    #

    def add_proxy(self, model=None, widgets=None):
        """
        Add a proxy to this view that automatically update a model when
        the view changes. Arguments:
          
          - model. the object we are proxing. It can be None if we don't have
          a model yet and we want to display the interface and set it up with
          future models.
          - widgets. the list of widgets that contains model attributes to be
          proxied. If it is None (or not specified) it will be the whole list
          of widgets this View has.

        This method return a Proxy object that you may want to use to force
        updates or setting new models. Keep a reference to it since there is
        no way to get that proxy later on. You have been warned (tm)
        """
        widgets = widgets or self.widgets

        for widget_name in widgets:
            widget = getattr(self, widget_name, None)
            if (widget is None or
                not isinstance(widget, MixinSupportValidation)):
                continue

            try:
                widget.connect_object('validation-changed',
                                      self._on_child__validation_changed,
                                      widget_name)
            except TypeError:
                raise AssertionError("%r does not have a validation-changed "
                                     "signal." % widget)

        proxy = Proxy(self, model, widgets)
        self.proxies.append(proxy)

        return proxy

    #
    # Validation
    #
    
    def _on_child__validation_changed(self, name, value):
        # Children of the view, eg slaves or widgets are connected to this signal
        # When validation changes of a validatable child this callback is called
        self._validation[name] = value

        self.check_and_notify_validity()
        
    def check_and_notify_validity(self, force=False):
        # Current view is only valid if we have no invalid children
        # their status are stored as values in the dictionary
        is_valid = True
        if False in self._validation.values():
            is_valid = False

        # Check if validation really changed
        if self._valid == is_valid and force == False:
            return

        self._valid = is_valid
        self.emit('validation-changed', is_valid)

        # FIXME: Remove and update all callsites to use validation-changed
        if self._validate_function:
            self._validate_function(is_valid)

    def force_validation(self):
        self.check_and_notify_validity(force=True)
        
gobject.type_register(SlaveView)

class BaseView(SlaveView):
    """A view with a toplevel window."""
    
    def __init__(self, toplevel=None, delete_handler=None, widgets=None,
                 gladefile=None, gladename=None, toplevel_name=None,
                 domain=None):
        """ toplevel is the widget to be set as `toplevel' (and which will
        be aliased as `win'); delete_handler allows setting a function
        to be called when this view's window is deleted."""
        try:
            SlaveView.__init__(self, toplevel, widgets, gladefile, gladename,
                               toplevel_name, domain)
        except KeyError:
            raise KeyError("Some widgets were defined in self.widgets "
                           "but not found in the glade tree (see previous "
                           "messages to see which ones).")
            

        if not isinstance(self.toplevel, gtk.Window):
            raise TypeError("toplevel widget must be a Window "
                            "(or inherit from it),\nfound `%s' %s" 
                            % (toplevel, self.toplevel))

        if delete_handler:
            id = self.toplevel.connect("delete_event", delete_handler)
            if not id:
                raise ValueError(
                    "Invalid delete handler provided: %s" % delete_handler)

    def _init_glade_adaptor(self):
        self.glade_adaptor = WidgetTree(self, self.gladefile,
                                        self.widgets, self.gladename)
        name = self.toplevel_name or self.glade_adaptor.gladename
        self.toplevel = self.glade_adaptor.get_widget(name)

        if self.toplevel.flags() & gtk.VISIBLE:
            _warn("Toplevel widget %s (%s) is visible; that's probably "
                  "wrong" % (self.toplevel, name))
            
    
    #
    # Hook for keypress handling
    #

    def _attach_callbacks(self, controller):
        super(BaseView, self)._attach_callbacks(controller)
        self._setup_keypress_handler(controller.on_key_press)
        
    def _setup_keypress_handler(self, keypress_handler):
        self.toplevel.connect_after("key_press_event", keypress_handler)

    #
    # Proxying for self.toplevel
    #
    def set_transient_for(self, view):
        """Makes the view a transient for another view; this is commonly done
        for dialogs, so the dialog window is managed differently than a
        top-level one.
        """
        if hasattr(view, 'toplevel') and isinstance(view.toplevel, gtk.Window):
            self.toplevel.set_transient_for(view.toplevel)
        # In certain cases, it is more convenient to send in a window;
        # for instance, in a deep slaveview hierarchy, getting the
        # top view is difficult. We used to print a warning here, I
        # removed it for convenience; we might want to put it back when
        # http://bugs.async.com.br/show_bug.cgi?id=682 is fixed
        elif isinstance(view, gtk.Window):
            self.toplevel.set_transient_for(view)
        else:
            raise TypeError("Parameter to set_transient_for should "
                            "be View (found %s)" % view)

    def set_title(self, title):
        """Sets the view's window title"""
        self.toplevel.set_title(title)

    #
    # Focus handling
    #

    def get_focus_widget(self):
        """Returns the currently focused widget in the window"""
        return self.toplevel.focus_widget

    def check_focus(self):
        """ Tests the focus in the window and prints a warning if no
        widget is focused.
        """
        focus = self.toplevel.focus_widget
        if focus:
            return
        values = self.__dict__.values()
        interactive = None
        # Check if any of the widgets is interactive
        for v in values:
            if (isinstance(v, gtk.Widget) and not
                isinstance(v, _non_interactive)):
                interactive = v
        if interactive:
            _warn("No widget is focused in view %s but you have an "
                  "interactive widget in it: %s""" % (self, interactive))

    #
    # Window show/hide and mainloop manipulation
    #

    def hide(self, *args):
        """Hide the view's window"""
        self.toplevel.hide()

    def show_all(self, parent=None, *args):
        self.toplevel.show_all()
        self.show(parent, *args)

    def show(self, parent=None, *args):
        """Show the view's window.
        If the parent argument is supplied and is a valid view, this view
        is set as a transient for the parent view.
        """
        # Uniconize window if minimized
        self.toplevel.present() # this call win.show() for us
        self.check_focus()
        if parent is not None:
            self.set_transient_for(parent)

    def quit_if_last(self, *args):
        quit_if_last(*args)
        
    def hide_and_quit(self, *args):
        """Hides the current window and breaks the GTK+ event loop if this
        is the last window.
        Its method signature allows it to be used as a signal handler.
        """
        self.toplevel.hide()
        self.quit_if_last()
