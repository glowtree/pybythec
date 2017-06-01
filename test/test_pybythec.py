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
    os.environ['PYBYTHEC_EXAMPLE_SHARED'] = '../../shared'
    
    self.builds = ['2015', '2017'] # corresponds to what was declared in example/projects/Main/pybythec.json

    
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
    pybythec.build()
    # pybythec.build(builds = self.builds)
    
    for b in self.builds:
      # exePath = './Main'
      exePath = './{0}/Main'.format(b)
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
    pybythec.cleanAll(builds = self.builds)
    
    os.chdir('../Plugin')
    pybythec.cleanAll()


if __name__ == '__main__':
  import sys
  sys.exit(unittest.main())
