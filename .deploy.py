
import os
import sys

if len(sys.argv) < 2:
  print('commit message needed')
  sys.exit(1)

# os.system('bumpversion patch --allow-dirty')
# os.system('python setup.py sdist bdist_wheel upload')
os.system('push ' + sys.argv[1])
