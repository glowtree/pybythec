#!/usr/bin/env python

import os
import sys
import pybythec

if __name__ == '__main__':
  
  os.environ['SHARED'] = '../../../shared'
  os.environ['PYBYTHEC_GLOBALS'] = '../../../shared/.pybythecGlobals.json'
  
  pybythec.build(sys.argv)
