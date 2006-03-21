#!/usr/bin/env python
import os
import sys

filters = [
    ('<requires lib="Kiwi2.Widgets"/>', '<requires lib="kiwi"/>'),
    ("Kiwi2+Widgets+CheckButton", "kiwi+ui+widgets+checkbutton"),
    ("Kiwi2+Widgets+ComboBox", "kiwi+ui+widgets+combobox"),
    ("Kiwi2+Widgets+Entry", "kiwi+ui+widgets+entry"),
    ("Kiwi2+Widgets+Label", "kiwi+ui+widgets+label"),
    ("Kiwi2+Widgets+List+List", "ObjectList"),
    ("Kiwi2+Widgets+RadioButton", "kiwi+ui+widgets+radiobutton"),
    ("Kiwi2+Widgets+SpinButton", "kiwi+ui+widgets+spinbutton"),
    ("Kiwi2+Widgets+TextView", "kiwi+ui+widgets+textview"),
    ("kiwi+ui+widgets+list+List", "ObjectList"),
    ("kiwi+ui+widgets+entry+Entry", "ProxyEntry"),
    ("kiwi+ui+widgets+radiobutton+RadioButton", "ProxyRadioButton"),
    ("kiwi+ui+widgets+combobox+ComboBox", "ProxyComboBox"),
    ("kiwi+ui+widgets+combobox+ComboBoxEntry", "ProxyComboBoxEntry"),
]

def apply_filter((first, second), line):
    if not first in line:
        return line

    return line.replace(first, second)

def main(args):
    if len(args) < 2:
        print 'Need a filename'
        return

    filename = args[1]
    tmp = filename + '.tmp'
    out = open(tmp, 'w')

    for line in open(filename).readlines():
        for filter in filters:
            line = apply_filter(filter, line)
        out.write(line)
    os.unlink(filename)
    os.rename(tmp, filename)

if __name__ == '__main__':
    sys.exit(main(sys.argv))
