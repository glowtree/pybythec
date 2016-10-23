import os
import json
import logging
import platform
from pybythec import utils

log = logging.getLogger('pybythec')


class BuildElements:
  def __init__(self, argv):
    '''
      argv (input): a list of arguments with a flag, value pairing ie ['-c', 'gcc'] (where -c is the flag and gcc is the value)
    '''

    # get any arguments passed in
    if type(argv) is not list:
      raise Exception('args must be a list, not a {0}'.format(argv))

    self.target = ''
    self.binaryType = ''  # exe, static, dynamic, plugin
    self.compiler = ''  # g++-4.4 g++ clang++ msvc110 etc
    self.osType = ''  # linux, osx, windows
    self.binaryFormat = '64bit'  # 32bit, 64bit etc
    self.buildType = 'debug'  # debug, release etc

    self.hiddenFiles = False  # if pybythec files are "hidden files"

    self.filetype = ''  # elf, mach-o, pe

    self.multithread = True

    self.locked = False

    self.showCompilerCmds = False
    self.showLinkerCmds = False

    self.buildDir = 'pybythec'
    self.hideBuildDirs = False

    self.installPath = '.'  #self.buildDir

    self.configKeys = [] # can be declared in the config files
    self.customKeys = [] # custom keys that are both declared on the command line and found in the config file(s)

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
      if not len(self.osType):
        self.osType = 'linux'
      if not len(self.compiler):
        self.compiler = 'g++'
      if not len(self.filetype):
        self.filetype = 'elf'
    elif platform.system() == 'Darwin':
      if not len(self.osType):
        self.osType = 'osx'
      if not len(self.compiler):
        self.compiler = 'clang++'
      if not len(self.filetype):
        self.filetype = 'mach-o'
    elif platform.system() == 'Windows':
      if not len(self.osType):
        self.osType = 'windows'
      if not len(self.compiler):
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
      if not len(self.filetype):
        self.filetype = 'pe'
    else:
      raise Exception('os does not appear to be Linux, OS X or Windows')

    #
    # parse the args
    #
    args = dict()
    argKey = str()
    keyFound = False

    for arg in argv:
      if keyFound:
        args[argKey] = arg
        keyFound = False
        continue
      if arg == '-cl' or arg == '-cla':  # cleaning
        args[arg] = ''
      elif arg == '-c' or arg == '-os' or arg == '-b' or arg == '-bf' or arg == '-d' or arg == '-p' or arg == '-ck':
        argKey = arg
        keyFound = True
      elif arg == '-v':
        raise Exception('version: {0}'.format(utils.__version__))
      else:
        raise Exception('{0} is not a valid argumnet\nvalid arguments:\n\n'
                        '-c   compiler: any variation of gcc, clang, or msvc ie g++-4.4, msvc110\n'
                        '-os  operating system: currently linux, osx, or windows\n'
                        '-b   build type: debug release etc \n'
                        '-bf  binary format: 32bit, 64bit etc\n'
                        '-p   path to a pybythec project config file (json format)\n'
                        '-cl  clean the build\n'
                        '-cla clean the build and the builds of all library dependencies\n'
                        '-v   version\n'
                        '-ck  custom keys that you want this build to use (comma delineated, no spaces ie foo,bar)\n'
                        '-d   directory of the library being built, likely only used when building a library as a dependency (ie from a project)\n'.format(arg))

    self.cwDir = os.getcwd()
    if '-d' in args:
      self.cwDir = args['-d']

  # json config files
    globalCf = None
    projectCf = None
    localCf = None

    # global config
    if not globalCf and '-g' in args:
      globalCf = utils.loadJsonFile(args['-g'])
    if 'PYBYTHEC_GLOBALS' in os.environ:
      globalCf = utils.loadJsonFile(os.environ['PYBYTHEC_GLOBALS'])
    if not globalCf:
      globalCf = utils.loadJsonFile('.pybythecGlobals.json')
    if not globalCf:
      globalCf = utils.loadJsonFile('pybythecGlobals.json')  
    if not globalCf:
      homeDirPath = os.environ['HOME']
      if platform.system() == 'Windows':
        homeDirPath = os.environ['USERPROFILE']
      globalCf = utils.loadJsonFile(homeDirPath + '/.pybythecGlobals.json')
      if not globalCf:
        globalCf = utils.loadJsonFile(homeDirPath + '/pybythecGlobals.json')
    if not globalCf:
      log.warning('no global pybythec json file found')

  # project config
    if 'PYBYTHEC_PROJECT' in os.environ:
      projectCf = os.environ['PYBYTHEC_PROJECT']
    if not projectCf and '-p' in args:
      projectCf = utils.loadJsonFile(args['-p'])
    if not projectCf:
      projectCf = utils.loadJsonFile(self.cwDir + '/pybythecProject.json')
    if not projectCf:
      projectCf = utils.loadJsonFile(self.cwDir + '/.pybythecProject.json')

  # local config, expected to be in the current working directory
    localConfigPath = self.cwDir + '/pybythec.json'
    if not os.path.exists(localConfigPath):
      localConfigPath = self.cwDir + '/.pybythec.json'
    if os.path.exists(localConfigPath):
      localCf = utils.loadJsonFile(localConfigPath)

    if globalCf is not None:
      self._getBuildElements(globalCf)
    if projectCf is not None:
      self._getBuildElements(projectCf)
    if localCf is not None:
      self._getBuildElements(localCf)

    # command line overrides
    if '-os' in args:
      self.osType = args['-os']

    if '-b' in args:
      self.buildType = args['-b']

    if '-bf' in args:
      self.binaryFormat = args['-bf']

    # compiler special case: os specific compiler selection
    if type(self.compiler) == dict:
      compiler = []
      self.keys = [self.osType]
      if globalCf and 'compiler' in globalCf:
        self._getArgsList(compiler, globalCf['compiler'])
      if projectCf and 'compiler' in projectCf:
        self._getArgsList(compiler, projectCf['compiler'])
      if localCf and 'compiler' in localCf:
        self._getArgsList(compiler, localCf['compiler'])
      if len(compiler):
        self.compiler = compiler[0]

    # one final commandline override: the compiler
    if '-c' in args:
      self.compiler = args['-c']

    # TODO: verify things like does this compiler actually exist (to prevent getting poor error messages)

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
    if '-ck' in args:
      cmdLineKeys = args['-ck']
      for ck in self.configKeys:
        if type(cmdLineKeys) == str:
          if ck == cmdLineKeys:
            self.customKeys.append(ck)
        else: # assume list
          if ck in cmdLineKeys:
            self.customKeys.append(ck)
      self.keys += self.customKeys

    if self.multithread:
      self.keys.append('multithread')

    if globalCf is not None:
      self._getBuildElements2(globalCf)
    if projectCf is not None:
      self._getBuildElements2(projectCf)
    if localCf is not None:
      self._getBuildElements2(localCf)

    # deal breakers
    if not len(self.target):
      raise Exception('no target specified')
    elif not len(self.binaryType):
      raise Exception('no binary type specified')
    elif not len(self.binaryFormat):
      raise Exception('no binary format specified')
    elif not len(self.buildType):
      raise Exception('no build type specified')
    elif not len(self.sources):
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
