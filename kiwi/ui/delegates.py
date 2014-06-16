#
# Kiwi: a Framework and Enhanced Widgets for Python
#
# Copyright (C) 2002, 2003 Async Open Source
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
#            Johan Dahlin <jdahlin@async.com.br>
#

"""Defines the Delegate classes that are included in the Kiwi Framework."""

from kiwi.ui.views import SlaveView, BaseView
from kiwi.controllers import BaseController


class Delegate(BaseView, BaseController):
    """A class that combines view and controller functionality into a
    single package. The Delegate class possesses a top-level window.
    """
    def __init__(self, toplevel=None, widgets=None, toplevel_name=None,
                 delete_handler=None, keyactions=None):
        """Creates a new Delegate.
        The keyactions parameter is sent to :class:`kiwi.controllers.BaseController`,
        the rest are sent to :class:`kiwi.ui.views.BaseView`
        """
        BaseView.__init__(self,
                          toplevel=toplevel,
                          widgets=widgets or [],
                          toplevel_name=toplevel_name,
                          delete_handler=delete_handler)
        BaseController.__init__(self, view=self, keyactions=keyactions)


class GladeDelegate(BaseView, BaseController):
    """A class that combines view and controller functionality into a
    single package. The Delegate class possesses a top-level window.
    """
    def __init__(self, gladefile=None, toplevel_name=None, domain=None,
                 delete_handler=None, keyactions=None):
        """Creates a new GladeDelegate.
        The keyactions parameter is sent to :class:`kiwi.controllers.BaseController`,
        the rest are sent to :class:`kiwi.ui.views.BaseView`
        """

        BaseView.__init__(self,
                          gladefile=gladefile,
                          toplevel_name=toplevel_name,
                          domain=domain,
                          delete_handler=delete_handler)
        BaseController.__init__(self, view=self, keyactions=keyactions)


class SlaveDelegate(SlaveView, BaseController):
    """A class that combines view and controller functionality into a
    single package. It does not possess a top-level window, but is instead
    intended to be plugged in to a View or Delegate using attach_slave().
    """
    def __init__(self, toplevel=None, widgets=None,
                 toplevel_name=None, keyactions=None):
        """
        The keyactions parameter is sent to :class:`kiwi.controllers.BaseController`,
        the rest are sent to :class:`kiwi.ui.views.SlaveView`
        """
        widgets = widgets or []
        SlaveView.__init__(self, toplevel, widgets, toplevel_name)
        BaseController.__init__(self, view=self, keyactions=keyactions)


class GladeSlaveDelegate(SlaveView, BaseController):
    """A class that combines view and controller functionality into a
    single package. It does not possess a top-level window, but is instead
    intended to be plugged in to a View or Delegate using attach_slave().
    """
    def __init__(self, gladefile=None,
                 toplevel_name=None, domain=None,
                 keyactions=None):
        """
        The keyactions parameter is sent to :class:`kiwi.controllers.BaseController`,
        the rest are sent to :class:`kiwi.ui.views.SlavseView`
        """
        SlaveView.__init__(self,
                           gladefile=gladefile,
                           toplevel_name=toplevel_name,
                           domain=domain)
        BaseController.__init__(self, view=self, keyactions=keyactions)


class ProxyDelegate(Delegate):
    """A class that combines view, controller and proxy functionality into a
    single package. The Delegate class possesses a top-level window.

    :ivar model: the model
    :ivar proxy: the proxy
    """
    def __init__(self, model, proxy_widgets=None, gladefile=None,
                 toplevel=None, widgets=None,
                 toplevel_name=None, domain=None, delete_handler=None,
                 keyactions=None):
        """Creates a new Delegate.
        :param model: instance to be attached
        :param proxy_widgets:
        The keyactions parameter is sent to :class:`kiwi.controllers.BaseController`,
        the rest are sent to :class:`kiwi.ui.views.BaseView`
        """
        widgets = widgets or []

        BaseView.__init__(self, toplevel, widgets, gladefile,
                          toplevel_name, domain,
                          delete_handler)
        self.model = model
        self.proxy = self.add_proxy(model, proxy_widgets)
        self.proxy.proxy_updated = self.proxy_updated

        BaseController.__init__(self, view=self, keyactions=keyactions)

    def set_model(self, model):
        """
        Set model.
        :param model:
        """
        self.proxy.set_model(model)
        self.model = model

    def proxy_updated(self, widget, attribute, value):
        # Can be overriden in subclasses
        pass

    def update(self, attribute):
        self.proxy.update(attribute)


class ProxySlaveDelegate(GladeSlaveDelegate):
    """A class that combines view, controller and proxy functionality into a
    single package. It does not possess a top-level window, but is instead
    intended to be plugged in to a View or Delegate using attach_slave()

    :ivar model: the model
    :ivar proxy: the proxy
    """
    def __init__(self, model, proxy_widgets=None, gladefile=None,
                 toplevel_name=None, domain=None, keyactions=None):
        """Creates a new Delegate.
        :param model: instance to be attached
        :param proxy_widgets:
        The keyactions parameter is sent to :class:`kiwi.controllers.BaseController`,
        the rest are sent to :class:`kiwi.ui.views.BaseView`
        """

        GladeSlaveDelegate.__init__(self, gladefile, toplevel_name,
                                    domain, keyactions)
        self.model = model
        self.proxy = self.add_proxy(model, proxy_widgets)
        self.proxy.proxy_updated = self.proxy_updated

    def set_model(self, model):
        """
        Set model.
        :param model:
        """
        self.proxy.set_model(model)
        self.model = model

    def proxy_updated(self, widget, attribute, value):
        # Can be overriden in subclasses
        pass

    def update(self, attribute):
        self.proxy.update(attribute)
