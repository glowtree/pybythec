#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
test_pybythec
----------------------------------

tests for pybythec module
'''

import os
import platform
import unittest
import subprocess
import pybythec
from pybythec.utils import f

log = pybythec.utils.Logger()


class TestPybythec(unittest.TestCase):

  def setUp(self):
    '''
      typical setup for building with pybythec
    '''

    # setup the environment variables...
    # normally you would probably set these in your .bashrc (linux / macOs), profile.ps1 (windows) file etc
    os.environ['PYBYTHEC_EXAMPLE_SHARED'] = os.getcwd() + '/example/shared'
    os.environ['PYBYTHEC_GLOBALS'] = os.getcwd() + '/globals.json'  # this overrides ~/.pybythecGlobals

  def test_000_something(self):
    '''
      build
    '''
    print('\n')

    # build Plugin
    os.chdir('./example/projects/Plugin')
    pybythec.build()

    # build Main (along with it's library dependencies)
    os.chdir('../Main')

    be = pybythec.getBuildElements()

    pybythec.build(be)

    for b in be.builds:
      exePath = f('./{0}/Main', b)
      if platform.system() == 'Windows':
        exePath += '.exe'

      self.assertTrue(os.path.exists(exePath))

      p = subprocess.Popen([exePath], stdout = subprocess.PIPE, stderr = subprocess.PIPE)
      stdout, stderr = p.communicate()
      stdout = stdout.decode('utf-8')
      log.info(stdout)

      if len(stderr):
        raise Exception(stderr)

      self.assertTrue(stdout.startswith('running an executable and a statically linked library and a dynamically linked library'))  # and a plugin'))

  def tearDown(self):
    '''
      clean the builds
    '''
    pybythec.cleanAll()

    os.chdir('../Plugin')
    pybythec.cleanAll()


if __name__ == '__main__':
  import sys
  sys.exit(unittest.main())
