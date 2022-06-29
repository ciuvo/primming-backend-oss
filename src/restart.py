#!/usr/bin/env python
# Copyright 2009-2021 Ciuvo GmbH. All rights reserved.
# This file is subject to the terms and conditions defined in
# file 'LICENSE', which is part of this source code package.

"""
For developer mode, since hypercorn's --reload param is lacking.
"""


import logging
import os
import re
import signal
import sys
import time

import psutil
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

log = logging.getLogger(__name__)


def start():
    """start the actual hypercorn instance"""
    # adapted from the hypercorn executable
    from hypercorn.__main__ import main  # NOQA

    sys.argv[0] = re.sub(r"(-script\.pyw|\.exe)?$", "", sys.argv[0])
    sys.exit(main())


def get_observer_path():
    """get the absolute root path of the kadoka project"""
    src_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), "../../")
    return os.path.abspath(src_path)


class ChildDiedException(Exception):
    pass


def child_health_check(pid):
    """check if the given pid is still healthy, raises a ChildDiedException if it isn't or a
    psutil.NoSuchProcess exception if you're the type to just make up your own numbers."""
    pinfo = psutil.Process(pid)
    if pinfo.status() in (psutil.STATUS_ZOMBIE, psutil.STATUS_STOPPED, psutil.STATUS_DEAD):
        raise ChildDiedException()


def stop_process_waiting(pid):
    """Stop the given pid (sending SIG_QUIT & waiting & SIG_KILL)"""
    try:
        os.kill(pid, signal.SIGQUIT)
        # wait for 5s for the process to exit gracefully, check every 100ms
        for _ in range(50):
            time.sleep(0.1)
            child_health_check(pid)
    except (ChildDiedException, psutil.NoSuchProcess, OSError):
        # we can exit silently as having a dead process is the desired path, actually
        pass

    # take care of potential remnants (the brute-force and ask-forgiveness approach)
    try:
        os.kill(pid, signal.SIGKILL)
    except OSError:
        # we can exit silently as having a dead process is the desired path, actually
        pass

    try:
        os.waitpid(pid, 0)
    except OSError:
        # we can exit silently as having a dead process is the desired path, actually
        pass


class CodeChangedEventHandler(FileSystemEventHandler):
    """if a file is modified that matches the pattern specified, it will kill the child-pid"""

    filename_pattern = re.compile(r"^.*\.(py|yaml)$")

    def __init__(self):
        self.running = False
        self.shutting_down = False  # semaphore system for thread safety
        self.pid = None

    def on_any_event(self, event):
        """if a file matching the pattern was modifed, stop the server"""
        if (
            self.running
            and self.pid
            and self.filename_pattern.match(event.src_path or event.dest_path)
        ):
            print("%s was modified, stopping instance..." % event.src_path)
            self.stop()

    def wait_blocking(self, pid):
        """wait for the child to exit for whatever reason"""
        self.running = True
        self.pid = pid
        while self.running:
            if not self.shutting_down:
                child_health_check(pid)
            time.sleep(1)

    def stop(self):
        """stopping the child process

        Note: the order of how the flags are set is important for thread safety"""
        self.shutting_down = True
        stop_process_waiting(self.pid)
        self.running = False
        self.shutting_down = False


class RestartOnFileModification(object):
    """Convenience wrapper for the observer class."""

    def __init__(
        self, path, child_process_entry_callback, event_handler_class=CodeChangedEventHandler
    ):
        """
        Parameters:
        -----------

        path: str
            the path to observe for code changes

        child_process_entry_callback: func
            a callable to start the code execution in the child

        event_handler_class: class
            the code changed event handler class
        """
        self.path = path
        self.start = child_process_entry_callback
        self.event_handler_class = event_handler_class

        # lazily initialize, we do not want to have it in the child process
        self._event_handler = None
        self._observer = None

    @property
    def event_handler(self):
        """lazily initialize the handler to prevent it being copied over to the child on fork"""
        if not self._event_handler:
            self._event_handler = self.event_handler_class()

        return self._event_handler

    def start_observer(self):
        """lazily initialize the observer to prevent it being copied over to the child on fork"""
        if not self._observer:
            self._observer = Observer()
            self._observer.schedule(self.event_handler, path=self.path, recursive=True)
            self._observer.start()
        return self._observer

    def run(self):
        """The main loop"""
        while True:
            child_pid = os.fork()
            if child_pid == 0:
                # I'm the child
                self.start()
                break
            else:
                # I'm the parent
                print("Started child with pid %d..." % child_pid)
                try:
                    self.start_observer()
                    self.event_handler.wait_blocking(child_pid)
                except (KeyboardInterrupt, ChildDiedException):
                    self.stop(child_pid)
                    exit(1)

    def stop(self, child_pid):
        """shut down the observer and wait for the child to exit"""
        self._observer.stop()
        stop_process_waiting(child_pid)
        self._observer.join()


if __name__ == "__main__":
    rtfm = RestartOnFileModification(get_observer_path(), start)
    rtfm.run()
