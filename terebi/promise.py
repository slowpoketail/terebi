#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#from multiprocessing_on_dill import Queue
#from multiprocessing import Queue
from queue import Queue


class Promise:

    """A promise is an object that represents a value that might not yet exist
    at the time of the creation of the promise, but will at a later point. A
    promise can be asked for the value it represents, and will block until that
    value is ready.

    Usage
    -----

    After creation, a promise is at first inactive. To activate it, call its
    activate() method, which will return a function object. This unary function
    can be called with any value to fulfill the promise.

    >>> promise = Promise()
    >>> fulfill = promise.activate()
    >>> fulfill('any value')
    >>> promise.ask()
    'any value'


    For convenience, simply use Promise.new(), which will return a two-tuple
    containing an activated promise and the function to fulfill it.

    >>> promise, fulfill = Promise.new()
    >>> fulfill('any value')
    >>> promise.ask()
    'any value'

    Promise.new() is available at the module level simply as new().

    XXX: Promises do, at the moment, not work with pickle (because they rely on
    closures) and are therefore unusable with anything that relies on
    serialization provided by the standard library (for example,
    multiprocessing.Queue). Promises do work with dill, a drop-in replacement
    for pickle which can serialize lambdas, closures, and many more things that
    pickle cannot.

    """

    def __init__(self):
        self._sentinel = object()
        self._value = self._sentinel
        self._active = False
        self._inbox = Queue(maxsize=1)

    @classmethod
    def new(cls):
        """Create a new promise.

        Returns a tuple containing the activated promise and the function to
        fulfill it.

        """
        p = cls()
        f = p.activate()
        return p, f

    def activate(self):
        """Activate the promise.

        This method returns a function which can be called with a value to
        fulfill the promise.
        """
        if self._active:
            raise Exception("Promise is already active.")
        self._active = True

        def fulfill(value):
            if self._value is not self._sentinel:
                raise Exception("Promise has alreday been fulfilled.")
            self._value = value
            self._inbox.put(value)

        return fulfill

    def ask(self, block=True, timeout=None):
        """Ask the promise for the value it represents.

        Should the value be ready, it will be returned now. Otherwise,
        ask() will block until the value is ready.

        ask() can safely be called any number of times afterwards, it will
        always return the same value.

        """
        if not self._active:
            raise Exception("Promise is not active.")
        if self._value is not self._sentinel:
            return self._value
        else:
            return self._inbox.get(block, timeout)

    def ask_nowait(self):
        """Ask the promise for the value it represents, but don't block.

        This will only get the promised value if it is immediately available.
        Otherwise raise the Empty exception.

        """
        return self.ask(block=False)


# convenience function
new = Promise.new
