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
    # setup the environment variables...
    # normally you would probably set these in your .bashrc (linux / os x) or profile.ps1 (windows) file
    os.environ['SHARED'] = '../../shared'
    
    
  def test_000_something(self):
    '''
      build
    '''
    print('\n')

    # build Plugin
    os.chdir('./example/projects/Plugin')
    pybythec.build()
    
    # build Main (along with it's library dependencies)
    os.chdir('../Main')
    # pybythec.build()
    pybythec.build(['-ck', '2016'])
    
    # exePath = './Main'
    exePath = './2016/Main'
    if platform.system() == 'Windows':
      exePath += '.exe'
    
    self.assertTrue(os.path.exists(exePath))
    
    p = subprocess.Popen([exePath], stdout = subprocess.PIPE, stderr = subprocess.PIPE)
    stdout, stderr = p.communicate()
    stdout = stdout.decode('utf-8')
    print(stdout)
    
    if len(stderr):
      raise Exception(stderr)
    
    self.assertTrue(stdout.startswith('running an executable and a statically linked library and a dynamically linked library'))# and a plugin'))


  def tearDown(self):
    '''
      clean the builds
    '''
    # pybythec.cleanall()
    pybythec.cleanall(['-ck', '2016'])
    
    os.chdir('../Plugin')
    pybythec.cleanall()


if __name__ == '__main__':
  import sys
  sys.exit(unittest.main())

