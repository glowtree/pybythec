#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
test_pybythec
----------------------------------

Tests for `pybythec` module.
"""

# import sys
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
    
    if platform.system() == 'Linux':
      pybythec.build(['-c', 'gcc', '-os', 'linux'])
      os.system('./main')
    elif platform.system() == 'Darwin':
      os.system('./main')
    elif platform.system() == 'Windows':
      os.system('./main.exe')
    else:
      print('unknown operating system')
       
if __name__ == '__main__':
  import sys
  sys.exit(unittest.main())

