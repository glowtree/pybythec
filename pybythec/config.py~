
'''
  recursivley parses args and appends it to argsList if it has any of the keys
  args can be a dict, str (space-deliminated), list, or tuple (of strings)
'''
def getArgsList(argsList, args, keys):
  if type(args).__name__ == 'dict':
    for key in keys:
      if key in args:
        getArgsList(argsList, args[key], keys)
  else:
    if type(args).__name__ == 'unicode':
      args = args.encode('ascii', 'ignore')
    if type(args).__name__ == 'str':
      args = args.split()
    if type(args).__name__ == 'list' or type(args).__name__ == 'tuple':
      for arg in args:
        argsList.append(arg)

class BuildElements:
  def __init__(self):
    self.target = ''
    self.binaryType = ''    # executable, static, dynamic, dynamicLib, dynamicMaya
    self.compiler = ''      # gcc-4.4 gcc clang msvc110 etc
    self.osType = ''        # linux, osx, windows
    self.binaryFormat = ''  # 32bit, 64bit etc
    self.buildType = ''     # debug, release etc
    self.locked = False
    
  def goodToBuild():
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

''' load a json config file '''
def loadJsonFile(jsonPath);
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

''' TODO: these need better names '''
def getConfig1(configObj, buildElements):
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
  
# TODO: include multithreaded
def getConfig2(configObj, keys, defines, flags, linkFlags, incPaths, libPaths, pathSeparator):

  if 'bins' in configObj: 
    bins = []
    getArgsList(bins, configObj['bins'], keys)
    for bin in bins: 
      os.environ['PATH'] = bin + pathSeparator + os.environ['PATH']
  
  if 'defines' in configObj:
    getArgsList(defines, configObj['defines'], keys)
    
  if 'flags' in configObj: 
    getArgsList(flags, configObj['flags'], keys)
    
  if 'linkFlags' in configObj: 
    getArgsList(linkFlags, configObj['linkFlags'], keys)
    
  if 'includes' in configObj:   
    getArgsList(incPaths, configObj['includes'], keys)
    
  if 'libs' in configObj: 
    getArgsList(libPaths, configObj['libs'], keys)   
