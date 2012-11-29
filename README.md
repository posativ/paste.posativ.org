Pastebin – a LodgeIt™ clone*
============================

\* without the good parts

This is a usual pastebin that allows anonymous pastes of code pieces. Syntax
highlighting is done via [highlight.js][1]. Every paste is saved as static
HTML and can served without this application. If you connect to a paste with
a headless client, say `curl` the server rebuilts the original code.

    $ easy_install jinja2 werkzeug httpbl

and clone this repository and launch with `python server.py`. To remove pastes
after a given time, use `cron` (the default location of pastes is `pastes/`:

    $ find /path/to/pastes -type f -mtime +30 -exec rm "{}" \;

[1]: http://softwaremaniacs.org/soft/highlight/en/

## /etc/init.d/pastebin

```bash
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
esac
```
