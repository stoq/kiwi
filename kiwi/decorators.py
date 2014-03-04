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
# Author(s): Johan Dahlin <jdahlin@async.com.br>
#

"""Function and method decorators used in kiwi"""

from kiwi.log import kiwi_log


class deprecated(object):
    """
    I am a decorator which prints a deprecation warning each
    time you call the decorated (and deprecated) function
    """
    def __init__(self, new, log=None):
        """
        Create a new deprecated object.

        :param new: the name of the new function replacing the old
            deprecated one.
        :type new: string.
        :param log: the lob object to use, optional.
        """
        self._new = new
        self._log = log or kiwi_log

    def __call__(self, func):
        def wrapper(*args, **kwargs):
            self._log.warn("%s is deprecated, use %s instead" %
                           (func.__name__, self._new))
            return func(*args, **kwargs)
        try:
            wrapper.__name__ = func.__name__
        except TypeError, e:
            # __name__ is readonly in Python 2.3
            if e.args and e.args[0].find('readonly') != -1:
                pass
            else:
                raise
        return wrapper


class signal_block(object):
    """
    A decorator to be used on :class:`kiwi.ui.views.SlaveView` methods.
    It takes a list of arguments which is the name of the widget and
    the signal name separated by a dot.

    For instance:

        >>> from kiwi.ui.views import SlaveView
        >>> class MyView(SlaveView):
        ...     @signal_block('money.changed')
        ...     def update_money(self):
        ...         self.money.set_value(10)
        ...     def on_money__changed(self):
        ...         pass


    When calling update_money() the value of the spinbutton called money
    will be updated, but on_money__changed will not be called.
    """

    def __init__(self, *signals):
        self.signals = []
        for signal in signals:
            if not isinstance(signal, str):
                raise TypeError("signals must be a list of strings")
            if signal.count('.') != 1:
                raise TypeError("signal must have exactly one dot")
            self.signals.append(signal.split('.'))

    def __call__(self, func):
        def wrapper(view, *args, **kwargs):
            for name, signal in self.signals:
                widget = getattr(view, name, None)
                if widget is None:
                    raise TypeError("Unknown widget %s in view " % name)
                view.handler_block(name, signal)

            retval = func(view, *args, **kwargs)

            for name, signal in self.signals:
                view.handler_unblock(name, signal)

            return retval
        wrapper.__name__ = func.__name__
        return wrapper
