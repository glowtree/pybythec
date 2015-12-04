

#
# py by the ca
#
# a cross platform build system for making c / c++ applications
#
# written by Tom Sirdevan @ glowtree
# 
# contact: pybythc@glowtree.com
#

#
# command line arguments
# 
# -c  compiler
# -o  os type: linux, osx, windows, android or ios
# -b  build type ie debug or release
# -bf binary format ie 32bit, 64bit etc
# -ws write the build status to a tmp file, 0 means don't write the status, 1 means do, by default NO tmp file is written
# -d  directory to build out of, becomes the current working directory
# -p  project directory, will search this directory for a pybythecProject.py config file and append any arguments ie defines 
#

#
# binaryType can be one of:
# static
# dynamic
# dynamicLib (for linux and osx this means prepending 'lib')
# dynamicMaya (for Windows this means the extension is '.mll' instead of '.dll)
# executable
#

# TODO: MSVC whole program optimization is turned off because it takes forever to compile and link, turn it on though if you ever actually release any software 
# -GL for the compiler and -LTCG for the linker

import utils

import os
import sys
import shutil
import time
import json
from jsmin import jsmin
import locale

import subprocess
from threading import Thread

logging.basicConfig(level = logging.DEBUG, format = '%(message)s') # DEBUG INFO
log = logging.getLogger('pybythec')

def compileSrc(source, incPaths, compileCmd, objPathFlag, objExt, buildDir, objPaths, output, results, i):
  '''
    return code:
    0 - failed
    1 - compiled
    2 - up to date, no compile happend
  '''
  results[i] = 0 # default to failed

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
    if not sourceNeedsBuilding(incPaths, source, objTimestamp):
      results[i] = 2
      return

  # compile
  cmd = compileCmd + source + ' ' + objPathFlag + objPath
  log.debug(cmd + '\n')
  try:
    compileProcess = subprocess.Popen(cmd, shell = True, stdout = subprocess.PIPE) # TODO: remove shell
  except OSError as e:
    log.error(str(e))
    return
  processOutput = compileProcess.communicate()[0]
  compileProcess.wait()

  if os.path.exists(objPath):
    if objExisted:
      if float(os.stat(objPath).st_mtime) > objTimestamp:
        results[i] = 1
    else:
      results[i] = 1

  if results[i] == 1:
    output[i] += 'compiled ' + os.path.basename(source)
  else:
    output[i] += processOutput.decode(locale.getdefaultlocale()[1])
  
  # time.sleep(0.1)

'''
  return code:
  0 - failed
  1 - built
  2 - up to date / locked, no build happened
'''
def buildLib(lib, libPaths, libSrcDir, compilerCmd, compiler, osType, fileExt, buildType, binaryFormat, projectDir, output, results, i):
  
  libPath      = str()
  libTimestamp = 0
  libExisted   = False

  # find the previously built lib in the lib install directories if it exists
  for libDir in libPaths:
    libPath = getLibPath(lib, libDir, compiler, fileExt)
    libExisted = os.path.exists(libPath)
    if libExisted:
      libTimestamp = float(os.stat(libPath).st_mtime)
      break
  
  # check / build the lib
  pyExecPath = os.path.join(libSrcDir, '.build.py')
  if not os.path.exists(pyExecPath):
    results[i] = 0
    log.warning(libSrcDir + ' does not have a .build.py file')
    return
  
  # TODO: don't need to pipe output anymore, could write output to the buildStatus.txt file instead
  
  # build
  libProcess = 0
  try:
    buildCmd = 'python {0} -c {1} -o {2} -d {3} -b {4} -bf {5} -ws 1 -p {6}'.format(pyExecPath, compiler, osType, libSrcDir, buildType, binaryFormat, projectDir)
    log.debug(buildCmd)
    libProcess = subprocess.Popen(buildCmd, shell = True, stdout = subprocess.PIPE, stderr = subprocess.PIPE)  # TODO: remove shell
  except OSError as e:
    results[i] = 0
    log.error('libProcess failed because ' + str(e))
    return
  time.sleep(0.01)
  processOutput = libProcess.communicate()
  libProcess.wait()
  
  poSize = len(processOutput)
  if poSize and len(processOutput[0]):
    output[i] = processOutput[0].decode('utf-8') # locale.getdefaultlocale()[1]) # convert from bytes to str

  if poSize > 1 and len(processOutput[1]):
    output[i] = processOutput[1].decode('utf-8') # locale.getdefaultlocale()[1])
  
  # read the build status
  bsPath = '{0}/.build/{1}/{2}/{3}/buildStatus.txt'.format(libSrcDir, buildType, binaryFormat, compiler) #Category)
  if not os.path.exists(bsPath):
    log.debug('error:{} doesn\'t exist'.format(bsPath))
    results[i] = 0
    return
  bsFile = open(bsPath, 'r')
  results[i] = int(bsFile.readline())
  # output[i] = int(bsFile.readline()) # TODO: use this if piping the output is no longer used 
  bsFile.close()

'''
  copy's the build target to the install target if the install target doesn't exist or is different than the build target
'''
def install(targetBuildPath, installBuildPath):
  if not len(installBuildPath):
    return
  
  if not os.path.exists(installBuildPath) or (float(os.stat(installBuildPath).st_mtime) != float(os.stat(targetBuildPath).st_mtime)):
    utils.copyfile(targetBuildPath, installBuildPath)


'''
  the main function
'''
def build():
  
  startTime = time.time()
      
  if binaryType == 'executable':
    print('') # formatting
  
  #
  # compiler specific initialization
  #
  compilerCmd = ''      # the compiler command ie if msvc090 is the compiler, but cl is the compilerCmd (with PATH pointing to the proper version of cl)
  # compilerVersion = 0   # the compiler version ie if msvc090 is the compiler, compilerVersion is 090
  compilerCategory = '' # compiler without the version ie if msvc090 is the compiler, compilerCategory is msvc
  linker      = str()
  targetFlag  = str()
  libFlag     = str()
  libPathFlag = str()
  objExt      = str()
  objPathFlag = str()
  
  sources   = []
  libs      = []
  defines   = []
  flags     = []
  linkFlags = []
  
  incPaths    = []
  libPaths    = []
  libSrcPaths = []
  
  gtClasses = []
  
  # json config files
  globalCf  = None
  projectCf = None
  localCf   = None

  if 'PYBYTHEC_GLOBAL' in os.environ:
    globalCf = loadJsonFile(os.environ['PYBYTHEC_GLOBAL'])
  elif 'g' in args:
    globalCf = loadJsonFile(args['g'])

  # project config
  if 'PYBYTHEC_PROJECT' in os.environ:
    projectCf = os.environ['PYBYTHEC_PROJECT'])
  elif 'p' in args:
    projectCf = loadJsonFile(args['p'])
  else:
    projectCf = loadJsonFile('.pybythecProject.json')

  # local config
  if os.path.exists('.pybythec.json'):
    localCf = loadJsonFile('.pybythec.json')
    
  be = BuildElements()
    
  if globalCf != None:
    getConfig1(globalCf, be)
  if projectCf != None:
    getConfig1(projectCf, be
  if localCf != None:
    getConfig1(localCf, be)
  
  if not be.goodToBuild():
    return
  
  writeBuildStatus = False
  
  pathSeparator = ':'
  
  # determine the compiler
  args = utils.getCmdLineArgs(argv)

  if 'c' in args:
    compiler = args['c']
  
  if 'o' in args:
    osType = args['o']
  
  if 'b' in args:
    buildType = args['b']
  
  if 'bf' in args:
    binaryFormat = args['bf']
  
  if 'ws' in args:
    writeBuildStatus = bool(int(args['ws']))
        
  compilerCategory = ''.join([i for i in compiler if i.isalpha()])
  
  compilerVersionStr = compiler.lstrip(compilerCategory)
  
  keys = ['all', compiler, osType, binaryType, buildType, binaryFormat]
  if compiler != compilerCategory:
    keys.append(compilerCategory)

  defines.append('_' + binaryFormat.upper())

  #
  # configuration files
  #
  # global config
  if 'PYBYTHEC_ROOT' in os.environ:
    rootPath = os.path.join(os.environ['PYBYTHEC_ROOT'], '.pybythecGlobals.json')
    loadConfigFile(rootPath, keys, defines, flags, linkFlags, incPaths, libPaths, pathSeparator)  

  # project config
  if 'p' in args:
    loadConfigFile(args['p'] + '/.pybythecProject.json', keys, defines, flags, linkFlags, incPaths, libPaths, pathSeparator)
  elif os.path.exists('.pybythecProject.json'):
    loadConfigFile('.pybythecProject.json', keys, defines, flags, linkFlags, incPaths, libPaths, pathSeparator)

  # local config
  if os.path.exists('.pybythec.json'):
    loadConfigFile('.pybythec.json', keys, defines, flags, linkFlags, incPaths, libPaths, pathSeparator)
  
  # supported compilers
  isGcc   = compiler.startswith('gcc')
  isClang = compiler.startswith('clang')
  isMsvc  = compiler.startswith('msvc')
  
  #
  # gcc / clang
  #
  if isGcc or isClang:
      
    compilerCmd = compiler
      
    if useCPlusPlus:
      if isGcc:
        compilerCmd = compilerCmd.replace('gcc', 'g++')
      else:
        compilerCmd = compilerCmd.replace('clang', 'clang++')
    
    objExt      = '.o'
    objPathFlag = '-o '
      
    # link
    linker        = compilerCmd
    targetFlag    = '-o '
    libFlag       = '-l'
    libPathFlag   = '-L'
    staticLibExt  = '.a'
    dynamicLibExt = '.so'
    if osType == 'osx' and isClang:
      dynamicLibExt = '.dylib'
      
    # if binaryType == 'static' or binaryType == 'dynamic':
    if binaryType == 'static' or binaryType == 'dynamicLib':
      target = 'lib' + target

    if binaryType == 'dynamicLib':
      binaryType = 'dynamic'

    if binaryType == 'static':
      target = target + '.a'
      linker = 'ar r'
      targetFlag = ''
    elif binaryType == 'dynamic':
      target = target + dynamicLibExt
    elif binaryType == 'bundle': # osx only
      target = target + '.bundle'
    elif binaryType == 'dynamicMaya':
      if osType == 'osx':
        target = target + '.bundle'
      else:
        target = target + dynamicLibExt
    elif binaryType != 'executable':
      log.error('unrecognized binary type: ' + binaryType)
      return False
          
    # default flags
    if useDefaultFlags:
      if multiThreaded and binaryType != 'static':
        libs.append('pthread')        

  #
  # msvc / msvc
  #
  elif compiler.startswith('msvc'):
      
    # compile
    compilerCmd = 'cl'
    objExt      = '.obj'
    objPathFlag = '/Fo'
    flags.append('/nologo /errorReport:prompt')
    pathSeparator = ';'
        
    if useDefaultFlags:
      # flags.append('/EHsc /Gy')
        
      if buildType == 'debug':
        flags.append('/W1 /RTC1 /Z7')
        if multiThreaded:
          flags.append('/MDd')
              
      elif buildType == 'release':
        flags.append('/DNDEBUG /O2') #' -GL'
        if multiThreaded:
          flags.append('/MD')
    
    # link 
    linker        = 'link'
    targetFlag    = '/OUT:' # can't be '-OUT:' for @tmpLinkCmd to work
    libFlag       = ''
    libPathFlag   = '/LIBPATH:'
    staticLibExt  = '.lib'
    dynamicLibExt = '.dll'
    linkFlags.append('/NOLOGO /ERRORREPORT:PROMPT')
    if binaryFormat == '64bit':
      linkFlags.append('/MACHINE:X64')
    
    if binaryType == 'static':
      target += staticLibExt
      linker  = 'lib'
    elif binaryType == 'dynamic':
      target    += dynamicLibExt
      linkFlags.append('/DLL')
    elif binaryType == 'dynamicMaya': # windows only
      target += '.mll'
      linkFlags.append('/DLL')
    elif binaryType == 'executable':
      target += '.exe'
    else:
      log.error('unrecognized binary type: ' + binaryType)
      return False
    
    if useDefaultFlags:
      linkFlags.append('/NODEFAULTLIB:LIBCMT') #:libc.lib' #-DYNAMICBASE -NXCOMPAT
      if buildType == 'debug':
        linkFlags.append('/DEBUG') # -INCREMENTAL 
      elif buildType == 'release':
        linkFlags.append('/INCREMENTAL:NO /OPT:REF /OPT:ICF') # -LTCG'

  else:
    log.error('unknown compiler')
    return False

  #
  # general initialization
  #
  threading = True
  
  # ensure all the paths are absolute for multi-threading
  cwDir = os.getcwd()
  if 'd' in args:
    cwDir = args['d']

  utils.makePathsAbsolute(cwDir, sources)
  utils.makePathsAbsolute(cwDir, incPaths)
  utils.makePathsAbsolute(cwDir, libPaths)
  utils.makePathsAbsolute(cwDir, libSrcPaths)
  
  binaryRelPath = '/{0}/{1}/{2}'.format(buildType, binaryFormat, compiler)
  
  buildPath = utils.makePathAbsolute(cwDir, './.build' + binaryRelPath)
  
  if len(installPath):
    installPath = utils.makePathAbsolute(cwDir, installPath)
    # if binaryType != 'executable':
    if binaryType == 'static':
      installPath += binaryRelPath

  for i in range(len(libPaths)):
    revisedLibPath = libPaths[i] + binaryRelPath
    if os.path.exists(revisedLibPath):
      libPaths[i] = revisedLibPath
    else: # in case there's also lib paths that don't have  buildType, ie for external libraries that only ever have the release version
      revisedLibPath = '{0}/{1}/{2}'.format(libPaths[i], binaryFormat, compiler) 
      if os.path.exists(revisedLibPath):
        libPaths[i] = revisedLibPath

  targetBuildPath   = os.path.join(buildPath,   target)
  targetInstallPath = os.path.join(installPath, target)
  
  #
  # clean
  #
  if 1 in args and args[1].startswith('clean'):
  
    if args[1] == 'cleanall':
      for lib in libs:
        for libSrcPath in libSrcPaths:
          utils.buildClean(os.path.join(libSrcPath, lib), buildType, binaryFormat, compiler)

    if not os.path.exists(buildPath):
      log.info('{0} ({1} {2} {3}) already clean'.format(target, buildType, binaryFormat, compiler))
      return True
        
    shutil.rmtree(buildPath)
    
    if os.path.exists(targetInstallPath):
      os.remove(targetInstallPath)
    
    log.info('{0} ({1} {2} {3}) all clean'.format(target, buildType, binaryFormat, compiler))
    return True

  # lock - early return
  if locked and os.path.exists(targetBuildPath):
    install(targetBuildPath, installPath)
    log.info(target + ' is locked')
    if writeBuildStatus:
        writeBS(buildPath, '2')
    return True

  #
  # building
  #
  log.info('building {0} ({1} {2} {3})'.format(target, buildType, compiler, binaryFormat))

  if not os.path.exists(buildPath):
    os.makedirs(buildPath)

  i = 0
  output  = []
  results = []
  threads = []
  
  #
  # compile source
  #
  incPathsStr = str()
  for incDir in incPaths:
    incPathsStr += ' -I"' + incDir + '" '
  
  definesStr = str()
  for define in defines:
    definesStr += '-D' + define + ' '
  
  flagsStr = ' '.join(flags)
  
  cmd = compilerCmd + ' -c' + incPathsStr + definesStr + flagsStr + ' '
  log.debug(cmd)

  objPaths = []
    
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
    sources.append(mocPath)

  if threading:
    for source in sources:

      output.append(str())
      results.append(0)
      thread = Thread(None, target = compileSrc, args = (source, incPaths, cmd, objPathFlag, objExt, buildPath, objPaths, output, results, i))
      thread.start()
      threads.append(thread)
      i += 1
  else:
    for source in sources:
      output.append(str())
      results.append(0)
      compileSrc(source, incPaths, cmd, objPathFlag, objExt, buildPath, objPaths, output, results, i)
      i += 1
  
  srcEndIndex = i - 1
  
  #
  # build library dependencies
  #
  libCmds = str()
  if len(libs):
    for lib in libs:

      libCmds += libFlag + lib
      if compiler.startswith('msvc'):
        libCmds += staticLibExt
      libCmds += ' '
        
      # check if the lib has a directory for building
      if threading:
        for libSrcDir in libSrcPaths:
          libSrcDir = '{0}/{1}'.format(libSrcDir, lib)
          if os.path.exists(libSrcDir):
            output.append(str())
            results.append(0)
            # TODO: staticLibExt should probably be a list with both static and dynamic file extensions
            thread = Thread(None, target = buildLib, args = (lib, libPaths, libSrcDir, compilerCmd, compiler, osType, staticLibExt, buildType, binaryFormat, cwDir, output, results, i))
            thread.start()
            threads.append(thread)
            i += 1
            break
      else:
        for libSrcDir in libSrcPaths:
          libSrcDir = '{0}/{1}'.format(libSrcDir, lib)
          if os.path.exists(libSrcDir):
            output.append(str())
            results.append(0)
            # TODO: staticLibExt should probably be a list with both static and dynamic file extensions
            buildLib(lib, libPaths, libSrcDir, compilerCmd, compiler, osType, staticLibExt, buildType, binaryFormat, cwDir, output, results, i)
            i += 1
            break

  # check the results of all the threads
  for thread in threads:
    thread.join()

  # for neater output
  if binaryType == 'executable':
    if len(output[srcEndIndex]):
      output[srcEndIndex] += '\n'
    else:
      output[srcEndIndex] = ' '
  
  i = 0
  allUpToDate = True
  for result in results:
    if len(output[i]):
      log.info(output[i])
    if result == 0:
      log.info('{0} ({1} {2} {3}) failed, determined in {4} seconds\n'.format(target, buildType, binaryFormat, compiler, str(int(time.time() - startTime))))
      if writeBuildStatus:   
        writeBS(buildPath, '0')
      return False
    elif result == 1:
      allUpToDate = False
    i += 1
  
  objPaths = ''.join(objPaths)

  #
  # link objs or libraries
  #    
  if allUpToDate and os.path.exists(targetBuildPath):
    install(targetBuildPath, installPath)
    log.info('{0} ({1} {2} {3}) is up to date, determined in {4} seconds\n'.format(target, buildType, binaryFormat, compiler, str(int(time.time() - startTime))))
    if writeBuildStatus:   
      writeBS(buildPath, '2')
    return True
  
  # microsoft's compiler / linker can only handle so many characters on the command line
  tmpLinkCmdFp = buildPath + '/tmpLinkCmd'
  if compiler.startswith('msvc'):
    msvcTmpFile = open(tmpLinkCmdFp, 'w')
    msvcTmpFile.write('{0}"{1}" {2} {3}'.format(targetFlag, targetBuildPath, objPaths, libCmds))
    msvcTmpFile.close()
    linkCmd = '{0} @{1} '.format(linker, tmpLinkCmdFp)
  else:                               
    linkCmd = '{0} {1} "{2}" {3} {4}'.format(linker, targetFlag, targetBuildPath, objPaths, libCmds)

  if binaryType != 'static':
    for libPath in libPaths:
      linkCmd += libPathFlag + '"' + os.path.normpath(libPath) + '" '
  
  if binaryType != 'static':
    linkCmd += ' '.join(linkFlags)
      
  log.debug(linkCmd + '\n')
  # print(linkCmd + '\n')
  
  # get the timestamp of the existing target if it exists
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
  
  if compiler.startswith('msvc') and os.path.exists(tmpLinkCmdFp):
    os.remove(tmpLinkCmdFp)
  
  if os.path.exists(targetBuildPath):
    if targetExisted:
      if float(os.stat(targetBuildPath).st_mtime) > oldTargetTimeStamp:
        linked = True
    else:
      linked = True    
  
  if linked:
    log.info('linked {0} ({1} {2} {3})'.format(target, buildType, binaryFormat, compiler))
  else:
    log.info(processOutput.decode('utf-8'))
    return False
      
  if compiler.startswith('msvc') and multiThreaded and binaryType != 'static':
      
    # TODO: figure out what this #2 shit is, took 4 hours of bullshit to find out it's needed for maya plugins
    mtCmd = 'mt -nologo -manifest ' + targetBuildPath + '.manifest -outputresource:' + targetBuildPath + ';#2'
    mtProcess = None
    try:
        mtProcess = subprocess.Popen(mtCmd, shell = True, stdout = subprocess.PIPE)  # TODO: remove shell
    except OSError as e:
        log.error(str(e))
        return False
    processOutput = mtProcess.communicate()[0]
    mtProcess.wait()			
    log.info(processOutput.decode('utf-8'))
  
  # install
  install(targetBuildPath, installPath)
  
  log.info('{0} ({1} {2} {3}) build completed in {4} seconds'.format(target, buildType, binaryFormat, compiler, str(int(time.time() - startTime))))
  if binaryType == 'executable':
    print('') # formatting
  sys.stdout.flush()
  
  if writeBuildStatus:
    writeBS(buildPath, '1')
  
  return True

