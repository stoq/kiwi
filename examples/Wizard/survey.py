import gtk

from kiwi.ui.wizard import PluggableWizard
from kiwi.ui.wizard import WizardStep
from kiwi.ui.delegates import SlaveDelegate

#
# First lets set up the slaves that will be used on each step of the wizard
#
class EmploymentStatusSlave(SlaveDelegate):
    def __init__(self, parent):
        self.parent = parent
        SlaveDelegate.__init__(self, gladefile="employment_status",
                               widgets=["rb_executive",
                                        "rb_management",
                                        "rb_other"])

class ProgrammingLangSlave(SlaveDelegate):
    def __init__(self, parent):
        self.parent = parent
        SlaveDelegate.__init__(self, gladefile="programming_lang",
                               widgets=["cb_python",
                                        "cb_java",
                                        "cb_perl",
                                        "cb_other"])

class ThankYouSlave(SlaveDelegate):
    def __init__(self, parent):
        self.parent = parent
        SlaveDelegate.__init__(self, gladefile="thank_you",
                               widgets=[])

#
# Now lets create the Wizard class that will hold and control all steps of the wizard
#

class ITSurvey(PluggableWizard):
    def __init__(self):
        self.first_step = ProgrammingLangStep(self)
        PluggableWizard.__init__(self, title='IT Survey', first_step=self.first_step,
                                 size=(580, 400))
        self.disable_next()
        self.retval = None

    # lets define the finish method
    def finish(self):
        PluggableWizard.finish(self)

#
# Time to set up the steps!
#

# first step
class ProgrammingLangStep(WizardStep, ProgrammingLangSlave):
    def __init__(self, wizard, previous=None):
        WizardStep.__init__(self, previous)
        self.wizard = wizard
        
        ProgrammingLangSlave.__init__(self, self.wizard)
    
    def on_cb_other__toggled(self, *args):
        if self.cb_other.get_active():
            self.cb_python.set_inconsistent(True)
            self.cb_java.set_inconsistent(True)
            self.cb_perl.set_inconsistent(True)
        else:
            self.cb_python.set_inconsistent(False)
            self.cb_java.set_inconsistent(False)
            self.cb_perl.set_inconsistent(False)
        self.wizard.enable_next()
    
    def on_cb_python__toggled(self, *args):
        self.wizard.enable_next()
        
    def on_cb_java__toggled(self, *args):
        self.wizard.enable_next()
        
    def on_cb_perl__toggled(self, *args):
        self.wizard.enable_next()
    
    def next_step(self):
        # called when next button is clicked
        return EmploymentStatusStep(self.wizard, previous=self)

# second step
class EmploymentStatusStep(WizardStep, EmploymentStatusSlave):
    def __init__(self, wizard, previous=None):
        WizardStep.__init__(self, previous)
        self.wizard = wizard
        
        EmploymentStatusSlave.__init__(self, self.wizard)
    
    def next_step(self):
        return ThankYouStep(self.wizard, previous=self)
    
# third step
class ThankYouStep(WizardStep, ThankYouSlave):
    def __init__(self, wizard, previous=None):
        WizardStep.__init__(self, previous)
        self.wizard = wizard
        
        ThankYouSlave.__init__(self, self.wizard)
    
    def post_init(self):
        # this is the last step so we change the next button to finish
        self.wizard.enable_finish()
    
    def next_step(self):
        print "The End"


if __name__ == "__main__":
    survey = ITSurvey()
    survey.show_all()
    gtk.main()
