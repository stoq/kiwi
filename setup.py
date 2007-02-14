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
    version = commands.getoutput('pkg-config pygtk-2.0 --modversion')
    if version and map(int, version.split('.')) < [2, 10]:
        pkgs = 'gdk-2.0 gtk+-2.0 pygtk-2.0'
        cflags = commands.getoutput('pkg-config --cflags %s' % pkgs)
        libs = commands.getoutput('pkg-config --libs %s' % pkgs)
        include_dirs = [part.strip() for part in cflags.split('-I') if part]
        libraries = [part.strip() for part in libs.split('-l') if part]
        ext_modules.append(Extension('kiwi/_kiwi', ['kiwi/_kiwi.c'],
                                     include_dirs=include_dirs,
                                     libraries=libraries))

setup(name="kiwi",
      version=".".join(map(str, kiwi_version)),
      description="A framework and a set of enhanced widgets based on PyGTK",
      long_description=__doc__,
      author="Async Open Source",
      author_email="kiwi@async.com.br",
      url="http://www.async.com.br/projects/kiwi/",
      license="GNU LGPL 2.1 (see COPYING)",
      data_files=[('$datadir/glade',
                   listfiles('glade', '*.glade')),
                  ('$datadir/pixmaps',
                   listfiles('pixmaps', '*.png')),
                  ('share/gazpacho/catalogs',
                   listfiles('gazpacho-plugin', 'kiwiwidgets.xml')),
                  ('share/gazpacho/resources/kiwiwidgets',
                   listfiles('gazpacho-plugin', 'resources',
                             'kiwiwidgets', '*.png')),
                  (get_site_packages_dir('gazpacho', 'widgets'),
                   listfiles('gazpacho-plugin', 'kiwiwidgets.py')),
                  ('share/doc/kiwi',
                   ('AUTHORS', 'ChangeLog', 'NEWS', 'README')),
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
