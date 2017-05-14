TEREBI(3)
========
slowpoke <mail+git@slowpoke.io>
:encoding: utf-8
:doctype: manpage

NAME
----
terebi - a python interface to mpv

DESCRIPTION
-----------

terebi is an asynchronous, simple, and promise-based interface to mpv's
JSON IPC, allowing full control over the player via its UNIX socket.

The mpv object is threaded, and works by returning promise objects that can be
ask()'d for their eventual value.


SEE ALSO
--------
mpv(1)
