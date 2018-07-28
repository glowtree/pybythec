import os
import platform
import subprocess
from pybythec import utils
from pybythec.utils import f
from pybythec.utils import PybythecError

log = utils.Logger('pybythec')


class BuildElements:

  def __init__(self,
               osType = None,
               compiler = None,
               buildType = None,
               binaryFormat = None,
               projConfigPath = None,
               globalConfigPath = None,
               projConfig = None,
               globalConfig = None,
               currentBuild = None,
               libDir = None
               ):
    '''
      osType: operating system: currently linux, macOs, or windows
      compiler: any variation of gcc, clang, or msvc ie gcc-4.4, msvc110, if plusplus is true gcc, clang will become g++, clang++
      buildType: debug release etc
      binaryFormat: 32bit, 64bit etc
      projConfigPath: path to a pybythec project config file (json)
      globalConfigPath: path to a pybythec global config file (json)
      projConfig: dict of the project config
      globalConfig: dict of the global config
      libDir: directory path of the library being built, likely only used when building a library as a dependency (ie from a project)
      currentBuild: current build from a potential list of custom builds, passed in when building library dependencies
      parses config files: global, project, local if they exist to determine build elements (state), uses function arguments as overrides
    '''

    self.localConfig = None
    self.projConfig = projConfig
    self.globalConfig = globalConfig
    self.currentBuild = currentBuild # current custom build if any
    self.libDir = libDir
    
    # overrides config files
    self.osTypeOverride = osType
    self.compilerOverride = compiler
    self.buildTypeOverride = buildType
    self.binaryFormatOverride = binaryFormat
    
    self.buildType = None
    self.version = None
    self.targetName = None # name of the target
    self.targetFilename = None # name of the target + extension
    self.builds = None  # a list of custom build keys
    
    self.osType = None  # linux, macOs, windows
    self.binaryType = None  # exe, static, dynamic, plugin
    
    self.version = 0
    self.binaryFormat = None # 32bit, 64bit etc
    self.libInstallPathAppend = True
    self.plusplus = True
    self.locked = False
    self.buildDir = '.'
    self.showCompilerCmds = False
    self.showLinkerCmds = False

    self.copyDynamicLibs = True

    self.msvcDefault = None

    self.cwDir = os.getcwd()
    if self.libDir:
      self.cwDir = self.libDir

    self.latestConfigTimestamp = 0

    # global config
    if not self.globalConfig:
      if 'PYBYTHEC_GLOBALS' in os.environ:
        globalConfigPath = os.environ['PYBYTHEC_GLOBALS']
        if not os.path.exists(globalConfigPath):
          globalConfigPath = None
          log.warning('PYBYTHEC_GLOBALS points to {0}, which doesn\'t exist', globalConfigPath)
      elif os.path.exists('.pybythecGlobals.json'):
        globalConfigPath = '.pybythecGlobals.json'
      elif os.path.exists('pybythecGlobals.json'):
        globalConfigPath = 'pybythecGlobals.json'
      else: # check the home directory
        homeDirPath = os.path.expanduser('~')
        if os.path.exists(homeDirPath + '/.pybythecGlobals.json'):
          globalConfigPath = homeDirPath + '/.pybythecGlobals.json'
        elif os.path.exists(homeDirPath + '/pybythecGlobals.json'):
          globalConfigPath = homeDirPath + '/pybythecGlobals.json'
        else: # end of the line
          log.warning('no pybythecGlobals.json found in the home directory (hidden or otherwise)')
      if globalConfigPath and os.path.exists(globalConfigPath):
        self.globalConfig = utils.loadJsonFile(globalConfigPath)
        self.latestConfigTimestamp = float(os.stat(globalConfigPath).st_mtime)    

    # project config
    if not self.projConfig:
      if 'PYBYTHEC_PROJECT' in os.environ:
        projConfigPath = os.environ['PYBYTHEC_PROJECT']
        if not os.path.exists(projConfigPath):
          log.warning('PYBYTHEC_PROJECT points to {0}, which doesn\'t exist', projConfigPath)
      else:
        if os.path.exists(self.cwDir + '/pybythecProject.json'):
          projConfigPath = self.cwDir + '/pybythecProject.json'
        elif os.path.exists(self.cwDir + '/.pybythecProject.json'):
          projConfigPath = self.cwDir + '/.pybythecProject.json'
      if projConfigPath and os.path.exists(projConfigPath):
        self.projConfig = utils.loadJsonFile(projConfigPath)
        projConfigTs = float(os.stat(projConfigPath).st_mtime)
        if projConfigTs > self.latestConfigTimestamp:
          self.latestConfigTimestamp = projConfigTs

    # local config, expected to be in the current working directory
    self.localConfig = None
    localConfigPath = self.cwDir + '/pybythec.json'
    if not os.path.exists(localConfigPath):
      localConfigPath = self.cwDir + '/.pybythec.json'
    if os.path.exists(localConfigPath):
      localConfigTs = float(os.stat(localConfigPath).st_mtime)
      if localConfigTs > self.latestConfigTimestamp:
        self.latestConfigTimestamp = localConfigTs
      self.localConfig = utils.loadJsonFile(localConfigPath)

    #
    # first iteration to get osType and custom keys (right now just for the compiler)
    #
    if self.globalConfig is not None:
      self._getBuildElements1(self.globalConfig)
    else:
      log.warning('not using a global configuration')
    if self.projConfig is not None:
      self._getBuildElements1(self.projConfig)
    if self.localConfig is not None:
      self._getBuildElements1(self.localConfig)
    else:
      log.warning('not using a local pybythec configuration')

    self.targetFilename = self.targetName

    if self.osTypeOverride:
      self.osType = self.osTypeOverride

    if self.osType:
      if self.osType not in ['linux', 'macOs', 'windows']: # validate
        log.warning('{0} invalid osType, defaulting to the native os', self.osType)
        self.osType = None
    if not self.osType: # use the native os
      if platform.system() == 'Linux':
        self.osType = 'linux'
      elif platform.system() == 'Darwin':
        self.osType = 'macOs'
      elif platform.system() == 'Windows':
        self.osType = 'windows'
      else:
        raise PybythecError('os needs to be linux, macOs or windows')


  def configBuild(self, currentBuild = None):
    '''
    '''
    if currentBuild:
      self.currentBuild = currentBuild
      os.environ['PYBYTHEC_BUILDVAR'] = self.currentBuild

    # set by the config files first
    self.compiler = None  # g++-4.4 g++ clang++ msvc-11.0 etc
    self.filetype = None  # elf, mach-o, pe
    self.installPath = None
  
    self.sources = []
    self.libs = []
    self.defines = []
    self.flags = []
    self.linkFlags = []

    self.incPaths = []
    self.extIncPaths = []  # these will not be checked for timestamps
    self.libPaths = []
    self.libSrcPaths = []

    self.qtClasses = []


    # 2 keys at this point for a potentially nested compiler: osType and currentBuild
    keys = [self.osType]
    if self.currentBuild:
      keys.append(self.currentBuild)

    #
    # second iteration to get the other configs that can't be nested (the compiler being the exception)
    #
    if self.globalConfig is not None:
      self._getBuildElements2(self.globalConfig, keys)
    if self.projConfig is not None:
      self._getBuildElements2(self.projConfig, keys)
    if self.localConfig is not None:
      self._getBuildElements2(self.localConfig, keys)

    # compiler stuff
    if self.compilerOverride:
      self.compiler = self.compilerOverride

    if not self.compiler:
      raise PybythecError('compiler not found')

    # validate compiler and determine root: can be gcc, clang or msvc
    self.compilerRoot = None
    if self.compiler.startswith('gcc') or self.compiler.startswith('g++'):
      self.compilerRoot = 'gcc'
    elif self.compiler.startswith('clang') or self.compiler.startswith('clang++'):
      self.compilerRoot = 'clang'
    elif self.compiler.startswith('msvc'):
      self.compilerRoot = 'msvc'
      if self.compiler == 'msvc': # needs a version ie msvc-11.0 for pathing
        if self.msvcDefault:
          self.compiler = self.msvcDefault
        else:
          raise PybythecError('msvc has no default set, try setting the compiler to a specific version ie msvc-14.0')
    else:
      raise PybythecError('unrecognized compiler {0}, using the default based on osType', self.compiler)


    if self.buildTypeOverride:
      self.buildType = self.buildTypeOverride

    if self.binaryFormatOverride:
      self.binaryFormat = self.binaryFormatOverride

    keys += ['all', self.compilerRoot, self.compiler, self.binaryType, self.buildType, self.binaryFormat]

    if self.globalConfig is not None:
      self._getBuildElements3(self.globalConfig, keys)
    if self.projConfig is not None:
      self._getBuildElements3(self.projConfig, keys)
    if self.localConfig is not None:
      self._getBuildElements3(self.localConfig, keys)

    # deal breakers (that don't appear in the default pybythecGlobals.json)
    if not self.targetName:
      raise PybythecError('no target specified')
    if not self.binaryType:
      raise PybythecError('no binary type specified')
    if self.binaryType not in ('exe', 'static', 'dynamic', 'plugin'):
      raise PybythecError('unrecognized binary type: ' + self.binaryType)
    if not self.sources:
      raise PybythecError('no source files specified')


    #
    # compiler config
    #
    self.compilerCmd = None
    self.linker = None
    self.targetFlag = None
    self.libFlag = None
    self.libPathFlag = None
    self.objExt = None
    self.objPathFlag = None
    self.staticExt = None
    self.dynamicExt = None
    self.pluginExt = None
    self.compilerVersion = None

    #
    # gcc / clang
    #
    if self.compilerRoot == 'gcc' or self.compilerRoot == 'clang':
      if self.plusplus:
        if self.compiler.startswith('gcc'):
          self.compiler = self.compiler.replace('gcc', 'g++')
        elif self.compiler.startswith('clang-') or self.compiler == ('clang'):
          self.compiler = self.compiler.replace('clang', 'clang++')
        
      self.compilerCmd = self.compiler
      self.objFlag = '-c'
      self.objExt = '.o'
      self.objPathFlag = '-o'
      self.defines.append('_' + self.binaryFormat.upper())  # TODO: you sure this is universal?

      # link
      self.linker = self.compilerCmd  # 'ld'
      self.targetFlag = '-o'
      self.libFlag = '-l'
      self.libPathFlag = '-L'
      self.staticExt = '.a'
      self.dynamicExt = '.so'
      self.pluginExt = '.so'

      if self.filetype == 'mach-o':
        self.dynamicExt = '.dylib'
        self.pluginExt = '.bundle'

      if self.binaryType == 'static' or self.binaryType == 'dynamic':
        self.targetFilename = 'lib' + self.targetName

      if self.binaryType == 'exe':
        pass
      elif self.binaryType == 'static':
        self.targetFilename = self.targetFilename + '.a'
        self.linker = 'ar'
        self.targetFlag = 'r'
      elif self.binaryType == 'dynamic':
        self.targetFilename = self.targetFilename + self.dynamicExt
      elif self.binaryType == 'plugin':
        self.targetFilename = self.targetFilename + self.pluginExt

      # get the compiler version
      compInfo = self.compiler.split('-')
      if len(compInfo) > 1:
        self.compilerVersion = self.compiler
      else:
        output = utils.runCmd([self.compiler, '-v'])
        start = output.find('version') + 8
        end = start
        numDots = 0
        while(True):
          end += 1
          c = output[end]
          if c == '.':
            numDots += 1
            if numDots == 2:
              break
        v = output[start:end].rstrip(' ')
        self.compilerVersion = f('{0}-{1}', self.compiler, v)

    #
    # msvc / msvc
    #
    elif self.compilerRoot == 'msvc':

      # compile
      self.compilerCmd = 'cl'
      self.objFlag = '/c'
      self.objExt = '.obj'
      self.objPathFlag = '/Fo'

      # link
      self.linker = 'link'
      self.targetFlag = '/OUT:'
      self.libFlag = ''
      self.libPathFlag = '/LIBPATH:'
      self.staticExt = '.lib'
      self.dynamicExt = '.dll'
      if self.binaryFormat == '64bit':
        self.linkFlags.append('/MACHINE:X64')

      if self.binaryType == 'exe':
        self.targetFilename = self.targetName + '.exe'
      elif self.binaryType == 'static':
        self.targetFilename = self.targetName + self.staticExt
        self.linker = 'lib'
      elif self.binaryType == 'dynamic' or self.binaryType == 'plugin':
        self.targetFilename = self.targetName + self.dynamicExt
        self.linkFlags.append('/DLL')

      self.compilerVersion = self.compiler

    else:
      raise PybythecError('unrecognized compiler root: {0}', self.compilerRoot)


    # make sure the compiler is in PATH
    try:
      subprocess.call(self.compilerCmd, stdout = subprocess.PIPE, stderr = subprocess.PIPE)
    except OSError:
      raise PybythecError('compiler {0} is not found in PATH', self.compilerCmd)

    # make sure the linker is in PATH
    try:
      subprocess.call(self.linker, stdout = subprocess.PIPE, stderr = subprocess.PIPE)
    except OSError:
      raise PybythecError('linker {0} is not found in PATH', self.linker)

    #
    # determine paths
    #
    self.installPath = utils.makePathAbsolute(self.cwDir, self.installPath)
    self._resolvePaths(self.cwDir, self.sources)
    self._resolvePaths(self.cwDir, self.incPaths)
    self._resolvePaths(self.cwDir, self.extIncPaths)
    self._resolvePaths(self.cwDir, self.libPaths)
    self._resolvePaths(self.cwDir, self.libSrcPaths)

    self.binaryRelPath = f('/{0}/{1}/{2}/{3}', self.osType, self.buildType, self.compilerVersion, self.binaryFormat)

    if self.currentBuild:
      self.binaryRelPath += '/' + self.currentBuild

    self.buildPath = utils.makePathAbsolute(self.cwDir, './' + self.buildDir + self.binaryRelPath)

    if self.libInstallPathAppend and (self.binaryType in ['static', 'dynamic']):
      self.installPath += self.binaryRelPath

    self.targetInstallPath = os.path.join(self.installPath, self.targetFilename)

    self.infoStr = f('{0} ({1} {2} {3} {4}', self.targetName, self.osType, self.buildType, self.compilerVersion, self.binaryFormat)
    if self.currentBuild:
      self.infoStr += ' ' + self.currentBuild
    self.infoStr += ')'



  def _getBuildElements1(self, configObj):
    '''
      elements that aren't nested
    '''
    if 'buildType' in configObj:
      self.buildType = os.path.expandvars(configObj['buildType'])

    if 'version' in configObj:
      self.version = os.path.expandvars(configObj['version'])

    if 'target' in configObj:
      self.targetName = os.path.expandvars(configObj['target'])

    if 'builds' in configObj:
      self.builds = configObj['builds']

    if 'osType' in configObj:
      self.osType = os.path.expandvars(configObj['osType'])

    if 'binaryType' in configObj:
      self.binaryType = os.path.expandvars(configObj['binaryType'])

    if 'binaryFormat' in configObj:
      self.binaryFormat = os.path.expandvars(configObj['binaryFormat'])

    if 'libInstallPathAppend' in configObj:
      self.libInstallPathAppend = configObj['libInstallPathAppend']

    if 'plusplus' in configObj:
      self.plusplus = configObj['plusplus']

    if 'locked' in configObj:
      self.locked = configObj['locked']

    if 'buildDir' in configObj:
      self.buildDir = configObj['buildDir']

    if 'showCompilerCmds' in configObj:
      self.showCompilerCmds = configObj['showCompilerCmds']

    if 'showLinkerCmds' in configObj:
      self.showLinkerCmds = configObj['showLinkerCmds']

    if 'copyDynamicLibs' in configObj:
      self.copyDynamicLibs = configObj['copyDynamicLibs']

    if 'msvc-default' in configObj:
      self.msvcDefault = configObj['msvc-default']


  def _getBuildElements2(self, configObj, keys = []):
    '''
      elements that are nested in a finite / special case way, currently just the compiler
    '''
    # compiler can be nested in a dict with 2 valid key types: osType and a build name
    if 'compiler' in configObj:
      compilerList = []
      self._getArgsList(compilerList, configObj['compiler'], keys)
      if len(compilerList):
        self.compiler = compilerList[0]
        if len(compilerList) > 1:
          log.warning('couldn\'t resolve to single compiler, compiler options: {0}, selecting {1}', compilerList, self.compiler)


  def _getBuildElements3(self, configObj, keys = []):
    '''
      elements that are potentially nested in any which way
    '''
    separartor = ':'
    if platform.system() == 'Windows':
      separartor = ';'

    # TODO: PATH will grow for any build with dependencies, is there a way to prevent it?
    if 'bins' in configObj:
      bins = []
      self._getArgsList(bins, configObj['bins'], keys)
      for bin in bins:
        os.environ['PATH'] = bin + separartor + os.environ['PATH']

    if 'sources' in configObj:
      self._getArgsList(self.sources, configObj['sources'], keys)

    if 'libs' in configObj:
      self._getArgsList(self.libs, configObj['libs'], keys)

    if 'defines' in configObj:
      self._getArgsList(self.defines, configObj['defines'], keys)

    if 'flags' in configObj:
      self._getArgsList(self.flags, configObj['flags'], keys)

    if 'linkFlags' in configObj:
      self._getArgsList(self.linkFlags, configObj['linkFlags'], keys)

    if 'incPaths' in configObj:
      self._getArgsList(self.incPaths, configObj['incPaths'], keys)

    if 'extIncPaths' in configObj:
      self._getArgsList(self.extIncPaths, configObj['extIncPaths'], keys)

    if 'libPaths' in configObj:
      self._getArgsList(self.libPaths, configObj['libPaths'], keys)

    if 'libSrcPaths' in configObj:
      self._getArgsList(self.libSrcPaths, configObj['libSrcPaths'], keys)

    if 'qtClasses' in configObj:
      self._getArgsList(self.qtClasses, configObj['qtClasses'], keys)

    if 'filetype' in configObj:
      filetypes = []
      self._getArgsList(filetypes, configObj['filetype'], keys)
      if len(filetypes):
        self.filetype = filetypes[0]

    if 'installPath' in configObj:
      installPaths = []
      self._getArgsList(installPaths, configObj['installPath'], keys)
      if len(installPaths):
        self.installPath = installPaths[0]

  def _resolvePaths(self, absPath, paths):
    '''
    '''
    i = 0
    for path in paths:
      paths[i] = utils.makePathAbsolute(absPath, path)
      i += 1

  def _getArgsList(self, argsList, args, keys = []):
    '''
      recursivley parses args and appends it to argsList if it has any of the keys
      args can be a dict, str (space-deliminated) or list
    '''
    if type(args) == dict:
      for key in keys:
        if key in args:
          self._getArgsList(argsList, args[key], keys)
    else:
      if type(args) == str or type(args).__name__ == 'unicode':
        argsList.append(os.path.expandvars(args))
      elif type(args) == list:
        for arg in args:
          argsList.append(os.path.expandvars(arg))
