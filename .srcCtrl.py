
import os
import sys
import subprocess

if len(sys.argv) < 2:
  print('pull or push required')
  sys.exit(1)

arg1 = sys.argv[1]
if arg1 == 'push':

  if len(sys.argv) < 3:
    print('message required')
    sys.exit(1)
  
  message = sys.argv[2]

  subprocess.call(['git', 'add', '-A'])
  subprocess.call(['git', 'commit', '-a', '-m', message])
  subprocess.call(['git', 'push'])

elif arg1 == 'pull':
  subprocess.call(['git', 'pull'])
    
else:
  print('pull or push required')

