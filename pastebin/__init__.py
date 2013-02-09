#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2012 posativ <info@posativ.org>. All rights reserved.
# License: BSD revised
#
# A simple Pastebin using werkzeug and Jinja2. To delete pastes older than 30
# days just set up a cron like ``find /path/ -type f -mtime +30 -exec rm "{}" \;``.

__version__ = '0.1'

import sys; reload(sys)
sys.setdefaultencoding('utf-8')

import io

from os import makedirs, unlink
from os.path import join, dirname, isfile, isdir
from optparse import OptionParser, make_option, SUPPRESS_HELP

from werkzeug.wsgi import SharedDataMiddleware
from werkzeug.routing import Map, Rule
from werkzeug.serving import run_simple
from werkzeug.wrappers import Request, Response
from werkzeug.exceptions import HTTPException, NotFound, InternalServerError, abort
from werkzeug.useragents import UserAgent

from itsdangerous import BadSignature, Signer

from httpbl import HttpBL, HARVESTER, COMMENT_SPAMMER
from jinja2 import Environment, FileSystemLoader

from pastebin.utils import hashgen, Strip


def create(app, request):
    """Create a new snippet: extract from fields (XXX linenos), render
    ``layouts/show.html`` and save it to data_dir."""

    rv = app.httpbl.query(request.environ.get("HTTP_X_REAL_IP", request.remote_addr))
    if any(filter(lambda typ: typ in (rv['type'] or []), [HARVESTER, COMMENT_SPAMMER])):
        abort(400)

    retry_count = 3
    short_id_length = 32 if request.form.get('private') else 3

    while True:
        pasteid = hashgen(short_id_length)

        if isfile(join(app.data_dir, pasteid)):
            retry_count += 1
            if retry_count > 3:
                short_id_length += 1
                retry_count = 1
        else:
            break

    text = request.form.get('code', request.files.get('file', '')).rstrip()
    lang = request.form.get('lang', 'text')
    linenos = request.form.get('linenos', False)

    if any(filter(lambda k: request.form.get(k) == 'on', ['human', 'tos'])):
        return Response('Moved Temporarily', 301, headers={'Location': '/dev/null'})

    with io.open(join(app.data_dir, pasteid), 'w') as fp:

        fp.write(app.render_template('show.html',
            lang=(None if lang == 'guess' else lang),
            hash=pasteid,
            linenos=(True if linenos == 'on' else False),
            paste=text,
            url=app.host+pasteid
        ))

    response = Response('Moved Temporarily', 301, headers={'Location': request.url_root+pasteid})
    response.set_cookie(pasteid, app.sign(pasteid), max_age=30*24*60*60)  # max. 30 days
    return response


def show(app, request, pasteid):
    """Show pasteid either as nice HTML or, when headless client, as pure text."""

    p = join(app.data_dir, pasteid)
    headless = lambda req: UserAgent(req.environ).browser is None
    source = lambda html: ''.join(Strip(html).code)

    if isfile(p):
        if not request.accept_mimetypes.accept_html or headless(request):
            return Response(source(io.open(p).read()), 200, content_type='text/plain')
        return Response(io.open(p), 200, content_type='text/html')
    else:
        return Response('Not Found', 404)


def remove(app, request, pasteid):
    """Remove paste on GET request if the user initially created that paste."""

    try:
        if app.unsign(request.cookies.get(pasteid, '')) != pasteid:
            raise ValueError
    except (BadSignature, ValueError):
        return abort(403)

    try:
        unlink(join(app.data_dir, pasteid))
    except OSError:
        abort(404)

    return Response('Paste successfully removed. Thanks for choosing paste.posativ.org.', 200)


def index(app, request):
    """Return / -- basic stuff."""

    return Response(app.render_template('main.html'), 200, content_type='text/html')


urlmap = Map([
    Rule('/', endpoint=index, methods=['GET', ]),
    Rule('/', endpoint=create, methods=['POST', ]),
    Rule('/<string(minlength=3):pasteid>', endpoint=show),
    Rule('/<string(minlength=3):pasteid>/remove', endpoint=remove),
])


class Pastie:

    SECRET_KEY = '\x85\xe1Pc\x11n\xe0\xc76\xa1\xd9\x93$\x1ei\x06'
    HTTBL_KEY = 'THIS IS NOT A VALID HTTPBL KEY'

    def __init__(self, data_dir='pastes/', host='http://localhost/'):

        self.httpbl = HttpBL(self.HTTBL_KEY)
        self.signer = Signer(self.SECRET_KEY)

        self.jinja_env = Environment(loader=FileSystemLoader(
            join(dirname(__file__), 'layouts'))
        )
        self.host = host
        self.data_dir = data_dir

        if not isdir(data_dir):
            makedirs(data_dir)

    def render_template(self, template_name, **kwargs):
        return self.jinja_env.get_template(template_name).render(**kwargs)

    def sign(self, value):
        return self.signer.sign(value)

    def unsign(self, value):
        return self.signer.unsign(value)

    def dispatch(self, request, start_response):

        adapter = urlmap.bind_to_environ(request.environ)
        request.adapter = adapter

        try:
            endpoint, values = adapter.match()
            return endpoint(self, request, **values)
        except NotFound, e:
            return Response('Not Found', 404)
        except HTTPException, e:
            return e
        except InternalServerError, e:
            return Response(e, 500)

    def wsgi_app(self, environ, start_response):

        request = Request(environ)
        response = self.dispatch(request, start_response)
        return response(environ, start_response)

    def __call__(self, environ, start_response):
        return self.wsgi_app(environ, start_response)


def main():

    options = [
        make_option("--data-dir", dest="data_dir", default="pastes/",
                    help="paste directory"),
        make_option("--host", dest="host", default="http://localhost/",
                    help="host shown for a paste"),
        make_option("--port", dest="port", default=8080, type=int,
                    help="port to serve on"),
        make_option("--use-reloader", action="store_true", dest="reloader",
                    help=SUPPRESS_HELP, default=False),
        make_option("--version", action="store_true", dest="version",
                    help=SUPPRESS_HELP, default=False),
    ]

    parser = OptionParser(option_list=options)
    (options, args) = parser.parse_args()

    app = SharedDataMiddleware(Pastie(options.data_dir, options.host), {
         '/static/': join(dirname(__file__), 'static/')
    })

    run_simple('127.0.0.1', options.port, app, use_reloader=options.reloader)
