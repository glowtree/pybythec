
#
# py by the c
#

# a cross platform build system for c/c++
#
# written by Tom Sirdevan at glowtree
#
# contact: pybythc@glowtree.com
#

#
# can build c/c++ projects that create ...
#
# executables
# static  libraries: (herein called staticLib)
# dynamic libraries  (herein called dynamicLib)
# dynamic plugins / packages, on osx / Mach-O referred to as a bundle (herein called dynamic)
#

import utils
from buildObjects import *

import os
import sys
import shutil
import time
import logging
import subprocess
from threading import Thread

log = logging.getLogger('pybythec')

def compileSrc(source, incPaths, compileCmd, objPathFlag, objExt, buildDir, objPaths, buildStatus):

  if not os.path.exists(source):
    log.warning(source + ' is missing, exiting build')
    return

  objFile = os.path.basename(source)
  objFile = objFile.replace(os.path.splitext(source)[1], objExt)
  objPath = os.path.join(buildDir, objFile)
  objPaths.append(objPath) # + ' ')
  
  # check if it's up to date
  objExisted = os.path.exists(objPath)
  if objExisted:
    objTimestamp = float(os.stat(objPath).st_mtime)
    if not utils.sourceNeedsBuilding(incPaths, source, objTimestamp):
      buildStatus.result = 2 # up to date
      return

  # compile
  cmd = compileCmd + [source, objPathFlag, objPath]
  log.debug(cmd)
  try:
    compileProcess = subprocess.Popen(cmd, stdout = subprocess.PIPE)
  except OSError as e:
    buildStatus.description = 'compileProcess failed because ' + str(e)
    log.error(buildStatus.description)
    return

  buildStatus.description = compileProcess.communicate()[0].decode('utf-8')

  if os.path.exists(objPath):
    if objExisted:
      if float(os.stat(objPath).st_mtime) > objTimestamp:
        buildStatus.result = 1
    else:
      buildStatus.result = 1

  if buildStatus.result == 1:
    buildStatus.description = 'compiled ' + os.path.basename(source)
  
  # time.sleep(0.1)


def buildLib(lib, libPaths, libSrcDir, compilerCmd, compiler, osType, fileExt, buildType, binaryFormat, projectDir, buildStatus):
  
  libPath      = str()
  # libTimestamp = 0 # TODO: why record the timestamp if you're not using it???
  libExisted   = False

  # find the previously built lib in the lib install directories if it exists
  for libDir in libPaths:
    libPath = utils.getLibPath(lib, libDir, compiler, fileExt)
    libExisted = os.path.exists(libPath)
    if libExisted:
      # libTimestamp = float(os.stat(libPath).st_mtime)
      break
  
  jsonPath = os.path.join(libSrcDir, '.pybythec.json')
  if not os.path.exists(jsonPath):
    buildStatus.description = libSrcDir + ' does not have a .pybythec.json file'
    log.warning(buildStatus.description)
    return
  
  # build
  try:
    buildCmd = ['pybythec', '-d', libSrcDir, '-os', osType, '-b', buildType, '-c', compiler, '-bf', binaryFormat, '-p', projectDir + '/.pybythecProject.json']
    log.debug(buildCmd)
    libProcess = subprocess.Popen(buildCmd) # , stdout = subprocess.PIPE, stderr = subprocess.PIPE)
  except OSError as e:
    buildStatus.description = 'libProcess failed because ' + str(e)
    log.error(buildStatus.description)
    return
  libProcess.wait()
  
  # read the build status
  buildStatus.readFromFile('{0}/.build/{1}/{2}/{3}'.format(libSrcDir, buildType, compiler, binaryFormat))
  
  # time.sleep(0.01)


'''
  the main function
'''
def build(argv):
  
  startTime = time.time()
  
  #
  # config initialization
  #

  # get any arguments passed in
  if type(argv) is not list:
    log.error('args must be a list')
    return

  args = dict()
  key = str()
  keyFound = False
  for arg in argv:
    if keyFound:
      args[key] = arg
      keyFound = False
      continue
    if arg == '-cl' or arg == '-cla':
      args[arg] = ''
    elif arg == '-c' or arg == '-os' or arg == '-b' or arg == '-bf' or arg == '-d' or arg == '-p':
      key = arg
      keyFound = True
    else:
      log.info(
        '\nvalid pybythec arguments:\n\n'
        '-c   compiler: gcc, clang, or msvc\n'
        '-os  operating system: linux, osx, or windows\n'
        '-b   build type: debug release\n'
        '-bf  binary format: 32bit, 64bit etc\n'
        '-d   src directory of the lib being built, to be used when building a lib as a dependency from elsewhere\n'
        '-p   path to the pybythec project config file (should be in json format)\n'
        '-cl  clean the build\n'
        '-cla clean the build as well the builds of any library dependencies\n'
      )
      return

  cwDir = os.getcwd()
  if '-d' in args:
    cwDir = args['-d']

  # json config files
  globalCf  = None
  projectCf = None
  localCf   = None

  # global config
  if 'PYBYTHEC_GLOBALS' in os.environ:
    globalCf = utils.loadJsonFile(os.environ['PYBYTHEC_GLOBALS'])
  elif '-g' in args:
    globalCf = utils.loadJsonFile(args['-g'])
  else:
    globalCf = utils.loadJsonFile('.pybythecGlobal.json')

  # project config
  if 'PYBYTHEC_PROJECT' in os.environ:
    projectCf = os.environ['PYBYTHEC_PROJECT']
  elif '-p' in args:
    projectCf = utils.loadJsonFile(args['-p']) # + '/.pybythecProject.json')
  else:
    projectCf = utils.loadJsonFile('.pybythecProject.json')

  # local config
  localConfigPath = cwDir + '/.pybythec.json'
  if os.path.exists(localConfigPath):
    localCf = utils.loadJsonFile(localConfigPath)
    
  be = BuildElements()
    
  if globalCf is not None:
    be.getBuildElements(globalCf)
  if projectCf is not None:
    be.getBuildElements(projectCf)
  if localCf is not None:
    be.getBuildElements(localCf)
    
  if be.binaryType == 'executable':
    print('') # formatting
  
  # command line overrides
  if '-c' in args:
    be.compiler = args['-c']
  
  if '-os' in args:
    be.osType = args['-os']
  
  if '-b' in args:
    be.buildType = args['-b']
  
  if '-bf' in args:
    be.binaryFormat = args['-bf']
  
  be.setKeys()

  if globalCf is not None:
    be.getBuildElements2(globalCf)
  if projectCf is not None:
    be.getBuildElements2(projectCf)
  if localCf is not None:
    be.getBuildElements2(localCf)
  
  if not be.goodToBuild():
    return
  
  #
  # compiler config
  #
  compilerCmd = ''      # the compiler command ie if msvc090 is the compiler, but cl is the compilerCmd
  linker      = str()
  targetFlag  = str()
  libFlag     = str()
  libPathFlag = str()
  objExt      = str()
  objPathFlag = str()
   
  isGcc   = be.compiler.startswith('gcc')
  isClang = be.compiler.startswith('clang')
  isMsvc  = be.compiler.startswith('msvc')
  
  #
  # gcc / clang
  #
  if isGcc or isClang:
      
    compilerCmd = be.compiler
      
    if be.plusplus:
      if isGcc:
        compilerCmd = compilerCmd.replace('gcc', 'g++')
      else:
        compilerCmd = compilerCmd.replace('clang', 'clang++')
    
    objExt      = '.o'
    objPathFlag = '-o'
    be.defines.append('_' + be.binaryFormat.upper()) # TODO you sure?
      
    # link
    linker        = compilerCmd
    targetFlag    = '-o'
    libFlag       = '-l'
    libPathFlag   = '-L'
    staticLibExt  = '.a'
    dynamicLibExt = '.so'
    dynamicExt    = '.so'
    if be.osType == 'osx' and isClang: # TODO: it's not clang that determines this, should have a var called osxConventions or something like that
      dynamicLibExt = '.dylib'
      dynamicExt    = '.bundle'
      
    if be.binaryType == 'staticLib' or be.binaryType == 'dynamicLib':
      be.target = 'lib' + be.target

    if be.binaryType == 'staticLib':
      be.target = be.target + '.a'
      linker = 'ar'
      targetFlag = 'r'
    elif be.binaryType == 'dynamicLib':
      be.target = be.target + dynamicLibExt
    elif be.binaryType == 'dynamic':
      be.target = be.target + dynamicExt
    elif be.binaryType != 'executable':
      log.error('unrecognized binary type: ' + be.binaryType)
      return False
    
    if be.multithread and be.binaryType != 'staticLib':
      be.libs.append('pthread')

  #
  # msvc / msvc
  #
  elif isMsvc:
      
    # compile
    compilerCmd = 'cl'
    objExt      = '.obj'
    objPathFlag = '/Fo'
    flags.append('/nologo /errorReport:prompt')
    
    # link
    linker        = 'link'
    targetFlag    = '/OUT:' # NOTE: can't be '-OUT:' for @tmpLinkCmd to work
    libFlag       = ''
    libPathFlag   = '/LIBPATH:'
    staticLibExt  = '.lib'
    dynamicLibExt = '.dll'
    if be.binaryFormat == '64bit':
      linkFlags.append('/MACHINE:X64')
    
    if be.binaryType == 'staticLib':
      be.target += staticLibExt
      linker = 'lib'
    elif be.binaryType == 'dynamicLib' or be.binaryType == 'dynamic':
      be.target += dynamicLibExt
      linkFlags.append('/DLL')
    elif be.binaryType == 'executable':
      be.target += '.exe'
    else:
      log.error('unrecognized binary type: ' + be.binaryType)
      return False
    
    if be.multithread:
      if be.buildType == 'debug':
        be.flags.append('/MDd')
      else:
        be.flags.append('/MD')

  else:
    log.error('{0} is an unknown compiler'.format(be.compiler))
    return False

  #
  # determine paths
  #
  be.resolvePaths(cwDir)
  
  binaryRelPath = '/{0}/{1}/{2}'.format(be.buildType, be.compiler, be.binaryFormat)
  
  buildPath = utils.makePathAbsolute(cwDir, './.build' + binaryRelPath)
  
  for i in range(len(be.libPaths)):
    revisedLibPath = be.libPaths[i] + binaryRelPath
    if os.path.exists(revisedLibPath):
      be.libPaths[i] = revisedLibPath
    else: # in case there's also lib paths that don't have buildType, ie for external libraries that only ever have the release version
      revisedLibPath = '{0}/{1}/{2}'.format(be.libPaths[i], be.compiler, be.binaryFormat)
      if os.path.exists(revisedLibPath):
        be.libPaths[i] = revisedLibPath
        
  if be.libInstallPathAppend and (be.binaryType == 'staticLib' or be.binaryType == 'dynamicLib'):
    be.installPath += binaryRelPath

  if not os.path.exists(be.installPath):
    utils.createDirs(be.installPath)
        
  targetInstallPath = os.path.join(be.installPath, be.target)

  #
  # clean
  #
  if '-cl' in args or '-cla' in args:
    if '-cla' in args:
      for lib in be.libs:
        for libSrcPath in be.libSrcPaths:
          libPath = os.path.join(libSrcPath, lib)
          if os.path.exists(libPath):
            try:
              cleanProcess = subprocess.Popen(['pybythec', 'clean', '-d', libPath, '-b', be.buildType, '-c', be.compiler, '-bf', be.binaryFormat], stdin = subprocess.PIPE)
            except OSError as e:
              log.error(str(e))
              return
            cleanProcess.wait()

    if not os.path.exists(buildPath):
      log.info('{0} ({1} {2} {3}) already clean'.format(be.target, be.buildType, be.compiler, be.binaryFormat))
      return True
        
    shutil.rmtree(buildPath)
    
    if os.path.exists(targetInstallPath):
      os.remove(targetInstallPath)
    log.info('{0} ({1} {2} {3}) all clean'.format(be.target, be.buildType, be.compiler, be.binaryFormat))
    return True

  # lock - early return
  if be.locked and os.path.exists(targetInstallPath):
    buildStatus.result = 2
    log.info(be.target + ' is locked')
    buildStatus.writeToFile(buildPath)
    return True

  #
  # building
  #
  threading = True
  
  log.info('building {0} ({1} {2} {3})'.format(be.target, be.buildType, be.compiler, be.binaryFormat))

  if not os.path.exists(buildPath):
    os.makedirs(buildPath)

  buildStatus = BuildStatus() # final build status
  buildStatusDeps = [] # the build status for each dependency: objs and libs
  threads = []
  i = 0
  
  incPathList = []
  for incPath in be.incPaths:
    incPathList += ['-I', incPath]
  
  definesList = []
  for define in be.defines:
    definesList += ['-D', define]
  
  #
  # Qt moc file compilation
  #
  # TODO: timestamp check to see if this needs to happen or if it's up to date
  mocPaths = []
  for qtClass in be.qtClasses:
    found = False
    qtClassSrc    = qtClass + '.cpp'
    qtClassHeader = qtClass + '.h'
    # TODO: should there be a separate list of headers ie be.mocIncPaths?
    for incPath in be.incPaths:  # find the header file
      includePath = incPath + '/' + qtClassHeader
      if os.path.exists(includePath):
        found = True
        mocPath = buildPath + '/moc_' + qtClassSrc
        mocCmd = ['moc'] + definesList + [includePath, '-o', mocPath]
        try:
          mocProcess = subprocess.Popen(mocCmd, stdin = subprocess.PIPE)
        except OSError as e:
          buildStatus.description = str(e)
          log.error(buildStatus.description)
          continue
        mocProcess.wait()
        mocPaths.append(mocPath)
        
    if not found:
      buildStatus.description = 'can\'t find {0} for qt moc compilation'.format(qtClassHeader)
      log.error(buildStatus.description)
      return

  for mocPath in mocPaths:
    be.sources.append(mocPath)

  #
  # compile sources
  #
  objPaths = []
  cmd = [compilerCmd, '-c'] + incPathList + definesList + be.flags
  
  if threading:
    for source in be.sources:
      buildStatusDep = BuildStatus()
      buildStatusDeps.append(buildStatusDep)
      thread = Thread(None, target = compileSrc, args = (source, be.incPaths, cmd, objPathFlag, objExt, buildPath, objPaths, buildStatusDep))
      thread.start()
      threads.append(thread)
      i += 1
  else:
    for source in be.sources:
      buildStatusDep = BuildStatus()
      buildStatusDeps.append(buildStatusDep)
      compileSrc(source, be.incPaths, cmd, objPathFlag, objExt, buildPath, objPaths, buildStatusDep)
      i += 1
  
  # srcEndIndex = i - 1
  
  #
  # build library dependencies
  #
  libCmds = []
  if len(be.libs):
    for lib in be.libs:
      libName = lib
      if be.compiler.startswith('msvc'):
        libName += staticLibExt
      libCmds += [libFlag, libName]
      # libCmds.append(libFlag + libName)
        
      # check if the lib has a directory for building
      if threading:
        for libSrcDir in be.libSrcPaths:
          libSrcDir = os.path.join(libSrcDir, lib)
          if os.path.exists(libSrcDir):
            buildStatusDep = BuildStatus()
            buildStatusDeps.append(buildStatusDep)
            # TODO: staticLibExt should probably be a list with both static and dynamic file extensions
            thread = Thread(None, target = buildLib, args = (lib, be.libPaths, libSrcDir, compilerCmd, be.compiler, be.osType, staticLibExt, be.buildType, be.binaryFormat, cwDir, buildStatusDep))
            thread.start()
            threads.append(thread)
            i += 1
            break
      else:
        for libSrcPath in be.libSrcPaths:
          libSrcPath = os.path.join(libSrcPath, lib)
          if os.path.exists(libSrcPath):
            buildStatusDep = BuildStatus()
            buildStatusDeps.append(buildStatusDep)
            # TODO: staticLibExt should probably be a list with both static and dynamic file extensions
            buildLib(lib, be.libPaths, be.libSrcPath, compilerCmd, be.compiler, be.osType, staticLibExt, be.buildType, be.binaryFormat, cwDir, buildStatusDep)
            i += 1
            break

  # check the results of all the threads
  for thread in threads:
    thread.join()

  # for neater output
  # if be.binaryType == 'executable':
  #   if len(output[srcEndIndex]):
  #     output[srcEndIndex] += '\n'
  #   else:
  #     output[srcEndIndex] = ' '
  
  allUpToDate = True
  for buildStatusDep in buildStatusDeps:
    if len(buildStatusDep.description):
      log.info(buildStatusDep.description)
    if buildStatusDep.result == 0:
      buildStatus.description = '{0} ({1} {2} {3}) failed, determined in {4} seconds\n'.format(be.target, be.buildType, be.binaryFormat, be.compiler, str(int(time.time() - startTime)))
      log.info(buildStatus.description)
      buildStatus.writeToFile(buildPath)
      return False
    elif buildStatusDep.result == 1:
      allUpToDate = False

  #
  # link objs or libraries
  #
  linkCmd = []
  if allUpToDate and os.path.exists(targetInstallPath):
    buildStatus.result = 2
    buildStatus.description = '{0} ({1} {2} {3}) is up to date, determined in {4} seconds\n'.format(be.target, be.buildType, be.binaryFormat, be.compiler, str(int(time.time() - startTime)))
    log.info(buildStatus.description)
    buildStatus.writeToFile(buildPath)
    return True
  
  # microsoft's compiler / linker can only handle so many characters on the command line
  tmpLinkCmdFp = buildPath + '/tmpLinkCmd'
  if be.compiler.startswith('msvc'):
    msvcTmpFile = open(tmpLinkCmdFp, 'w')
    # msvcTmpFile.write('{0}"{1}" {2} {3}'.format(targetFlag, targetBuildPath, objPaths, libCmds))
    # TODO: objectPaths and libCmds will have to be formatted
    msvcTmpFile.write('{0}"{1}" {2} {3}'.format(targetFlag, targetInstallPath, objPaths, libCmds))
    msvcTmpFile.close()
    # linkCmd = '{0} @{1} '.format(linker, tmpLinkCmdFp)
    linkCmd += [linker, '@' + tmpLinkCmdFp]
  else:
    linkCmd += [linker, targetFlag, targetInstallPath] + objPaths + libCmds

  if be.binaryType != 'staticLib':
    linkCmd += be.linkFlags
    if be.binaryType != 'dynamicLib':
      for libPath in be.libPaths:
        linkCmd += [libPathFlag, os.path.normpath(libPath)]
  
  log.debug(linkCmd)
  # log.info(linkCmd)
  
  # get the timestamp of the existing target if it exists
  linked = False
  targetExisted = False
  oldTargetTimeStamp = None
  if os.path.exists(targetInstallPath):
    oldTargetTimeStamp = float(os.stat(targetInstallPath).st_mtime)
    targetExisted = True
  else:
    if not os.path.exists(be.installPath): # TODO: isn't this alread accomplished? (above)
      utils.createDirs(be.installPath)
  
  linkProcess = None
  try:
    linkProcess = subprocess.Popen(linkCmd, stdout = subprocess.PIPE)
  except OSError as e:
    buildStatus.description = 'linking failed because: ' + str(e)
    log.error(buildStatus.description)
    buildStatus.writeToFile(buildPath)
    return False
  processOutput = linkProcess.communicate()[0]

  if be.compiler.startswith('msvc') and os.path.exists(tmpLinkCmdFp):
    os.remove(tmpLinkCmdFp)
  
  if os.path.exists(targetInstallPath):
    if targetExisted:
      if float(os.stat(targetInstallPath).st_mtime) > oldTargetTimeStamp:
        linked = True
    else:
      linked = True
  
  if linked:
    # buildStatus.description = 'linked {0} ({1} {2} {3})'.format(be.target, be.buildType, be.binaryFormat, be.compiler)
    # log.info(buildStatus.description)
    log.info('linked {0} ({1} {2} {3})'.format(be.target, be.buildType, be.binaryFormat, be.compiler))
  else:
    buildStatus.description = 'linking failed because ' + processOutput.decode('utf-8')
    log.info('linking failed because ' + buildStatus.description)
    # if writeBuildStatus:
    buildStatus.writeToFile(buildPath)
    return False
      
  if be.compiler.startswith('msvc') and multiThreaded and (be.binaryType == 'dynamic' or be.binaryType == 'executable'):
      
    # TODO: figure out what this #2 shit is, took 4 hours of bullshit to find out it's needed for maya plugins
    # mtCmd = 'mt -nologo -manifest ' + targetBuildPath + '.manifest -outputresource:' + targetBuildPath + ';#2'
    mtCmd = ['mt', '-nologo', '-manifest', targetInstallPath + '.manifest', '-outputresource:', targetInstallPath + ';#2']
    mtProcess = None
    try:
      mtProcess = subprocess.Popen(mtCmd, stdout = subprocess.PIPE) # shell = True,
    except OSError as e:
      log.error(str(e))
      return False
    processOutput = mtProcess.communicate()[0]

    buildStatus.description = processOutput.decode('utf-8')
    log.info(buildStatus.description)
  
  # install
  buildStatus.result = 1
  buildStatus.description = '{0} ({1} {2} {3}) build completed in {4} seconds'.format(be.target, be.buildType, be.binaryFormat, be.compiler, str(int(time.time() - startTime)))
  log.info(buildStatus.description)
  if be.binaryType == 'executable':
    print('') # formatting
  sys.stdout.flush()
  
  # if writeBuildStatus:
  buildStatus.writeToFile(buildPath)
  
  return True

