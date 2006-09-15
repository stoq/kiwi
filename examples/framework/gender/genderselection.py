import gtk

from kiwi.ui.views import BaseView, quit_if_last

class Person:
    gender = "Male"

class GenderSelection(BaseView):
    gladefile = 'gender'
    widgets = ['male', 'female', 'other']

    def __init__(self):
        BaseView.__init__(self, delete_handler=quit_if_last)
        self.model = Person()
        self.add_proxy(self.model, self.widgets)

view = GenderSelection()
view.show_all()
gtk.main()
print view.model.gender
