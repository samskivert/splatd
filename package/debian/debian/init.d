#! /bin/sh
#
# Based on: @(#)skeleton 1.9 26-Feb-2001 miquels@cistron.nl
# Modified for splatd package by Nick Barkas <snb@threerings.net>

PATH=/usr/local/sbin:/usr/local/bin:/sbin:/bin:/usr/sbin:/usr/bin
DAEMON=/usr/sbin/splatd
NAME=splatd
DESC="Scalable Periodic LDAP Attribute Transmogrifier"
PIDFILE=/var/run/splatd.pid

test -x $DAEMON || exit 0

if test -f /etc/default/splatd; then
    . /etc/default/splatd
fi

set -e

case "$1" in
    start)
        echo -n "Starting $DESC: "
        if test -f $PIDFILE ; then
            echo "$PIDFILE exists... is $NAME already running?"
        else
            $DAEMON $DAEMON_OPTS -p $PIDFILE
            echo "$NAME started."
        fi
        ;;
    stop)
        echo -n "Stopping $DESC: "
        if test -f $PIDFILE ; then
            kill `cat $PIDFILE` && rm -f $PIDFILE
            echo "$NAME stopped."
        else
            echo "$PIDFILE not found... is $NAME running?"
        fi
        ;;
    restart|force-reload)
        echo -n "Restarting $DESC: "
        if test -f $PIDFILE ; then
            kill `cat $PIDFILE` && rm -f $PIDFILE
            echo "$NAME stopped... "
        else
            echo "$PIDFILE not found... is $NAME running?"
        fi
        sleep 1
        if test -f $PIDFILE ; then
            echo "$PIDFILE exists... is $NAME already running?"
        else
            $DAEMON $DAEMON_OPTS -p $PIDFILE
            echo "$NAME started."
        fi
        ;;
    *)
        N=/etc/init.d/$NAME
        echo "Usage: $N {start|stop|restart|force-reload}" >&2
        exit 1
        ;;
esac

exit 0
