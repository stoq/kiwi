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

import sys

from kiwi import kiwi_version
from kiwi.dist import setup, listfiles, listpackages


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
      data_files=[
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
      test_requires=['mock'],
      resources=dict(locale='$prefix/share/locale'),
      )
