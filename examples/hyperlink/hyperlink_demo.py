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
# This module: (C) Ali Afshar <aafshar@gmail.com>
# (contact if you require release under a different license)


""" HyperLink demo application. """


import time

import gtk

from kiwi.ui import hyperlink


class App(object):

    def __init__(self):
        self._window = gtk.Window()
        self._window.connect('destroy', self._on_window__destroy)
        self._window.set_title('Hyperlink Widget Demo')
        vb = gtk.VBox(spacing=3)
        vb.set_border_width(12)
        self._window.add(vb)
        self._build_basic_hyperlink(vb)
        vb.pack_start(gtk.HSeparator(), expand=False, padding=6)
        self._build_formatted_hyperlink(vb)
        vb.pack_start(gtk.HSeparator(), expand=False, padding=6)
        self._build_menu_hyperlink(vb)
        vb.pack_start(gtk.HSeparator(), expand=False, padding=6)
        sw = gtk.ScrolledWindow()
        vb.pack_start(sw)
        sw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_ALWAYS)
        self._logger = gtk.TextView()
        sw.add(self._logger)
        self._logger.set_editable(False)
        self._window.show_all()

    def _build_basic_hyperlink(self, vb):
        self._hl1 = hyperlink.HyperLink('basic hyperlink')
        vb.pack_start(self._hl1, expand=False)
        self._hl1.connect('clicked', self._on_hl1__clicked)
        self._hl1.connect('right-clicked', self._on_hl1__right_clicked)
        d1 = gtk.Label(
            'I am a basic hyperlink. The signals I emit are "clicked" and'
            ' "right-clicked". Try me out')
        d1.set_line_wrap(True)
        vb.pack_start(d1, expand=False)

    def _build_formatted_hyperlink(self, vb):
        self._hl2 = hyperlink.HyperLink('hyperlink with formatting')
        vb.pack_start(self._hl2, expand=False)
        self._hl2.normal_color = '#c000c0'
        self._hl2.hover_color = '#00c0c0'
        self._hl2.active_color = '#000000'
        self._hl2.hover_bold = True
        self._hl2.active_bold = True
        self._hl2.connect('clicked', self._on_hl2__clicked)
        self._hl2.connect('right-clicked', self._on_hl2__right_clicked)
        d1 = gtk.Label(
            'I am a formatted hyperlink. I can be modified by setting'
            ' my properties like normal-color. Click me to change me!')
        d1.set_line_wrap(True)
        vb.pack_start(d1, expand=False)

    def _build_menu_hyperlink(self, vb):
        self._hl3 = hyperlink.HyperLink('menu hyperlink')
        vb.pack_start(self._hl3, expand=False)
        self._hl3.connect('clicked', self._on_hl3__clicked)
        self._hl3.connect('right-clicked', self._on_hl3__right_clicked)
        self._hl3.hover_underline = False
        self._hl3.active_underline = False
        menu = gtk.Menu()
        m1 = gtk.MenuItem()
        m1.add(gtk.Label('toggle bold'))
        menu.add(m1)
        m1.connect('activate', self._on_m1_activated)
        m2 = gtk.MenuItem()
        m2.add(gtk.Label('toggle underline'))
        menu.add(m2)
        m2.connect('activate', self._on_m2_activated)
        menu.show_all()
        self._hl3.set_menu(menu)
        d1 = gtk.Label(
            'I am a hyperlink with a menu. Right click me to pop it up.')
        d1.set_line_wrap(True)
        vb.pack_start(d1, expand=False)

    def start(self):
        gtk.main()

    def stop(self):
        gtk.main_quit()

    def _on_window__destroy(self, window):
        self.stop()

    def _on_hl1__clicked(self, hyperlink):
        self.log('basic hyperlink clicked')

    def _on_hl1__right_clicked(self, hyperlink):
        self.log('basic hyperlink right-clicked')

    def _on_hl2__clicked(self, hyperlink):
        self.log('formatted hyperlink clicked')
        hyperlink.normal_color = '#c00000'
        hyperlink.normal_bold = True
        if not hyperlink.text.startswith('au'):
            hyperlink.text = 'automatically! by setting self.text = foo'
        else:
            hyperlink.text = 'and changed back again'

    def _on_hl2__right_clicked(self, hyperlink):
        self.log('formatted hyperlink right-clicked')

    def _on_hl3__clicked(self, hyperlink):
        self.log('menu hyperlink clicked')

    def _on_hl3__right_clicked(self, hyperlink):
        self.log('menu hyperlink right-clicked')

    def _on_m1_activated(self, menuitem):
        self.log('menuitem 1 activated')
        self._hl3.normal_bold = not self._hl3.normal_bold
        self._hl3.hover_bold = not self._hl3.hover_bold
        self._hl3.active_bold = not self._hl3.active_bold

    def _on_m2_activated(self, menuitem):
        self.log('menuitem 2 activated')
        self._hl3.normal_underline = not self._hl3.normal_underline
        self._hl3.hover_underline = not self._hl3.hover_underline
        self._hl3.active_underline = not self._hl3.active_underline

    def log(self, msg):
        buf = self._logger.get_buffer()
        timestr = time.strftime('%H:%M:%S')
        buf.insert(buf.get_start_iter(), '%s...%s\n' % (timestr, msg))


def main():
    a = App()
    a.start()

if __name__ == '__main__':
    main()
