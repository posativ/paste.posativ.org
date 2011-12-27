#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys; reload(sys); sys.setdefaultencoding('utf-8')

import cgitb; cgitb.enable()  # for troubleshooting
from sys import argv
from os import listdir, path, remove, stat, environ as env
from cgi import FieldStorage
from time import time
from layouts.shpaml import convert_text

def clean(root):
    '''cleans everything in root folder [non-recursive] which is older than 7 days
       and is not the script's name'''
    
    for item in listdir(root):
        if path.isfile(item) and item != argv[0].rsplit('/', 1)[-1]:
            if (time() - stat(root + '/' + item).st_mtime)/3600/24 >= 28:
                remove(item)
                
def create(text, syntax, linenos=False):
    
    def hash():
        '''generates a pseudo secure 8 chars long hash using /dev/random'''
        
        from os import urandom
        from string import ascii_letters, digits
        
        h = []
        for char in urandom(32).encode('base64'):
            if char in ascii_letters + digits:
                h.append(char)
            if len(h) >= 8:
                break
        return ''.join(h)

    
    def hilite(text, syntax=False, linenos=False):
        '''hilites text in syntax's highlighting using pygments'''
        from pygments import highlight
        from pygments.lexers import get_lexer_by_name, guess_lexer
        from pygments.formatters import HtmlFormatter

        if syntax:
            lexer = get_lexer_by_name(syntax, stripall=True)
            formatter = HtmlFormatter(linenos=linenos, encoding='utf-8')
            return highlight(text, lexer, formatter)
        else:
            lexer = guess_lexer(text, stripall=True) #  guess
            formatter = HtmlFormatter(linenos=linenos, encoding='utf-8')
            return highlight(text, lexer, formatter)
            
    doc = '''<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 4.01//EN" "http://www.w3.org/TR/html4/strict.dtd">  
<html> 
    <head> 
        <title>Pastebin &mdash posativ.org</title> 
        <link rel="stylesheet" href="layouts/hilite.css"> 
        <meta http-equiv="content-type" content="text/html; charset=utf-8"> 
    </head> 
    <body>
        %s
    </body>
</html>'''

    filename = hash()
    
    if path.exists(filename):
        print 'Duplicate entry... seems /dev/random is not reliable'
    else:
        file = open(filename, 'w')
        text = hilite(text, syntax, linenos)
        file.write(doc % text)
        file.close()
        
    return filename

def read(h):
    if path.isfile(h):
        return open(h).read()
    else:
        return 'No such entry!'
    
if __name__ == '__main__':
    
    PATH = '.'
    clean(PATH)

    print 'Content-Type: text/html\n'
    
    if env['REQUEST_METHOD'] == 'GET':
        print convert_text(open('layouts/main.shpaml').read()) % {'lang': open('layouts/lang.html').read()}
        
    elif env['REQUEST_METHOD'] == 'POST':
        args = FieldStorage()
        text = unicode(args.getvalue('code')) if not args.getvalue('file', None) else args.getvalue('file')
        lang = False if args.getvalue('lang') == 'guess' else args.getvalue('lang')
        h = create(text, lang, linenos=args.getvalue('linenos', False))
        print '''<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 4.01//EN" "http://www.w3.org/TR/html4/strict.dtd">
                 <html><head><meta http-equiv="refresh" content="0; URL=%s" /></head></html>''' % h
