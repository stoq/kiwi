# This example illustrates the use of entries with validations

import datetime

import gtk

from kiwi.datatypes import ValidationError
from kiwi.currency import currency
from kiwi.ui.delegates import GladeDelegate


class Person:
    pass


class Form(GladeDelegate):

    def __init__(self):
        GladeDelegate.__init__(self,
                               gladefile="personalinformation.ui",
                               delete_handler=self.quit_if_last)

        self.nationality.prefill(['Brazilian',
                                  'Yankee',
                                  'Other'])
        self.gender.prefill(('Male', 'Female'))
        self.age.set_mask('00')

        self.register_validate_function(self.validity)
        # XXX: Get rid of this
        self.force_validation()

    # here we define our custom validation. When a user types anything,
    # the validate signal calls methods with the signature
    # on_widgetname__validate
    def on_name__validate(self, widget, data):
        if len(data) > 20:
            # we need to return an exception that will be displayed on
            # the information tooltip and the delegate option
            return ValidationError("The name is too long")

    def on_age__validate(self, widget, year):
        if year > 75:
            return ValidationError("Too old")

    def on_height__validate(self, widget, data):
        if data > 200:
            return ValidationError("The height is too tall")

    def on_weight__validate(self, widget, data):
        if float(data) > 90:
            # this is really not the type of validation that you would use :)
            # anyway, it's just for reference
            return ValidationError("Dude! You need to lose "
                                   "some weight!")

    def on_nationality__validate(self, widget, data):
        if data != 'Yankee':
            return ValidationError("Go home terrorist!")

    def validity(self, valid):
        self.ok_btn.set_sensitive(valid)

    def on_about__validate(self, widget, data):
        if not 'kinda' in data.lower():
            return ValidationError("use a better language")

person = Person()
person.name = u'John Doe'
person.age = 36
person.birthdate = datetime.datetime(year=1969, month=2, day=20)
person.height = 183.0
person.weight = 86.0
person.nationality = 'Yankee'
person.about = 'Kinda fat'
person.status = True
person.gender = 'Female'
person.salary = currency(1234)

form = Form()
proxy = form.add_proxy(person, ['name', 'age', 'birthdate',
                                'height', 'weight', 'about',
                                'nationality', 'status', 'gender', 'salary'])
form.show_all()


def on_ok_btn_clicked(widget):
    print "Name:", person.name
    print "Age:", person.age
    print "Birthday:", person.birthdate
    print "Height:", person.height
    print "Weight:", person.weight
    print "Nationality:", person.nationality
    print "About Your self:", person.about
    print "Status:", person.status

    gtk.main_quit()

form.ok_btn.connect("clicked", on_ok_btn_clicked)
gtk.main()
