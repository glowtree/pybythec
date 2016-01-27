#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import platform
import pybythec

if __name__ == '__main__':
  
  os.environ['PYBYTHEC_GLOBALS'] = '../.pybythecGlobals.json'
  
  if platform.system() == 'Linux':
    pybythec.build(sys.argv[1:] + ['-c', 'gcc', '-os', 'linux'])
  elif platform.system() == 'Darwin':
    pybythec.build(sys.argv[1:] + ['-c', 'clang', '-os', 'osx'])
  elif platform.system() == 'Windows':
    pybythec.build(sys.argv[1:] + ['-c', 'msvc', '-os', 'windows'])
  else:
    print('unknown platform / system')

