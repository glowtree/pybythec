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
    os.environ['PYBYTHEC_GLOBALS'] = '../.pybythecGlobals.json'
    self.lastCwd = os.getcwd()
    os.chdir('./tests/src/exe')

  def tearDown(self):
    os.chdir(self.lastCwd)
  
  def test_000_something(self):
    
    print('\n')

    if platform.system() == 'Linux':
      pybythec.cleanall(['-c', 'gcc', '-os', 'linux']) 
      pybythec.build(['-c', 'gcc', '-os', 'linux'])
    elif platform.system() == 'Darwin':
      pybythec.cleanall(['-c', 'clang', '-os', 'osx']) 
      pybythec.build(['-c', 'clang', '-os', 'osx'])
    elif platform.system() == 'Windows':
      pybythec.cleanall(['-c', 'msvc100', '-os', 'windows']) 
      pybythec.build(['-c', 'msvc100', '-os', 'windows'])
    else:
      print('unknown operating system')
      return
      
    self.assertTrue(os.path.exists('./main'))
      
    p = subprocess.Popen(['./main'], stdout = subprocess.PIPE, stderr = subprocess.PIPE)
    stdout = p.communicate()[0].decode('utf-8')
    print(stdout)
    self.assertEqual(stdout, 'running exe and static electricity\n')
      
if __name__ == '__main__':
  import sys
  sys.exit(unittest.main())

