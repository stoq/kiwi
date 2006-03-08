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
# Author(s): Johan Dahlin <jdahlin@async.com.br>
#            Lorenzo Gil Sanchez <lgs@sicem.biz>
#

import gtk

(COL_COMBO_LABEL,
 COL_COMBO_DATA) = range(2)

(COMBO_MODE_UNKNOWN,
 COMBO_MODE_STRING,
 COMBO_MODE_DATA) = range(3)

class ComboMixin(object):
    """Our combos always have one model with two columns, one for the string
    that is displayed and one for the object it cames from.
    """
    def __init__(self):
        """Call this constructor after the Combo one"""
        model = gtk.ListStore(str, object)
        self.set_model(model)
        self.mode = COMBO_MODE_UNKNOWN

    def set_mode(self, mode):
        if self.mode != COMBO_MODE_UNKNOWN:
            raise AssertionError
        self.mode = mode

    def __nonzero__(self):
        return True

    def __len__(self):
        return len(self.get_model())

    def prefill(self, itemdata, sort=False):
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
        if not isinstance(itemdata, (list, tuple)):
            raise TypeError("'data' parameter must be a list or tuple of item "
                            "descriptions, found %s") % type(itemdata)

        self.clear()
        if len(itemdata) == 0:
            return

        if self.mode == COMBO_MODE_UNKNOWN:
            first = itemdata[0]
            if isinstance(first, str):
                self.set_mode(COMBO_MODE_STRING)
            elif isinstance(first, (tuple, list)):
                self.set_mode(COMBO_MODE_DATA)
            else:
                raise TypeError("Could not determine type, items must "
                                "be strings or tuple/list")

        mode = self.mode
        model = self.get_model()

        values = {}
        if mode == COMBO_MODE_STRING:
            if sort:
                itemdata.sort()

            for item in itemdata:
                if item in values:
                    raise KeyError("Tried to insert duplicate value "
                                   "%s into Combo!" % item)
                else:
                    values[item] = None

                model.append((item, None))
        elif mode == COMBO_MODE_DATA:
            if sort:
                itemdata.sort(lambda x, y: cmp(x[0], y[0]))

            for item in itemdata:
                text, data = item
                if text in values:
                    raise KeyError("Tried to insert duplicate value "
                                   "%s into Combo!" % item)
                else:
                    values[text] = None
                model.append((text, data))
        else:
            raise TypeError("Incorrect format for itemdata; see "
                            "docstring for more information")

    def append_item(self, label, data=None):
        """ Adds a single item to the Combo. Takes:
        - label: a string with the text to be added
        - data: the data to be associated with that item
        """
        if not isinstance(label, str):
            raise TypeError("label must be string, found %s" % label)

        if self.mode == COMBO_MODE_UNKNOWN:
            if data is not None:
                self.set_mode(COMBO_MODE_DATA)
            else:
                self.set_mode(COMBO_MODE_STRING)

        model = self.get_model()
        if self.mode == COMBO_MODE_STRING:
            if data is not None:
                raise TypeError("data can not be specified in string mode")
            model.append((label, None))
        elif self.mode == COMBO_MODE_DATA:
            if data is None:
                raise TypeError("data must be specified in string mode")
            model.append((label, data))
        else:
            raise AssertionError

    def clear(self):
        """Removes all items from list"""
        model = self.get_model()
        model.clear()

    def select(self, data):
        mode = self.mode
        if self.mode == COMBO_MODE_STRING:
            self.select_item_by_label(data)
        elif self.mode == COMBO_MODE_DATA:
            self.select_item_by_data(data)
        else:
            # XXX: When setting the datatype to non string, automatically go to
            #      data mode
            raise TypeError("unknown ComboBox mode. Did you call prefill?")

    def select_item_by_position(self, pos):
        self.set_active(pos)

    def select_item_by_label(self, label):
        model = self.get_model()
        for row in model:
            if row[COL_COMBO_LABEL] == label:
                self.set_active_iter(row.iter)
                break
        else:
            raise KeyError("No item correspond to label %r in the combo %s"
                           % (label, self.name))

    def select_item_by_data(self, data):
        if self.mode != COMBO_MODE_DATA:
            raise TypeError("select_item_by_data can only be used in data mode")

        model = self.get_model()
        for row in model:
            if row[COL_COMBO_DATA] == data:
                self.set_active_iter(row.iter)
                break
        else:
            raise KeyError("No item correspond to data %r in the combo %s"
                           % (data, self.name))

    def get_model_strings(self):
        return [row[COL_COMBO_LABEL] for row in self.get_model()]

    def get_model_items(self):
        if self.mode != COMBO_MODE_DATA:
            raise TypeError("get_model_items can only be used in data mode")

        model = self.get_model()
        items = {}
        for row in model:
            items[row[COL_COMBO_LABEL]] = row[COL_COMBO_DATA]

        return items

    def get_selected_label(self):
        iter = self.get_active_iter()
        if not iter:
            return

        model = self.get_model()
        return model[iter][COL_COMBO_LABEL]

    def get_selected_data(self):
        if self.mode != COMBO_MODE_DATA:
            raise TypeError("get_selected_data can only be used in data mode")

        iter = self.get_active_iter()
        if not iter:
            return

        model = self.get_model()
        return model[iter][COL_COMBO_DATA]

    def get_selected(self):
        mode = self.mode
        if mode == COMBO_MODE_STRING:
            return self.get_selected_label()
        elif mode == COMBO_MODE_DATA:
            return self.get_selected_data()
        else:
            raise AssertionError

