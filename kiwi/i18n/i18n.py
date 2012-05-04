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

"""Internationalization utilities. Requires intltool and gettext"""

from distutils.dep_util import newer
from distutils.filelist import FileList, findall
from optparse import OptionParser
import os
from shutil import copyfile

from kiwi.dist import listfiles

# This is a template, used to generate a list of translatable file
# which intltool can understand.
# It reuses the syntax from distutils MANIFEST files, a POTFILES.in
# will be generate from it, see update_po()
POTFILES = 'POTFILES.list'


def check_directory(root):
    po_dir = os.path.join(root, 'po')
    if not os.path.exists(po_dir):
        raise SystemExit("A 'po` directory must exist")
    if not os.path.isdir(po_dir):
        raise SystemExit("po must be a directory")

    locale_dir = os.path.join(root, 'locale')
    if os.path.exists(locale_dir):
        if not os.path.isdir(po_dir):
            raise SystemExit("locale must be a directory")


def check_pot_file(root, package):
    pot_file = os.path.join(root, 'po', '%s.pot' % package)
    if not os.path.exists(pot_file):
        raise SystemExit("Need a pot file, run --update first")
    return pot_file


def get_translatable_files(root):
    pofiles = os.path.join(root, 'po', POTFILES)
    if not os.path.exists(pofiles):
        print 'Warning: Could not find %s' % pofiles
        return []

    filelist = FileList()

    fp = open(pofiles)
    for line in fp.readlines():
        filelist.process_template_line(line)
    return sorted(filelist.files)


def list_languages(root):
    return [os.path.basename(po_file[:-3])
            for po_file in listfiles(root, 'po', '*.po')]


def update_po(root, package):
    update_pot(root, package)

    old = os.getcwd()
    os.chdir(os.path.join(root, 'po'))

    for lang in list_languages(root):
        new = lang + '.new.po'
        cmd = ('intltool-update --dist --gettext-package=%s '
               '-o %s %s > /dev/null' % (package, new, lang))
        os.system(cmd)
        if not os.path.exists(new):
            raise SystemExit("ERROR: intltool failed, see above")

        os.rename(new, lang + '.po')

    os.chdir(old)


def update_pot(root, package):
    files = get_translatable_files(root)
    potfiles_in = os.path.join(root, 'po', 'POTFILES.in')
    if os.path.exists(potfiles_in):
        os.unlink(potfiles_in)

    rml_files = _extract_rml_files(root)

    fd = open(potfiles_in, 'w')
    for filename in files + rml_files:
        # FIXME: workaround for bug
        # https://bugzilla.redhat.com/show_bug.cgi?id=504483
        if filename.endswith('.ui'):
            filename = '[type: gettext/glade]' + filename
        fd.write(filename + '\n')
    fd.close()

    old = os.getcwd()
    os.chdir(os.path.join(root, 'po'))

    if os.system('intltool-update 2> /dev/null > /dev/null') != 0:
        raise SystemExit('ERROR: intltool-update could not be found')

    # POT file first
    res = os.system('intltool-update --pot --gettext-package=%s' % package)
    if res != 0:
        raise SystemExit("ERROR: failed to generate pot file")

    os.chdir(old)

    for f in rml_files:
        os.unlink(f)

    os.unlink(potfiles_in)


def _clean_rml(data):
    fixed = ''
    while data:
        start_pos = data.find('<%')
        if start_pos == -1:
            break

        fixed += data[:start_pos]
        data = data[start_pos:]
        end_pos = data.find('%>')
        if end_pos == -1:
            end_pos = data.find('/>')
            assert end_pos != -1
        data = data[end_pos + 2:]
    return fixed


def _extract_rml_files(root):
    files = []
    for rml_file in sorted(findall(root)):
        if not rml_file.endswith('.rml'):
            continue
        data = open(rml_file).read()
        data = _clean_rml(data)
        if not len(data):
            continue
        extracted = rml_file + '.extracted'
        if os.path.exists(extracted):
            os.unlink(extracted)
        open(extracted, 'w').write(data)
        extracted = extracted[len(root) + 1:]
        cmd = 'intltool-extract -q --type=gettext/xml %s' % extracted
        res = os.system(cmd)
        if res != 0:
            raise SystemExit("ERROR: failed to generate pot file")
        os.unlink(extracted)
        files.append(extracted + '.h')
    return files


def compile_po_files(root, package):
    if os.system('msgfmt 2> /dev/null') != 256:
        print 'msgfmt could not be found, disabling translations'
        return

    mo_file = package + '.mo'
    for po_file in listfiles(root, 'po', '*.po'):
        lang = os.path.basename(po_file[:-3])
        mo = os.path.join(root, 'locale', lang, 'LC_MESSAGES', mo_file)

        if not os.path.exists(mo) or newer(po_file, mo):
            directory = os.path.dirname(mo)
            if not os.path.exists(directory):
                os.makedirs(directory)
            os.system('msgfmt %s -o %s' % (po_file, mo))


def main(args):
    parser = OptionParser()
    parser.add_option('-a', '--add',
                      action="store", type="string",
                      dest="lang",
                      help="Add a new language")
    parser.add_option('-l', '--list',
                      action="store_true",
                      dest="list",
                      help="List all supported languages")
    parser.add_option('-u', '--update',
                      action="store_true",
                      dest="update",
                      help="Update pot file and all po files")
    parser.add_option('-t', '--update-pot',
                      action="store_true",
                      dest="update_pot",
                      help="Update pot file")
    parser.add_option('-c', '--compile',
                      action="store_true",
                      dest="compile",
                      help="Compile all .po files into .mo")
    parser.add_option('-p', '--package',
                      action="store", type="string",
                      dest="package",
                      help="Package name")

    options, args = parser.parse_args(args)

    root = os.getcwd()
    check_directory(root)

    if options.package:
        package = options.package
    else:
        package = os.path.split(root)[1]

    if options.lang:
        pot_file = check_pot_file(root, package)
        copyfile(pot_file, os.path.join(root, 'po', options.lang + '.po'))
        return
    elif options.list:
        for lang in list_languages(root):
            print lang
        return

    if options.update:
        update_po(root, package)

    if options.update_pot:
        update_pot(root, package)

    if options.compile:
        check_pot_file(root, package)
        compile_po_files(root, package)
