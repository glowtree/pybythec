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
    os.environ['SHARED'] = '../../../shared'
    os.environ['PYBYTHEC_GLOBALS'] = '{0}/.pybythecGlobals.json'.format(os.environ['SHARED'])
    
    
  def tearDown(self):
    
    # self._clean()
    # os.chdir('../../Plugin/src')
    # self._clean()
    
    os.chdir(self.lastCwd)


  def test_000_something(self):
    print('\n')
    
    # build Plugin
    os.chdir('./example/projects/Plugin/src')
    
    # build Main (along with it's library dependencies)
    os.chdir('../../Main/src')
    
    exePath = '../Main'
    if platform.system() == 'Windows':
      exePath += '.exe'
    
    self.assertTrue(os.path.exists(exePath))
    
    p = subprocess.Popen([exePath], stdout = subprocess.PIPE, stderr = subprocess.PIPE)
    stdout, stderr = p.communicate()
    
    if len(stderr):
      raise Exception(stderr)
    
    print(stdout)
    self.assertTrue(stdout.startswith('running the executable and the statically linked library and the dynamically linked library and the plugin'))
      
    
  def _build(self):
    if platform.system() == 'Linux':
      pybythec.build(['', '-c', 'g++', '-os', 'linux'])
    elif platform.system() == 'Darwin':
      pybythec.build(['', '-c', 'clang++', '-os', 'osx'])
    elif platform.system() == 'Windows':
      pybythec.build(['', '-c', 'msvc100', '-os', 'windows'])
    else:
      raise Exception('unknown operating system')
    
  def _clean(self):
    if platform.system() == 'Linux':
      pybythec.cleanall(['', '-c', 'g++', '-os', 'linux'])
    elif platform.system() == 'Darwin':
      pybythec.cleanall(['', '-c', 'clang++', '-os', 'osx'])
    elif platform.system() == 'Windows':
      pybythec.cleanall(['', '-c', 'msvc100', '-os', 'windows'])
    else:
      raise Exception('unknown operating system')
      
if __name__ == '__main__':
  import sys
  sys.exit(unittest.main())

