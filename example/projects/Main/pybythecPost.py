
from pybythec.utils import Logger
log = Logger('pybythecPost')

def run(be):
  '''
    override this function in your own pybythecPost.py, just make sure it's called run and has the single argument:
    be: build elements object, see BuildElements.py for all the member variables
  '''
  log.info(f'...post-build demonstration...\ntarget: {be.targetName}, install path: {be.installPath}\n')
