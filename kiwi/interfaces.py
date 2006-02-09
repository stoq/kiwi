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

"""Interface specifications and utilities"""

from kiwi.component import Interface

Nothing = object()

class Mixin(Interface):
    # gsignal('content-changed')
    # gproperty('data-type')
    # gproperty('model-attribute')
    # gproperty('validation-changed')

    def read(self):
        pass

    def update(self, value):
        pass

class MixinSupportValidation(Interface):
    # gproperty('mandatory')
    def is_valid(self):
        pass

    # These two are mainly used by subclasses
    def validate(self, data=Nothing, force=False):
        pass

    def before_validate(self, data):
        pass

class AbstractGladeAdaptor(Interface):
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
