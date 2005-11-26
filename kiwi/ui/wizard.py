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
        """A method called after the wizard step constructor and the main
        wizard update_view method.
        This is a virtual method, which must be redefined on children 
        classes, if applicable.
        """
    
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
    gladefile = 'PluggableWizard'
    retval = None

    def __init__(self, title, first_step, size=None, edit_mode=False):
        Delegate.__init__(self, delete_handler=self.quit_if_last,
                          gladefile=self.gladefile, 
                          widgets=self.widgets)
        self.set_title(title)
        self.first_step = first_step
        self.edit_mode = edit_mode
        if size:
            self.get_toplevel().set_default_size(size[0], size[1])
        self.change_step(first_step)
        self.get_toplevel().show_all()
        if not self.edit_mode:
            self.ok_button.hide()
        
    def change_step(self, step=None):
        if step is None:
            # This is the last step and we can finish the job here
            self.finish()
            return 
        step.show()
        holder_name = 'slave_area'
        if self.get_slave(holder_name):
            self.detach_slave(holder_name)
        self.attach_slave(holder_name, step)
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
        if self.edit_mode:
            self.ok_button.set_sensitive(True)
        if not self.current.has_previous_step():
            self.enable_next()
            self.disable_back()
            self.disable_finish()
            self.notification_lbl.hide()
        # Middle page
        elif self.current.has_next_step(): 
            self.enable_back()
            self.enable_next()
            self.disable_finish()
            self.notification_lbl.hide()
        # Last page
        else:
            self.enable_back()
            self.notification_lbl.show()
            if self.edit_mode:
                self.disable_next()
            else:
                self.enable_next()
            self.enable_finish()

    def enable_next(self):
        self.next_button.set_sensitive(True)

    def enable_back(self):
        self.previous_button.set_sensitive(True)

    def enable_finish(self):
        if self.edit_mode:
            widget = self.ok_button
        else:
            widget = self.next_button
        widget.set_label(gtk.STOCK_APPLY)
        self.wizard_finished = True
    
    def disable_next(self):
        self.next_button.set_sensitive(False)

    def disable_back(self):
        self.previous_button.set_sensitive(False)

    def disable_finish(self):
        if self.edit_mode:
            self.ok_button.set_label(gtk.STOCK_OK)
        else:
            self.next_button.set_label(gtk.STOCK_GO_FORWARD)

    def _call_step(self):
        """Call the next step performing first a small check in the 
        current one.
        """
        if not self.current.has_next_step():
            # This is the last step
            self.change_step()
            return
        self.change_step(self.current.next_step())

    def on_next_button__clicked(self, button):
        self._call_step()

    def on_ok_button__clicked(self, button):
        self._call_step()
            
    def on_previous_button__clicked(self, button):
        self.change_step(self.current.previous_step())

    def on_cancel_button__clicked(self, button):
        self.cancel()

    def set_message(self, message):
        self.notification_lbl.set_text(message)

    def cancel(self, *args):
        # Redefine this method if you want something done when cancelling the
        # wizard.
        self.retval = None

    def finish(self):
        # Redefine this method if you want something done when finishing the
        # wizard.
        pass
