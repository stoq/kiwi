#!/usr/bin/env python

# Setup.py for Kiwi
# Code by Async Open Source <http://www.async.com.br>
# setup.py written by Christian Reis <kiko@async.com.br>
# re-written various times by Johan Dahlin <jdahlin@async.com.br>

"""
Kiwi is a framework and a set of enhanced PyGTK widgets designed to
make building programs with graphical interfaces both easy to write
and easy to maintain.

Kiwi consists of a set of classes and wrappers for PyGTK that were
developed to provide a sort of framework for applications. Fully
object-oriented, and roughly Smalltalk's MVC, Kiwi provides a simple,
practical way to build forms, windows and widgets that transparently
access and display your object data.

Kiwi is inspired by Allen Holub's Visual Proxy.
"""

import sys

from kiwi import kiwi_version
from kiwi.dist import setup, listfiles, listpackages


pixmaps = listfiles('data', 'kiwiwidgets',
                    'glade-plugin', 'resources', 'kiwiwidgets', '*.png')

# When uploading to pypi or building a wheel or an egg
if 'upload' in sys.argv or 'bdist_wheel' in sys.argv or 'bdist_egg' in sys.argv:
    name = 'kiwi-gtk'
else:
    name = 'kiwi'

with open('requirements.txt') as f:
    install_requires = [l.strip() for l in f.readlines() if
                        l.strip() and not l.startswith('#')]

setup(name=name,
      packagename='kiwi',
      version=".".join(map(str, kiwi_version)),
      description="A framework and a set of enhanced widgets based on PyGTK",
      long_description=__doc__,
      author="Async Open Source",
      author_email="kiwi@async.com.br",
      url="http://www.async.com.br/projects/kiwi/",
      license="GNU LGPL 2.1 (see COPYING)",
      data_files=[
          # Glade3
          ('share/glade3/catalogs', ['data/kiwiwidgets/kiwiwidgets.xml']),
          ('$libdir/glade3/modules', ['data/kiwiwidgets/kiwiwidgets.py']),
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
      test_requires=['mock'],
      install_requires=install_requires,
      )
