
import os
import json
import logging
import platform
from pybythec import utils

log = logging.getLogger('pybythec')


class BuildElements:
  def __init__(self):
    self.target = ''
    self.binaryType = ''         # executable, static, dynamic, dynamicLib, dynamicMaya
    self.compiler = ''           # gcc-4.4 gcc clang msvc110 etc
    self.osType = ''             # linux, osx, windows
    self.binaryFormat = '64bit'  # 32bit, 64bit etc
    self.buildType = 'debug'     # debug, release etc

    self.libInstallPathAppend = True
    self.plusplus = True

    self.multithread = True
    
    self.locked = False
    
    self.installPath = '.build' # [] #
    
    self.sources = []
    self.libs    = []
    self.defines = []
    self.flags = []
    self.linkFlags = []
    
    self.incPaths = []
    self.libPaths = []
    self.libSrcPaths = []
    self.keys = []
    
    self.qtClasses = []
    
    
  def getBuildElements(self, configObj):
    if 'target' in configObj:
      self.target = configObj['target']
    
    if 'binaryType' in configObj:
      self.binaryType = configObj['binaryType']
    
    if 'compiler' in configObj:
      self.compiler = configObj['compiler']

    if 'osType' in configObj:
      self.osType = configObj['osType']
    
    if 'buildType' in configObj:
      self.buildType = configObj['buildType']
    
    if 'binaryFormat' in configObj:
      self.binaryFormat = configObj['binaryFormat']
    
    if 'libInstallPathAppend' in configObj:
      self.libInstallPathAppend = configObj['libInstallPathAppend']
    
    if 'plusplus' in configObj:
      self.plusplus = configObj['plusplus']
    
    if 'multithread' in configObj:
      self.multithread = configObj['multithread']
      
    if 'locked' in configObj:
      self.locked = configObj['locked']
      
      
  def setKeys(self):
    self.keys = ['all', self.compiler, self.osType, self.binaryType, self.buildType, self.binaryFormat]
    
    
  def getBuildElements2(self, configObj):
  
    separartor = ':'
    if platform.system() == 'Windows':
      separartor = ';'
    
    if 'bins' in configObj:
      bins = []
      self._getArgsList(bins, configObj['bins'])
      for bin in bins:
        os.environ['PATH'] = bin + separartor + os.environ['PATH']
    
    if 'sources' in configObj:
      self._getArgsList(self.sources, configObj['sources'])
    
    if 'libs' in configObj:
      self._getArgsList(self.libs, configObj['libs'])
    
    if 'defines' in configObj:
      self._getArgsList(self.defines, configObj['defines'])
      
    if 'flags' in configObj:
      self._getArgsList(self.flags, configObj['flags'])
      
    if 'linkFlags' in configObj:
      self._getArgsList(self.linkFlags, configObj['linkFlags'])
      
    if 'incPaths' in configObj:
      self._getArgsList(self.incPaths, configObj['incPaths'])
      
    if 'libPaths' in configObj:
      self._getArgsList(self.libPaths, configObj['libPaths'])

    if 'libSrcPaths' in configObj:
      self._getArgsList(self.libSrcPaths, configObj['libSrcPaths'])

    if 'qtClasses' in configObj:
      self._getArgsList(self.qtClasses, configObj['qtClasses'])

    if 'installPath' in configObj:
      installPaths = []
      self._getArgsList(installPaths, configObj['installPath'])
      if len(installPaths):
        self.installPath = installPaths[0]


  def goodToBuild(self):
    if not len(self.target):
      log.error('no target specified')
      return False
    elif not len(self.binaryType):
      log.error('no binary type specified')
      return False
    elif not len(self.compiler):
      log.error('no compiler specified')
      return False
    elif not len(self.osType):
      log.error('no os specified')
      return False
    elif not len(self.binaryFormat):
      log.error('no binary format specified')
      return False
    elif not len(self.buildType):
      log.error('no build type specified')
      return False
    elif not len(self.sources):
      log.error('no source files specified')
      return False
    return True


  def resolvePaths(self, absPath):
    self.installPath = utils.makePathAbsolute(absPath, os.path.expandvars(self.installPath))
    self._resolvePaths(absPath, self.sources)
    self._resolvePaths(absPath, self.incPaths)
    self._resolvePaths(absPath, self.libPaths)
    self._resolvePaths(absPath, self.libSrcPaths)


  def _resolvePaths(self, absPath, paths):
    i = 0
    for path in paths:
      paths[i] = utils.makePathAbsolute(absPath, os.path.expandvars(path))
      i += 1


  '''
    recursivley parses args and appends it to argsList if it has any of the keys
    args can be a dict, str (space-deliminated) or list
  '''
  def _getArgsList(self, argsList, args):
    if type(args).__name__ == 'dict':
      for key in self.keys:
        if key in args:
          self._getArgsList(argsList, args[key])
    else:
      if type(args).__name__ == 'str' or type(args).__name__ == 'unicode':
        args = args.split()
      if type(args).__name__ == 'list':
        for arg in args:
          argsList.append(arg)


class BuildStatus:
  '''
    contains the build status integer:
    0 - failed (default)
    1 - built successfully
    2 - up-to-date or locked
    
    and a description of the build
  '''
  def __init__(self, path = '', result = 0, description = ''):
    self.path = path
    self.result = result
    self.description = description
    
  def readFromFile(self, buildPath):
    contents = utils.loadJsonFile(buildPath + '/.pybythecStatus.json')
    if not contents:
      self.description = 'couldn\'t find build status in ' + buildPath
      log.error('couldn\'t find build status in ' + self.description)
      return
    if 'result' in contents:
      self.result = contents['result']
    else:
      self.description = 'couldn\'t find the build status in ' + buildPath
      log.error(self.description)
    if 'description' in contents:
      self.description = contents['description']
    else:
      self.description = buildPath + ' doesn\'t contain a description'
      log.warning(self.description)

  def writeInfo(self, status, msg):
    log.info(msg)
    self.result = status
    self.description = msg
    self._writeToFile()
    
  def writeError(self, msg):
    log.error(msg)
    self.description = msg
    self._writeToFile()

  def _writeToFile(self):
    if not os.path.exists(self.path):
      return
    with open(self.path + '/.pybythecStatus.json', 'w') as f:
      json.dump({'result': self.result, 'description': self.description}, f, indent = 4)

