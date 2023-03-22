

name = 'pybythec'

description = 'c++ build system written in python'

authors = [
  'Tom Sirdevan'
]

requires = [
  'gcc',
  'python'
]

def commands():

    env.PYBYTHEC_GLOBALS = '{root}/.pybythecGlobals.json'
    env.PYBYTHEC_CMD = '{root}/python/pybythec/command_line.py'
    env.PYTHONPATH.append('{root}/python')
    


with scope('config') as config:
    config.release_packages_path = '/mnt/rez/release/int'
    config.release_as = 'int'