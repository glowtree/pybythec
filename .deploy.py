
import os
import sys

os.system('bumpversion patch --allow-dirty')
os.system('sudo python setup.py sdist upload') # bdist_wheel

