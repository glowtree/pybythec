# -*- coding: utf-8 -*-

from pybythec import main
import logging
logging.basicConfig(level = logging.DEBUG, format = '%(message)s') # DEBUG INFO

__author__ = 'glowtree'
__email__ = 'tom@glowtree.com'
__version__ = '0.1.0'

# wrapper functions to be used by the outside world
def build(argv):
  main.build(argv)

def clean(argv):
  main.clean(argv)
  
def cleanall(argv):
  main.cleanall(argv)

