#!/bin/env python

from pastebin import Pastie

class MyPastie(Pastie):

    SECRET_KEY = '12345'  # os.urandom(24)
    HTTLBL_KEY = '...'

app = MyPastie('pastes/', 'http://paste.domain.tld/')

