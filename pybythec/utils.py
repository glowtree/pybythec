from __future__ import print_function

import json
import shutil
import subprocess
import platform
import sys
import os


class PybythecError(Exception):
  def __init__(self, msg, *args):
    super(PybythecError, self).__init__(msg.format(*args))


def f(s, *args):
  '''
  '''
  # return s.format(*args)
  try:
    return s.format(*args)
  except Exception: # so far the only exception raised has been because of unicode chars  u'\u2018' and u'\u2019'
    newArgs = []
    for a in args:
      newArgs.append(a.replace(u'\u2018', '\'').replace(u'\u2019', '\''))
    return s.format(*newArgs)


class Logger:

  wf = None  # static

  def __init__(self, name = None, debug = False):
    self.name = name
    if self.name:
      self.name += ': '
    else:
      self.name = ''
    self._debug = debug

  def setDebug(self, v):
    self._debug = v

  @classmethod
  def setFilepath(cls, filepath):
    if filepath:
      cls.wf = open(filepath, 'w')

  def _getStr(self, s, *args):
    if type(s) is not str:
      s = f('{0}', s)
    if len(args):
      return self.name + f(s, *args)
    else:
      return self.name + s

  def debug(self, s, *args):
    if self._debug:
      print('debug: ' + self._getStr(s, *args), file = Logger.wf)
      if Logger.wf:
        Logger.wf.flush()  # necessary for running as a systemd service for some reason

  def info(self, s, *args):
    print(self._getStr(s, *args), file = Logger.wf)
    if Logger.wf:
      Logger.wf.flush()

  def warning(self, s, *args):
    print('warning: ' + self._getStr(s, *args), file = Logger.wf)
    if Logger.wf:
      Logger.wf.flush()

  def error(self, s, *args):
    lwf = Logger.wf
    if not lwf:
      lwf = sys.stderr
    print('error: ' + self._getStr(s, *args), file = lwf)
    if Logger.wf:
      Logger.wf.flush()

  def raw(self, s, *args):  # no adding the name
    if type(s) is not str:
      s = f('{0}', s)
    if len(args):
      print(f(s, *args))
    else:
      print(s)

  # shorthands
  def d(self, s, *args):
    self.debug(s, *args)

  def i(self, s, *args):
    self.info(s, *args)

  def w(self, s, *args):
    self.warning(s, *args)

  def e(self, s, *args):
    self.error(s, *args)

  def r(self, s, *args):
    self.raw(s, *args)


log = Logger('pybythec')


def srcNewer(srcPath, dstPath):
  if int(os.stat(srcPath).st_mtime) > int(os.stat(dstPath).st_mtime):
    return True
  return False


def checkTimestamps(incPaths, src, timestamp):
  '''
    finds the newest timestamp of everything upstream of the src file, including the src file
  '''
  if not os.path.exists(src):
    log.warning('checkTimestamps: {0} doesn\'t exist', src)
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
      if (filename[0] == '"'):
        filename = filename.strip('"')
        for dir in incPaths:
          filepath = os.path.join(dir, filename)
          if os.path.exists(filepath):
            checkTimestamps(incPaths, filepath, timestamp)


def sourceNeedsBuilding(incPaths, src, objTimestamp):
  '''
    determines whether a source file needs to be built or not
  '''
  timestamp = [0]  # [] so it's passed as a reference
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

def getPathDelineator():
  '''
  '''
  delin = ':'
  if platform.system() == 'Windows':
    delin = ';'
  return delin


def isWindowsPath(path):
  '''
    path: assume it's an absolute path ie C:/hi
  '''
  if len(path) < 3:
    return False
  if path[0].isalpha() and path[1] == ':' and path[2] == '/':
    return True
  return False


def windowsToLinux(p):
  '''
  '''
  np = p.replace('\\', '/')
  driveLetter = np[0].lower()
  return f'/mnt/{driveLetter}{np[2:]}'

  
def linuxToWindows(p):
  '''
  '''
  np = p.lstrip('/mnt/')
  return np[0].upper() + ':' + np[1:]


def pathExists(path):
  '''
  '''
  if not isWindowsPath(path):
    return os.path.exists(path)
  if platform.system() == 'Windows':
    return os.path.exists(path)
  return os.path.exists(windowsToLinux(path))
  

def getShellPath(path):
  '''
    path: assume absolute path
    returns the usable path for the current shell
  '''
  if not isWindowsPath(path):
    return path
  if platform.system() == 'Linux' or platform.system() == 'Darwin':
    return windowsToLinux(path)
  return path
    
def getShellOsType():
  '''
  '''
  if platform.system() == 'Linux':
    return 'linux'
  elif platform.system() == 'Darwin':
    return 'macOs'
  elif platform.system() == 'Windows':
    return 'windows'
  else:
    raise PybythecError('os needs to be linux, macOs or windows')

def _getAbsPath(cwDir, path):
  '''
  '''
  _cwDir = cwDir.replace('\\', '/')
  if not _cwDir.endswith('/'):
    _cwDir += '/'
  _path = path.replace('\\', '/')
  if len(path) < 2:
    if path[0] == '.':
      return _cwDir.rstrip('/')
  if _path[0] == '.' and path[1].isalpha(): # ie .pybythec
    return _cwDir + _path
  # TODO: handle the case when it's ./.pybythec
  return _cwDir + _path.lstrip('./\\')


def getAbsPath(cwDir, path):
  '''
    cwDir: current working dir path
    path: may be relative or absolute
    returns absolute path
  '''
  if isWindowsPath(path):
    return path
  if os.path.isabs(path):
    return path
  return _getAbsPath(cwDir, path)


def resolvePaths(cwDir, paths):
  '''
  '''
  i = 0
  for path in paths:
    paths[i] = getAbsPath(cwDir, path)
    i += 1


# def makePathAbsolute(absPath, path):
#   '''
#     make a relative file path absolute
#   '''
#   if os.path.isabs(path):
#     return path
#   return os.path.normpath(os.path.join(absPath, './' + path))


def createDirs(path):
  '''
   recursively goes up the path heiarchy creating the necessary directories along the way
   similar to os.makedirs except doesn't throw an exception if a directory's already exists
   also os.makedirs throws the same exception whether the directory already exists or it couldn't create it, not ideal
  '''
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
  except Exception: # OSError:
    # log.warning('failed to make {0} because {1}', path, e)
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
  createDirs(dstDir)

  shutil.copy2(srcPath, dstDir)

  log.debug('{0} copied to {1}', srcPath, dstPath)

  return True


def loadJsonFile(jsonPath):
  '''
    load a json config file
    NOTE: no check for existence of the path so that logging warnings can be controlled elsewhere
  '''
  if os.path.splitext(jsonPath)[1] != '.json':
    # raise PybythecError('{0} is not a json file', jsonPath)
    return None
  if not os.path.exists(jsonPath):
    raise PybythecError('{0} doesn\'t exist', jsonPath)
  try:
    with open(jsonPath) as f:
      return json.loads(removeComments(f))
  except Exception as e:
    raise PybythecError('failed to parse {0}: {1}', jsonPath, e)
    


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
    p = subprocess.Popen(cmd, stdout = subprocess.PIPE, stderr = subprocess.PIPE)
  except subprocess.CalledProcessError as e:
    return f('cmd failed: {0} because: {1}', ' '.join(cmd), e.output)
  except Exception:
    return f('cmd failed: {0}', ' '.join(cmd))
  stdout, stderr = p.communicate()
  output = ''
  if len(stderr):
    output += stderr.decode('utf-8')
  if len(stdout):
    output += stdout.decode('utf-8')
  return output


if __name__ == '__main__':

  print(getAbsPath('C:/Users/tom', '\Intel-HID-Event-Filter-Driver_V2HFM_WIN_2.2.1.384_A16_07.EXE', 'windows'))