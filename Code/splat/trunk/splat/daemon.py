# daemon.py vi:ts=4:sw=4:expandtab:
#
# Splat Daemon Support.
# Author:
#       Will Barton <wbb4@opendarwin.org>
#       Landon Fuller <landonf@threerings.net>
#
# Copyright (c) 2005 Three Rings Design, Inc.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
# 1. Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in the
#    documentation and/or other materials provided with the distribution.
# 3. Neither the name of the copyright owner nor the names of contributors
#    may be used to endorse or promote products derived from this software
#    without specific prior written permission.
# 
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

# This file contains everything necessary to run a Daemon that
# distributes information from LDAP using helper classes based on the
# frequency specification of sections in a lid.conf file.

import splat
from splat import plugin

from twisted.internet import reactor, task, defer

import ldap, logging

class Context(object):
    # Splat Daemon Context
    def __init__(self, ldapConnection):
        """
        Initialize a Splat Daemon context
        @param ldapConnection: A connected instance of ldaputils.Connection
        """
        self.svc = {}
        self.tasks = {}
        self.ldapConnection = ldapConnection

    def addHelper(self, controller):
        """
        Add a helper controller to the daemon context
        @param controller: HelperController
        """
        self.svc[controller.name] = controller

    def removeHelper(self, name):
        """
        From a helper controller from the daemon context
        @param name: Unique caller-assigned name.
        """
        # Stop the task, if started, and delete the associated entry
        if (self.tasks.has_key(name)):
            self.tasks[name].stop()
            self.tasks.pop(name)

        # Delete the controller entry
        self.svc.pop(name)

    def _invokeHelper(self, name):
        # Has helper been removed?
        if (not self.svc.has_key(name)):
            return

        ctrl = self.svc[name]
        ctrl.work(self.ldapConnection)

    def start(self):
        """
        Add the daemon context to the twisted runloop
        """
        for name, ctrl in self.svc.items():
            t = task.LoopingCall(self._invokeHelper, name)
            t.start(ctrl.interval)
            self.tasks[name] = t

        # Provide the caller our deferred result
        self.deferResult = defer.Deferred()
        return self.deferResult

    def stop(self):
        # Stop all running tasks
        try:
            for key in self.tasks.keys():
                task = self.tasks.pop(key)
                task.stop()
        except Exception, e:
            self.deferResult.errback(e)
            return

        # All tasks stopped.
        self.deferResult.callback(True)

    def run(self):
        """
        Run the associated helper tasks once
        """
        for name, ctrl in self.svc.items():
                self._invokeHelper(name)
