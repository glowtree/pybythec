#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
test_pybythec
----------------------------------

Tests for `pybythec` module.
'''

import os
import platform
import unittest
import subprocess
import pybythec

class TestPybythec(unittest.TestCase):
  
  def setUp(self):
    self.lastCwd = os.getcwd()
    os.chdir('./example/projects/Main/src')
    os.environ['PYBYTHEC_GLOBALS'] = '../../../shared/.pybythecGlobals.json'

  def tearDown(self):
    if platform.system() == 'Linux':
      pybythec.cleanall(['', '-c', 'g++', '-os', 'linux']) 
    elif platform.system() == 'Darwin':
      pybythec.cleanall(['', '-c', 'clang++', '-os', 'osx']) 
    elif platform.system() == 'Windows':
      pybythec.cleanall(['', '-c', 'msvc100', '-os', 'windows']) 
    else:
      print('unknown operating system')
    os.chdir(self.lastCwd)

  def test_000_something(self):
    print('\n')
    exePath = '../Main'
    if platform.system() == 'Linux':
      pybythec.build(['', '-c', 'g++', '-os', 'linux'])
    elif platform.system() == 'Darwin':
      pybythec.build(['', '-c', 'clang++', '-os', 'osx'])
    elif platform.system() == 'Windows':
      pybythec.build(['', '-c', 'msvc100', '-os', 'windows'])
      exePath += '.exe'
    else:
      print('unknown operating system')
      return
      
    self.assertTrue(os.path.exists(exePath))
    
    p = subprocess.Popen([exePath], stdout = subprocess.PIPE, stderr = subprocess.PIPE)
    stdout = p.communicate()[0].decode('utf-8')
    print(stdout)
    self.assertTrue(stdout.startswith('running the executable and the statically linked library')) # and the dynamically linked library'))
      
if __name__ == '__main__':
  import sys
  sys.exit(unittest.main())

