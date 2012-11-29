#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2012 posativ <info@posativ.org>. All rights reserved.
# License: BSD revised

import random

from string import ascii_lowercase, digits
from HTMLParser import HTMLParser, HTMLParseError


def hashgen(length=8, charset=ascii_lowercase+digits):
    """generates a pseudorandom string of a-z0-9 of given length"""
    return ''.join([random.choice(charset) for x in xrange(length)])


class Strip(HTMLParser):
    """Try to return the original code."""

    def __init__(self, html):

        self.inside = False
        self.code = []

        HTMLParser.__init__(self)
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
        self.code.append(self.unescape('&#' + char + ';'))
