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

from distutils.dep_util import newer
from distutils.filelist import FileList
from fnmatch import fnmatch
from optparse import OptionParser
import os
from shutil import copyfile

def listfiles(*dirs):
    dir, pattern = os.path.split(os.path.join(*dirs))
    return [os.path.join(dir, filename)
            for filename in os.listdir(os.path.abspath(dir))
                if filename[0] != '.' and fnmatch(filename, pattern)]

def is_skipped(filename, skips):
    for skip in skips:
        if fnmatch(filename, skip):
            return True
    return False
    
def listfiles_recursive(directory, pattern, skips=[]):
    files = []
    for short in os.listdir(directory):
        if short == '.':
            continue

        if is_skipped(short, skips):
            continue
            
        filename = os.path.join(directory, short)
        if fnmatch(filename, pattern):
            files.append(filename)
            
        if os.path.isdir(filename):
            files.extend(listfiles_recursive(filename, pattern))

    return files

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
    
def get_translatable_files(root):
    pofiles = os.path.join(root, 'po', 'POFILES.in')
    if not os.path.exists(pofiles):
        print 'Warning: Could not find %s' % pofiles
        return []

    filelist = FileList()

    fp = open(pofiles)
    for line in fp.readlines():
        filelist.process_template_line(line)
    return filelist.files

def list_languages(root):
    for po_file in listfiles(root, 'po', '*.po'):
        lang = os.path.basename(po_file[:-3])
        print lang
        
def update_pot(root, pot_file):
    from kiwi.i18n.pygettext import extract_strings, Options

    files = get_translatable_files(root)
    opt = Options()
    opt.outfile = pot_file
    extract_strings(opt, files)

def update_po_files(root, pot_file):
    for po_file in listfiles(root, 'po', '*.po'):
        if os.system('msgmerge -q %s %s -o %s.tmp' % (po_file,
                                                      pot_file, po_file)) != 0:
            raise SystemExit
        os.rename(po_file + '.tmp', po_file)

def compile_po_files(root, package):
    from kiwi.i18n.msgfmt import make
    mo_file = package + '.mo'
    for po_file in listfiles(root, 'po', '*.po'):
        lang = os.path.basename(po_file[:-3])
        mo = os.path.join(root, 'locale', lang,
                          'LC_MESSAGES', mo_file)
        
        if not os.path.exists(mo) or newer(po_file, mo):
            directory = os.path.dirname(mo)
            if not os.path.exists(directory):
                os.makedirs(directory)
            make(po_file, mo)
    
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
        check_pot_file(root, package)
        copyfile(pot_file, os.path.join(root, 'po', options.lang + '.po'))
        return
    elif options.list:
        list_languages(root)
        return
    
    if options.update:
        pot_file = os.path.join(root, 'po', '%s.pot' % package)
        update_pot(root, pot_file)
        update_po_files(root, pot_file)

    if options.compile:
        check_pot_file(root, package)
        compile_po_files(root, package)
