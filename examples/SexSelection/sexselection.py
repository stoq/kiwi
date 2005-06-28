from kiwi.initgtk import gtk, quit_if_last
from kiwi.Views import BaseView 

class person:
    pass

class sexselection(BaseView):
    gladefile = 'sex_selection'
    widgets = ['male', 'female', 'other']

    def __init__(self):
        BaseView.__init__(self, self.gladefile, delete_handler=quit_if_last)
        self.obj = person()
        self.add_proxy(self.obj, self.widgets)
          
test = sexselection()
test.show_all()
gtk.main()
print test.obj.sex

