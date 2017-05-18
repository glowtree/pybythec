import os
import logging
import platform
from pybythec import utils

log = logging.getLogger('pybythec')


class BuildElements:

  def __init__(self,
               compiler = None,
               osType = None,
               buildType = None,
               binaryFormat = None,
               projConfig = None,
               projConfigPath = None,
               globalConfig = None,
               globalConfigPath = None,
               customKeys = None,
               libDir = None):
    '''
    '''

    # set by the config files first
    self.target = None
    self.binaryType = None  # exe, static, dynamic, plugin
    self.compiler = None  # g++-4.4 g++ clang++ msvc110 etc
    self.osType = None  # linux, osx, windows
    self.binaryFormat = None  # 32bit, 64bit etc
    self.buildType = None  # debug, release etc
    self.filetype = None  # elf, mach-o, pe

    self.hiddenFiles = False  # if pybythec files are "hidden files" - start with .

    self.multithread = True

    self.locked = False

    self.showCompilerCmds = False
    self.showLinkerCmds = False

    self.buildDir = 'pybythec'
    self.hideBuildDirs = False

    self.installPath = '.'

    self.configKeys = []  # can be declared in the config files
    self.customKeys = []  # custom keys that are both declared on the command line and found in the config file(s)

    self.sources = []
    self.libs = []
    self.defines = []
    self.flags = []
    self.linkFlags = []

    self.incPaths = []
    self.extIncPaths = []  # these will not be checked for timestamps
    self.libPaths = []
    self.libSrcPaths = []
    self.keys = []

    self.qtClasses = []

    self.libInstallPathAppend = True
    self.plusplus = True

    # defaults
    if platform.system() == 'Linux':
      if not self.osType:
        self.osType = 'linux'
      if not self.compiler:
        self.compiler = 'g++'
      if not self.filetype:
        self.filetype = 'elf'
    elif platform.system() == 'Darwin':
      if not self.osType:
        self.osType = 'osx'
      if not self.compiler:
        self.compiler = 'clang++'
      if not self.filetype:
        self.filetype = 'mach-o'
    elif platform.system() == 'Windows':
      if not self.osType:
        self.osType = 'windows'
      if not self.compiler:  # find the latest visual studio verison
        i = 25  # NOTE: hopefully that covers enough VisualStudio releases
        vcPath = 'C:/Program Files (x86)/Microsoft Visual Studio {0}.0/VC'
        foundVc = False
        while i > 5:
          if os.path.exists(vcPath.format(i)):
            foundVc = True
            break
          i -= 1
        if foundVc:
          self.compiler = 'msvc-{0:02}0'.format(i)
        else:
          raise Exception('can\'t find a compiler for Windows')
      if not self.filetype:
        self.filetype = 'pe'
    else:
      raise Exception('os needs to be Linux, OS X or Windows')

    self.cwDir = os.getcwd()
    if libDir:
      self.cwDir = libDir
    
    #
    # config files
    #
    if not libDir: # libDir means this is a dependency build, so skip the global and project config finding
      # global config
      if not globalConfig:
        if globalConfigPath:
          if not os.path.exists(globalConfigPath):
            log.warning('{0} doesn\'t exist'.format(globalConfigPath))
          globalConfig = utils.loadJsonFile(globalConfigPath)
        elif 'PYBYTHEC_GLOBALS' in os.environ:
          globalConfigPath = os.environ['PYBYTHEC_GLOBALS']
          if os.path.exists(globalConfigPath):
            globalConfig = utils.loadJsonFile(globalConfigPath)
          else:
            log.warning('PYBYTHEC_GLOBALS points to {0}, which doesn\'t exist'.format(globalConfigPath))
        elif os.path.exists('.pybythecGlobals.json'):
          globalConfig = utils.loadJsonFile('.pybythecGlobals.json')
        elif os.path.exists('pybythecGlobals.json'):
          globalConfig = utils.loadJsonFile('pybythecGlobals.json')
        else: # check the home directory
          homeDirPath = ''
          if platform.system() == 'Windows':
            homeDirPath = os.environ['USERPROFILE']
          else:
            homeDirPath = os.environ['HOME']
          if os.path.exists(homeDirPath + '/.pybythecGlobals.json'):
            globalConfig = utils.loadJsonFile(homeDirPath + '/.pybythecGlobals.json')
          elif os.path.exists(homeDirPath + '/pybythecGlobals.json'):
            globalConfig = utils.loadJsonFile(homeDirPath + '/pybythecGlobals.json')
          else: # end of the line
            log.warning('no pybythecGlobals.json found in the home directory (hidden or otherwise)')
      if not globalConfig:
        log.warning('not using a global configuration')
      
      # project config
      if not projConfig:
        if projConfigPath:
          if not os.path.exists(projConfigPath):
            log.warning('{0} doesn\'t exist'.format(projConfigPath))
          projConfig = utils.loadJsonFile(projConfigPath)
        elif 'PYBYTHEC_PROJECT' in os.environ:
          projConfPath = os.environ['PYBYTHEC_PROJECT']
          if os.path.exists(projConfPath):
            projConfig = utils.loadJsonFile(projConfPath)
          else:
            log.warning('PYBYTHEC_PROJECT points to {0}, which doesn\'t exist'.format(projConfPath))
        else:
          if os.path.exists(self.cwDir + '/pybythecProject.json'):
            projConfig = utils.loadJsonFile(self.cwDir + '/pybythecProject.json')
          elif os.path.exists(self.cwDir + '/.pybythecProject.json'):
            projConfig = utils.loadJsonFile(self.cwDir + '/.pybythecProject.json')
      # if not projConfig:
        # log.warning('not using a project pybythec configuration')

    self.globalConfig = globalConfig  
    self.projConfig = projConfig
      

    # local config, expected to be in the current working directory
    localConfig = None
    localConfigPath = self.cwDir + '/pybythec.json'
    if not os.path.exists(localConfigPath):
      localConfigPath = self.cwDir + '/.pybythec.json'
    if os.path.exists(localConfigPath):
      localConfig = utils.loadJsonFile(localConfigPath)

    if globalConfig is not None:
      self._getBuildElements(globalConfig)
    if projConfig is not None:
      self._getBuildElements(projConfig)
    if localConfig is not None:
      self._getBuildElements(localConfig)

    # command line overrides
    if osType:
      self.osType = osType

    if buildType:
      self.buildType = buildType

    if binaryFormat:
      self.binaryFormat = binaryFormat

    # compiler special case: os specific compiler selection
    if type(self.compiler) == dict:
      compilerList = []
      self.keys = [self.osType]
      if globalConfig and 'compiler' in globalConfig:
        self._getArgsList(compilerList, globalConfig['compiler'])
      if projConfig and 'compiler' in projConfig:
        self._getArgsList(compilerList, projConfig['compiler'])
      if localConfig and 'compiler' in localConfig:
        self._getArgsList(compilerList, localConfig['compiler'])
      if len(compilerList):
        self.compiler = compilerList[0]

    if compiler:
      self.compiler = compiler

    # currently compiler root can either be gcc, clang or msvc
    self.compilerRoot = self.compiler
    if self.compilerRoot.startswith('gcc') or self.compilerRoot.startswith('g++'):
      self.compilerRoot = 'gcc'
    elif self.compilerRoot.startswith('clang') or self.compilerRoot.startswith('clang++'):
      self.compilerRoot = 'clang'
    elif self.compilerRoot.startswith('msvc'):
      self.compilerRoot = 'msvc'
    else:
      raise Exception('unrecognized compiler {0}'.format(self.compiler))

    # compiler version
    self.compilerVersion = ''
    v = self.compiler.split('-')
    if len(v) > 1:
      self.compilerVersion = '-' + v[1]

    self.keys = ['all', self.compilerRoot, self.compiler, self.osType, self.binaryType, self.buildType, self.binaryFormat]

    # custom keys
    if customKeys:
      for ck in self.configKeys:
        if ck in customKeys:
          self.customKeys.append(ck)
      self.keys += self.customKeys

    if self.multithread:
      self.keys.append('multithread')

    if globalConfig is not None:
      self._getBuildElements2(globalConfig)
    if projConfig is not None:
      self._getBuildElements2(projConfig)
    if localConfig is not None:
      self._getBuildElements2(localConfig)

    # deal breakers
    if not self.target:
      raise Exception('no target specified')
    if not self.binaryType:
      raise Exception('no binary type specified')
    if not self.binaryFormat:
      raise Exception('no binary format specified')
    if not self.buildType:
      raise Exception('no build type specified')
    if not self.sources:
      raise Exception('no source files specified')

    if not (self.binaryType == 'exe' or self.binaryType == 'static' or self.binaryType == 'dynamic' or self.binaryType == 'plugin'):
      raise Exception('unrecognized binary type: ' + self.binaryType)

    if self.hideBuildDirs:
      self.buildDir = '.' + self.buildDir

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

      # TODO: verify that the compiler exists

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

      # log.info('*** filetype {0}'.format(self.filetype))

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
        raise Exception('compiler not found, check the paths set in bins')

    else:
      raise Exception('unrecognized compiler root: ' + self.compilerRoot)

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
    for ck in self.customKeys:
      binRelPath += '/' + ck

    self.buildPath = utils.makePathAbsolute(self.cwDir, './' + self.buildDir + binRelPath)

    if self.libInstallPathAppend and (self.binaryType == 'static' or self.binaryType == 'dynamic'):
      self.installPath += binRelPath

    self.targetInstallPath = os.path.join(self.installPath, self.target)

    self.infoStr = '{0} ({1} {2} {3}'.format(self.target, self.buildType, self.compiler, self.binaryFormat)
    if len(self.customKeys):
      for ck in self.customKeys:
        self.infoStr += ' ' + ck
    self.infoStr += ')'

  def _getBuildElements(self, configObj):
    '''
    '''
    if 'target' in configObj:
      self.target = os.path.expandvars(configObj['target'])

    if 'binaryType' in configObj:
      self.binaryType = os.path.expandvars(configObj['binaryType'])

    if 'compiler' in configObj:
      self.compiler = os.path.expandvars(configObj['compiler'])

    if 'osType' in configObj:
      self.osType = os.path.expandvars(configObj['osType'])

    if 'buildType' in configObj:
      self.buildType = os.path.expandvars(configObj['buildType'])

    if 'binaryFormat' in configObj:
      self.binaryFormat = os.path.expandvars(configObj['binaryFormat'])

    if 'libInstallPathAppend' in configObj:
      self.libInstallPathAppend = configObj['libInstallPathAppend']

    if 'plusplus' in configObj:
      self.plusplus = configObj['plusplus']

    if 'multithread' in configObj:
      self.multithread = configObj['multithread']

    if 'locked' in configObj:
      self.locked = configObj['locked']

    if 'hideBuildDirs' in configObj:
      self.hideBuildDirs = configObj['hideBuildDirs']

    if 'showCompilerCmds' in configObj:
      self.showCompilerCmds = configObj['showCompilerCmds']

    if 'showLinkerCmds' in configObj:
      self.showLinkerCmds = configObj['showLinkerCmds']

    if 'customKeys' in configObj:
      self.configKeys = configObj['customKeys']

  def _getBuildElements2(self, configObj):
    '''
    '''
    separartor = ':'
    if platform.system() == 'Windows':
      separartor = ';'

    # TODO: PATH will grow for any build with dependencies, is there a way to prevent it?
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

    if 'extIncPaths' in configObj:
      self._getArgsList(self.extIncPaths, configObj['extIncPaths'])

    if 'libPaths' in configObj:
      self._getArgsList(self.libPaths, configObj['libPaths'])

    if 'libSrcPaths' in configObj:
      self._getArgsList(self.libSrcPaths, configObj['libSrcPaths'])

    if 'qtClasses' in configObj:
      self._getArgsList(self.qtClasses, configObj['qtClasses'])

    if 'filetype' in configObj:
      filetypes = []
      self._getArgsList(filetypes, configObj['filetype'])
      if len(filetypes):
        self.filetype = filetypes[0]

    if 'installPath' in configObj:
      installPaths = []
      self._getArgsList(installPaths, configObj['installPath'])
      if len(installPaths):
        self.installPath = installPaths[0]

  def _resolvePaths(self, absPath, paths):
    i = 0
    for path in paths:
      paths[i] = utils.makePathAbsolute(absPath, path)
      i += 1

  def _getArgsList(self, argsList, args):
    '''
      recursivley parses args and appends it to argsList if it has any of the keys
      args can be a dict, str (space-deliminated) or list
    '''
    if type(args) == dict:
      for key in self.keys:
        if key in args:
          self._getArgsList(argsList, args[key])
    else:
      if type(args) == str or type(args).__name__ == 'unicode':
        argsList.append(os.path.expandvars(args))
      elif type(args) == list:
        for arg in args:
          argsList.append(os.path.expandvars(arg))
