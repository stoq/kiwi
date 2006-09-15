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

from kiwi import kiwi_version
from kiwi.dist import setup, listfiles, listpackages, get_site_packages_dir

setup(name="kiwi",
      version=".".join(map(str, kiwi_version)),
      description="A framework and a set of enhanced widgets based on PyGTK",
      long_description=__doc__,
      author="Async Open Source",
      author_email="kiwi@async.com.br",
      url="http://www.async.com.br/projects/",
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
      resources=dict(locale='$prefix/share/locale'),
      global_resources=dict(glade='$datadir/glade',
                            pixmap='$datadir/pixmaps'),
      )
