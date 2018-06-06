
import os
from pybythec.utils import Logger

log = Logger()

def main():
  '''
    to be called when globals.json is modified
    rebuilds setup.py with globals.json baked in for installations, and attempts to deploy globals.json to ~/.pybythecGlobals.json for testing
  '''

  #
  # rebuild setup.py
  #
  log.info('rebuilding setup.py')
  with open('./setup.py', 'w') as wf:
    wf.write(
'''
import os
from setuptools import setup
from setuptools.command.install import install as baseInstall
''')

    with open('./globals.json') as grf:
      wf.write('\npybythecGlobals = \'\'\'\n')
      wf.write(grf.read())
      wf.write('\'\'\'\n')

    wf.write(
'''
class installer(baseInstall):

  def run(self):
    globalsPath = os.path.expanduser('~') + '/.pybythecGlobals.json'
    print('installing ' + globalsPath)
    with open(globalsPath, 'w') as f:
      f.write(pybythecGlobals)
    baseInstall.run(self)


description = 'A lightweight cross-platform build system for c/c++, written in python'

setup(
    name = 'pybythec',
    version = '0.9.41',
    author = 'glowtree',
    author_email = 'tom@glowtree.com',
    url = 'https://github.com/glowtree/pybythec',
    description = description,
    long_description = str(open('README.rst', 'r').read()).replace(description, ''),
    packages = ['pybythec'],
    entry_points = {
        'console_scripts': ['pybythec=pybythec.command_line:main'],
    },
    license = 'LICENSE',
    test_suite = 'test',
    cmdclass = {'install': installer}
)
''')

    #
    # create / attempt to replace ~/.pybythecGlobals.json
    #
    globalsPath = os.path.expanduser('~') + '/.pybythecGlobals.json'
    try:
      log.info('writing to {0}', globalsPath)
      with open(globalsPath, 'w') as wf:
        with open('./globals.json') as rf:
          wf.write(rf.read())
    except Exception:
      log.error('failed to write to {0}', globalsPath)


if __name__ == '__main__':
  main()
