#!/usr/bin/env python

import os
import sys
import platform
import pybythec

if __name__ == '__main__':
  
  os.environ['SHARED'] = '../../../shared'
  os.environ['PYBYTHEC_GLOBALS'] = '../../../shared/.pybythecGlobals.json'
  
  if platform.system() == 'Linux':
    pybythec.build(sys.argv + ['-c', 'g++', '-os', 'linux'])
  elif platform.system() == 'Darwin':
    pybythec.build(sys.argv + ['-c', 'clang++', '-os', 'osx'])
  elif platform.system() == 'Windows':
    pybythec.build(sys.argv + ['-c', 'msvc110', '-os', 'windows'])
  else:
    print('unknown platform / system')
