# All Rights Reserved.
# 
# Author: Will Barton
#
# lids - LDAP Information Distribution System
# A library for retrieving, formatting, and updating information stored in 
# an LDAP database
#
# This file contains everything necessary to run a Daemon that
# distributes information from LDAP using helper classes based on the
# frequency specification of sections in a lid.conf file.
#
# lids.daemon(conf) is all that should be necessary to call, where conf
# is a lids.parse_config()-parsed configuration file dictionary.
#


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

