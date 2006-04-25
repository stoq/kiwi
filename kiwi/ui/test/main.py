#
# Kiwi: a Framework and Enhanced Widgets for Python
#
# Copyright (C) 2005,2006 Async Open Source
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

"""
Kiwi UI Test: command line interface
"""

import optparse
import sys

def _play(filename, args):
    from kiwi.ui.test.player import play_file
    play_file(filename, args)

def _record(filename, args):
    from kiwi.ui.test.listener import Listener

    Listener(filename, args[1:])

    sys.argv = args[1:]
    execfile(sys.argv[0])

def main(args):
    parser = optparse.OptionParser()
    parser.add_option('', '--record', action="store",
                      dest="record")
    options, args = parser.parse_args(args)

    if options.record:
        _record(options.record, args)
    else:
        if len(args) < 2:
            raise SystemExit("Error: needs a filename to play")
        _play(args[1], args[2:])
