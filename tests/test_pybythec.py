#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
test_pybythec
----------------------------------

Tests for `pybythec` module.
"""

import os
import platform
import unittest
import subprocess
import pybythec

class TestPybythec(unittest.TestCase):
  
  def setUp(self):
    os.environ['PYBYTHEC_GLOBALS'] = './src/.pybythecGlobals.json'
    self.lastCwd = os.getcwd()
    os.chdir('./tests/src/exe')

  def tearDown(self):
    os.chdir(self.lastCwd)
  
  def test_000_something(self):
    
    print('\n')
    pybythec.build(['-cla']) # clean all
    
    if platform.system() == 'Linux':
      pybythec.build(['-c', 'gcc', '-os', 'linux'])
      exe = './main'
    elif platform.system() == 'Darwin':
      pybythec.build(['-c', 'clang', '-os', 'osx'])
      exe = './main'
    elif platform.system() == 'Windows':
      pybythec.build(['-c', 'msvc', '-os', 'windows'])
      exe = './main.exe'
    else:
      print('unknown operating system')
      return
      
    p = subprocess.Popen([exe], stdout = subprocess.PIPE, stderr = subprocess.PIPE)
    stdout = p.communicate()[0].decode('utf-8')
    print(stdout)
    self.assertEqual(stdout, 'running exe and static electricity\n')
      
if __name__ == '__main__':
  import sys
  sys.exit(unittest.main())

