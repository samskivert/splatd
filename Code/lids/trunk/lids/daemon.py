# daemon.py vi:ts=4:sw=4:expandtab:
#
# LIDS Daemon Support.
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
#
# lids.daemon(conf) is all that should be necessary to call, where conf
# is a lids.parse_config()-parsed configuration file dictionary.

from lids import plugin

from twisted.internet import reactor, task

import ldap

class Context(object):
    # LIDS Daemon Context
    def __init__(self, ldapConnection):
        """
        Initialize a LIDS Daemon context
        @param ldapConnection: A connected instance of ldaputils.Connection
        """
        self.svc = {}
        self.tasks = {}
        self.l = ldapConnection

    def addHelper(self, name, controller):
        """
        Add a helper controller to the daemon context
        @param name: Unique caller-assigned name. Helpers with non-unique names will overwrite previous additions.
        @param controller: HelperController
        """
        self.svc[name] = controller

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

        # XXX TODO LDAP scope && group filter support
        entries = self.l.search(ctrl.searchBase, ldap.SCOPE_SUBTREE, ctrl.searchFilter, ctrl.searchAttr)
        for entry in entries:
            ctrl.work(entry)

    def start(self, once = False):
        """
        Add the daemon context to the twisted runloop
        """
        for name, ctrl in self.svc.items():
            t = task.LoopingCall(self._invokeHelper, name)
            t.start(ctrl.interval)
            self.tasks[name] = t

    def run(self):
        """
        Run the associated helper tasks once
        """
        for name, ctrl in self.svc.items():
                self._invokeHelper(name)


import functions
import classes

import os, sys, signal, sched, time, logging

#logger = logging.getLogger("lids")

# XXX: See if datetime or time can do this
_times = {"hours":3600, "minute":60, "day":86400, "seconds":1}

# We'll use this list to keep track of scheduled events, since the sched
# module doesn't seem to be provide access to the list of events.  This
# is in case we need to clean up, to cancel all of the events before
# deleting the scheduler.
_events = []

def _create_daemon():
    """ Detach a process from the terminal and run it as a daemon """
    logger = logging.getLogger("lids")

    try:
        logger.info("Detaching...")
        pid = os.fork()
        logger = logging.getLogger("lids")
    except OSError, e:
        logger.critical("An OSError occurred in daemon._create_daemon: %s", e)
        raise LIDSError, "An OSError occurred: %s" % e

    if pid == 0:
        # become the session leader
        os.setsid()

        # ignore SIGHUP, since children are sent SIGHUP when the parent
        # terminates
        signal.signal(signal.SIGHUP, signal.SIG_IGN)

        try:
            # second child to prevent zombies
            pid = os.fork()
            logger = logging.getLogger("lids")
        except OSError, e:
            logger.critical("An OSError occurred in daemon._create_daemon: %s", e)
            raise LIDSError, "An OSError occurred: %s" % e

        if pid == 0:
            # Make sure we don't keep any directory in use
            os.chdir("/")
            os.umask(0)
        else:
            os._exit(0)
    else:
        os._exit(0)

    try:
        maxfd = os.sysconf("SC_OPEN_MAX")
    except (AttributeError, ValueError):
        maxfd = 256

    for fd in range(0, maxfd):
        try:
            os.close(fd)
        except OSError:
            pass

    os.open("/dev/null", os.O_RDONLY)   # stdin
    os.open("/dev/null", os.O_RDWR)     # stdout
    os.open("/dev/null", os.O_RDWR)     # stderr

    logger.debug("Finished daemonizing")

    return 0

def _next_push(when):
    logger = logging.getLogger("lids")
    number,unit = when.split(" ")
    unit = unit.lower()
    if unit not in _times: return 0
    return (number * _times[unit])

def perform_push(conf, scheduler, section, event_id):
    global _events
    logger = logging.getLogger("lids")
    
    # First, delete this event in the event list
    if event_id != None:
        logger.info("Deleting current event id %d" % event_id)
        del _events[event_id]

    # First, schedule the next push for this event
    nextdelay = float(_next_push(conf[section + ".frequency"]))
    event = scheduler.enter(nextdelay, 1, perform_push, 
            (conf, scheduler, section, len(_events)))
    _events.append(event)
    logger.info("Scheduling event for %s in %d seconds" \
            % (section, nextdelay))
    ## XXX: Why don't we have access to the scheduler's event list?
    ## Keeping _event around seems messy
    
    # Now, actually perform it
    #print "Pushing %s" % section
    logger.info("Performing event for %s" % section)
    functions.push(conf, section)

def daemon(conf):
    global _events
    logger = logging.getLogger("lids")

    # Daemonize the process (fork, etc)
    logger.info("Daemonizing LIDS")
    #_create_daemon()

    s = sched.scheduler(time.time, time.sleep)   

    # First, find a list of all the sections we should be calling the
    # worker for, and how often we should be doing it.
    for opt in conf:
        section,option = opt.split(".", 1)
        if option == "frequency":
            logger.info("Found section %s to call every %s" \
                    % (section, conf[opt]))
            perform_push(conf, s, section, None)

    s.run()
    
    #try:
    #    s.run()
    #except Exception, e:
    #    # Clean up
    #    logger.info("Caught exception, cleaning up: " + str(e))
    #    print "UID: " + str(os.getuid())
    #    for e in _events:
    #        logger.debug("Cancelling event for %s" % e[3][2])
    #        s.cancel(e)
    #    del s
    #    sys.exit(1)

    sys.exit()

