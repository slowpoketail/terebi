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


class Mpv(Thread):

    """ An interface to mpv's JSON IPC.

    """

    def __init__(self, mpv_sock_path):
        super().__init__()
        self._mpv_sock_path = mpv_sock_path
        self._events = Queue()
        self._awaiting_reply = Queue()
        self._mpvsock = self._make_socket()
        self._keep_going = True

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
        self._connect_socket()
        # temporary storage for partial lines
        partial_line = ""
        while self._keep_going:
            data = partial_line + self._mpvsock.recv(4096).decode()
            if data == "":
                break
            lines = data.split("\n")
            for line in lines[:-1]:
                self._read_json(line)

            partial_line = lines[-1]
        self._mpvsock.close()

    def get_event(self, block=True, timeout=None):
        return self._events.get(block, timeout)

    def get_event_nowait(self):
        return self.get_event(block=False)

    def stop(self):
        """Stop the daemon."""
        self._keep_going = False
        # we send a command to get the loop to terminate
        self.send_command("get_property", "pause")

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
