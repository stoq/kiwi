#!/usr/bin/env python
import os
import unittest

def test_filename(filename):
    # Run each tests in a child process, since kiwis ui test framework
    # is not completely capable of cleaning up all it's state
    # seems to be highly threads related.
    pid = os.fork()
    if not pid:
        # Do thread initialization here, in the child process
        # avoids strange X errors
        from kiwi.ui.test.player import play_file, TimeOutError

        try:
            play_file(filename)
        except TimeOutError, e:
            print '*' * 50
            print '* TIMEOUT ERROR: %s' % e
            print '*' * 50
            os._exit(1)
        os._exit(0)

    pid, status = os.waitpid(pid, 0)
    if status != 0:
        return 1

def run():
    testdir = os.path.dirname(os.path.abspath(__file__))
    uidir = os.path.join(testdir, 'ui')
    rootdir = os.path.dirname(testdir)

    olddir = os.getcwd()
    os.chdir(rootdir)

    for filename in os.listdir(uidir):
        if not filename.endswith('.py'):
            continue
        test_filename(os.path.join(uidir, filename))

    os.chdir(olddir)

if __name__ == '__main__':
    run()
