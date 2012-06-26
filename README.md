Pastebin -- a LodgeIt™ clone*
=============================

\* without the good parts

## /etc/init.d/pastebin

```shell
#!/bin/sh

NAME=pastebin
CHDIR=/home/py/pastebin/
USER=py
CMD=/usr/local/bin/gunicorn
DAEMON_OPTS="-b 127.0.0.1:8016 server:application"

case $1 in
    start)
    echo -n "Starting $NAME: "
    start-stop-daemon --start --pidfile /var/run/$NAME.pid --chdir $CHDIR \
    --chuid $USER --make-pidfile --background --exec $CMD \
    -- $DAEMON_OPTS || true
    echo "$NAME."
       ;;
stop)  start-stop-daemon --stop --pidfile /var/run/$NAME.pid
       ;;
esac```
