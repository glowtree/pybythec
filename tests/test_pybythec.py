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
import pybythec

class TestPybythec(unittest.TestCase):
  
  def setUp(self):
    self.lastCwd = os.getcwd()
    os.chdir('./tests/exe')
  
  def tearDown(self):
    os.chdir(self.lastCwd)
  
  def test_000_something(self):
    
    pybythec.build(['-cla']) # clean all
    
    if platform.system() == 'Linux':
      pybythec.build(['-c', 'gcc', '-os', 'linux'])
      # os.system('./main')
    elif platform.system() == 'Darwin':
      pybythec.build(['-c', 'clang', '-os', 'osx'])
      os.system('./main')
    elif platform.system() == 'Windows':
      pybythec.build(['-c', 'msvc', '-os', 'windows'])
      os.system('./main.exe')
    else:
      print('unknown operating system')
       
if __name__ == '__main__':
  import sys
  sys.exit(unittest.main())

