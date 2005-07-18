#!/usr/bin/env python

# Setup file for Kiwi 
# Code by Async Open Source <http://www.async.com.br>
# setup.py writen by Christian Reis <kiko@async.com.br>

from fnmatch import fnmatch
import os
from distutils.core import setup

def listfiles(*dirs):
    dir, pattern = os.path.split(os.path.join(*dirs))
    return [os.path.join(dir, filename)
            for filename in os.listdir(os.path.abspath(dir))
                if filename[0] != '.' and fnmatch(filename, pattern)]

execfile("kiwi/__version__.py")

setup(
    name = "kiwi",
    version =  ".".join(map(str, version)),
    description = "A framework and a set of enhanced widgets based on PyGTK",
    long_description = """
    kiwi offers a set of enhanced widgets for
    Python based on PyGTK. It also includes a framework designed to make
    creating Python applications using PyGTK and libglade much
    simpler.""",

    author = "Async Open Source",
    author_email = "kiko@async.com.br",
    url = "http://www.async.com.br/projects/",
    license = "GNU LGPL 2.1 (see COPYING)",
    data_files = [
        ('share/gazpacho/catalogs',
         listfiles('gazpacho-plugin', 'kiwi.xml')),
        ('share/gazpacho/resources/kiwi',
         listfiles('gazpacho-plugin', 'resources', '*.png')),
        ('lib/gazpacho/widgets',
         listfiles('gazpacho-plugin', 'kiwi.py')),
        ],
    packages = ['kiwi',
                'kiwi.ui',
                'kiwi.ui.widgets'],
    )
