#
# Kiwi: a Framework and Enhanced Widgets for Python
#
# Copyright (C) 2003-2005 Async Open Source
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
# Author(s): Christian Reis <kiko@async.com.br>
#            Lorenzo Gil Sanchez <lgs@sicem.biz>
#            Johan Dahlin <jdahlin@async.com.br>
#         

import os
import string

#
# Gladepath handling
#

gladepath = []

if os.environ.has_key('KIWI_GLADE_PATH'):
    gladepath = os.environ['KIWI_GLADE_PATH'].split(':')

def set_gladepath(path):
    """Sets a new path to be used to search for glade files when creating
    GladeViews or it's subclasses
    """
    global gladepath
    gladepath = path

def get_gladepath():
    global gladepath
    return gladepath

def find_in_gladepath(filename):
    """Looks in gladepath for the file specified"""

    gladepath = get_gladepath()
    
    # check to see if gladepath is a list or tuple
    if not isinstance(gladepath, (tuple, list)):
        msg ="gladepath should be a list or tuple, found %s"
        raise ValueError(msg % type(gladepath))
    if os.sep in filename or not gladepath:
        if os.path.isfile(filename):
            return filename
        else:
            raise IOError("%s not found" % filename)

    for path in gladepath:
        # append slash to dirname
        if not path:
            continue
        # if absolute path
        fname = os.path.join(path, filename)
        if os.path.isfile(fname):
            return fname

    raise IOError("%s not found in path %s.  You probably need to "
                  "kiwi.environ.set_gladepath() correctly" % (filename,
                                                              gladepath))

#
# Image path resolver
#

imagepath = ''

if os.environ.has_key ('KIWI_IMAGE_PATH'):
    imagepath = string.split(os.environ['KIWI_IMAGE_PATH'])

def set_imagepath(path):
    global imagepath
    imagepath = path

def get_imagepath():
    global imagepath
    return imagepath

def image_path_resolver(filename):
    imagepath = get_imagepath()

    # check to see if imagepath is a list or tuple
    if not isinstance(imagepath, (list, tuple)):
        msg ="imagepath should be a list or tuple, found %s"
        raise ValueError(msg % type(imagepath))

    if not imagepath:
        if os.path.isfile(filename):
            return filename
        else:
            raise IOError("%s not found" % filename)

    basefilename = os.path.basename(filename)
    
    for path in imagepath:
        if not path:
            continue
        fname = os.path.join(path, basefilename)
        if os.path.isfile(fname):
            return fname

    raise IOError("%s not found in path %s. You probably need to "
                  "kiwi.environ.set_imagepath() correctly" % (filename,
                                                              imagepath))


require_gazpacho_loader = False

def require_gazpacho():
    global require_gazpacho_loader
    require_gazpacho_loader = True

