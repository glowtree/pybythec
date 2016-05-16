
import sys
import platform
import subprocess

subprocess.call(['bumpversion', 'patch', '--allow-dirty'])

if platform.system() == 'Linux' or platform.system() == 'Darwin':
  subprocess.call(['sudo', 'python', 'setup.py', 'sdist', 'upload'])
else:
  subprocess.call(['python', 'setup.py', 'sdist', 'upload'])

if len(sys.argv) < 2:
    print('message required')
    sys.exit(1)

subprocess.call(['git', 'add', '-A'])
subprocess.call(['git', 'commit', '-a', '-m', sys.argv[1]])
subprocess.call(['git', 'push'])

