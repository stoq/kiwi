import gobject

from kiwi.tasklet import Tasklet, WaitForTimeout, WaitForMessages, Message, \
    WaitForTasklet, get_event

## ----------------------------
## And here's an example...
## ----------------------------


class _CountSomeNumbers2(Tasklet):
    '''Counts numbers with at random time spacings'''

    def __init__(self, count, timeout):
        self.count = count
        self.timeout = timeout
        Tasklet.__init__(self)

    def run(self):
        '''Execute the task.'''
        import random
        for i in xrange(self.count):
            print ">> _count_some_numbers2", i
            yield (WaitForTimeout(random.randint(70, self.timeout)),
                   WaitForMessages(accept='quit'))
            event = get_event()
            if isinstance(event, Message) and event.name == 'quit':
                ## this would be the place to do some cleanup.
                return
        raise StopIteration(self.count * 2)


def _count_some_numbers1(count):
    '''Counts numbers with at fixed time spacings'''
    timeout = WaitForTimeout(500)
    for i in xrange(count):
        print "_count_some_numbers1", i
        task2 = _CountSomeNumbers2(10, 70)
        yield timeout, task2
        event = get_event()
        if event is timeout:
            print ">>> Got tired of waiting for task!! Canceling!"
            ## send a message asking the tasklet to stop
            yield Message('quit', dest=task2)
        elif isinstance(event, WaitForTasklet):
            print ">>> task returned %r, good task!" % event.retval
            ## restart timeout from scratch, otherwise it keeps
            ## running and we end up giving the next task too little
            ## time.
            timeout.restart()
        else:
            assert False, "strange event"

    raise SystemExit


def _test():
    '''a simple test/example'''
    Tasklet(_count_some_numbers1(5))
    gobject.MainLoop().run()


if __name__ == '__main__':
    _test()
