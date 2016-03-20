
import os
import sys


os.system('bumpversion patch --allow-dirty')
os.system('sudo python setup.py sdist upload') # bdist_wheel


# if len(sys.argv) < 2:
#   print('commit message needed')
#   sys.exit(1)

# os.system('push ' + sys.argv[1])
