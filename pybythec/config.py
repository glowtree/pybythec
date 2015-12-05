
import os
import logging
import json
from jsmin import jsmin
import platform

logging.basicConfig(level = logging.DEBUG, format = '%(message)s') # DEBUG INFO
log = logging.getLogger('pybythec')


''' load a json config file '''
def loadJsonFile(jsonPath):
  if not os.path.exists(jsonPath):
    return
  if os.path.splitext(jsonPath)[1] != '.json':
    log.warning('{0} is not json'.format(jsonPath))
    return

  with open(jsonPath) as f:
    minifiedJsonStr = jsmin(f.read())
    if len(minifiedJsonStr):
      cf = json.loads(minifiedJsonStr)
      return cf
  return None

class BuildElements:
  def __init__(self):
    self.target = ''
    self.binaryType = ''    # executable, static, dynamic, dynamicLib, dynamicMaya
    self.compiler = ''      # gcc-4.4 gcc clang msvc110 etc
    self.osType = ''        # linux, osx, windows
    self.binaryFormat = ''  # 32bit, 64bit etc
    self.buildType = ''     # debug, release etc
    self.usePlusPlus = True 
    self.locked = False
    self.defines = ''
    self.flags = ''    # executable, static, dynamic, dynamicLib, dynamicMaya
    self.linkFlags = ''      # gcc-4.4 gcc clang msvc110 etc
    self.incPaths = ''        # linux, osx, windows
    self.libPaths = ''  # 32bit, 64bit etc
    self.pathSeparator = ''     # debug, release etc
    self.keys = []
    
  def getBuildElements(self, configObj):
    if 'target' in configObj:
      buildElements.target = configObj['target']
    if 'binaryType' in configObj:
      buildElements.binaryType = configObj['binaryType']
    if 'compiler' in configObj:
      buildElements.compiler = configObj['compiler']
    if 'osType' in configObj:
      buildElements.osType = configObj['osType']
    if 'buildType' in configObj:
      buildElements.buildType = configObj['buildType']
    if 'binaryFormat' in configObj:
      buildElements.binaryFormat = configObj['binaryFormat']
    if 'locked' in configObj:
      buildElements.locked = configObj['locked']
    if 'usePlusPlus' in configObj:
      buildElements.usePlusPlus = configObj['usePlusPlus']
  
  def goodToBuild(self):
    if not len(self.target):
      log.error('no target specified')
      return False
    elif not len(self.binaryType):
      log.error('no specified')
      return False
    elif not len(self.compiler):
      log.error('no compiler specified')
      return False
    elif not len(self.osType):
      log.error('no osType specified')
      return False
    elif not len(self.binaryFormat):
      log.error('no binaryFormat specified')
      return False
    elif not len(self.buildType):
      log.error('no buildType specified')
      return False
    return True
  
  def setKeys(self):
    self.keys = ['all', self.compiler, self.osType, self.binaryType, self.buildType, self.binaryFormat]
    self.defines.append('_' + be.binaryFormat.upper())
  
  
  # TODO: include multithreaded
  def getBuildElements2(self, configObj):
  
    separartor = ':'
    elif platform.system() == 'Windows':
      separartor = ';'
    
    if 'bins' in configObj: 
      bins = []
      _getArgsList(bins, configObj['bins'], keys)
      for bin in bins: 
        os.environ['PATH'] = bin + pathSeparator + os.environ['PATH']
    
    if 'defines' in configObj:
      _getArgsList(be.defines, configObj['defines'])
      
    if 'flags' in configObj: 
      _getArgsList(be.flags, configObj['flags'])
      
    if 'linkFlags' in configObj: 
      _getArgsList(be.linkFlags, configObj['linkFlags'])
      
    if 'includes' in configObj:   
      _getArgsList(be.incPaths, configObj['includes'])
      
    if 'libs' in configObj: 
      _getArgsList(be.libPaths, configObj['libs'])


  '''
    recursivley parses args and appends it to argsList if it has any of the keys
    args can be a dict, str (space-deliminated) or list
  '''
  def _getArgsList(self, argsList, args):
    if type(args).__name__ == 'dict':
      for key in self.keys:
        if key in args:
          _getArgsList(argsList, args[key])
    else:
      if type(args).__name__ == 'unicode':
        args = args.encode('ascii', 'ignore')
      if type(args).__name__ == 'str':
        args = args.split()
      if type(args).__name__ == 'list':
        for arg in args:
          argsList.append(arg)
