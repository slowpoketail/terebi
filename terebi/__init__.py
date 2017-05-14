#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# terebi - a python interface to mpv
#
# Author: slowpoke <mail+git@slowpoke.io>
#
# This program is Free Software under the non-terms
# of the Anti-License. Do whatever the fuck you want.

"""terebi - a no bullshit interface to mpv.

Terebi is an asynchronous, simple, and promise-based interface to mpv's
JSON IPC, allowing full control over the player via its UNIX socket.

"""

from mpv import LogLevel, Mpv
