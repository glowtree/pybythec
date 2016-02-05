#!/usr/bin/env python
# -*- coding: utf-8 -*-

try:
  from setuptools import setup
except ImportError:
  from distutils.core import setup

with open('README.rst') as readme_file:
  readme = readme_file.read()

history = ''
try: # travis ci might not be able to find this path
  with open('./docs/history.rst') as history_file:
    history = history_file.read().replace('.. :changelog:', '')
except:
  pass

setup(
  name = 'pybythec',
  version = '0.1.1',
  description = "a lightweight python build system for c/c++",
  long_description = readme + '\n\n' + history,
  author = "glowtree",
  author_email = 'tom@glowtree.com',
  url = 'https://github.com/glowtree/pybythec',
  packages = ['pybythec'],
  scripts = ['bin/pybythec'],
  include_package_data = True,
  install_requires = [],
  license = "ISCL",
  zip_safe = False,
  keywords = 'pybythec',
  classifiers = [
    'Development Status :: 2 - Pre-Alpha',
    'Intended Audience :: Developers',
    'License :: OSI Approved :: ISC License (ISCL)',
    'Natural Language :: English',
    "Programming Language :: Python :: 2",
    'Programming Language :: Python :: 2.6',
    'Programming Language :: Python :: 2.7',
    'Programming Language :: Python :: 3',
    'Programming Language :: Python :: 3.3',
    'Programming Language :: Python :: 3.4'
  ],
  test_suite = 'tests',
  tests_require = []
)
