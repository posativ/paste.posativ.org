#!/usr/bin/env python
# -*- encoding: utf-8 -*-

import sys
import re

from setuptools import setup, find_packages

version = re.search("__version__ = '([^']+)'",
                    open('pastebin/__init__.py').read()).group(1)

setup(
    name='pastebin',
    version=version,
    author='posativ',
    author_email='info@posativ.org',
    packages=find_packages(),
    zip_safe=True,
    url='https://github.com/posativ/paste.posativ.org/',
    license='BSD revised',
    description='logdeit clone',
    classifiers=[
        "Development Status :: 4 - Beta",
        "Topic :: Internet",
        "Topic :: Internet :: WWW/HTTP :: HTTP Servers",
        "Topic :: Internet :: WWW/HTTP :: WSGI :: Application",
        "License :: OSI Approved :: BSD License",
        "Programming Language :: Python :: 2.6",
        "Programming Language :: Python :: 2.7"
    ],
    install_requires=['werkzeug', 'jinja2', 'httpbl', 'itsdangerous'],
    entry_points={
        'console_scripts':
            ['pastebin = pastebin:main'],
    },
)