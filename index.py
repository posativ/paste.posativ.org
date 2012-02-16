#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys; reload(sys);
sys.setdefaultencoding('utf-8')

from sys import argv
from os import listdir, path, remove, stat, environ as env, makedirs
from os.path import join, dirname, exists, getmtime
from cgi import FieldStorage
from time import time

from werkzeug.wrappers import Request, Response
from werkzeug.routing import Map, Rule, BaseConverter
from werkzeug.exceptions import HTTPException, NotFound, NotImplemented, InternalServerError

from pygments import highlight
from pygments.lexers import get_lexer_by_name, guess_lexer, get_all_lexers
from pygments.formatters import HtmlFormatter


url_map = Map([
    Rule('/', endpoint='index', methods=['GET', ]),
    Rule('/', endpoint='create', methods=['POST', ]),
    Rule('/<string(length=8):hash>', endpoint='show', methods=['GET', ]),
])


def hash(length):
    '''generates a pseudo secure 8 chars long hash using /dev/random'''
    
    from os import urandom
    from string import ascii_letters, digits
    
    h = []
    for char in urandom(32).encode('base64'):
        if char in ascii_letters + digits:
            h.append(char)
        if len(h) >= length:
            break
    return ''.join(h)


class Pastie(object):

    def __init__(self, data_dir):
        self.data_dir = data_dir
        if not exists(data_dir):
            makedirs(data_dir)
        with open('layouts/main.html', 'r') as fp:
            self.tt = fp.read() % {'lang': '\n'.join([
                '<option value="%s">%s</option>' % (val[1][0], val[0])
                    for val in sorted(get_all_lexers(), key=lambda k: k[1][0])
            ])}
    
    def dispatch(self, request, start_response):
        adapter = url_map.bind_to_environ(request.environ)
        try:
            endpoint, values = adapter.match()
            handler = getattr(self, 'on_'+endpoint)
            # if hasattr(endpoint, '__call__'):
            #     handler = endpoint
            # else:
            #     module, function = endpoint.split('.', 1)
            #     handler = getattr(globals()[module], function)
            return handler(request.environ, request, **values)
        except NotFound, e:
            return Response('Not Found', 404)
        except HTTPException, e:
            return e
        except InternalServerError, e:
            return Response(e, 500)

    def wsgi_app(self, environ, start_response):
        environ['data_dir'] = self.data_dir
        request = Request(environ)
        response = self.dispatch(request, start_response)
        return response(environ, start_response)
    
    def __call__(self, environ, start_response):
        return self.wsgi_app(environ, start_response)

    def _clean(self, threshold=1000):
        '''cleans oldest entries in data_dir if threshold is exceeded'''
        
        amount = len(listdir(self.data_dir))
        if amount > threshold:
            files = (join(self.data_dir, f) for f in listdir(self.data_dir))
            i = amount - threshold
            to_be_deleted = sorted([(p, getmtime(p)) for p in files], key=lambda k: k[1])[:i]

            for item in to_be_deleted:
                remove(item[0])

    def on_create(self, environ, request):
        '''hilites text in syntax's highlighting using pygments'''

        self._clean()

        text = request.form.get('code', request.files.get('file', ''))
        linenos = request.form.get('linenos', False)
        lexer = guess_lexer(text, stripall=True) if request.form.get('lang') == 'guess' \
                            else get_lexer_by_name(request.form.get('lang', 'text'), stripall=True)

        formatter = HtmlFormatter(linenos=linenos, encoding='utf-8')
        htext = highlight(text, lexer, formatter)

        doc = '''<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 4.01//EN" "http://www.w3.org/TR/html4/strict.dtd">  
<html> 
    <head>
        <title>Pastebin – paste.posativ.org</title>
        <link rel="stylesheet" href="layouts/hilite.css">
        <link rel="stylesheet" href="layouts/style.css">
        <meta http-equiv="content-type" content="text/html; charset=utf-8">
    </head>
    <body id="hilite">
        %s
    </body>
</html>'''
        
        filename = hash(length=8)
        with open(join(self.data_dir, filename), 'w') as fp:
            fp.write(doc % htext)
            
        return Response('Moved Temporarily', 301,
                        headers={'Location': request.url_root+filename})
        
    
    def on_show(self, environ, request, hash):

        p = join(self.data_dir, hash)
        if exists(p):
            return Response(file(p), 201, content_type='text/html')
        else:
            return Response('Not Found', 404)
    
    def on_index(self, environ, request):
        return Response(self.tt, 200, content_type='text/html')


class ReverseProxied(object):
    '''Wrap the application in this middleware and configure the
    front-end server to add these headers, to let you quietly bind
    this to a URL other than / and to an HTTP scheme that is
    different than what is used locally.

    In nginx:
    location /myprefix {
    proxy_pass http://192.168.0.1:5001;
    proxy_set_header Host $host;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Scheme $scheme;
    proxy_set_header X-Script-Name /myprefix;
    }

    :param app: the WSGI application
    '''
    def __init__(self, app, prefix):
        self.app = app
        self.prefix = prefix if prefix is not None else ''

    def __call__(self, environ, start_response):
        script_name = environ.get('HTTP_X_SCRIPT_NAME', self.prefix)
        if script_name:
            environ['SCRIPT_NAME'] = script_name
            path_info = environ['PATH_INFO']
            if path_info.startswith(script_name):
                environ['PATH_INFO'] = path_info[len(script_name):]

        scheme = environ.get('HTTP_X_SCHEME', '')
        if scheme:
            environ['wsgi.url_scheme'] = scheme
        return self.app(environ, start_response)


def make_app(data_dir='.data/', prefix=None):
    application = Pastie(data_dir)
    application.wsgi_app = ReverseProxied(application.wsgi_app, prefix=prefix)
    return application


application = make_app('pastes')


if __name__ == '__main__':

    from werkzeug import SharedDataMiddleware
    from werkzeug.serving import run_simple

    app = make_app('pastes')
    app = SharedDataMiddleware(app, {
         '/layouts/': join(dirname(__file__), 'layouts'),
    })
    run_simple('127.0.0.1', 8080, app, use_reloader=True)
