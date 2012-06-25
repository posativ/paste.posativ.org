#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2012 posativ <info@posativ.org>. All rights reserved.
# License: BSD revised
#
# A simple Pastebin using werkzeug and Jinja2. To delete pastes older than 30
# days just set up a cron like ``find . -type f -mtime +30 -exec rm "{}" \;``.

import io

from os import makedirs, urandom
from os.path import join, dirname, exists

from string import ascii_letters, digits
from HTMLParser import HTMLParser

from werkzeug.wrappers import Request, Response
from werkzeug.routing import Map, Rule
from werkzeug.exceptions import HTTPException, NotFound, InternalServerError
from werkzeug.wsgi import SharedDataMiddleware
from werkzeug.useragents import UserAgent

from jinja2 import Environment, FileSystemLoader


def hash(length):
    """generates a pseudo secure 8 chars long hash using /dev/random"""

    h = []
    for char in urandom(32).encode('base64'):
        if char in ascii_letters + digits:
            h.append(char)
        if len(h) >= length:
            break
    return ''.join(h)


class Strip(HTMLParser):
    """Try to return the original code."""

    def __init__(self, html):
        HTMLParser.__init__(self)

        self.inside = False

        self.code = []
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        if tag == 'code':
            self.inside = True

    def handle_endtag(self, tag):
        if tag == 'code':
            self.inside = False

    def handle_data(self, data):

        if self.inside:
            self.code.append(data)

    def handle_entityref(self, name):
        self.code.append(self.unescape('&' + name + ';'))

    def handle_charref(self, char):
        """An escaped umlaut like ``"&auml;"``"""
        self.code.append(self.unescape('&#' + char + ';'))


def create(app, request):
    """Create a new snippet: extract from fields (XXX linenos), render
    ``snippet.html`` and save it to data_dir."""

    filename = hash(length=8)

    text = request.form.get('code', request.files.get('file', '')).rstrip()
    lang = request.form.get('lang', 'text')
    linenos = request.form.get('linenos', False)

    with io.open(join(app.data_dir, filename), 'w') as fp:

        fp.write(app.render_template('paste.html',
            lang=(None if lang == 'guess' else lang),
            hash=filename,
            linenos=(True if linenos == 'on' else False),
            paste=text)
        )

    return Response('Moved Temporarily', 301,
                    headers={'Location': request.url_root+filename})


def show(app, request, paste):
    """Show paste either as nice HTML or, when headless client, as pure text."""

    p = join(app.data_dir, paste)
    headless = lambda req: UserAgent(req.environ).browser is None
    source = lambda html: ''.join(Strip(html).code)

    if exists(p):
        if not request.accept_mimetypes.accept_html or headless(request):
            return Response(source(io.open(p).read()), 200, content_type='text/plain')
        return Response(io.open(p), 200, content_type='text/html')
    else:
        return Response('Not Found', 404)


def index(app, request):
    """Return / -- basic stuff."""

    return Response(app.render_template('main.html'), 200, content_type='text/html')


urlmap = Map([
    Rule('/', endpoint=index, methods=['GET', ]),
    Rule('/', endpoint=create, methods=['POST', ]),
    Rule('/<string(length=8):paste>', endpoint=show, methods=['GET', ]),
])


class Pastie:

    data_dir = 'pastes/'
    template = 'main.html'
    jinja2 = Environment(loader=FileSystemLoader('.'))

    def __init__(self, data_dir=None):

        if data_dir:
            self.data_dir = data_dir

        try:
            makedirs(self.data_dir)
        except OSError:
            pass

        self.jinja_env = Environment(loader=FileSystemLoader('.'))

    def render_template(self, template_name, **kwargs):
        return self.jinja_env.get_template(template_name).render(**kwargs)

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


def make_app():

    return SharedDataMiddleware(Pastie(), {
         '/static/': join(dirname(__file__), 'static/')
    })


application = make_app()


if __name__ == '__main__':

    from werkzeug.serving import run_simple

    app = make_app()
    run_simple('127.0.0.1', 8080, app, use_reloader=True)
