
import os
import shutil
import logging
import subprocess



# TODO: integrate this insteand of using output[] and results[]
class BuildStatus:
  '''
    contains the build status integer:
    0 - failed
    1 - built successfully
    2 - up-to-date or locked
    
    and a description of the build
  '''
  def __init__(self, result = 0, description = ''):
    self.result = result
    self.description = description

def writeBS(buildPath, status):
  '''
    write a tmp file that contains the build status information
    0 - failed
    1 - built successfully
    2 - up-to-date or locked
  '''
  bsPath = buildPath + '/buildStatus.txt'
  # log.debug('writing {}'.format(bsPath))
  tmpFile = open(bsPath, 'w')
  tmpFile.write(status)
  tmpFile.close()


def checkTimestamps(incPaths, src, timestamp):
  '''
    finds the newest timestamp of everything upstream of the src file, including the src file
  '''
  if not os.path.exists(src):
    s = 'does NOT exist: ' + src
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
  if compiler.startswith('gcc'):# or compiler.startswith('g++'):
    libPath += 'lib'
  libPath += libName + libExt
  return libPath


def srcNewer(srcPath, dstPath):
  if int(os.stat(srcPath).st_mtime) > int(os.stat(dstPath).st_mtime):
    return True
  return False

def getCmdLineArgs(args):
  '''
    returns a dictionary of options (flags) and arguments where each cmd line option starts with a '-'
    arguments that don't begin with a '-' get a numeric key begining with 1
  '''
  result = dict()
  key = str()
  nKey = 0
  keyFound = False
  for arg in args:
    
    if keyFound:
      result[key] = arg
      keyFound = False
      continue
    
    if arg[0] == '-':
      key = arg.lstrip('-')
      keyFound = True
    
    else:
      if nKey:
        result[nKey] = arg
      nKey += 1
    
  return result

def makePathAbsolute(absPath, path):
  '''
    make a relative file path absolute 
  '''
  if os.path.isabs(path):
    return path
  return os.path.normpath(os.path.join(absPath, './' + path))
    
def makePathsAbsolute(absPath, paths):
  
  i = 0
  for path in paths:
    paths[i] = makePathAbsolute(absPath, path)
    i += 1

def buildClean(dir, buildType = str(), binaryFormat = str(), compiler = str()):
  '''
    does a build clean on the specified directory
  '''
  pyExecPath = os.path.join(dir, '.build.py')
  
  if os.path.exists(pyExecPath):
    try:
      libProcess = subprocess.Popen('python {0} clean -d {1} -b {2} -bf {3} -c {4}'.format(pyExecPath, dir, buildType, binaryFormat, compiler), shell = True, stdin = subprocess.PIPE)
    except OSError as e:
      print(str(e))
      return
    libProcess.wait()


# 
# TODO: doesn't os.mkdirs do this???
#
def createDirs(path):
  '''
   recursively goes up the path heiarchy creating the necessary directories along the way
  '''
  
  if path == None or not len(path):
    print('createDirs: empty path')
    return
  
  # in case path ends with a '/'
  path = path.rstrip('/')
  
  if os.path.exists(path):
    return
  
  print('creating dir {0}'.format(path))

  # if the path above the current one doesn't exist, create it
  abovePath = os.path.dirname(path)
  if not os.path.exists(abovePath):
    createDirs(abovePath)

  os.mkdir(path)


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
  # TODO: use os.mkdirs
  # createDirs(dstDir)
  os.makedirs(dstDir)
    
  shutil.copy2(srcPath, dstDir)

  # print('{0} copied to {1}'.format(srcPath, dstPath))
      
  return True 
  

