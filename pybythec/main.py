

#
# py by the c
#
# a cross platform build system for making c / c++ applications
#
# written by Tom Sirdevan @glowtree
# 
# contact: pybythc@glowtree.com
#

#
# command line arguments
# 
# -c  be.compiler
# -o  os type: linux, osx, windows, android or ios
# -b  build type ie debug or release
# -bf binary format ie 32bit, 64bit etc
# -ws write the build status to a tmp file, 0 means don't write the status, 1 means do, by default NO tmp file is written
# -d  directory to build out of, becomes the current working directory
# -p  project directory, will search this directory for a pybythecProject.py config file and append any arguments ie defines 
#

#
# binaryType can be one of:
# staticLib  
# dynamicLib (for linux and osx this means prepending 'lib')
# dynamic
# executable
#

# for staticLib and dynamicLib on linux and osx this means prepending 'lib'
# on osx dynamic refers to a bundle


import utils
from buildObjects import *

import os
import sys
import shutil
import time
import logging
import locale
import subprocess
from threading import Thread

log = logging.getLogger('pybythec')

# def compileSrc(source, incPaths, compileCmd, objPathFlag, objExt, buildDir, objPaths, output, results, i):
def compileSrc(source, incPaths, compileCmd, objPathFlag, objExt, buildDir, objPaths, buildStatus):#output, results, i):

  # buildStatus.result = 0 # default to failed

  if not os.path.exists(source):
    log.warning(source + ' is missing, exiting build')
    return

  objFile = os.path.basename(source)
  objFile = objFile.replace(os.path.splitext(source)[1], objExt)
  objPath = os.path.join(buildDir, objFile)
  objPaths.append(objPath + ' ')
  
  # check if it's up to date
  objExisted = os.path.exists(objPath)
  if objExisted:
    objTimestamp = float(os.stat(objPath).st_mtime)
    if not utils.sourceNeedsBuilding(incPaths, source, objTimestamp):
      buildStatus.result = 2 # up to date
      return

  # compile
  cmd = compileCmd + source + ' ' + objPathFlag + objPath
  # cm = ['
  log.debug(cmd + '\n')
  try:
    compileProcess = subprocess.Popen(cmd, shell = True, stdout = subprocess.PIPE) # TODO: remove shell
    # compileProcess = subprocess.Popen(cmd, shell = True, stdout = subprocess.PIPE) # TODO: remove shell
  except OSError as e:
    log.error(str(e))
    return
  processOutput = compileProcess.communicate()[0]
  # compileProcess.wait()

  if os.path.exists(objPath):
    if objExisted:
      if float(os.stat(objPath).st_mtime) > objTimestamp:
        buildStatus.result = 1
    else:
      buildStatus.result = 1

  if buildStatus.result == 1:
    buildStatus.description += 'compiled ' + os.path.basename(source)
  else:
    buildStatus.description += processOutput.decode(locale.getdefaultlocale()[1])
  
  # time.sleep(0.1)

'''
  return code:
  0 - failed
  1 - built
  2 - up to date / locked, no build happened
'''
def buildLib(lib, libPaths, libSrcDir, compilerCmd, compiler, osType, fileExt, buildType, binaryFormat, projectDir, buildStatus:
  
  libPath      = str()
  libTimestamp = 0
  libExisted   = False

  # find the previously built lib in the lib install directories if it exists
  for libDir in libPaths:
    libPath = utils.getLibPath(lib, libDir, compiler, fileExt)
    libExisted = os.path.exists(libPath)
    if libExisted:
      libTimestamp = float(os.stat(libPath).st_mtime)
      break
  
  # check / build the lib
  # pyExecPath = os.path.join(libSrcDir, '.build.py')
  # if not os.path.exists(pyExecPath):
  #   results[i] = 0
  #   log.warning(libSrcDir + ' does not have a .build.py file')
  #   return
  
  jsonPath = os.path.join(libSrcDir, '.pybythec.json')
  if not os.path.exists(jsonPath):
    # results[i] = 0
    log.warning(libSrcDir + ' does not have a .pybythec.json file')
    return
  
  # TODO: don't need to pipe output anymore, could write output to the buildStatus.txt file instead
  
  # build
  libProcess = 0
  try:
    # buildCmd = 'python {0} -c {1} -o {2} -d {3} -b {4} -bf {5} -ws 1 -p {6}'.format(pyExecPath, compiler, osType, libSrcDir, buildType, binaryFormat, projectDir)
    buildCmd = 'pybythc -c {0} -o {1} -d {2} -b {3} -bf {4} -ws 1 -p {5}'.format(compiler, osType, libSrcDir, buildType, binaryFormat, projectDir)
    log.debug(buildCmd)
    libProcess = subprocess.Popen(buildCmd, shell = True)#, stdout = subprocess.PIPE, stderr = subprocess.PIPE)  # TODO: remove shell
  except OSError as e:
    # results[i] = 0
    # buildStatus.result = 0
    log.error('libProcess failed ause ' + str(e))
    return
  time.sleep(0.01)
  # processOutput = libProcess.communicate()
  libProcess.wait()
  
  # poSize = len(processOutput)
  # if poSize and len(processOutput[0]):
  #   output[i] = processOutput[0].decode('utf-8') # locale.getdefaultlocale()[1]) # convert from bytes to str

  # if poSize > 1 and len(processOutput[1]):
  #   output[i] = processOutput[1].decode('utf-8') # locale.getdefaultlocale()[1])
  
  # read the build status
  bsPath = '{0}/.build/{1}/{2}/{3}/buildStatus.txt'.format(libSrcDir, buildType, binaryFormat, compiler) #Category)
  if not os.path.exists(bsPath):
    log.debug('error:{0} doesn\'t exist'.format(bsPath))
    # buildStatus.result = 0
    return
  bsFile = open(bsPath, 'r')
  buildStatus.result = int(bsFile.readline())
  buildStatus.description = bsFile.readline()
  # results[i] = int(bsFile.readline())
  # output[i] = int(bsFile.readline()) # TODO: use this if piping the output is no longer used 
  bsFile.close()

# '''
#   copy's the build target to the install target if the install target doesn't exist or is different than the build target
# '''
# def install(targetBuildPath, installBuildPath):
#   if not len(installBuildPath):
#     return
  
#   if not os.path.exists(installBuildPath) or (float(os.stat(installBuildPath).st_mtime) != float(os.stat(targetBuildPath).st_mtime)):
#     utils.copyfile(targetBuildPath, installBuildPath)


'''
  the main function
'''
def build(argv):
  
  startTime = time.time()
    
  #
  # compiler specific initialization
  #
  compilerCmd = ''      # the compiler command ie if msvc090 is the compiler, but cl is the compilerCmd
  linker      = str()
  targetFlag  = str()
  libFlag     = str()
  libPathFlag = str()
  objExt      = str()
  objPathFlag = str()
  
  gtClasses = []
  
  args = utils.getCmdLineArgs(argv)
  
  # json config files
  globalCf  = None
  projectCf = None
  localCf   = None

  # global config
  if 'PYBYTHEC_GLOBALS' in os.environ:
    globalCf = utils.loadJsonFile(os.environ['PYBYTHEC_GLOBALS'])
  elif 'g' in args:
    globalCf = utils.loadJsonFile(args['g'])
  else:
    globalCf = utils.loadJsonFile('.pybythecGlobal.json')

  # project config
  if 'PYBYTHEC_PROJECT' in os.environ:
    projectCf = os.environ['PYBYTHEC_PROJECT']
  elif 'p' in args:
    projectCf = utils.loadJsonFile(args['p'])
  else:
    projectCf = utils.loadJsonFile('.pybythecProject.json')

  # local config
  if os.path.exists('.pybythec.json'):
    localCf = utils.loadJsonFile('.pybythec.json')
    
  be = BuildElements()
    
  if globalCf != None:
    be.getBuildElements(globalCf)
  if projectCf != None:
    be.getBuildElements(projectCf)
  if localCf != None:
    be.getBuildElements(localCf)
    
  if be.binaryType == 'executable':
    print('') # formatting
  
  writeBuildStatus = False
  
  # command line overrides
  if 'c' in args:
    be.compiler = args['c']
  
  if 'o' in args:
    be.osType = args['o']
  
  if 'b' in args:
    be.buildType = args['b']
  
  if 'bf' in args:
    be.binaryFormat = args['bf']
  
  if 'ws' in args:
    writeBuildStatus = bool(int(args['ws']))
  
  be.setKeys()

  if globalCf != None:
    be.getBuildElements2(globalCf)
  if projectCf != None:
    be.getBuildElements2(projectCf)
  if localCf != None:
    be.getBuildElements2(localCf)
  
  # ensure all the paths are absolute for multi-threading
  cwDir = os.getcwd()
  if 'd' in args:
    cwDir = args['d']
    
  be.resolvePaths(cwDir)
   
  if not be.goodToBuild():
    return
   
  # supported compilers
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
    objPathFlag = '-o '
    be.defines.append('_' + be.binaryFormat.upper()) # TODO you sure?
      
    # link
    linker        = compilerCmd
    targetFlag    = '-o '
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
      linker = 'ar r'
      targetFlag = ''
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
    targetFlag    = '/OUT:' # can't be '-OUT:' for @tmpLinkCmd to work
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
    log.error('unknown compiler')
    return False

  #
  # general initialization
  #
  binaryRelPath = '/{0}/{1}/{2}'.format(be.buildType, be.compiler, be.binaryFormat)
  
  buildPath = utils.makePathAbsolute(cwDir, './.build' + binaryRelPath)
  
  if be.libInstallPathAppend and (be.binaryType == 'staticLib' or be.binaryType == 'dynamicLib'):
    be.installPath += binaryRelPath

  for i in range(len(be.libPaths)):
    revisedLibPath = be.libPaths[i] + binaryRelPath
    if os.path.exists(revisedLibPath):
      be.libPaths[i] = revisedLibPath
    else: # in case there's also lib paths that don't have  be.buildType, ie for external libraries that only ever have the release version
      revisedLibPath = '{0}/{1}/{2}'.format(be.libPaths[i], be.binaryFormat, be.compiler) 
      if os.path.exists(revisedLibPath):
        be.libPaths[i] = revisedLibPath

  targetBuildPath   = os.path.join(buildPath,   be.target)
  targetInstallPath = os.path.join(be.installPath, be.target)
  
  # log.debug('be.installPath {0}'.format(targetInstallPath))
  
  #
  # clean
  #
  if 1 in args and args[1].startswith('clean'):
  
    if args[1] == 'cleanall':
      for lib in libs:
        for libSrcPath in libSrcPaths:
          utils.buildClean(os.path.join(libSrcPath, lib), be.buildType, be.binaryFormat, be.compiler)

    if not os.path.exists(buildPath):
      log.info('{0} ({1} {2} {3}) already clean'.format(be.target, be.buildType, be.binaryFormat, be.compiler))
      return True
        
    shutil.rmtree(buildPath)
    
    if os.path.exists(targetInstallPath):
      os.remove(targetInstallPath)
    
    log.info('{0} ({1} {2} {3}) all clean'.format(be.target, be.buildType, be.binaryFormat, be.compiler))
    return True

  # lock - early return
  if be.locked and os.path.exists(targetBuildPath):
    install(targetBuildPath, installPath)
    log.info(be.target + ' is be.locked')
    if writeBuildStatus:
        writeBS(buildPath, '2')
    return True

  #
  # building
  #
  threading = True
  
  log.info('building {0} ({1} {2} {3})'.format(be.target, be.buildType, be.compiler, be.binaryFormat))

  if not os.path.exists(buildPath):
    os.makedirs(buildPath)

  i = 0
  buildResults = []
  # output  = []
  # results = []
  threads = []
  
  #
  # compile source
  #
  incPathsStr = str()
  for incDir in be.incPaths:
    incPathsStr += ' -I"' + incDir + '" '
  
  definesStr = str()
  for define in be.defines:
    definesStr += '-D' + define + ' '
  
  flagsStr = ' '.join(be.flags)
  
  cmd = compilerCmd + ' -c' + incPathsStr + definesStr + flagsStr + ' '

  objPaths = []
    
  #
  # Qt moc file compilation
  #
  # TODO: timestamp check to see if this needs to happen or if it's up to date
  mocPaths = []
  for qtClass in gtClasses:
    found = False
    qtClassSrc    = qtClass + '.cpp'
    qtClassHeader = qtClass + '.h'
    for incPath in incPaths:  # find the header file
      includePath = incPath + '/' + qtClassHeader
      if os.path.exists(includePath):
        found = True
        mocPath = buildPath + '/moc_' + qtClassSrc
        # mocCmd = 'moc {0} {1} {2} -o {3}'.format(incPathsStr, definesStr, includePath, mocPath)
        mocCmd = 'moc {0} {1} -o {2}'.format(definesStr, includePath, mocPath)
        try:
          mocProcess = subprocess.Popen(mocCmd, shell = True, stdin = subprocess.PIPE)
        except OSError as e:
          log.error(str(e))
          continue
        mocProcess.wait()
        mocPaths.append(mocPath)
        
    if not found:    
      log.error('can\'t find {0} for qt moc compilation'.format(qtClassHeader))
      return

  for mocPath in mocPaths:
    be.sources.append(mocPath)

  if threading:
    for source in be.sources:
      # output.append(str())
      # results.append(0)
      buildStatus.append(BuildStatus())
      thread = Thread(None, target = compileSrc, args = (source, be.incPaths, cmd, objPathFlag, objExt, buildPath, objPaths, buildResults[i]))#output, results, i))
      thread.start()
      threads.append(thread)
      i += 1
  else:
    for source in be.sources:
      # output.append(str())
      # results.append(0)
      buildStatus.append(BuildStatus())
      # compileSrc(source, be.incPaths, cmd, objPathFlag, objExt, buildPath, objPaths, output, results, i)
      compileSrc(source, be.incPaths, cmd, objPathFlag, objExt, buildPath, objPaths, buildResults[i])
      i += 1
  
  srcEndIndex = i - 1
  
  #
  # build library dependencies
  #
  libCmds = str()
  if len(be.libs):
    for lib in be.libs:

      libCmds += libFlag + lib
      if be.compiler.startswith('msvc'):
        libCmds += staticLibExt # TODO: both the staticLibExt and dynamicLibExt
      libCmds += ' '
        
      # check if the lib has a directory for building
      if threading:
        for libSrcDir in be.libSrcPaths:
          libSrcDir = '{0}/{1}'.format(libSrcDir, lib)
          if os.path.exists(libSrcDir):
            buildResults.append(BuildStats())
            # output.append(str())
            # results.append(0)
            # TODO: staticLibExt should probably be a list with both static and dynamic file extensions
            thread = Thread(None, target = buildLib, args = (lib, be.libPaths, libSrcDir, compilerCmd, be.compiler, be.osType, staticLibExt, be.buildType, be.binaryFormat, cwDir, buildResults[i]))
            thread.start()
            threads.append(thread)
            i += 1
            break
      else:
        for libSrcPath in be.libSrcPaths:
          libSrcPath = '{0}/{1}'.format(libSrcPath, lib)
          if os.path.exists(libSrcPath):
            buildResults.append(BuildStats())
            # output.append(str())
            # results.append(0)
            # TODO: staticLibExt should probably be a list with both static and dynamic file extensions
            buildLib(lib, be.libPaths, be.libSrcPath, compilerCmd, be.compiler, be.osType, staticLibExt, be.buildType, be.binaryFormat, cwDir, buildResults[i])
            i += 1
            break

  # check the results of all the threads
  for thread in threads:
    thread.join()

  # for neater output
  if be.binaryType == 'executable':
    if len(output[srcEndIndex]):
      output[srcEndIndex] += '\n'
    else:
      output[srcEndIndex] = ' '
  
  allUpToDate = True
  for buildStatus in buildResults:
    if len(buildStatus.description):
      log.info(result.description)
    if buildStatus.result == 0:
      log.info('{0} ({1} {2} {3}) failed, determined in {4} seconds\n'.format(be.target, be.buildType, be.binaryFormat, be.compiler, str(int(time.time() - startTime))))
      if writeBuildStatus:   
        writeBS(buildPath, '0')
      return False
    elif buildStatus.result == 1:
      allUpToDate = False

  objPaths = ''.join(objPaths)

  #
  # link objs or libraries
  #    
  if allUpToDate and os.path.exists(targetBuildPath):
    # install(targetBuildPath, be.installPath)
    log.info('{0} ({1} {2} {3}) is up to date, determined in {4} seconds\n'.format(be.target, be.buildType, be.binaryFormat, be.compiler, str(int(time.time() - startTime))))
    if writeBuildStatus:   
      writeBS(buildPath, '2')
    return True
  
  # microsoft's compiler / linker can only handle so many characters on the command line
  tmpLinkCmdFp = buildPath + '/tmpLinkCmd'
  if be.compiler.startswith('msvc'):
    msvcTmpFile = open(tmpLinkCmdFp, 'w')
    # msvcTmpFile.write('{0}"{1}" {2} {3}'.format(targetFlag, targetBuildPath, objPaths, libCmds))
    msvcTmpFile.write('{0}"{1}" {2} {3}'.format(targetFlag, targetInstallPath, objPaths, libCmds))
    msvcTmpFile.close()
    linkCmd = '{0} @{1} '.format(linker, tmpLinkCmdFp)
  else:                               
    # linkCmd = '{0} {1} "{2}" {3} {4}'.format(linker, targetFlag, targetBuildPath, objPaths, libCmds)
    linkCmd = '{0} {1} "{2}" {3} {4}'.format(linker, targetFlag, targetInstallPath, objPaths, libCmds)

  if be.binaryType != 'staticLib': # and be.binaryType != 'dynamicLib':
    linkCmd += ' '.join(be.linkFlags)
    if be.binaryType != 'dynamicLib':
      for libPath in libPaths:
        linkCmd += libPathFlag + '"' + os.path.normpath(libPath) + '" '
  
  log.debug(linkCmd + '\n')
  # print(linkCmd + '\n')
  
  # get the timestamp of the existing be.target if it exists
  linked = False
  targetExisted = False
  oldTargetTimeStamp = None
  if os.path.exists(targetBuildPath):
    oldTargetTimeStamp = float(os.stat(targetBuildPath).st_mtime)
    targetExisted = True
      
  linkProcess = None
  try:
    linkProcess = subprocess.Popen(linkCmd, shell = True, stdout = subprocess.PIPE)  # TODO: remove shell
  except OSError as e:
    log.error(str(e))
    return False
  processOutput = linkProcess.communicate()[0]
  linkProcess.wait()
  
  if be.compiler.startswith('msvc') and os.path.exists(tmpLinkCmdFp):
    os.remove(tmpLinkCmdFp)
  
  if os.path.exists(targetBuildPath):
    if targetExisted:
      if float(os.stat(targetBuildPath).st_mtime) > oldTargetTimeStamp:
        linked = True
    else:
      linked = True    
  
  if linked:
    log.info('linked {0} ({1} {2} {3})'.format(be.target, be.buildType, be.binaryFormat, be.compiler))
  else:
    log.info(processOutput.decode('utf-8'))
    return False
      
  if be.compiler.startswith('msvc') and multiThreaded and (be.binaryType == 'dynamic' or be.binaryType == 'executable'):
      
    # TODO: figure out what this #2 shit is, took 4 hours of bullshit to find out it's needed for maya plugins
    mtCmd = 'mt -nologo -manifest ' + targetBuildPath + '.manifest -outputresource:' + targetBuildPath + ';#2'
    mtProcess = None
    try:
      mtProcess = subprocess.Popen(mtCmd, stdout = subprocess.PIPE)  # shell = True
    except OSError as e:
      log.error(str(e))
      return False
    processOutput = mtProcess.communicate()[0]
    mtProcess.wait()			
    log.info(processOutput.decode('utf-8'))
  
  # install
  # install(targetBuildPath, be.installPath)
  
  log.info('{0} ({1} {2} {3}) build completed in {4} seconds'.format(be.target, be.buildType, be.binaryFormat, be.compiler, str(int(time.time() - startTime))))
  if be.binaryType == 'executable':
    print('') # formatting
  sys.stdout.flush()
  
  if writeBuildStatus:
    writeBS(buildPath, '1')
  
  return True

