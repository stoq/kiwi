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
# Author(s): Johan Dahlin <jdahlin@async.com.br>
#         

from distutils.command.install_lib import install_lib
from distutils.dep_util import newer
from distutils.log import info
from fnmatch import fnmatch
import os

class TemplateInstallLib(install_lib):
    # Overridable by subclass
    resources = {}
    global_resources = {}
    name = None
    
    def generate_template(self, resources, global_resources):
        filename = os.path.join(self.install_dir, self.name,
                                '__installed__.py')
        self.mkpath(os.path.dirname(filename))
        fp = open(filename, 'w')
        fp.write('# Generated by setup.py do not modify\n')
        self._write_dictionary(fp, 'resources', resources)
        self._write_dictionary(fp, 'global_resources', global_resources)
        fp.close()

	return filename
    
    def _write_dictionary(self, fp, name, dictionary):
        fp.write('%s = {}\n' % name)
        for key, value in dictionary.items():
            value = value.replace('$prefix', self._prefix)
            value = value.replace('$datadir', self._datadir)
            fp.write("%s['%s'] = '%s'\n" % (name, key, value))

    def install(self):
        if not self.name:
            raise TypeError("%r is missing name" % self)
        
        install = self.distribution.get_command_obj('install')
        self._prefix = install.prefix
        self._datadir = os.path.join(self._prefix, 'share', self.name)

        template = self.generate_template(self.resources,
                                          self.global_resources)
        return install_lib.install(self) + [template]

def listfiles(*dirs):
    dir, pattern = os.path.split(os.path.join(*dirs))
    return [os.path.join(dir, filename)
            for filename in os.listdir(os.path.abspath(dir))
                if filename[0] != '.' and fnmatch(filename, pattern)]

def compile_po_files(appname, dirname='locale'):
    data_files = []
    for po in listfiles('po', '*.po'):
        lang = os.path.basename(po[:-3])
        mo = os.path.join(dirname, lang, 'LC_MESSAGES', appname + '.mo')

        if not os.path.exists(mo) or newer(po, mo):
            directory = os.path.dirname(mo)
            if not os.path.exists(directory):
                info("creating %s" % directory)
                os.makedirs(directory)
            cmd = 'msgfmt -o %s %s' % (mo, po)
            info('compiling %s -> %s' % (po, mo))
            if os.system(cmd) != 0:
                raise SystemExit("Error while running msgfmt")
        dest = os.path.dirname(os.path.join('share', mo))
        data_files.append((dest, [mo]))

    return data_files