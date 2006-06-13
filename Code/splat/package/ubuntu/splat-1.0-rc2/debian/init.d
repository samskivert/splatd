#! /bin/sh
#
# Based on: @(#)skeleton  1.9  26-Feb-2001  miquels@cistron.nl
# Modified for splat-ldap package by Nick Barkas <snb@threerings.net>

PATH=/usr/local/sbin:/usr/local/bin:/sbin:/bin:/usr/sbin:/usr/bin
DAEMON=/usr/sbin/splatd
NAME=splatd
DESC="Scalable Periodic LDAP Attribute Transmogrifier"
PIDFILE=/var/run/splatd.pid

test -x $DAEMON || exit 0

if test -f /etc/default/splat-ldap; then
    . /etc/default/splat-ldap
fi

set -e

case "$1" in
  start)
	echo -n "Starting $DESC: "
    $DAEMON $DAEMON_OPTS -p $PIDFILE
	echo "$NAME."
	;;
  stop)
	echo -n "Stopping $DESC: "
    if [ -e $PIDFILE ] ; then
        kill `cat $PIDFILE`
        rm -f $PIDFILE
    fi
	echo "$NAME."
	;;
  restart|force-reload)
	echo -n "Restarting $DESC: "
    if [ -e $PIDFILE ] ; then
        kill `cat $PIDFILE`
        rm -f $PIDFILE
    fi
	sleep 1
    $DAEMON $DAEMON_OPTS -p $PIDFILE
	echo "$NAME."
	;;
  *)
	N=/etc/init.d/$NAME
	echo "Usage: $N {start|stop|restart|force-reload}" >&2
	exit 1
	;;
esac

exit 0
