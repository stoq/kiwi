import commands
import os

from kiwi.dist import listfiles, setup

GLADELIB = 'libgladeui-1.0'

def glade3_exists():
    status, output = commands.getstatusoutput('pkg-config --exists %s' %
                                              GLADELIB)
    return not status

def get_glade3_variable(variablename):
    return commands.getoutput('pkg-config --variable=%s %s' % (variablename,
                                                               GLADELIB))

if glade3_exists():
    catalogdir = get_glade3_variable('catalogdir')
    moduledir = get_glade3_variable('moduledir')
    pixmapdir = get_glade3_variable('pixmapdir')
    pixmaps = listfiles('..', 'gazpacho-plugin',
                        'resources', 'kiwiwidgets', '*.png')
    print catalogdir
    setup(
        data_files=[
            (catalogdir, ['kiwiwidgets.xml']),
            (moduledir, ['kiwiwidgets.py']),
            (os.path.join(pixmapdir, '16x16'), pixmaps),
            (os.path.join(pixmapdir, '22x22'), pixmaps),
        ]
    )
else:
    print 'Glade 3 is not installed, neither will be this plugin.'


