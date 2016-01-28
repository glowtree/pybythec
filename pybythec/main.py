
#
# py by the c
#

#
# a cross platform build system for c/c++
#
# written by Tom Sirdevan at glowtree
#
# contact: tom@glowtree.com
#

#
# can build c/c++ projects that create ...
#
# executables
# static  libraries: (herein called staticLib)
# dynamic libraries  (herein called dynamicLib)
# dynamic bundles / plugins, on OS X / Mach-O it's referred to as a bundle (herein called dynamic)
#

# _ (underscore) prefix denotes a private function

from pybythec import utils
from pybythec.BuildStatus import *
from pybythec.BuildElements import *

import os
import sys
import shutil
import time
import logging
import subprocess
from threading import Thread

log = logging.getLogger('pybythec')


# def _compileSrc(source, incPaths, compileCmd, objPathFlag, objExt, buildDir, objPaths, buildStatus):
def _compileSrc(be, compileCmd, source, objPaths, buildStatus):
  '''
    be (in): BuildElements object
    compileCmd (in): the compile command so far 
    source (in): the c or cpp source file to compile
    objPaths (out): list of all object paths that will be passed to the linker
    buildStatus (out): build status for this particular compile
  '''

  if not os.path.exists(source):
    buildStatus.writeError(source + ' is missing, exiting build')
    return

  objFile = os.path.basename(source)
  objFile = objFile.replace(os.path.splitext(source)[1], be.objExt)
  objPath = os.path.join(be.buildPath, objFile)
  objPaths.append(objPath) # + ' ')
  
  # check if it's up to date
  objExisted = os.path.exists(objPath)
  if objExisted:
    objTimestamp = float(os.stat(objPath).st_mtime)
    if not utils.sourceNeedsBuilding(be.incPaths, source, objTimestamp):
      buildStatus.result = 2 # up to date
      return

  # stupid Microsoft Visual C has to have the objPathFlag cuddled up directly next to the objPath - no space in between them!
  if be.compiler.startswith('msvc'):
    cmd = compileCmd + [source, be.objPathFlag + objPath]
  else:
    cmd = compileCmd + [source, be.objPathFlag, objPath]
  log.debug('\n' + ' '.join(cmd) + '\n')
  
  # compile
  try:
    # stupid Microsoft: pipes compiler info to stderr, so if you don't catch it here it spits it to the command line
    compileProcess = subprocess.Popen(cmd, stdout = subprocess.PIPE, stderr = subprocess.PIPE) 
  except OSError as e:
    buildStatus.writeError('compileProcess failed because ' + str(e))
    return
  buildStatus.description = compileProcess.communicate()[0].decode('utf-8')
  log.info(buildStatus.description)

  if os.path.exists(objPath):
    if objExisted:
      if float(os.stat(objPath).st_mtime) > objTimestamp:
        buildStatus.result = 1
    else:
      buildStatus.result = 1

  if buildStatus.result == 1:
    buildStatus.description = 'compiled ' + os.path.basename(source)
    

# def _buildLib(lib, libSrcDir, compilerCmd, compiler, osType, fileExt, buildType, binaryFormat, projectDir, buildStatus):
def _buildLib(be, libSrcDir, buildStatusDep):
  
  jsonPath = os.path.join(libSrcDir, '.pybythec.json')
  if not os.path.exists(jsonPath):
    buildStatus.writeError(libSrcDir + ' does not have a .pybythec.json file')
    return
  
  # build
  build(['-d', libSrcDir, '-os', be.osType, '-b', be.buildType, '-c', be.compiler, '-bf', be.binaryFormat, '-p', be.cwDir + '/.pybythecProject.json'])
  
  # read the build status
  buildStatusDep.readFromFile('{0}/.build/{1}/{2}/{3}'.format(libSrcDir, be.buildType, be.compiler, be.binaryFormat))


def _clean(be):
  '''
    cleans the current project
    be (in): BuildElements object
  '''

  if not os.path.exists(be.buildPath):
    log.info('{0} ({1} {2} {3}) already clean'.format(be.target, be.buildType, be.compiler, be.binaryFormat))
    return True
  
  for f in os.listdir(be.buildPath):
    os.remove(be.buildPath + '/' + f)
  os.removedirs(be.buildPath)

  if os.path.exists(be.targetInstallPath):
    os.remove(be.targetInstallPath)
  try:
    os.removedirs(be.installPath)
  except:
    pass
    
  log.info('{0} ({1} {2} {3}) all clean'.format(be.target, be.buildType, be.compiler, be.binaryFormat))
  return True


def _cleanall(be):
  '''
    cleans both the current project and also the dependencies

    be (input): BuildElements object
  '''
  _clean(be)
  for lib in be.libs:
    for libSrcPath in be.libSrcPaths:
      libPath = os.path.join(libSrcPath, lib)
      if os.path.exists(libPath):
        clean(['-d', libPath, '-os', be.osType, '-b', be.buildType, '-c', be.compiler, '-bf', be.binaryFormat])

#
# external functions to be called by the masses
#
def clean(argv):
  '''
  '''
  try:
    be = BuildElements(argv)
  except Exception as e:
    log.error(str(e))
    return False
  return _clean(be)

def cleanall(argv):
  '''
  '''
  try:
    be = BuildElements(argv)
  except Exception as e:
    log.error(str(e))
    return False
  return _cleanall(be)
    
def build(argv):
  '''
  '''
  #
  # cleaning
  #
  if '-cl' in argv:
    return clean(argv)
  if '-cla' in argv:
    return cleanall(argv)
  
  try:
    be = BuildElements(argv)
  except Exception as e:
    log.error(str(e))
    return False

  # lock - early return
  if be.locked and os.path.exists(be.targetInstallPath):
    buildStatus.writeInfo(2, be.target + ' is locked')
    return True

  #
  # building
  #
  startTime = time.time()
  
  threading = True
  
  log.info('building {0} ({1} {2} {3})'.format(be.target, be.buildType, be.compiler, be.binaryFormat))

  if not os.path.exists(be.installPath):
    utils.createDirs(be.installPath)

  if not os.path.exists(be.buildPath):
    os.makedirs(be.buildPath)

  incPathList = []
  for incPath in be.incPaths:
    incPathList += ['-I', incPath]
  
  definesList = []
  for define in be.defines:
    definesList += ['-D', define]
  
  buildStatus = BuildStatus(be.buildPath) # final build status

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
        mocPath = be.buildPath + '/moc_' + qtClassSrc
        mocCmd = ['moc'] + definesList + [includePath, '-o', mocPath]
        try:
          mocProcess = subprocess.call(mocCmd)
        except OSError as e:
          buildStatus.writeError('qt moc compilation failed because ' + str(e))
          return
        mocPaths.append(mocPath)
        
    if not found:
      buildStatus.writeError('can\'t find {0} for qt moc compilation'.format(qtClassHeader))
      return False

  for mocPath in mocPaths:
    be.sources.append(mocPath)

  buildStatusDeps = [] # the build status for each dependency: objs and libs
  threads = []
  i = 0

  #
  # compile
  #
  objPaths = []
  # cmd = [be.compilerCmd, '-c'] + incPathList + definesList + be.flags 
  cmd = [be.compilerCmd] + incPathList + definesList + be.flags
  
  if threading:
    for source in be.sources:
      buildStatusDep = BuildStatus()
      buildStatusDeps.append(buildStatusDep)
      # thread = Thread(None, target = _compileSrc, args = (source, be.incPaths, cmd, be.objPathFlag, be.objExt, be.buildPath, objPaths, buildStatusDep))
      thread = Thread(None, target = _compileSrc, args = (be, cmd, source, objPaths, buildStatusDep))
      thread.start()
      threads.append(thread)
      i += 1
  else:
    for source in be.sources:
      buildStatusDep = BuildStatus()
      buildStatusDeps.append(buildStatusDep)
      # _compileSrc(source, be.incPaths, cmd, be.objPathFlag, be.objExt, be.buildPath, objPaths, buildStatusDep)
      _compileSrc(be, cmd, source, objPaths, buildStatusDep)
      i += 1

  #
  # build dependencies
  #
  libCmds = []

  for lib in be.libs:
    libName = lib
    if be.compiler.startswith('msvc'): # stupid Microsoft again
      # TODO: somehow figure out if this lib is static or dynamic
      libCmds += [libName + be.staticLibExt]
    else:
      libCmds += [be.libFlag, libName]
      
    # check if the lib has a directory for building
    if threading:
      for libSrcDir in be.libSrcPaths:
        libSrcDir = os.path.join(libSrcDir, lib)
        if os.path.exists(libSrcDir):
          buildStatusDep = BuildStatus()
          buildStatusDeps.append(buildStatusDep)
          # thread = Thread(None, target = _buildLib, args = (lib, libSrcDir, be.compilerCmd, be.compiler, be.osType, be.staticLibExt, be.buildType, be.binaryFormat, be.cwDir, buildStatusDep))
          thread = Thread(None, target = _buildLib, args = (be, libSrcDir, buildStatusDep))
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
          # _buildLib(lib, be.libSrcPath, be.compilerCmd, be.compiler, be.osType, be.staticLibExt, be.buildType, be.binaryFormat, be.cwDir, buildStatusDep)
          _buildLib(be, libSrcDir, buildStatusDep)
          i += 1
          break

  # wait for all the threads before testing the results
  for thread in threads:
    thread.join()

  allUpToDate = True
  for buildStatusDep in buildStatusDeps:
    if buildStatusDep.result == 0:
      buildStatus.writeError('{0} ({1} {2} {3}) failed, determined in {4} seconds\n'.format(be.target, be.buildType, be.binaryFormat, be.compiler, str(int(time.time() - startTime))))
      return False
    elif buildStatusDep.result == 1:
      allUpToDate = False

  # revise the library paths
  for i in range(len(be.libPaths)):
    revisedLibPath = be.libPaths[i] + be.binaryRelPath
    if os.path.exists(revisedLibPath):
      be.libPaths[i] = revisedLibPath
    else: # in case there's also lib paths that don't have buildType, ie for external libraries that only ever have the release version
      revisedLibPath = '{0}/{1}/{2}'.format(be.libPaths[i], be.compiler, be.binaryFormat)
      if os.path.exists(revisedLibPath):
        be.libPaths[i] = revisedLibPath

  #
  # linking
  #
  linkCmd = []
  if allUpToDate and os.path.exists(be.targetInstallPath):
    buildStatus.writeInfo(2, '{0} ({1} {2} {3}) is up to date, determined in {4} seconds\n'.format(be.target, be.buildType, be.binaryFormat, be.compiler, str(int(time.time() - startTime))))
    return True
  
  # microsoft's compiler / linker can only handle so many characters on the command line (because it's stupid)
  tmpLinkCmdFp = be.buildPath + '/tmpLinkCmd'
  if be.compiler.startswith('msvc'):
    msvcTmpFile = open(tmpLinkCmdFp, 'w')
    msvcTmpFile.write('{0}"{1}" {2} {3}'.format(be.targetFlag, be.targetInstallPath, ' '.join(objPaths), ' '.join(libCmds)))
    msvcTmpFile.close()
    linkCmd += [be.linker, '@' + tmpLinkCmdFp]
  else:
    linkCmd += [be.linker, be.targetFlag, be.targetInstallPath] + objPaths + libCmds

  if be.binaryType != 'staticLib':
    linkCmd += be.linkFlags
    if be.binaryType != 'dynamicLib':
      for libPath in be.libPaths:
        if be.compiler.startswith('msvc'):
          linkCmd += [be.libPathFlag + os.path.normpath(libPath)]
        else:
          linkCmd += [be.libPathFlag, os.path.normpath(libPath)]
  
  # get the timestamp of the existing target if it exists
  linked = False
  targetExisted = False
  oldTargetTimeStamp = None
  if os.path.exists(be.targetInstallPath):
    oldTargetTimeStamp = float(os.stat(be.targetInstallPath).st_mtime)
    targetExisted = True
  else:
    if not os.path.exists(be.installPath): # TODO: isn't this alread accomplished? (above)
      utils.createDirs(be.installPath)
  
  log.debug('\n' + ' '.join(linkCmd) + '\n')
  
  linkProcess = None
  try:
    linkProcess = subprocess.Popen(linkCmd, stdout = subprocess.PIPE, stderr = subprocess.PIPE)
  except OSError as e:
    buildStatus.writeError('linking failed because: ' + str(e))
    return False
  processOutput = linkProcess.communicate()[0].decode('utf-8')

  if be.compiler.startswith('msvc') and os.path.exists(tmpLinkCmdFp):
    os.remove(tmpLinkCmdFp)
  
  if os.path.exists(be.targetInstallPath):
    if targetExisted:
      if float(os.stat(be.targetInstallPath).st_mtime) > oldTargetTimeStamp:
        linked = True
    else:
      linked = True
  
  if linked:
    log.info('linked {0} ({1} {2} {3})'.format(be.target, be.buildType, be.binaryFormat, be.compiler))
  else:
    buildStatus.writeError('linking failed because ' + processOutput)
    return False
  
  # TODO: finish this part
  # if be.compiler.startswith('msvc') and be.multithread and (be.binaryType == 'executable' or be.binaryType == 'dynamicLib' or be.binaryType == 'dynamic' ):
      
  #   # TODO: figure out what this #2 shit is, took 4 hours of bullshit to find out it's needed for maya plugins
  #   # mtCmd = 'mt -nologo -manifest ' + targetBuildPath + '.manifest -outputresource:' + targetBuildPath + ';#2'
  #   mtCmd = ['mt', '-nologo', '-manifest', be.targetInstallPath + '.manifest', '-outputresource:', be.targetInstallPath + ';#2']
  #   mtProcess = None
  #   try:
  #     mtProcess = subprocess.Popen(mtCmd, stdout = subprocess.PIPE)
  #   except OSError as e:
  #     buildStatus.writeError('mt failed because ' + str(e))
  #     return False

  #   log.info(mtProcess.communicate()[0].decode('utf-8'))
  
  # final check that binary file has appeared
  # startTime = time.time()
  # while not os.path.exists(targetInstallPath):
  #   time.sleep(0.01)
  #   if time.time() - startTime > 10: # shouldn't take more than 10 seconds for a file write
  #     buildStatus.writeError('{0} ({1} {2} {3}) build completed BUT {4} can\'t be found'.format(be.target, be.buildType, be.binaryFormat, be.compiler, targetInstallPath), buildPath)
  #     return False

  buildStatus.writeInfo(1, '{0} ({1} {2} {3}) build completed in {4} seconds ({5}\n)'.format(be.target, be.buildType, be.binaryFormat, be.compiler, str(int(time.time() - startTime)), be.targetInstallPath))
  
  sys.stdout.flush()

  return True

