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

class SlaveDelegate(SlaveView, BaseController):
    """A class that combines view and controller functionality into a
    single package. It does not possess a top-level window, but is instead
    intended to be plugged in to a View or Delegate using attach_slave().
    """
    def __init__(self, toplevel=None, widgets=[], gladefile=None,
                 gladename=None, toplevel_name=None, domain=None,
                 keyactions=None):
        """Create new SlaveDelegate. toplevel is the toplevel widget,
        defaults to the value of the class' toplevel attribute, and if not
        present, raises AttributeError.
        """
        SlaveView.__init__(self, toplevel, widgets, gladefile, gladename,
                           toplevel_name, domain)
        BaseController.__init__(self, view=self, keyactions=keyactions)

class Delegate(BaseView, BaseController):
    """A class that combines view and controller functionality into a
    single package. The Delegate class possesses a top-level window.
    """
    def __init__(self, toplevel=None, delete_handler=None, widgets=[],
                 gladefile=None, gladename=None, toplevel_name=None,
                 domain=None, keyactions=None):
        """Creates a new Delegate. For parameters , see BaseView.__init__"""
        BaseView.__init__(self, toplevel, delete_handler, widgets,
                          gladefile, gladename, toplevel_name, domain)
        BaseController.__init__(self, view=self, keyactions=keyactions)

