#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
test_pybythec
----------------------------------

tests for pybythec module
'''

import os
import unittest
import subprocess
import pybythec

log = pybythec.utils.log


class TestPybythec(unittest.TestCase):
    def setUp(self):
        '''
            typical setup for building with pybythec
        '''

        # setup the environment variables...
        # normally you would probably set these in your .bashrc (linux / macOs), profile.ps1 (windows) file etc
        cwd = os.getcwd()
        cwd = cwd.replace('\\', '/')
        os.environ['PYBYTHEC_EXAMPLE_SHARED'] = cwd + '/example/shared'
        os.environ['PYBYTHEC_GLOBALS'] = cwd + '/globals.json'  # this overrides ~/.pybythecGlobals

    def test_000_something(self):
        '''
            build
        '''
        # print('\n')
        log.raw('\n')
        log.info(f'cwd: {os.getcwd()}')

        # build Plugin
        log.raw('\n')
        os.chdir('./example/projects/Plugin')
        pybythec.build()
        log.raw('\n')

        # build Main (along with it's library dependencies)
        log.raw('\n')
        os.chdir('../Main')
        be = pybythec.getBuildElements()
        pybythec.build(be)
        log.raw('\n')

        for b in be.builds:

            # log.debug(b)
            # continue

            exePath = f'./{b}/Main'
            if be.osType == 'windows':
                exePath += '.exe'

            log.info(f'checking that {exePath} exists...')
            self.assertTrue(os.path.exists(exePath))

            p = subprocess.Popen([exePath], stdout = subprocess.PIPE, stderr = subprocess.PIPE)
            stdout, stderr = p.communicate()
            stdout = stdout.decode('utf-8')
            log.info(stdout)

            if len(stderr):
                raise Exception(stderr)

            self.assertTrue(
                stdout.startswith('running an executable and a statically linked library and a dynamically linked library'))  # and a plugin'))
            
            log.raw('\n')

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
