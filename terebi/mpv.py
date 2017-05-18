#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# terebi - a python interface to mpv
#
# Author: slowpoke <mail+git@slowpoke.io>
#
# This program is Free Software under the non-terms
# of the Anti-License. Do whatever the fuck you want.

from threading import Thread
from queue import Queue, Empty

from . import promise

import socket
import json
import os

from enum import Enum

from subprocess import Popen

import selectors

from errno import ECONNREFUSED

class LogLevel(Enum):
    NONE = 'none'
    FATAL = 'fatal'
    ERROR = 'error'
    WARN = 'warn'
    INFO = 'info'
    V = 'v'
    DEBUG = 'debug'
    TRACE = 'trace'


class Mpv(Thread):

    """ An interface to mpv's JSON IPC.

    """

    def __init__(self, mpv_sock_path):
        super().__init__()
        self._mpv_sock_path = mpv_sock_path
        self._events = Queue()
        self._awaiting_reply = Queue()
        self._keep_going = True
        self._mpv_started = False
        self._selector = selectors.DefaultSelector()
        self._partial_line = ""
        self._connecting = False

    @staticmethod
    def _make_socket():
        return socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)

    def _connect_socket(self):
        self._mpvsock.connect(self._mpv_sock_path)

    @staticmethod
    def _make_json_command(cmd_name, *params):
        command = [cmd_name]
        command.extend(params)
        msg = {"command": command}
        return json.dumps(msg).encode() + b"\n"

    def _read_json(self, jstring):
        what = json.loads(jstring)
        if "error" in what.keys():
            try:
                fulfill = self._awaiting_reply.get_nowait()
                fulfill(what)
            except Empty:
                pass
        elif "event" in what.keys():
            self._events.put(what)
        else:
            pass

    def _start_mpv(self, path_or_url):
        with open(os.devnull) as devnull:
            Popen(["mpv", path_or_url],
                   stdin=devnull, stdout=devnull, stderr=devnull)
        # recreate socket
        print("making new socket")
        self._mpvsock = self._make_socket()

        # register socket to selector
        def recv(conn, mask):
            data = self._partial_line + conn.recv(4096).decode()
            if not data:
                # mpv was most likely closed
                print("connection to mpv lost")
                self._selector.unregister(conn)
                conn.close()
                self._partial_line = ""
                self._mpv_started = False
                return
            lines = data.split("\n")
            for line in lines[:-1]:
                self._read_json(line)
            self._partial_line = lines[-1]

        print("socket registered")
        self._selector.register(self._mpvsock,
                                selectors.EVENT_READ + selectors.EVENT_WRITE,
                                recv)
        # wait until socket connection is available
        print("waiting for connection to socket")
        self._connecting = True
        while True:
            try:
                self._connect_socket()
            except OSError as e:
                if e.errno == ECONNREFUSED:
                    print("derp")
                    continue
                else:
                    raise
            break
        self._connecting = False
        self._selector.select()
        self._mpv_started = True
        if not self.is_alive():
            print("starting thread")
            self.start()

    def send_command(self, cmd_name, *params):
        """Send a command to mpv.

        This method will return a promise as a reply, which can be ask()'d for
        its value. This will block until the reply arrives.

        """
        if not self.is_alive():
            raise Exception("Listening process is no longer alive.")
        cmd = self._make_json_command(cmd_name, *params)
        reply_promise, fulfill = promise.new()
        self._awaiting_reply.put(fulfill)
        self._mpvsock.send(cmd)
        return reply_promise

    def run(self):
        while self._keep_going:
            if self._connecting:
                print("skipping")
                continue
            events = self._selector.select()
            for key, mask in events:
                f = key.data
                f(key.fileobj, mask)

    def get_event(self, block=True, timeout=None):
        return self._events.get(block, timeout)

    def get_event_nowait(self):
        return self.get_event(block=False)

    def stop_daemon(self):
        """Stop the daemon."""
        self._keep_going = False

    def client_name(self):
        """Return the client name."""
        return self.send_command(self, "client_name")

    def get_time(self):
        """Get the system time (get_time_us command)."""
        return self.send_command(self, "get_time_us")

    def set_property(self, name, value, string=False):
        """Set the value of a property.

        If the string argument is set to True, this will act like mpv's
        set_property_string command and always expect a string as the value.
        """
        cmd = "set_property_string" if string else "set_property"
        return self.send_command(cmd, name, value)

    def get_property(self, name, string=False):
        """Get the value of a property.

        If the string argument is set to True, this will act like mpv's
        get_property_string command and always return a string.
        """
        cmd = "get_property_string" if string else "get_property"
        return self.send_command(cmd, name)

    def enable_event(self, name):
        """Enable the named event. If name is 'all', enable all events."""
        return self.send_command("enable_event", name)

    def disable_event(self, name):
        """Disable the named event. If name is 'all', disable all events."""
        return self.send_command("disable_event", name)

    def request_log_messages(self, level):
        """Enable mpv log messages.

        Log levels are defined in the LogLevels enum.

        Log messages will be send as events.
        """
        if not level in LogLevel:
            raise ValueError("{} is not a valid log level.".format(level))
        return self.send_command("request_log_messages", level.value)

    def play(self, path_or_url, unpause=True):
        """Play a given file or URL.

        By default, this will immediately start playback of the loaded file.
        To disable this, pass unpause=False.
        """
        if not self._mpv_started:
            self._start_mpv(path_or_url)
        ret = self.send_command("loadfile", path_or_url)
        self.set_property("pause", not unpause)
        return ret

    def pause(self):
        """Pause playback."""
        return self.set_property("pause", True)

    def unpause(self):
        """Resume playback."""
        return self.set_property("pause", False)

    def stop(self):
        """Stop playback."""
        return self.send_command("stop")
