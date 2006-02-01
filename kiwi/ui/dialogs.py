#
# Kiwi: a Framework and Enhanced Widgets for Python
#
# Copyright (C) 2005 Async Open Source
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.
#
# Author(s): Johan Dahlin <jdahlin@async.com.br>
#

import gettext

import gtk

__all__ = ['error', 'info', 'messagedialog', 'warning', 'yesno']

_ = gettext.gettext

def messagedialog(dialog_type, short, long=None, parent=None,
                  buttons=gtk.BUTTONS_OK, default=-1):
    """Create and show a MessageDialog.

    @param dialog_type: one of constants
      - gtk.MESSAGE_INFO
      - gtk.MESSAGE_WARNING
      - gtk.MESSAGE_QUESTION
      - gtk.MESSAGE_ERROR
    @param short:       A header text to be inserted in the dialog.
    @param long:        A long description of message.
    @param parent:      The parent widget of this dialog
    @type parent:       a gtk.Window subclass
    @param buttons:     The button type that the dialog will be display,
      one of the constants:
       - gtk.BUTTONS_NONE
       - gtk.BUTTONS_OK
       - gtk.BUTTONS_CLOSE
       - gtk.BUTTONS_CANCEL
       - gtk.BUTTONS_YES_NO
       - gtk.BUTTONS_OK_CANCEL
      or a tuple or 2-sized tuples representing label and response. If label
      is a stock-id a stock icon will be displayed.
    @param default: optional default response id
    """
    if buttons in (gtk.BUTTONS_NONE, gtk.BUTTONS_OK, gtk.BUTTONS_CLOSE,
                   gtk.BUTTONS_CANCEL, gtk.BUTTONS_YES_NO,
                   gtk.BUTTONS_OK_CANCEL):
        dialog_buttons = buttons
        buttons = []
    else:
        if type(buttons) != tuple:
            raise TypeError(
                "buttons must be a GtkButtonsTypes constant or a tuple")
        dialog_buttons = gtk.BUTTONS_NONE

    if parent and not isinstance(parent, gtk.Window):
        raise TypeError("parent must be a gtk.Window subclass")

    d = gtk.MessageDialog(parent=parent, flags=gtk.DIALOG_MODAL,
                          type=dialog_type, buttons=dialog_buttons)
    for text, response in buttons:
        d.add_buttons(text, response)

    d.set_markup("<span size=\"larger\"><b>%s</b></span>" % short)

    if long:
        if isinstance(long, gtk.Widget):
            widget = long
        elif isinstance(long, basestring):
            widget = gtk.Label()
            widget.set_markup(long)
        else:
            raise TypeError("long must be a gtk.Widget or a string")

        expander = gtk.Expander(_("Click here for details"))
        expander.set_border_width(6)
        expander.add(widget)
        d.vbox.pack_end(expander)

    if parent:
        d.set_title('')

    if default != -1:
        d.set_default_response(default)

    d.show_all()
    response = d.run()
    d.destroy()
    return response

def _simple(type, short, long=None, parent=None, buttons=gtk.BUTTONS_OK,
          default=-1):
    if buttons == gtk.BUTTONS_OK:
        default = gtk.RESPONSE_OK
    return messagedialog(type, short, long,
                         parent=parent, buttons=buttons,
                         default=default)

def error(short, long=None, parent=None, buttons=gtk.BUTTONS_OK, default=-1):
    return _simple(gtk.MESSAGE_ERROR, short, long, parent=parent,
                   buttons=buttons, default=default)

def info(short, long=None, parent=None, buttons=gtk.BUTTONS_OK, default=-1):
    return _simple(gtk.MESSAGE_INFO, short, long, parent=parent,
                   buttons=buttons, default=default)

def warning(short, long=None, parent=None, buttons=gtk.BUTTONS_OK, default=-1):
    return _simple(gtk.MESSAGE_WARNING, short, long, parent=parent,
                   buttons=buttons, default=default)

def yesno(text, parent=None, default=gtk.RESPONSE_YES):
    return messagedialog(gtk.MESSAGE_WARNING, text, None, parent,
                         buttons=gtk.BUTTONS_YES_NO,
                         default=default)

def _test():
    yesno('Kill?', default=gtk.RESPONSE_NO)

    info('Do it', buttons=((gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL),
                           ('Resume', gtk.RESPONSE_OK)),
         default=gtk.RESPONSE_OK,
         )

    error('An error occurred', gtk.Button('Woho'))
    error('An error occurred',
          'Long description bla bla bla bla bla bla bla bla bla\n'
          'bla bla bla bla bla lblabl lablab bla bla bla bla bla\n'
          'lbalbalbl alabl l blablalb lalba bla bla bla bla lbal\n')

if __name__ == '__main__':
    _test()
