
import os
import sys
import subprocess

# os.system('bumpversion patch --allow-dirty')
# os.system('sudo python setup.py sdist upload') # bdist_wheel

if len(sys.argv) < 2:
  print('commit message needed')
  sys.exit(1)

  subprocess.call(['git', 'add', '-A'])
  subprocess.call(['git', 'commit', '-a', '-m', sys.argv[1]])
  subprocess.call(['git', 'push'])
  
