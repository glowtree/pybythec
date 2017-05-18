
import logging
log = logging.getLogger('pybythecPost')

def run(be):
  '''
    override this function in your own pybythecPost.py, just make sure it's called run and has the single argument:
    be: build elements object, see BuildElements.py for all the member variables
  '''
  log.info('...post-build demonstration...\ntarget: {0}, install path: {1}\n'.format(be.target, be.installPath))
