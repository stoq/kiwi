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
#

"""Holds the models part of the Kiwi Framework"""

import os
import pickle

from kiwi import _warn
#
# A model that implements half of an observer pattern; when its
# attributes are changed, it notifies any proxies of the change.
#

class Model:
    """
    The Model is a mixin to be used by domain classes when attached to
    Proxies.  It also provides autonotification of changes to the
    attached proxies. Note that if using setters, a specific call to
    notify_proxies() may be necessary; see the doc for __setattr__."""
    def __init__(self):
        self.ensure_init()

    def ensure_init(self):
        """
        Sets up the variables so the Model's getattr hook and proxy
        notification work properly.
        """
        # Work around setattr hook. The _v prefixes to the variables let
        # the ZODB know that there are non-persistant values. This
        # workaround is fine because the API protects them and it
        # doesn't affect any other persistence mechanism I know of.
        self.__dict__["_v_blocked_proxies"] = []
        self.__dict__["_v_proxies"] = {}
        self.__dict__["_v_autonotify"] = 1

    def disable_autonotify(self):
        """
        disable automatic notification to proxies based on __setattr__.
        All changes to the model must be followed by a call to
        notify_proxies() to allow the proxies to notice the change."""
        if not hasattr(self, "_v_proxies"): self.ensure_init()
        self._v_autonotify = 0

    def notify_proxies(self, attr):
        """Notify proxies that an attribute value has changed."""
        if not hasattr(self, "_v_proxies"): self.ensure_init()
        for proxy in self._v_proxies.get(attr, []):
            if proxy not in self._v_blocked_proxies:
                proxy.notify(attr)

    def register_proxy_for_attribute(self, attr, proxy):
        """
        Attach a proxy to an attribute. The proxy will be notified of
        changes to that particular attribute (my means of
        Proxy.notify())."""
        if not hasattr(self, "_v_proxies"): self.ensure_init()
        proxies = self._v_proxies
        # XXX: should use weakref if possible, and if not, warn of leaks
        if not proxies.has_key(attr):
            proxies[attr]=[proxy]
        else:
            if proxy in proxies[attr]:
                raise AssertionError, ("Tried to attach proxy %s "
                                       "twice to attribute `%s'." 
                                       % ( proxy, attr ))
            proxies[attr].append(proxy)

    def unregister_proxy_for_attribute(self, attr, proxy):
        """Detach a proxy from an attribute."""
        if not hasattr(self, "_v_proxies"): self.ensure_init()
        proxies = self._v_proxies
        if proxies.has_key(attr) and proxy in proxies[attr]:
            # Only one listener per attribute per proxy, so remove()
            # works
            proxies[attr].remove(proxy)

    def unregister_proxy(self, proxy):
        """Deattach a proxy completely from the model"""
        if not hasattr(self, "_v_proxies"): self.ensure_init()
        proxies = self._v_proxies
        for attribute in proxies.keys():
            if proxy in proxies[attribute]:
                # Only one listener per attribute per proxy, so remove()
                # works
                proxies[attribute].remove(proxy)

    def flush_proxies(self):
        """Removes all proxies attached to Model"""
        self._v_proxies = {}
        self._v_blocked_proxies = []

    def block_proxy(self, proxy):
        """
        Temporarily block a proxy from receiving any notification. See
        unblock_proxy()"""
        if not hasattr(self, "_v_proxies"): self.ensure_init()
        blocked_proxies = self._v_blocked_proxies
        if proxy not in blocked_proxies:
            blocked_proxies.append(proxy)
    
    def unblock_proxy(self, proxy):
        """Re-enable notifications to a proxy"""
        if not hasattr(self, "_v_proxies"): self.ensure_init()
        blocked_proxies = self._v_blocked_proxies
        if proxy in blocked_proxies:
            blocked_proxies.remove(proxy)

    def __setattr__(self, attr, value):
        """
        A special setattr hook that notifies the registered proxies that
        the model has changed. Work around it setting attributes
        directly to self.__dict__.

        Note that setattr() assumes that the name of the attribute being
        changed and the proxy attribute are the same. If this is not the
        case (as may happen when using setters) you must call
        notify_proxies() manually from the subclass' setter.
        """
        # XXX: this should be done last, since the proxy notification
        # may raise an exception. Or do we ignore this fact?
        self.__dict__[attr] = value

        if not hasattr(self, "_v_proxies"): self.ensure_init()

        if self._v_autonotify and self._v_proxies.has_key(attr):
            self.notify_proxies(attr)

#
# A sample model that pickles itself into a file
#

class PickledModel(Model):
    """
    PickledModel is a model that is able to save itself into a pickle
    using save().  This has all the limitations of a pickle: its
    instance variables must be picklable, or pickle.dump() will raise
    exceptions. You can prefix variables with an underscore to make them
    non-persistent (and you can restore them accordingly by overriding
    __setstate__, but don't forget to call PickledModel.__setstate__)"""

    def save(self, file=None):
        """
        Saves the instance to a pickle file. If no file argument is
        provided, will try to use the internal _file attribute that is
        set using set_filename()"""
        file = file or getattr(self, "_file", None)
        if not file:
            msg = "No pickle specified, don't know where to save myself"
            raise AttributeError, msg
        fh = open(file, "w")
        try:
            pickle.dump(self, fh)
        except pickle.PicklingError, e:
            fh.close()
            msg = ("Tried to pickle an instance variable that isn't "
                   "supported by pickle.dump(). To work around this, you "
                   "can prefix the variable name with an underscore "
                   " and it will be ignored by the pickle machinery "
                   "in PickledModel. The original error "
                   "follows:\n\n%s")
            raise AttributeError, msg % e
        fh.close()

    def set_filename(self, filename):
        """
        Sets the name of the file which will be used to pickle the
        model"""
        self._file = filename

    def __getstate__(self):
        """Gets the state from the instance to be pickled"""
        odict = self.__dict__
        for key in odict.keys():
            if key[0] == "_":
                del odict[key]
        return odict

    def __setstate__(self,dict):
        """Sets the state to the instance when being unpickled"""
        Model.__dict__["__init__"](self)
        self.__dict__.update(dict)

def unpickle_model(klass, file=None):
    """
    Loads an instance from a pickle file; if it fails for some reason,
    create a new instance.

        - klass: a class to instance if the pickle is non-existent,
          empty or invalid

        - file: the file from which the pickle should be loaded. If file
          is not provided, the name of the class suffixed by ".pickle"
          is used (i.e.  "FooClass.pickle" for the class FooClass).

    If the pickle file is damaged, it will be saved with the extension
    ".err"; if a file with that name also exists, it will use ".err.1"
    and so on. This is to avoid the damaged file being clobbered by an
    instance calling save() unsuspectingly.
    """
    if not file:
        file = klass.__name__ + ".pickle"

    if not os.path.exists(file):
        ret = klass()
        ret.set_filename(file)
        return ret

    fh = open(file, "r")
    try:
        data = fh.read()
        ret = pickle.loads(data)
    except (EOFError, KeyError):
        # save backup of original pickle with an extension of 
        # .err, .err.1, .err.2, etc.
        stem = file + ".err"
        i = 0
        backup = stem
        while os.path.exists(backup):
            i = i + 1
            backup = stem + ".%d" % i
        open(backup, "w").write(data)
        _warn("pickle in %r was broken, saving backup in %r and creating "
              "new <%s> instance\n""" % (file, backup, klass.__name__))
        ret = klass()
    fh.close()
    ret.set_filename(file)
    return ret

# TODO: implement a Model that saves itself as CSV/XML?

