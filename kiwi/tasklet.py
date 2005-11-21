#
# Kiwi: a Framework and Enhanced Widgets for Python
#
# Copyright (C) 2005 Gustavo J. A. M. Carneiro
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
# Author(s): Gustavo J. A. M. Carneiro <gjc@inescporto.pt>
#

"""
Pseudo-thread (coroutines) framework

Introduction
============

  This module adds infrastructure for managing tasklets.  In this
  context, a X{tasklet} is defined as a routine that explicitly gives
  back control to the main program a certain points in the code, while
  waiting for certain events.  Other terms that may be used to describe
  tasklets include I{coroutines}, or I{cooperative threads}.

  The main advantages of tasklets are:

    - Eliminates the danger of unexpected race conditions or deadlocks
      that happen with preemptive (regular) threads;

    - Reduces the number of callbacks in your code, that sometimes are
      so many that you end up with I{spaghetti code}.

  The fundamental block used to create tasklets is Python's generators.
  Generators are objects that are defined as functions, and when called
  produce iterators that return values defined by the body of the
  function, specifically C{yield} statements.

  The neat thing about generators are not the iterators themselves but
  the fact that a function's state is completely frozen and restored
  between one call to the iterator's C{next()} and the following
  one. This allows the function to return control to a program's main
  loop while waiting for an event, such as IO on a socket, thus allowing
  other code to run in the mean time.  When the specified event occurs,
  the function regains control and continues executing as if nothing had
  happened.

Structure of a tasklet
======================

  At the outset, a tasklet is simply a python U{generator
  function<http://www.python.org/peps/pep-0255.html>}, i.e. a function
  or method containing one or more C{yield} statements.  Tasklets add a
  couple more requirements to regular generator functions:

    1. The values contained in C{yield} statements cannot be arbitrary
       (see below);

    2. After each C{yield} that indicates events, the function
       L{kiwi.tasklet.get_event} must be called to retrieve the event that
       just occurred.

Syntax for yield in tasklets
============================

  Inside tasklet functions, C{yield} statements are used to suspend
  execution of the tasklet while waiting for certain events.  Valid
  C{yield} values are:

    - A single L{Message} object, with a correctly set I{dest}
      parameter.  With this form, a message is sent to the indicated
      tasklet.  When C{yield} returns, no event is generated, so the
      tasklet should B{not} call L{get_event}.

    - One, or a sequence of:

       - L{WaitCondition}, meaning to wait for that specific condition

       - L{Tasklet}, with the same meaning as L{WaitForTasklet}C{(tasklet)}
       
       - generator, with the same meaning as L{WaitForTasklet}C{(Tasklet(gen))}

      In this case, the tasklet is suspended until either one of the
      indicated events occurs.  The tasklet must call L{get_event} in
      this case.

Launching a tasklet
===================

  To start a tasklet, the L{Tasklet} constructor must be used::
    from kiwi import tasklet

    def my_task(x):
        [...]

    tasklet.Tasklet(my_task(x=0))

  Alternatively, L{kiwi.tasklet.run} can be used to the same effect::
    from kiwi import tasklet
    tasklet.run(my_task(x=0))

Examples
========

  Background timeout task
  -----------------------
    This example demonstrates basic tasklet structure and timeout events::
      import gobject
      from kiwi import tasklet

      mainloop = gobject.MainLoop()

      def simple_counter(numbers):
          timeout = tasklet.WaitForTimeout(1000)
          for x in xrange(numbers):
              print x
              yield timeout
              tasklet.get_event()
          mainloop.quit()

      tasklet.run(simple_counter(10))
      mainloop.run()

  Message passing
  ---------------
    This example extends the previous one and demonstrates message passing::

      import gobject
      from kiwi import tasklet

      mainloop = gobject.MainLoop()

      def printer():
          msgwait = tasklet.WaitForMessages(accept=("quit", "print"))
          while True:
              yield msgwait
              msg = tasklet.get_event()
              if msg.name == "quit":
                  return
              assert msg.name == 'print'
              print ">>> ", msg.value

      def simple_counter(numbers, task):
          timeout = tasklet.WaitForTimeout(1000)
          for x in xrange(numbers):
              yield tasklet.Message('print', dest=task, value=x)
              yield timeout
              tasklet.get_event()
          yield tasklet.Message('quit', dest=task)
          mainloop.quit()

      task = tasklet.run(printer())
      tasklet.run(simple_counter(10, task))
      mainloop.run()

"""

import types
import warnings

import gobject

from kiwi.argcheck import argcheck

if gobject.pygtk_version <= (2, 8):
    raise RuntimeError("PyGTK 2.8 or later is required for kiwi.tasklet")

_event = None

def get_event():
    """
    Return the last event that caused the current tasklet to regain control.

    @warning: this function should be called exactly once after each
    yield that includes a wait condition.

    """
    global _event
    assert _event is not None
    event = _event
    _event = None
    return event

def run(gen):
    """Start running a generator as a L{Tasklet}.

    @parameter gen: generator object that implements the tasklet body.
    @return: a new L{Tasklet} instance, already running.

    @note: this is strictly equivalent to calling C{Tasklet(gen)}.

    """
    return Tasklet(gen)


class WaitCondition(object):
    '''
    Base class for all wait-able condition objects.

    WaitConditions are used in a yield statement inside tasklets body
    for specifying what event(s) it should wait for in order to
    receive control once more.'''
    
    def __init__(self):
        '''Abstract base class, do not call directly'''
        self.triggered = False

    def arm(self, tasklet):
        '''Prepare the wait condition to receive events.

        When a wait condition receives the event it is waiting for, it
        should call the method
        L{wait_condition_fired<Tasklet.wait_condition_fired>} of the
        tasklet with the wait condition as argument.  The method
        returns True or False; if it returns True, it means the
        WaitCondition object must "rearm" itself (continue to monitor
        events), otherwise it should disarm.

        @parameter tasklet: the tasklet instance the wait condition is
          to be associated with.
        @attention: this method normally should not be called directly
          by the programmer.

        '''
        raise NotImplementedError

    def disarm(self):
        '''Stop the wait condition from receiving events.

        @attention: this method normally should not be called by the
        programmer.'''
        raise NotImplementedError


class WaitForIO(WaitCondition):
    '''An object that waits for IO conditions on sockets or file
    descriptors.
    '''
    def __init__(self, filedes, condition=gobject.IO_IN,
                 priority=gobject.PRIORITY_DEFAULT):
        '''
        @param filedes: object to monitor for IO
        @type filedes: int file descriptor, or a
        gobject.IOChannel, or an object with a C{fileno()}
        method, such as socket or unix file.

        @param condition: IO event mask
        @type condition: a set of C{gobject.IO_*} flags ORed together
        @param priority: mainloop source priority
        '''
        
        WaitCondition.__init__(self)
        self.filedes = filedes
        self._condition = condition # listen condition
        self.condition = None # last occurred condition
        self._callback = None
        self._id = None
        self._priority = priority

    def arm(self, tasklet):
        '''Overrides WaitCondition.arm'''
        self._callback = tasklet.wait_condition_fired
        if self._id is None:
            try:
                ## http://bugzilla.gnome.org/show_bug.cgi?id=139176
                iochan = isinstance(self.filedes, gobject.IOChannel)
            except AttributeError:
                iochan = False
            if iochan:
                self._id = self.filedes.add_watch(self._condition,
                                                  self._io_cb,
                                                  priority=self._priority)
            else:
                if isinstance(self.filedes, int):
                    filedes = self.filedes
                else:
                    filedes = self.filedes.fileno()
                self._id = gobject.io_add_watch(filedes, self._condition,
                                                 self._io_cb,
                                                 priority=self._priority)

    def disarm(self):
        '''Overrides WaitCondition.disarm'''
        if self._id is not None:
            gobject.source_remove(self._id)
            self._id = None
            self._callback = None

    def _io_cb(self, unused_filedes, condition):
        self.triggered = True
        self.condition = condition
        retval = self._callback(self)
        self.triggered = False
        if not retval:
            self._id = None
        return retval


class WaitForTimeout(WaitCondition):
    '''An object that waits for a specified ammount of time (a timeout)'''
    def __init__(self, timeout, priority=gobject.PRIORITY_DEFAULT):
        '''An object that waits for a specified ammount of time.

        @param timeout: ammount of time to wait, in miliseconds
        @param priority: mainloop priority for the timeout event
        '''
        
        WaitCondition.__init__(self)
        self.timeout = timeout
        self._id = None
        self._tasklet = None
        self._priority = priority
        
    def arm(self, tasklet):
        '''See L{WaitCondition.arm}'''
        if self._id is None:
            self._tasklet = tasklet
            self._id = gobject.timeout_add(self.timeout, self._timeout_cb,
                                           priority=self._priority)

    def disarm(self):
        '''See L{WaitCondition.disarm}'''
        if self._id is not None:
            gobject.source_remove(self._id)
            self._id = None
            self._tasklet = None

    def restart(self):
        '''Restart the timeout.  Makes time counting start again from zero.'''
        tasklet = self._tasklet
        self.disarm()
        self.arm(tasklet)

    def _timeout_cb(self):
        self.triggered = True
        retval = self._tasklet.wait_condition_fired(self)
        assert retval is not None
        self.triggered = False
        if not retval:
            self._id = None
        return retval

class WaitForIdle(WaitCondition):
    '''An object that waits for the main loop to become idle'''

    def __init__(self, priority=gobject.PRIORITY_DEFAULT_IDLE):
        '''An object that waits for the main loop to become idle, with a
        priority indicated by @priority'''
        WaitCondition.__init__(self)
        self._callback = None
        self._id = None
        self._priority = priority

    def arm(self, tasklet):
        '''See L{WaitCondition.arm}'''
        if self._id is None:
            self._callback = tasklet.wait_condition_fired
            self._id = gobject.idle_add(self._idle_cb, self._priority)

    def disarm(self):
        '''See L{WaitCondition.disarm}'''
        if self._id is not None:
            gobject.source_remove(self._id)
            self._id = None
            self._callback = None

    def _idle_cb(self):
        self.triggered = True
        retval = self._callback(self)
        self.triggered = False
        if not retval:
            self._id = None
        return retval


class WaitForTasklet(WaitCondition):
    '''An object that waits for a tasklet to complete'''
    def __init__(self, tasklet):
        '''An object that waits for another tasklet to complete'''
        
        WaitCondition.__init__(self)
        self._tasklet = tasklet
        self._id = None
        self._idle_id = None
        self._callback = None
        self.retval = None
        
    def arm(self, tasklet):
        '''See L{WaitCondition.arm}'''
        self._callback = tasklet.wait_condition_fired
        if self._id is None:
            self._id = self._tasklet.add_join_callback(self._join_cb)

    def disarm(self):
        '''See L{WaitCondition.disarm}'''
        if self._idle_id is not None:
            gobject.source_remove(self._idle_id)
            self._idle_id = None
        if self._id is not None:
            self._tasklet.remove_join_callback(self._id)
            self._id = None
            self._callback = None

    def _join_cb(self, tasklet, retval):
        assert tasklet is self._tasklet
        assert self._idle_id is None
        self._id = None
        self._idle_id = gobject.idle_add(self._idle_cb)
        self.retval = retval

    def _idle_cb(self):
        self.triggered = True
        self._callback(self)
        self.triggered = False
        self._tasklet = None
        self._callback = None
        self._id = None
        self._idle_id = None
        return False

class WaitForSignal(WaitCondition):
    '''An object that waits for a signal emission'''

    @argcheck(gobject.GObject, str)
    def __init__(self, obj, signal):
        '''Waits for a signal to be emitted on a specific GObject instance.

        @param obj: object monitor for the signal
        @type obj: gobject.GObject
        @param signal: signal name
        @type signal: str
        '''
        WaitCondition.__init__(self)
        self.object = obj
        self.signal = signal
        self._callback = None
        self._id = None
        self._destroy_id = None
        self.signal_args = None

    def arm(self, tasklet):
        '''See L{WaitCondition.arm}'''
        if self._id is None:
            self._callback = tasklet.wait_condition_fired
            self._id = self.object.connect(self.signal, self._signal_cb)
            if gobject.signal_lookup("destroy", self.object):
                self._destroy_id = self.object.connect("destroy",
                                                       self._object_destroyed)
                
    def _object_destroyed(self, obj):
        self.object = None
        self._id = None
        self._destroy_id = None
        self._callback = None

    def disarm(self):
        '''See WaitCondition.disarm'''
        if self._id is not None:
            self.object.disconnect(self._id)
            self._id = None
            self._callback = None
        if self._destroy_id is not None:
            self.object.disconnect(self._destroy_id)
            self._destroy_id = None

    def _signal_cb(self, obj, *args):
        assert obj is self.object
        self.triggered = True
        self.signal_args = args
        retval = self._callback(self)
        self.triggered = False
        if not retval:
            self._id = None
        return retval


class WaitForProcess(WaitCondition):
    '''An object that waits for a process to end'''
    def __init__(self, pid):
        '''
        Creates an object that waits for a subprocess

        @parameter pid: Process identifier
        @type pid: int
        '''
        WaitCondition.__init__(self)
        self.pid = pid
        self._callback = None
        self._id = None
        self.status = None

    def arm(self, tasklet):
        '''See L{WaitCondition.arm}'''
        self._callback = tasklet.wait_condition_fired
        if self._id is None:
            self._id = gobject.child_watch_add(self.pid, self._child_cb)

    def disarm(self):
        '''See L{WaitCondition.disarm}'''
        if self._id is not None:
            gobject.source_remove(self._id)
            self._id = None
            self._callback = None

    def _child_cb(self, unused_pid, status):
        self.triggered = True
        self.status = status
        self._callback(self)
        self.triggered = False
        self.status = None
        self._id = None


class Message(object):
    '''A message that can be received by or sent to a tasklet.'''
    
    _slots_ = 'name', 'dest', 'value', 'sender'

    ACCEPT, DEFER, DISCARD = range(3)

    def __init__(self, name, dest=None, value=None, sender=None):
        '''
        @param name: name of message
        @type name: str
        @param dest: destination tasklet for this message
        @type dest: L{Tasklet}
        @param value: value associated with the message
        @param sender: sender tasklet for this message
        @type sender: L{Tasklet}

        '''
        assert isinstance(sender, (Tasklet, type(None)))
        assert isinstance(dest, (Tasklet, type(None)))
        assert isinstance(name, basestring)
        self.name = name
        self.value = value
        self.sender = sender
        self.dest = dest
        
#     def get_name(self):
#         """Return the message name"""
#         return self.name
#     def get_value(self):
#         """Return the message value"""
#         return self.value
#     def get_sender(self):
#         """Return the message sender"""
#         return self.sender
#     def get_dest(self):
#         """Return the message destination"""
#         return self.dest


def _normalize_list_argument(arg, name):
    """returns a list of strings from an argument that can be either
    list of strings, None (returns []), or a single string returns
    ([arg])"""
    
    if arg is None:
        return []
    elif isinstance(arg, basestring):
        return [arg]
    elif isinstance(arg, (list, tuple)):
        return arg
    raise TypeError("Argument '%s' must be None, a string, or "
                    "a sequence of strings, not %r" % (name, type(arg)))


class WaitForMessages(WaitCondition):
    '''An object that waits for messages to arrive'''
    def __init__(self, accept=None, defer=None, discard=None):
        '''Creates an object that waits for a set of messages to
        arrive.

        @warning: unlike other wait conditions, when a message
          is received, a L{Message} instance is returned by L{get_event()},
          not the L{WaitForMessages} instance.
        @param accept: message name or names to accept (receive) in
          the current state
        @type accept: string or sequence of string
        @param defer: message name or names to defer (queue) in the
          current state
        @type defer: string or sequence of string
        @param discard: message name or names to discard (drop) in the
          current state
        @type discard: string or sequence of string
        '''
        WaitCondition.__init__(self)
        self._tasklet = None
        accept = _normalize_list_argument(accept, 'accept')
        defer = _normalize_list_argument(defer, 'defer')
        discard = _normalize_list_argument(discard, 'discard')
        self.actions = dict()
        for name in accept:
            self.actions[name] = Message.ACCEPT
        for name in defer:
            self.actions[name] = Message.DEFER
        for name in discard:
            self.actions[name] = Message.DISCARD
        
    def arm(self, tasklet):
        '''Overrides WaitCondition.arm'''
        self._tasklet = tasklet
        tasklet.message_actions.update(self.actions)

    def disarm(self):
        '''Overrides WaitCondition.disarm'''
        assert self._tasklet is not None
        for name in self.actions:
            del self._tasklet.message_actions[name]


class Tasklet(object):
    '''An object that launches and manages a tasklet.'''

    STATE_RUNNING, STATE_SUSPENDED, STATE_MSGSEND = range(3)
    
    def __init__(self, gen=None):
        '''
        Launch a generator tasklet.

        @param gen: a generator object that implements the tasklet main body

        If `gen` is omitted or None, L{run} should be overridden in a
        subclass.

        '''
        self._event = None
        self._join_callbacks = {}
        self.wait_list = []
        self._message_queue = []
        self._message_actions = {}
        self.state = Tasklet.STATE_SUSPENDED
        if gen is None:
            self.gen = self.run()
        else:
            assert isinstance(gen, types.GeneratorType)
            self.gen = gen
        self._next_round() # bootstrap

    def get_message_actions(self):
        """Dictionary mapping message names to actions ('accept' or
        'discard' or 'defer').  Should normally not be accessed
        directly by the programmer.
        """
        return self._message_actions

    message_actions = property(get_message_actions)
        
    def run(self):
        """
        Method that executes the task.

        Should be overridden in a subclass if no generator is passed
        into the constructor."""
        raise ValueError("Should be overridden in a subclass "
                         "if no generator is passed into the constructor")

    def _invoke(self):
        global _event
        assert _event is None
        had_event = (self._event is not None)
        _event = self._event
        try:
            self.state = Tasklet.STATE_RUNNING
            gen_value = self.gen.next()
            self.state = Tasklet.STATE_SUSPENDED
            assert gen_value is not None
        except StopIteration, ex:
            if ex.args:
                retval, = ex.args
            else:
                retval = None
            self._join(retval)
            return None
        if __debug__:
            if had_event and _event is not None:
                warnings.warn("Tasklet %s forgot to read an event!" % self)
        self._event = None
        return gen_value

    def _next_round(self):
        assert self.state == Tasklet.STATE_SUSPENDED
        old_wait_list = self.wait_list
        while True: # loop while tasklet yields tasklet.post_message(...)

            gen_value = self._invoke()
            if gen_value is None:
                return

            if isinstance(gen_value, Message):
                msg = gen_value
                self.state = Tasklet.STATE_MSGSEND
                msg.dest.send_message(msg)
                continue # loop because we posted a message
            elif isinstance(gen_value, tuple):
                self.wait_list = list(gen_value)
            elif isinstance(gen_value, list):
                self.wait_list = gen_value
            else:
                self.wait_list = [gen_value]
            
            for i, val in enumerate(self.wait_list):
                if isinstance(val, WaitCondition):
                    continue
                elif isinstance(val, types.GeneratorType):
                    self.wait_list[i] = WaitForTasklet(Tasklet(val))
                elif isinstance(val, Tasklet):
                    self.wait_list[i] = WaitForTasklet(val)
                else:
                    raise TypeError("yielded values must be WaitConditions,"
                                    " generators, or a single Message")

            self._update_wait_conditions(old_wait_list)

            msg = self._dispatch_message()
            if msg is not None:
                self._event = msg
                continue ## send a message

            break

    def _dispatch_message(self):
        '''get next message that a tasklet wants to receive; discard
        messages that should be discarded'''
        ## while sending out messages, the tasklet implicitly queues
        ## all incoming messages
        if self.state == Tasklet.STATE_MSGSEND:
            return None

        ## filter out messages with discard action
        def _get_action(msg):
            try:
                return self._message_actions[msg.name]
            except KeyError:
                warnings.warn("Implicitly discarding message %s"
                              " directed to tasklet %s" % (msg, self))
                return Message.DISCARD
        if __debug__:
            self._message_queue = [msg
                                   for msg in self._message_queue
                                       if _get_action(msg) != Message.DISCARD]
        else:
            ## slightly more efficient version of the above
            self._message_queue = [msg for msg in self._message_queue
                if (self._message_actions.getdefault(msg.name, Message.DISCARD)
                    != Message.DISCARD)]

        ## find next ACCEPT-able message from queue, and pop it out
        for idx, msg in enumerate(self._message_queue):
            if self._message_actions[msg.name] == Message.ACCEPT:
                break
        else:
            return None
        return self._message_queue.pop(idx)
    

    def _update_wait_conditions(self, old_wait_list):
        '''disarm wait conditions removed and arm new wait conditions'''
        
        ## disarm conditions removed from the wait list
        for cond in old_wait_list:
            if cond not in self.wait_list:
                cond.disarm()
        
        ## arm the conditions added to the wait list
        for cond in self.wait_list:
            if cond not in old_wait_list:
                cond.arm(self)

    def wait_condition_fired(self, triggered_cond):
        """Method that should be called when a wait condition fires"""
        assert triggered_cond in self.wait_list
        assert self._event is None
        self._event = triggered_cond
        self._next_round()
        self._event = None
        if self.wait_list is None:
            return False
        else:
            return (triggered_cond in self.wait_list)

    def add_join_callback(self, callback):
        '''
        Add a callable to be invoked when the tasklet finishes.
        Return a connection handle that can be used in
        remove_join_callback()

        The callback will be called like this::
              callback(tasklet, retval)
        where tasklet is the tasklet that finished, and retval its
        return value (or None).

        When a join callback is invoked, it is automatically removed,
        so calling L{remove_join_callback} afterwards produces a KeyError
        exception.

        '''
        handle = hash(callback)
        while handle in self._join_callbacks: # handle collisions
            handle += 1
        self._join_callbacks[handle] = callback
        return handle

    def remove_join_callback(self, handle):
        '''Remove a join callback previously added with L{add_join_callback}'''
        del self._join_callbacks[handle]

    def _join(self, retval):
        for cond in self.wait_list:
            cond.disarm()
        self.gen = None
        self.wait_list = []
        callbacks = self._join_callbacks.values()
        self._join_callbacks.clear()
        for callback in callbacks:
            callback(self, retval)

    def send_message(self, message):
        """Send a message to be received by the tasklet as an event.

        @warning: Don't call this from another tasklet, only from the
        main loop!  To send a message from another tasklet, yield a
        L{Message} with a correctly set 'dest' parameter.

        """
        assert isinstance(message, Message)
        assert self._event is None
        if message.dest is None:
            message.dest = self
        self._message_queue.append(message)
        self._event = self._dispatch_message()
        if self._event is not None:
            self._next_round()
