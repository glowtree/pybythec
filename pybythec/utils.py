
import os
import json
import shutil
import logging
import subprocess

__author__ = 'glowtree'
__email__ = 'tom@glowtree.com'
__version__ = '0.9.10'

log = logging.getLogger('pybythec')


def srcNewer(srcPath, dstPath):
  if int(os.stat(srcPath).st_mtime) > int(os.stat(dstPath).st_mtime):
    return True
  return False


def checkTimestamps(incPaths, src, timestamp):
  '''
    finds the newest timestamp of everything upstream of the src file, including the src file
  '''
  if not os.path.exists(src):
    log.warning('checkTimestamps: {0} doesn\'t exist'.format(src))
    return

  srcTimeStamp = float(os.stat(src).st_mtime)
  if srcTimeStamp > timestamp[0]:
    timestamp[0] = srcTimeStamp

  fileCopy = str()
  srcFile = open(src, 'r')
  for line in srcFile:
    fileCopy += line
  srcFile.close()
  
  for line in fileCopy.split('\n'):
    if line.startswith('#include'):
      filename = line.lstrip('#include')
      filename = filename.strip()
      if(filename[0] == '"'):
        filename = filename.strip('"')
        for dir in incPaths:
          filepath = os.path.join(dir, filename)
          if os.path.exists(filepath):
            checkTimestamps(incPaths, filepath, timestamp)
     
     
def sourceNeedsBuilding(incPaths, src, objTimestamp):
  '''
    determines whether a source file needs to be built or not
  '''
  timestamp = [0] # [] so it's passed as a reference
  checkTimestamps(incPaths, src, timestamp)
  
  if timestamp[0] > objTimestamp:
    return True
    
  return False
  

def getLibPath(libName, libPath, compiler, libExt):
  '''
      get the lib path with the os / compiler specific prefix and file extension
  '''
  libPath += '/'
  if compiler.startswith('gcc') or compiler.startswith('clang'):
    libPath += 'lib'
  libPath += libName + libExt
  return libPath


def makePathAbsolute(absPath, path):
  '''
    make a relative file path absolute
  '''
  if os.path.isabs(path):
    return path
  return os.path.normpath(os.path.join(absPath, './' + path))
    

def createDirs(path):
  '''
   recursively goes up the path heiarchy creating the necessary directories along the way
  '''
  # if path == None or not len(path):
  if path is None or not len(path):
    log.warning('createDirs: empty path')
    return
  
  # in case path ends with a '/'
  path = path.rstrip('/')
  
  if os.path.exists(path):
    return
  
  # if the path above the current one doesn't exist, create it
  abovePath = os.path.dirname(path)
  if not os.path.exists(abovePath):
    createDirs(abovePath)

  try:
    os.mkdir(path)
  except OSError as e:
    # log.warning('failed to make {0} because {1}'.format(path, str(e)))
    pass
  

def copyfile(srcPath, dstDir):
  '''
    copies srcPath to dstPath, creating the directory structure if necessary for the destination
    srcPath: absolute file path
    dstDir:  absolute directory path
  '''
  
  if not os.path.exists(srcPath):
    return False

  dstPath = os.path.join(dstDir, os.path.basename(srcPath))

  if os.path.exists(dstPath):
    if not srcNewer(srcPath, dstPath):
      return

  # in case the path doesn't already exist
  # NOTE: os.mkdirs throws the same exception whether it couldn't create the directory or it was already there, therefor not ideal
  createDirs(dstDir)

  shutil.copy2(srcPath, dstDir)

  log.debug('{0} copied to {1}'.format(srcPath, dstPath))
      
  return True
  

def loadJsonFile(jsonPath):
  ''' 
    load a json config file
  '''
  
  if not os.path.exists(jsonPath):
    return None
  if os.path.splitext(jsonPath)[1] != '.json':
    log.warning('{0} is not json'.format(jsonPath))
    return None

  try:
    with open(jsonPath) as f:
      return json.loads(removeComments(f))
  except ValueError as e: # Exception as e:
    log.warning('failed to read {0} because {1}'.format(jsonPath, str(e)))
  return None


def removeComments(f):
  '''
    removes // style comments from a file, num of lines stays the same
  '''
  sansComments = ''
  inQuotes = False
  for l in f:
    i = 0
    for c in l:
      if c == '"':
        inQuotes = not inQuotes
      elif c == '/' and l[i + 1] == '/' and not inQuotes:
        sansComments += '\n'
        break
      i += 1
      sansComments += c
  return sansComments
  

def runCmd(cmd):
  ''' 
    runs a command and blocks until it's done, returns the output
  '''
  try:
    compileProcess = subprocess.Popen(cmd, stdout = subprocess.PIPE, stderr = subprocess.PIPE) 
  except OSError as e:
    return str(e)
  stdout, stderr = compileProcess.communicate()
  output = ''
  if len(stderr):
    output += stderr.decode('utf-8')
  if len(stdout):
    output += stdout.decode('utf-8')

  return output
