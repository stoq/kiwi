import time
import math
import unittest
import os
import sys

from gi.repository import GObject, GLib

from kiwi import tasklet


class C(GObject.GObject):
    __gsignals__ = {'my-signal': (GObject.SignalFlags.RUN_FIRST, None,
                                  (GObject.TYPE_INT,))}

    def do_my_signal(self, arg):
        self.arg = arg


class TestWaitForSignal(unittest.TestCase):
    def testBadArguments(self):
        self.assertRaises(TypeError, tasklet.WaitForSignal, '', '')
        self.assertRaises(ValueError, tasklet.WaitForSignal, GObject.GObject(), 'foo')

    def testGoodArguments(self):
        tasklet.WaitForSignal(GObject.GObject(), 'notify')

    def testSignal(self):
        obj = C()

        def some_task(obj):
            yield tasklet.WaitForSignal(obj, 'my-signal')
            tasklet.get_event()
            raise StopIteration("return-val")

        task = tasklet.run(some_task(obj))
        obj.emit("my-signal", 1)
        self.assertEqual(task.state, tasklet.Tasklet.STATE_ZOMBIE)
        self.assertEqual(task.return_value, "return-val")

    def testEmissionHook(self):
        obj = C()

        def some_task():
            yield tasklet.WaitForSignal(C, 'my-signal')
            tasklet.get_event()
            raise StopIteration("return-val")

        task = tasklet.run(some_task())
        obj.emit("my-signal", 1)
        self.assertEqual(task.state, tasklet.Tasklet.STATE_ZOMBIE)
        self.assertEqual(task.return_value, "return-val")


class TestWaitForTimeout(unittest.TestCase):
    def time(self):
        if sys.platform == 'win32':
            return time.clock()
        else:
            return time.time()

    def testTimeout(self):
        def some_task():
            yield tasklet.WaitForTimeout(100)
            tasklet.get_event()
            raise StopIteration("return-val")

        mainloop = GObject.MainLoop()
        t1 = self.time()
        task = tasklet.run(some_task())
        task.add_join_callback(lambda task, retval: mainloop.quit())
        mainloop.run()
        t2 = self.time()
        self.assertEqual(task.state, tasklet.Tasklet.STATE_ZOMBIE)
        self.assertEqual(task.return_value, "return-val")
        ## check that elapsed time aproximately 100 ms second, give or take 50 ms
        ## (glib doesn't guarantee precise timing)
        self.assertTrue(
            math.fabs((t2 - t1) - 0.1) < 0.05,
            "elapsed time was %f, expected 0.1" % ((t2 - t1), ))


class TestMessages(unittest.TestCase):
    def testPing(self):
        def pinger(remote, value):
            yield tasklet.Message('echo-request', dest=remote, value=value)
            yield tasklet.WaitForMessages(accept='echo-reply')
            msg = tasklet.get_event()
            raise StopIteration(msg.value)

        def echoer():
            yield tasklet.WaitForMessages(accept='echo-request')
            msg = tasklet.get_event()
            assert isinstance(msg, tasklet.Message)
            assert msg.sender is not None
            yield tasklet.Message('echo-reply', dest=msg.sender, value=msg.value)

        task = tasklet.run(pinger(tasklet.run(echoer()), 123))
        self.assertEqual(task.state, tasklet.Tasklet.STATE_ZOMBIE)
        self.assertEqual(task.return_value, 123)


class TestIO(unittest.TestCase):
    def testPipe(self):
        #
        # Disable this test for win32, because it fails and warns:
        #
        # File "tests\test_tasklet.py", line 81, in pipe_reader
        #    assert chan.get_flags() & GObject.IO_FLAG_IS_READABLE
        #
        # ???:81: g_io_channel_get_flags: assertion `channel != NULL' failed
        # ???:95: giowin32.c:1669: 4 is neither a file descriptor or a socket
        # ???:96: g_io_channel_set_flags: assertion `channel != NULL' failed
        #
        if sys.platform == 'win32':
            return

        def pipe_reader(chan):
            assert chan.get_flags() & GObject.IO_FLAG_IS_READABLE
            yield tasklet.WaitForIO(chan, GObject.IO_IN)
            tasklet.get_event()
            c = chan.read(1)
            raise StopIteration(c)

        def pipe_writer(chan, c):
            assert chan.get_flags() & GObject.IO_FLAG_IS_WRITEABLE
            yield tasklet.WaitForIO(chan, GObject.IO_OUT)
            tasklet.get_event()
            chan.write(c)

        read_fd, write_fd = os.pipe()

        read_chan = GLib.IOChannel(read_fd)
        read_chan.set_flags(GObject.IO_FLAG_NONBLOCK)
        reader = tasklet.run(pipe_reader(read_chan))

        write_chan = GLib.IOChannel(write_fd)
        write_chan.set_flags(GObject.IO_FLAG_NONBLOCK)
        write_chan.set_encoding(None)
        write_chan.set_buffered(False)
        tasklet.run(pipe_writer(write_chan, b'{'))

        mainloop = GObject.MainLoop()
        reader.add_join_callback(lambda task, retval: mainloop.quit())
        mainloop.run()

        self.assertEqual(reader.state, tasklet.Tasklet.STATE_ZOMBIE)
        self.assertEqual(reader.return_value, b'{')


class TestCallback(unittest.TestCase):
    def testCallback(self):

        def dispatch_callback(callback):
            callback(123, 456, foo="bar")
            return False

        def register_callback(callback):
            GObject.timeout_add(100, dispatch_callback, callback)

        def task_func():
            callback = tasklet.WaitForCall()
            register_callback(callback)
            yield callback
            tasklet.get_event()
            callback.return_value = False
            mainloop.quit()
            raise StopIteration((callback.args, callback.kwargs))

        task = tasklet.run(task_func())

        mainloop = GObject.MainLoop()
        mainloop.run()

        self.assertEqual(task.state, tasklet.Tasklet.STATE_ZOMBIE)
        args, kwargs = task.return_value
        self.assertEqual(args, (123, 456))
        self.assertEqual(kwargs, dict(foo="bar"))


class TestWaitForTasklet(unittest.TestCase):
    def testWaitForInstantaneousTask(self):
        """Test waiting for a tasklet that is already finished."""

        def quick_task():
            if 1:
                raise StopIteration(123)
            yield None

        def task_waiter():
            yield quick_task()
            taskwait = tasklet.get_event()
            raise StopIteration(taskwait.retval)

        mainloop = GObject.MainLoop()
        task = tasklet.run(task_waiter())
        task.add_join_callback(lambda task, retval: mainloop.quit())
        mainloop.run()
        self.assertEqual(task.return_value, 123)

if __name__ == '__main__':
    unittest.main()
