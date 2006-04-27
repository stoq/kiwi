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
# Author(s): Johan Dahlin <jdahlin@async.com.br
#

"""User interface: Testing

This is a framework for testing graphical applications.
The two main parts of the framework are the
L{Player<kiwi.ui.test.player.Player>} and the
L{Recorder<kiwi.ui.test.recorder.Recorder>}.

The recorder listens to certain events happening inside the application
and writes a script which later on can be played back by the player.

To record a test::

    kiwi-ui-test --record=script.py application [arguments]

To play back a recorded test::

    kiwi-ui-test script.py

"""
