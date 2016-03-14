#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
test_pybythec
----------------------------------

tests for pybythec module
'''

import os
import platform
import unittest
import subprocess
import pybythec

class TestPybythec(unittest.TestCase):
  
  def setUp(self):
    '''
      typical setup for building with pybythc
    '''
    self.lastCwd = os.getcwd()
    os.environ['SHARED'] = '../../../shared'
    os.environ['PYBYTHEC_GLOBALS'] = '{0}/.pybythecGlobals.json'.format(os.environ['SHARED'])
    
    
  def tearDown(self):
    '''
    '''
    self._clean()
    # os.chdir('../../Plugin/src')
    # self._clean()
    os.chdir(self.lastCwd)


  def test_000_something(self):
    '''
    '''
    print('\n')
    
    # # build Plugin
    # os.chdir('./example/projects/Plugin/src')
    # self._build()
    # os.chdir('../../Main/src')
    
    # build Main (along with it's library dependencies)
    os.chdir('./example/projects/Main/src')
    self._build()
    
    exePath = '../Main'
    if platform.system() == 'Windows':
      exePath += '.exe'
    
    self.assertTrue(os.path.exists(exePath))
    
    p = subprocess.Popen([exePath], stdout = subprocess.PIPE, stderr = subprocess.PIPE)
    stdout, stderr = p.communicate()
    stdout = stdout.decode('utf-8')
    print(stdout)
    
    if len(stderr):
      raise Exception(stderr)
    
    self.assertTrue(stdout.startswith('running an executable and a statically linked library and a dynamically linked library'))
    # and a plugin'))
      
  # private  
  def _build(self):
    if platform.system() == 'Windows':
      pybythec.build(['', '-c', 'msvc110']) # TODO: check which version if any is installed
    else:
      pybythec.build([''])
    
  def _clean(self):
    if platform.system() == 'Windows':
      pybythec.cleanall(['', '-c', 'msvc110'])
    else:
      pybythec.cleanall([''])


if __name__ == '__main__':
  import sys
  sys.exit(unittest.main())

