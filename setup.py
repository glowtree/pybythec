#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import platform
from setuptools import setup
from setuptools.command.install import install as baseInstall

class installer(baseInstall):
  def run(self):
    baseInstall.run(self)
    if platform.system() == 'Windows':
      batPath = os.path.dirname(sys.executable) + '/Scripts/pybythec.bat'
      with open(batPath, 'w') as f:
        f.write('@echo off\ncall python %~dp0\pybythec')

setup(
  name = 'pybythec',
  version = '0.2.1',
  author = 'glowtree',
  author_email = 'tom@glowtree.com',
  url = 'https://github.com/glowtree/pybythec',
  description = 'a lightweight python build system for c/c++',
  long_description = open('README.rst').read(),
  packages = ['pybythec'],
  scripts = ['bin/pybythec'],
  license = 'LICENSE',
  test_suite = 'test',
  cmdclass={'install': installer},
  # entry_points = {'console_scripts': ['pybythec = pybythec:main']}
)
