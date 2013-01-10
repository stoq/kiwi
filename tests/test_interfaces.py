#
# Kiwi: a Framework and Enhanced Widgets for Python
#
# Copyright (C) 2012 Async Open Source
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
## Author(s): Thiago Bellini <hackedbellini@async.com.br>
#

import unittest

from zope.interface import implementedBy
from zope.interface.exceptions import Invalid
from zope.interface.verify import verifyClass

from .utils import get_interfaces_for_package


class TestInterfaces(unittest.TestCase):
    def testInterfaces(self):
        for klass in get_interfaces_for_package('kiwi'):
            for iface in implementedBy(klass):
                try:
                    verifyClass(iface, klass)
                except Invalid as err:
                    self.fail("%s(%s): %s" % (klass.__name__,
                                              iface.__name__, err))
