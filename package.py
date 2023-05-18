

name = 'pybythec'

description = 'c++ build system written in python'

authors = [
  'Tom Sirdevan'
]

requires = [
#   'gcc',
  'python'
]

def commands():
    env.PYBYTHEC_GLOBALS = '{root}/.pybythecGlobals.json'
    env.PYTHONPATH.append('{root}/python')
    command('source /opt/rh/devtoolset-6/enable')
    
with scope('config') as c:
    release_as = 'int'
    import os
    if release_as == 'int':
        c.release_packages_path = os.environ['SSE_REZ_REPO_RELEASE_INT']
    elif release_as == 'ext':
        c.release_packages_path = os.environ['SSE_REZ_REPO_RELEASE_EXT']