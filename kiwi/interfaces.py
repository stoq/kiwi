#
# Kiwi: a Framework and Enhanced Widgets for Python
#
# Copyright (C) 2005-2006 Async Open Source
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

class IProxyWidget(Interface):
    """
    IProxyWidget is a widget that can be attached to a proxy.

    Signals::
       content-changed: This must be emitted when the content changes

    Properties::
       data-type: string, data type of the model
       model-attribute: string, name of the attribute in the model
    """

    def read():
        """
        Reads the content of the widget and returns in an appropriate
        data type.
        ValueUnset is returned when the user has not modified the entry
        """
        pass

    def update(value):
        """
        Updates the content of the widget with a value
        """
        pass

class IValidatableProxyWidget(IProxyWidget):
    """
    IValidatableProxyWidget extends IProxyWidget with validation support

    Signals::
       validate: This emitted so each widget can provide it's own
         custom validation.
       validation-changed: This is emitted when the validation status
         changes, mainly used by the proxy.

    Properties::
       mandatory: bool, if the widget is mandatory
    """

    def is_valid():
        pass

    def validate(force=False):
        pass

class IEasyCombo(Interface):

    def prefill(itemdata, sort=False):
        """Fills the Combo with listitems corresponding to the itemdata
        provided.

        Parameters:
          - itemdata is a list of strings or tuples, each item corresponding
            to a listitem. The simple list format is as follows::

            >>> [ label0, label1, label2 ]

            If you require a data item to be specified for each item, use a
            2-item tuple for each element. The format is as follows::

            >>> [ ( label0, data0 ), (label1, data1), ... ]

          - Sort is a boolean that specifies if the list is to be sorted by
            label or not. By default it is not sorted
        """

    def append_item(label, data=None):
        """Adds a single item to the Combo.
        @param label: a string with the text to be added
        @param data: the data to be associated with that item
        """

    def clear():
        """Removes all items from the widget"""

    def select(data):
        """
        Select an item giving data which could be an object or text.
        @param data: data or text to select
        """

    def select_item_by_position(position):
        """
        Selects an item in the combo from a integer where 0
        represents the first item.
        @param position: an integer
        """

    def select_item_by_label(text):
        """
        Select item given text.
        @param text: text to select
        """

    def select_item_by_data(data):
        """
        Select item given data.
        @param data: object to select
        """

    def get_selected_label():
        """
        Gets the label of the currently selected item.
        @returns: the selected label.
        """

    def get_selected_data():
        """
        Gets the data of the the currently selected item.
        @returns: the selected data.
        """

    def get_selected():
        """
        Get  the text or item  of the currently selected item
        or None if nothing is selected.
        @returns: selected text or item or None.
        """

    def get_model_strings():
        pass

    def get_model_items():
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

class ISearchFilter(Interface):

    def get_state():
        """
        Gets the state.
        @rtype: L{QueryState}
        """
