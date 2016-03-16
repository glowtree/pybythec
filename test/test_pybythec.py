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
    
    #
    # setup the environment variables used in the build
    #
    os.environ['SHARED'] = '../../../shared'
    os.environ['PYBYTHEC_GLOBALS'] = '{0}/.pybythecGlobals.json'.format(os.environ['SHARED'])
    
    
  def tearDown(self):
    '''
    '''
    self._clean()
    os.chdir('../../Plugin/src')
    self._clean()
    os.chdir(self.lastCwd)


  def test_000_something(self):
    '''
    '''
    print('\n')
    
    # build Plugin
    os.chdir('./example/projects/Plugin/src')
    self._build()
    
    # build Main (along with it's library dependencies)
    os.chdir('../../Main/src')
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
    
    self.assertTrue(stdout.startswith('running an executable and a statically linked library and a dynamically linked library\r\n and a plugin'))


  # private  
  def _build(self):
    pybythec.build(['']) # TODO: shouldn't have to enter an empty list
    
  def _clean(self):
    pybythec.cleanall([''])


if __name__ == '__main__':
  import sys
  sys.exit(unittest.main())

