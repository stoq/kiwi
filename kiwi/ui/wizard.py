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
# Author(s): Gustavo Rahal <gustavo@async.com.br>
#            Evandro Vale Miquelito <evandro@async.com.br>
#            

import gtk

from kiwi.ui.delegates import Delegate

class WizardStep:
    """ This class must be inherited by the steps """
    def __init__(self, previous=None, header=None):
        self.previous = previous
        self.header = header

    def post_init(self):
        # This is a virtual method, which must be redefined on children 
        # classes, if applicable.
        pass
    
    def next_step(self):
        # This is a virtual method, which must be redefined on children 
        # classes. It should not be called by the last step (in this case,
        # has_next_step should return 0).
        raise NotImplementedError
       
    def has_next_step(self):
        # This method should return False on last step classes
        return True

    def has_previous_step(self): 
        # This method should return False on first step classes; since
        # self.previous is normally None for them, we can get away with
        # this simplified check. Redefine as necessary.
        return self.previous is not None

    def previous_step(self):
        return self.previous

class PluggableWizard(Delegate):
    """ Wizard controller and view class """
    retval = None
    def __init__(self, title, first_step, size=None):
        self._create_gui()
        Delegate.__init__(self, delete_handler=self.quit_if_last,
                          toplevel=self.wizard)
        self.set_title(title)
        self.first_step = first_step
        if size:
            self.get_toplevel().set_default_size(size[0], size[1])
        self.change_step(first_step)

    def _create_gui(self):
        self.next_btn = gtk.Button(stock=gtk.STOCK_GO_FORWARD)
        self.next_btn.set_use_stock(True)
        self.previous_btn = gtk.Button(stock=gtk.STOCK_GO_BACK)
        self.previous_btn.set_use_stock(True)
        self.cancel_btn = gtk.Button(stock=gtk.STOCK_CANCEL)
        self.cancel_btn.set_use_stock(True)
        
        self.message_lbl = gtk.Label("message")
        self.header_lbl = gtk.Label("header")
        
        cancel_btn_hbox = gtk.HButtonBox()
        cancel_btn_hbox.pack_start(self.cancel_btn)
        cancel_btn_hbox.set_spacing(10)
        cancel_btn_hbox.set_border_width(15)
        cancel_btn_hbox.set_layout('start')
        
        prev_next_btns_hbox = gtk.HButtonBox()
        prev_next_btns_hbox.pack_start(self.previous_btn)
        prev_next_btns_hbox.pack_start(self.next_btn)
        prev_next_btns_hbox.set_spacing(10)
        prev_next_btns_hbox.set_border_width(15)
        prev_next_btns_hbox.set_layout('end')
        
        self.wizard_slave_ev = gtk.EventBox()
        btns_hbox = gtk.HBox()
        btns_hbox.pack_start(cancel_btn_hbox)
        btns_hbox.pack_start(prev_next_btns_hbox)
        
        vbox = gtk.VBox()
        vbox.pack_start(self.header_lbl)
        vbox.pack_start(self.wizard_slave_ev)
        vbox.pack_start(btns_hbox)
        vbox.pack_start(self.message_lbl)
        vbox.set_child_packing(self.header_lbl, expand=False, fill=True, 
                               padding=0, pack_type='start')
        vbox.set_child_packing(self.message_lbl, expand=False, fill=True, 
                               padding=0, pack_type='start')
        vbox.set_child_packing(btns_hbox, expand=False, fill=True, 
                               padding=0, pack_type='start')
        
        self.wizard = gtk.Window()
        self.wizard.add(vbox)
        
    def change_step(self, step):
        if step is None:
            # Sometimes for different reasons the wizard needs to be
            # interrupted. In this case, next/previous_step should return
            # None to get the wizard interrupted. self.cancel is called
            # because it is the most secure action to do, since interrupt
            # here does not mean success
            return self.cancel()
        self.attach_slave('wizard_slave_ev', step)
        self.current = step
        if step.header:
            self.header_lbl.show()
            self.header_lbl.set_text(step.header)
        else:
            self.header_lbl.hide()
        self.update_view()
        self.current.post_init()
        return None

    def update_view(self): 
        # First page
        if not self.current.has_previous_step():
            self.enable_next()
            self.disable_back()
            self.disable_finish()
            self.message_lbl.hide()
        # Middle page
        elif self.current.has_next_step(): 
            self.enable_back()
            self.enable_next()
            self.disable_finish()
            self.message_lbl.hide()
        # Last page
        else:
            self.enable_back()
            self.disable_next()
            self.enable_finish()
            self.message_lbl.show()

    def enable_next(self):
        self.next_btn.set_sensitive(True)

    def enable_back(self):
        self.previous_btn.set_sensitive(True)

    def enable_finish(self):
        self.next_btn.set_label(gtk.STOCK_APPLY)
        self.wizard_finished = True
    
    def disable_next(self):
        self.next_btn.set_sensitive(False)

    def disable_back(self):
        self.previous_btn.set_sensitive(False)
        
    def disable_finish(self):
        self.next_btn.set_label(gtk.STOCK_GO_FORWARD)

    def on_next_btn__clicked(self, *args):
        assert self.current.has_next_step(), self.current
        self.change_step(self.current.next_step())
            
    def on_previous_btn__clicked(self, *args):
        self.change_step(self.current.previous_step())

    def on_cancel_btn__clicked(self, *args):
        self.cancel()

    def set_message(self, message):
        self.message_lbl.set_text(message)

    def cancel(self, *args):
        # Redefine this method if you want something done when cancelling the
        # wizard.
        self.retval = None

    def finish(self):
        # Redefine this method if you want something done when finishing the
        # wizard.
        pass
