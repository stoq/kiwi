#!/usr/bin/env python

# Setup.py for Kiwi
# Code by Async Open Source <http://www.async.com.br>
# setup.py written by Christian Reis <kiko@async.com.br>
# re-written various times by Johan Dahlin <jdahlin@async.com.br>

"""
kiwi offers a set of enhanced widgets for
Python based on PyGTK. It also includes a framework designed to make
creating Python applications using PyGTK and libglade much
simpler.
"""

import commands
from distutils.extension import Extension
import sys

from kiwi import kiwi_version
from kiwi.dist import setup, listfiles, listpackages, get_site_packages_dir


ext_modules = []

# Build a helper module for testing on gtk+ versions lower than 2.10.
# Don't build it on windows due to easy availability compilers and
# the lack of pkg-config.
if sys.platform != 'win32' and not 'bdist_wininst' in sys.argv:
    exists = commands.getstatusoutput('pkg-config pygtk-2.0 --exists')[0] == 0
    version = commands.getoutput('pkg-config pygtk-2.0 --modversion')
    if exists and version and map(int, version.split('.')) < [2, 10]:
        pkgs = 'gdk-2.0 gtk+-2.0 pygtk-2.0'
        cflags = commands.getoutput('pkg-config --cflags %s' % pkgs)
        libs = commands.getoutput('pkg-config --libs %s' % pkgs)
        include_dirs = [part.strip() for part in cflags.split('-I') if part]
        libraries = [part.strip() for part in libs.split('-l') if part]
        ext_modules.append(Extension('kiwi/_kiwi', ['kiwi/_kiwi.c'],
                                     include_dirs=include_dirs,
                                     libraries=libraries))

pixmaps = listfiles('glade-plugin', 'resources', 'kiwiwidgets', '*.png')
# When uploading to pypi
if 'upload' in sys.argv:
    name = 'kiwi-gtk'
else:
    name = 'kiwi'
setup(name=name,
      version=".".join(map(str, kiwi_version)),
      description="A framework and a set of enhanced widgets based on PyGTK",
      long_description=__doc__,
      author="Async Open Source",
      author_email="kiwi@async.com.br",
      url="http://www.async.com.br/projects/kiwi/",
      license="GNU LGPL 2.1 (see COPYING)",
      data_files=[('$datadir/glade',
                   listfiles('glade', '*.glade') + listfiles('glade', '*.ui')),
                  ('$datadir/pixmaps',
                   listfiles('pixmaps', '*.png')),
                  # Glade3
                  ('share/glade3/catalogs', ['kiwiwidgets.xml']),
                  ('$libdir/glade3/modules', ['kiwiwidgets.py']),
                  ('share/glade3/pixmaps', pixmaps),
                  # Documentation
                  ('share/doc/kiwi',
                   ('AUTHORS', 'NEWS', 'README')),
                  ('share/doc/kiwi/howto',
                   listfiles('doc/howto/', '*')),
                  ('share/doc/kiwi/api',
                   listfiles('doc/api/', '*')),
                  ],
      scripts=['bin/kiwi-i18n',
               'bin/kiwi-ui-test'],
      packages=listpackages('kiwi'),
      ext_modules=ext_modules,
      resources=dict(locale='$prefix/share/locale'),
      global_resources=dict(glade='$datadir/glade',
                            pixmap='$datadir/pixmaps'),
      )
