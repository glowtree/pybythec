import os
import logging
import platform
from pybythec import utils

log = logging.getLogger('pybythec')

class PybythecError(Exception):
  pass

class BuildElements:

  def __init__(self,
               osType = None,
               projConfigPath = None,
               globalConfigPath = None,
               builds = None,
               projConfig = None,
               globalConfig = None,
               libDir = None):
    '''
      osType: the operating system, currently linux, macOs or windows
      projConfigPath:
      globalConfigPath:
      builds:

      preliminary setup, parses config files if they exist
    '''

    self.localConfig = None
    self.projConfig = projConfig
    self.globalConfig = globalConfig
    self.libDir = libDir

    self.osType = None  # linux, macOs, windows
    self.builds = None # build variations

    self.cwDir = os.getcwd()
    if self.libDir:
      self.cwDir = self.libDir
    
    # global config
    if not self.globalConfig:
      if globalConfigPath:
        if os.path.exists(globalConfigPath):
          self.globalConfig = utils.loadJsonFile(globalConfigPath)
        else:
          log.warning('{0} doesn\'t exist'.format(globalConfigPath))
      elif 'PYBYTHEC_GLOBALS' in os.environ:
        globalConfigPath = os.environ['PYBYTHEC_GLOBALS']
        if os.path.exists(globalConfigPath):
          self.globalConfig = utils.loadJsonFile(globalConfigPath)
        else:
          log.warning('PYBYTHEC_GLOBALS points to {0}, which doesn\'t exist'.format(globalConfigPath))
      elif os.path.exists('.pybythecGlobals.json'):
        self.globalConfig = utils.loadJsonFile('.pybythecGlobals.json')
      elif os.path.exists('pybythecGlobals.json'):
        self.globalConfig = utils.loadJsonFile('pybythecGlobals.json')
      else: # check the home directory
        homeDirPath = ''
        if platform.system() == 'Windows':
          homeDirPath = os.environ['USERPROFILE']
        else:
          homeDirPath = os.environ['HOME']
        if os.path.exists(homeDirPath + '/.pybythecGlobals.json'):
          self.globalConfig = utils.loadJsonFile(homeDirPath + '/.pybythecGlobals.json')
        elif os.path.exists(homeDirPath + '/pybythecGlobals.json'):
          self.globalConfig = utils.loadJsonFile(homeDirPath + '/pybythecGlobals.json')
        else: # end of the line
          log.warning('no pybythecGlobals.json found in the home directory (hidden or otherwise)')
    if not self.globalConfig:
      log.warning('not using a global configuration')
    
    # project config
    if not self.projConfig:
      if projConfigPath:
        if os.path.exists(projConfigPath):
          self.projConfig = utils.loadJsonFile(projConfigPath)
        else:
          log.warning('{0} doesn\'t exist'.format(projConfigPath))
      elif 'PYBYTHEC_PROJECT' in os.environ:
        projConfPath = os.environ['PYBYTHEC_PROJECT']
        if os.path.exists(projConfPath):
          self.projConfig = utils.loadJsonFile(projConfPath)
        else:
          log.warning('PYBYTHEC_PROJECT points to {0}, which doesn\'t exist'.format(projConfPath))
      else:
        if os.path.exists(self.cwDir + '/pybythecProject.json'):
          self.projConfig = utils.loadJsonFile(self.cwDir + '/pybythecProject.json')
        elif os.path.exists(self.cwDir + '/.pybythecProject.json'):
          self.projConfig = utils.loadJsonFile(self.cwDir + '/.pybythecProject.json')
    # if not projConfig:
      # log.warning('not using a project pybythec configuration')

    # local config, expected to be in the current working directory
    self.localConfig = None
    localConfigPath = self.cwDir + '/pybythec.json'
    if not os.path.exists(localConfigPath):
      localConfigPath = self.cwDir + '/.pybythec.json'
    if os.path.exists(localConfigPath):
      self.localConfig = utils.loadJsonFile(localConfigPath)

    #
    # first iteration to get osType and custom keys (right now just for the compiler)
    #
    if globalConfig is not None:
      self._getBuildElements1(self.globalConfig)
    if projConfig is not None:
      self._getBuildElements1(self.projConfig)
    if self.localConfig is not None:
      self._getBuildElements1(self.localConfig)

    # osType
    if osType: # command line override
      self.osType = osType
    if self.osType:
      if self.osType not in ['linux', 'macOs', 'windows']: # validate
        log.warning('{0} invalid osType, defaulting to the native os'.format(self.osType))
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

    # builds
    if builds: # command line override
      self.builds = builds
    if not self.builds:
      self.builds = [None]


  def configBuild(self, compiler = None, buildType = None, binaryFormat = None, buildName = None):
    '''
    '''
    # set by the config files first
    self.target = None
    self.binaryType = None  # exe, static, dynamic, plugin
    self.compiler = None  # g++-4.4 g++ clang++ msvc110 etc
    self.binaryFormat = None  # 32bit, 64bit etc
    self.buildType = None  # debug, release etc
    self.filetype = None  # elf, mach-o, pe
    self.buildDir = None
    self.installPath = None
  
    self.locked = False

    self.showCompilerCmds = False
    self.showLinkerCmds = False

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

    self.libInstallPathAppend = True
    self.plusplus = True

    # 2 keys at this point for a potentially nested compiler: osType and buildName
    keys = [self.osType]
    if buildName:
      keys.append(buildName)

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
    if compiler: # command line override
      self.compiler = compiler

    if not self.compiler:
      raise PybythecError('compiler not found')

    # validate compiler and  determine root: can be gcc, clang or msvc
    self.compilerRoot = None
    if self.compiler.startswith('gcc') or self.compiler.startswith('g++'):
      self.compilerRoot = 'gcc'
    elif self.compiler.startswith('clang') or self.compiler.startswith('clang++'):
      self.compilerRoot = 'clang'
    elif self.compiler.startswith('msvc'):
      self.compilerRoot = 'msvc'
    else:
      raise PybythecError('unrecognized compiler {0}, using the default based on osType'.format(self.compiler))

    # TODO: verify that the compiler exists / runs

    if buildType: # command line override
      self.buildType = buildType

    if binaryFormat: # command line override
      self.binaryFormat = binaryFormat

    keys += ['all', self.compilerRoot, self.compiler, self.binaryType, self.buildType, self.binaryFormat]

    if self.globalConfig is not None:
      self._getBuildElements3(self.globalConfig, keys)
    if self.projConfig is not None:
      self._getBuildElements3(self.projConfig, keys)
    if self.localConfig is not None:
      self._getBuildElements3(self.localConfig, keys)

    # deal breakers (that don't appear in the default pybythecGlobals.json)
    if not self.target:
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
    self.compilerCmd = self.compiler
    self.linker = ''
    self.targetFlag = ''
    self.libFlag = ''
    self.libPathFlag = ''
    self.objExt = ''
    self.objPathFlag = ''

    self.staticExt = ''
    self.dynamicExt = ''
    self.pluginExt = ''

    #
    # gcc / clang
    #
    if self.compilerRoot == 'gcc' or self.compilerRoot == 'clang':

      if not self.plusplus:  # if forcing plain old C (ie when a library is being built as a dependency that is only C compatible)
        if self.compilerRoot == 'gcc':
          self.compilerCmd = self.compilerCmd.replace('g++', 'gcc')
        elif self.compilerRoot == 'clang':
          self.compilerCmd = self.compilerCmd.replace('clang++', 'clang')

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
        self.target = 'lib' + self.target

      if self.binaryType == 'exe':
        pass
      elif self.binaryType == 'static':
        self.target = self.target + '.a'
        self.linker = 'ar'
        self.targetFlag = 'r'
      elif self.binaryType == 'dynamic':
        self.target = self.target + self.dynamicExt
      elif self.binaryType == 'plugin':
        self.target = self.target + self.pluginExt

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
        self.target += '.exe'
      elif self.binaryType == 'static':
        self.target += self.staticExt
        self.linker = 'lib'
      elif self.binaryType == 'dynamic' or self.binaryType == 'plugin':
        self.target += self.dynamicExt
        self.linkFlags.append('/DLL')

      # make sure the compiler is in PATH
      if utils.runCmd(self.compilerCmd).startswith('[WinError 2]'):
        raise PybythecError('compiler not found, check the paths set in bins')

    else:
      raise PybythecError('unrecognized compiler root: {0}'.format(self.compilerRoot))

    #
    # determine paths
    #
    self.installPath = utils.makePathAbsolute(self.cwDir, self.installPath)
    self._resolvePaths(self.cwDir, self.sources)
    self._resolvePaths(self.cwDir, self.incPaths)
    self._resolvePaths(self.cwDir, self.extIncPaths)
    self._resolvePaths(self.cwDir, self.libPaths)
    self._resolvePaths(self.cwDir, self.libSrcPaths)

    self.binaryRelPath = '/{0}/{1}/{2}'.format(self.buildType, self.compiler, self.binaryFormat)

    binRelPath = self.binaryRelPath
    if buildName:
      binRelPath += '/' + buildName

    self.buildPath = utils.makePathAbsolute(self.cwDir, './' + self.buildDir + binRelPath)

    # if self.libInstallPathAppend and (self.binaryType == 'static' or self.binaryType == 'dynamic'):
    if self.libInstallPathAppend and (self.binaryType in ['static', 'dynamic']):
      self.installPath += binRelPath

    self.targetInstallPath = os.path.join(self.installPath, self.target)

    self.infoStr = '{0} ({1} {2} {3}'.format(self.target, self.buildType, self.compiler, self.binaryFormat)
    if buildName:
      self.infoStr += ' ' + buildName
    self.infoStr += ')'



  def _getBuildElements1(self, configObj, keys = []):
    '''
    '''
    if 'osType' in configObj:
      self.osType = os.path.expandvars(configObj['osType'])

    if 'builds' in configObj:
      self.builds = configObj['builds']


  def _getBuildElements2(self, configObj, keys = []):
    '''
    '''
    if 'target' in configObj:
      self.target = os.path.expandvars(configObj['target'])

    if 'binaryType' in configObj:
      self.binaryType = os.path.expandvars(configObj['binaryType'])

    # special case: compiler can be nested in a dict with 2 valid key types: osType and a build name
    if 'compiler' in configObj:
      compilerList = []
      self._getArgsList(compilerList, configObj['compiler'], keys)
      if len(compilerList):
        self.compiler = compilerList[0]
        if len(compilerList) > 1:
          log.warning('couldn\'t resolve to single compiler, compiler options: {0}, selecting {1}'.format(compilerList, self.compiler))

    if 'buildType' in configObj:
      self.buildType = os.path.expandvars(configObj['buildType'])

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


  def _getBuildElements3(self, configObj, keys = []):
    '''
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
