#!/usr/bin/env python

# Setup file for Kiwi 
# Code by Async Open Source <http://www.async.com.br>
# setup.py written by Christian Reis <kiko@async.com.br>

"""
kiwi offers a set of enhanced widgets for
Python based on PyGTK. It also includes a framework designed to make
creating Python applications using PyGTK and libglade much
simpler.
"""

from distutils.core import setup
import os
import sys

from kiwi.dist import listfiles, listpackages, TemplateInstallLib, \
     get_site_packages_dir

class InstallLib(TemplateInstallLib):
    name = 'kiwi'
    global_resources = dict(glade='$datadir/glade')
    
version = ''
execfile("kiwi/__version__.py")
assert version

setup(name="kiwi",
      version=".".join(map(str, version)),
      description="A framework and a set of enhanced widgets based on PyGTK",
      long_description=__doc__,
      author="Async Open Source",
      author_email="kiko@async.com.br",
      url="http://www.async.com.br/projects/",
      license="GNU LGPL 2.1 (see COPYING)",
      data_files=[('share/kiwi/glade',
                   listfiles('glade', '*.glade')),
                  ('share/gazpacho/catalogs',
                   listfiles('gazpacho-plugin', 'kiwiwidgets.xml')),
                  ('share/gazpacho/resources/kiwiwidgets',
                   listfiles('gazpacho-plugin', 'resources', '*.png')),
                  (get_site_packages_dir('gazpacho', 'widgets'),
                   listfiles('gazpacho-plugin', 'kiwiwidgets.py')),
                  ('share/doc/kiwi',
                   ('AUTHORS', 'ChangeLog', 'NEWS', 'README')),
                  ],
      scripts=['bin/kiwi-i18n',
               'bin/kiwi-ui-test'],
      packages=listpackages('kiwi'),
      cmdclass=dict(install_lib=InstallLib),
      )
