# -*- coding: utf-8 -*-

from pybythec import main
import logging

# DEPLOY
logging.basicConfig(level = logging.INFO, format = '%(name)s: %(levelname)s: %(message)s')

# wrapper functions to be used by the outside world
def build(argv = []):
  main.build(argv)

def clean(argv = []):
  main.clean(argv)
  
def cleanall(argv = []):
  main.cleanall(argv)
