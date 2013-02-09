#!/usr/bin/python
# import sys
# sys.path.insert(0, '<your_local_path>/lib/python2.6/site-packages')

from flup.server.fcgi import WSGIServer
from pastebin import Pastie

class MyPastie(Pastie):

    SECRET_KEY = '12345'  # os.urandom(24)
    HTTLBL_KEY = '...'

app = MyPastie('pastes/', 'http://paste.domain.tld/')

class ScriptNameStripper(object):
   def __init__(self, app):
       self.app = app

   def __call__(self, environ, start_response):
       environ['SCRIPT_NAME'] = ''
       return self.app(environ, start_response)

app = ScriptNameStripper(app)

