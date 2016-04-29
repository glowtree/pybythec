#!/usr/bin/env python

import os
import sys
import pybythec

if __name__ == '__main__':
  
  os.environ['SHARED'] = '../../../shared'
  
  pybythec.build(sys.argv)
