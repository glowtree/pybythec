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
from pybythec.utils import f

log = pybythec.utils.Logger('pybythecTest')

class TestPybythec(unittest.TestCase):
  
  def setUp(self):
    '''
      typical setup for building with pybythec
    '''
    # setup the environment variables...
    # normally you would probably set these in your .bashrc (linux / macOs), profile.ps1 (windows) file etc
    os.environ['PYBYTHEC_EXAMPLE_SHARED'] = '../../shared'
    
    self.builds = ['buildVar1', 'buildVar3'] # corresponds to build vartions declared in example/projects/Main/pybythec.json

    # make sure we have a .pybythecGlobals.json in the home directory
    globalsPath = os.path.expanduser('~') + '/.pybythecGlobals.json'
    if not os.path.exists(globalsPath):
      log.info('creating {0}', globalsPath)
      with open(globalsPath, 'w') as wf:
        with open('./globals.json') as rf:
          wf.write(rf.read())
    self.assertTrue(os.path.exists(os.path.expanduser('~') + '/.pybythecGlobals.json'))


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
    
    for b in self.builds:
      exePath = f('./{0}/Main', b)
      if platform.system() == 'Windows':
        exePath += '.exe'
      
      self.assertTrue(os.path.exists(exePath))
      
      p = subprocess.Popen([exePath], stdout = subprocess.PIPE, stderr = subprocess.PIPE)
      stdout, stderr = p.communicate()
      stdout = stdout.decode('utf-8')
      log.info(stdout)
      
      if len(stderr):
        raise Exception(stderr)
      
      self.assertTrue(stdout.startswith('running an executable and a statically linked library and a dynamically linked library'))# and a plugin'))


  def tearDown(self):
    '''
      clean the builds
    '''
    pybythec.cleanAll()
    
    os.chdir('../Plugin')
    pybythec.cleanAll()


if __name__ == '__main__':
  import sys
  sys.exit(unittest.main())
