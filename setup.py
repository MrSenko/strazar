#!/usr/bin/env python

from setuptools import setup, find_packages

with open('README.rst') as file:
    long_description = file.read()

config = {
    'name' : 'strazar',
    'version' : '0.2.7',
    'packages' : find_packages(),
    'author' : 'Mr. Senko',
    'author_email' : 'atodorov@mrsenko.com',
    'license' : 'BSD',
    'description' : 'Automatic upstream dependency testing',
    'long_description' : long_description,
    'url' : 'https://github.com/MrSenko/strazar',
    'keywords' : ['testing'],
    'classifiers' : [
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
    ],
    'zip_safe' : False,
    'install_requires' : ['PyYAML'],
}

setup(**config)
