#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
import os
import sys
import platform
from setuptools import setup
from setuptools.command.install import install as baseInstall

#
# custom install...
#
class installer(baseInstall):
  def run(self):
    
    globalsPath = ''
    
    if platform.system() == 'Linux' or platform.system() == 'Darwin':
      globalsPath = os.environ['HOME'] + '/.pybythecGlobals.json' 
          
    elif platform.system() == 'Windows':
      batPath = os.path.dirname(sys.executable) + '/Scripts/pybythec.bat'
      with open(batPath, 'w') as f:
        f.write('@echo off\ncall python %~dp0\pybythec %*')
      globalsPath = os.environ['USERPROFILE'] + '/.pybythecGlobals.json' 

    else:
      print('unsupported operating system')
      return
    
    with open('./pybythec/pybythecGlobals.json') as rf:
      pybythecGlobals = rf.read()

      print('installing ' + globalsPath)
      with open(globalsPath, 'w') as f:
        f.write(pybythecGlobals)

    baseInstall.run(self)


description = 'A lightweight cross-platform build system for c/c++, written in python'

setup(
  name = 'pybythec',
  version = '0.9.7',
  author = 'glowtree',
  author_email = 'tom@glowtree.com',
  url = 'https://github.com/glowtree/pybythec',
  description = description,
  long_description = str(open('README.rst', 'r').read()).replace(description, ''),
  packages = ['pybythec'],
  scripts = ['bin/pybythec'],
  license = 'LICENSE',
  test_suite = 'test',
  cmdclass = {'install': installer}
  # entry_points = {'console_scripts': ['pybythec = pybythec:main']}
)
