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
# Author(s): Johan Dahlin <jdahlin@async.com.br>
#

from gtk import gdk


def pixbuf_from_string(pixbuf_data, format='png', width=None, height=None):
    loader = gdk.PixbufLoader(format)
    loader.write(pixbuf_data)
    loader.close()
    pixbuf = loader.get_pixbuf()
    if width is not None or height is not None:
        scaled_pixbuf = pixbuf.scale_simple(width, height, gdk.INTERP_BILINEAR)
        if scaled_pixbuf is None:
            print 'Warning: could not scale image'
        else:
            pixbuf = scaled_pixbuf
    return pixbuf
