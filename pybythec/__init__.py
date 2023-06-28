# -*- coding: utf-8 -*-
from pybythec import utils
from pybythec.utils import PybythecError
from pybythec.BuildStatus import BuildStatus
from pybythec.BuildElements import BuildElements
from multiprocessing import Process, Queue
from threading import Thread
import traceback
import os
import time

log = utils.log

__author__ = 'glowtree'
__email__ = 'tom@glowtree.com'
__version__ = '0.9.64'


def getBuildElements(osType = None,
                     compiler = None,
                     buildType = None,
                     binaryFormat = None,
                     projConfigPath = None,
                     globalConfigPath = None,
                     projConfig = None,
                     globalConfig = None,
                     currentBuild = None,
                     libDir = None):
    '''
        passthrough function that catches and reports exceptions
    '''
    try:
        return BuildElements(osType = osType,
                             compiler = compiler,
                             buildType = buildType,
                             binaryFormat = binaryFormat,
                             projConfig = projConfig,
                             projConfigPath = projConfigPath,
                             globalConfig = globalConfig,
                             globalConfigPath = globalConfigPath,
                             currentBuild = currentBuild,
                             libDir = libDir)
    except PybythecError as e:
        log.error(e)
        return None
    except Exception as e:
        log.error(f'unknown exception: {str(e)}\n{traceback.format_exc()}')
        return None


def build(be = None, builds = None):
    '''
        be: BuildElements object
        builds: list of build overrides
    '''
    if not be:
        be = getBuildElements()
        if not be:
            return

    _runPreScript(be)

    buildsRef = builds
    if not buildsRef:
        buildsRef = be.builds
    if type(buildsRef) is not list:
        buildsRef = [buildsRef]

    for br in buildsRef:
        try:
            be.configBuild(currentBuild = br)
        except PybythecError as e:
            log.error(e)
            continue
        except Exception as e:
            log.error(f'unknown exception: {str(e)}\n{traceback.format_exc()}')
            continue
        log.debug(br)
        _build(be)


def _build(be):
    '''
        does the dirty work of compiling and linking based on the state setup in the BuildElements object be
    '''

    buildStatus = BuildStatus(be.targetFilename, be.buildDirPathShell)

    # lock - early return
    if be.locked and utils.pathExists(be.installPathShell):
        buildStatus.writeInfo('locked', f'{be.targetName} is locked')
        return True

    startTime = time.time()

    log.info(f'building {be.infoStr}')

    buildingLib = False
    if be.libDir:
        buildingLib = True

    if not utils.pathExists(be.buildDirPathShell):
        utils.createDirs(be.buildDirPathShell)

    if not utils.pathExists(be.installDirPathShell):
        utils.createDirs(be.installDirPathShell)

    incPathList = []
    for incPath in be.incPaths:
        if utils.pathExists(incPath):
            incPathList += ['-I', incPath]
        else:
            log.warning(f'incPath {incPath} doesn\'t exist')

    for extIncPath in be.extIncPaths:  # external include libs (for cases where 3rd party header includes are using "" instead of <> ie Unreal)
        if utils.pathExists(extIncPath):
            incPathList += ['-I', extIncPath]
        else:
            log.warning(f'extIncPath {extIncPath} doesn\'t exist')

    definesList = []
    for define in be.defines:
        definesList += ['-D', define]

    #
    # qt moc file compilation, TODO: make this another compiler option, along with asm
    #
    mocPaths = []
    for qtClass in be.qtClasses:
        found = False
        mocPath = f'{be.buildDirPath}/moc_{qtClass}.cpp'
        qtClassHeader = qtClass + '.h'

        for incPath in be.incPaths:  # find the header file, # TODO: should there be a separate list of headers ie be.mocIncPaths?
            includePath = f'{incPath}/{qtClassHeader}'
            if not utils.pathExists(includePath):
                continue

            if utils.pathExists(mocPath) and float(os.stat(mocPath).st_mtime) < float(os.stat(includePath).st_mtime) or not utils.pathExists(mocPath):
                buildStatus.description = 'qt moc: ' + utils.runCmd(['moc'] + definesList + [includePath, '-o', mocPath])

            if not utils.pathExists(mocPath):
                buildStatus.writeError(buildStatus.description)
                return False

            mocPaths.append(mocPath)
            found = True

        if not found:
            buildStatus.writeError(f'can\'t find {qtClassHeader} for qt moc compilation')
            return False

    for mocPath in mocPaths:
        be.sources.append(mocPath)

    threads = []
    buildStatusQueue = Queue()  # the build status for each dependency: objs and libs
    objPathQueue = Queue()

    if be.processType is utils.MULTI_PROCESS:
        log.debug(f'using multiprocessing')
    elif be.processType is utils.MULTI_THREAD:
        log.debug(f'using multithreading')
    else:
        log.debug(f'using single process')
    
    #
    # compile
    #
    objPaths = []
    cmd = [be.compilerCmd, be.objFlag] + incPathList + definesList + be.flags

    for source in be.sources:
        if be.processType is utils.MULTI_PROCESS:
            thread = Process(target = _compileSrc, args = (be, cmd, source, objPathQueue, buildStatusQueue))
        elif be.processType is utils.MULTI_THREAD:
            thread = Thread(target = _compileSrc, args = (be, cmd, source, objPathQueue, buildStatusQueue))
        else:
            _compileSrc(be, cmd, source, objPathQueue, buildStatusQueue)
        if be.processType > 0:
            thread.start()
            threads.append(thread)

    #
    # build library dependencies
    #
    libCmds = []
    if be.binaryType == 'exe' or be.binaryType == 'plugin':
        for lib in be.libs:
            libName = lib
            if be.compiler.startswith('msvc'):
                libCmds += [libName + be.staticExt]  # you need to link against the .lib stub file even if it's ultimately a .dll that gets linked
            else:
                libCmds += [be.libFlag, libName]

    # check if the lib has a directory for building
    for libSrcPath in be.libSrcPaths:
        if utils.pathExists(libSrcPath):
            if be.processType is utils.MULTI_PROCESS:
                thread = Process(target = _buildLib, args = (be, libSrcPath, buildStatusQueue))
            elif be.processType is utils.MULTI_THREAD:
                thread = Thread(target = _buildLib, args = (be, libSrcPath, buildStatusQueue))
            else:
                _buildLib(be, libSrcPath, buildStatusQueue)
            if be.processType > 0:
                thread.start()
                threads.append(thread)

    # wait for all the threads before checking the results
    for thread in threads:
        thread.join()

    allUpToDate = True
    while not buildStatusQueue.empty():
        bs = buildStatusQueue.get()
        if bs.status == 'failed':
            # NOTE: changed from bs.description.encode('ascii', 'ignore') which fixed issue on macOs
            totalTime = int(time.time() - startTime)
            buildStatus.writeError(
                f'{be.infoStr} failed because {bs.name} failed because...\n\n{bs.description}\n...determined in {totalTime} seconds\n\n')
            return False
        elif bs.status == 'built':
            allUpToDate = False

    # objPaths = []
    while not objPathQueue.empty():
        objPaths.append(objPathQueue.get())

    # revise the library paths
    extraLibPaths = []
    for i in range(len(be.libPaths)):

        revisedLibPath = f'{be.libPaths[i]}/{be.osType}/{be.compilerVersion}'
        if utils.pathExists(revisedLibPath):
            be.libPaths[i] = revisedLibPath

        revisedLibPath_ = f'{revisedLibPath}/{be.binaryFormat}'
        if utils.pathExists(revisedLibPath_):
            revisedLibPath = revisedLibPath_
            extraLibPaths.append(revisedLibPath)

        revisedLibPath_ = f'{revisedLibPath}/{be.buildType}'
        if utils.pathExists(revisedLibPath_):
            revisedLibPath = revisedLibPath_
            extraLibPaths.append(revisedLibPath)

        if be.currentBuild:
            revisedLibPath += f'/{be.currentBuild}'
            if utils.pathExists(revisedLibPath):
                extraLibPaths.append(revisedLibPath)

    for xlp in extraLibPaths:
        be.libPaths.insert(0, xlp)

    #
    # linking
    #
    linkCmd = []

    if allUpToDate and utils.pathExists(be.installPathShell):
        totalTime = int(time.time() - startTime)
        buildStatus.writeInfo('up to date', f'{be.infoStr} is up to date, determined in {totalTime} seconds\n')
        if not buildingLib:
            _runPostScript(be)
        return True

    # microsoft's compiler / linker can only handle so many characters on the command line
    if be.compiler.startswith('msvc'):
        objPathsStr = '" "'.join(objPaths)
        libCmdsStr = ' '.join(libCmds)
        msvcLinkCmd = f'{be.targetFlag}"{be.installPath}" "{objPathsStr}" {libCmdsStr}'
        with open(be.buildDirPathShell + '/linkCmd', 'w') as wf:
            wf.write(msvcLinkCmd)

        linkCmd += [be.linker, '@' + be.buildDirPath + '/linkCmd']
        if be.showLinkerCmds:
            log.info(f'\nmsvcLinkCmd: {msvcLinkCmd}\n')
    else:
        linkCmd += [be.linker, be.targetFlag, be.installPath] + objPaths + libCmds

    if be.binaryType != 'static':
        linkCmd += be.linkFlags

    if be.binaryType == 'exe' or be.binaryType == 'plugin' or (be.compilerRoot == 'msvc' and be.binaryType == 'dynamic'):

        for libPath in be.libPaths:
            if not utils.pathExists(libPath):
                log.warning(f'libPath {libPath} doesn\'t exist')
                continue
            if be.compiler.startswith('msvc'):
                linkCmd += [be.libPathFlag + os.path.normpath(libPath)]
            else:
                linkCmd += [be.libPathFlag, os.path.normpath(libPath)]

    # get the timestamp of the existing target if it exists
    linked = False
    targetExisted = False
    oldTargetTimeStamp = None
    if utils.pathExists(be.installPathShell):
        oldTargetTimeStamp = float(os.stat(be.installPathShell).st_mtime)
        targetExisted = True

    if be.showLinkerCmds:
        linkCmdStr = ' '.join(linkCmd)
        log.info(f'\n{linkCmdStr}\n')

    buildStatus.description = utils.runCmd(linkCmd)

    if utils.pathExists(be.installPathShell):
        if targetExisted:
            if float(os.stat(be.installPathShell).st_mtime) > oldTargetTimeStamp:
                linked = True
        else:
            linked = True

    if linked:
        log.info(f'linked {be.infoStr}')
    else:
        buildStatus.writeError(f'linking failed because {buildStatus.description}')
        return False

    # copy dynamic library dependencies to the install path
    if be.copyDynamicLibs:
        if be.binaryType == 'exe' or be.binaryType == 'plugin':
            for lib in be.libs:
                for libPath in be.libPaths:
                    dynamicPath = libPath + '/'
                    if be.compilerRoot == 'gcc' or be.compilerRoot == 'clang':
                        dynamicPath += 'lib'
                    dynamicPath += lib + be.dynamicExt
                    dynamicPath = utils.getShellPath(dynamicPath)
                    if utils.pathExists(dynamicPath):
                        utils.copyfile(dynamicPath, be.installDirPathShell)

    totalTime = int(time.time() - startTime)
    buildStatus.writeInfo('built', f'{be.infoStr} built {be.installPath}\ncompleted in {totalTime} seconds\n')

    # run a post-build script if it exists
    if not buildingLib:
        _runPostScript(be)

    return True


#
# private functions
#
def _compileSrc(be, compileCmd, source, objPathQueue, buildStatusQueue):
    '''
        be (in): BuildElements object
        compileCmd (in): the compile command so far
        source (in): the c or cpp source file to compile (every source file gets it's own object file)
        objPaths (out): list of all object paths that will be passed to the linker
        buildStatus (out): build status for this particular compile, defaults to failed
    '''

    buildStatus = BuildStatus(source)

    if not utils.pathExists(source):
        buildStatus.writeError(f'{source} is missing, exiting build')
        buildStatusQueue.put(buildStatus)
        return

    objFile = os.path.basename(source)
    objFile = objFile.replace(os.path.splitext(source)[1], be.objExt)
    objPath = f'{be.buildDirPath}/{objFile}'
    objPathQueue.put(objPath)

    # check if it's up to date
    objExisted = utils.pathExists(objPath)
    if objExisted:
        objTimestamp = float(os.stat(utils.getShellPath(objPath)).st_mtime)
        if objTimestamp > be.latestConfigTimestamp and not utils.sourceNeedsBuilding(be.incPaths, source, objTimestamp):
            buildStatus.status = 'up to date'
            buildStatusQueue.put(buildStatus)
            return

        # if not utils.sourceNeedsBuilding(be.incPaths, source, objTimestamp):
        #   buildStatus.status = 'up to date'
        #   return

    # Microsoft Visual C has to have the objPathFlag cuddled up directly next to the objPath - no space in between them (grrr)
    if be.compiler.startswith('msvc'):
        cmd = compileCmd + [source, be.objPathFlag + objPath]
    else:
        cmd = compileCmd + [source, be.objPathFlag, objPath]

    if be.showCompilerCmds:
        cmdStr = ' '.join(cmd)
        log.info(f'\n{cmdStr}\n')

    buildStatus.description = utils.runCmd(cmd)

    if utils.pathExists(objPath):
        if objExisted:
            if float(os.stat(utils.getShellPath(objPath)).st_mtime) > objTimestamp:
                buildStatus.status = 'built'
        else:
            buildStatus.status = 'built'

    if buildStatus.status == 'built':
        buildStatus.description = 'compiled ' + os.path.basename(source)
    else:
        log.error(f'{objPath} failed to build')

    buildStatusQueue.put(buildStatus)


def _buildLib(be, libSrcDir, buildStatusQueue):
    '''
    '''
    libBe = getBuildElements(osType = be.osType,
                             compiler = be.compiler,
                             buildType = be.buildType,
                             binaryFormat = be.binaryFormat,
                             projConfig = be.projConfig,
                             globalConfig = be.globalConfig,
                             currentBuild = be.currentBuild,
                             libDir = libSrcDir)
    if not libBe:
        return

    build(libBe)

    buildStatus = BuildStatus(libSrcDir)
    buildStatus.readFromFile(libSrcDir, be.buildDir, be.binaryRelPath)
    buildStatusQueue.put(buildStatus)


def clean(be = None, builds = None):
    '''
    '''
    if not be:
        be = getBuildElements()
        if not be:
            return

    buildsRef = builds
    if not buildsRef:
        buildsRef = be.builds
    if type(buildsRef) is not list:
        buildsRef = [buildsRef]

    for build in buildsRef:
        try:
            be.configBuild(currentBuild = build)
        except PybythecError as e:
            log.error(e)
            return
        except Exception as e:
            log.error(f'unknown exception: {str(e)}\n{traceback.format_exc()}')
            return
        _clean(be)


def _clean(be = None):
    '''
        cleans the current project
        be (in): BuildElements object
    '''

    # remove any dynamic libs that are sitting next to the exe
    if utils.pathExists(be.installDirPathShell) and (be.binaryType == 'exe' or be.binaryType == 'plugin'):
        for fl in os.listdir(be.installDirPathShell):
            libName, ext = os.path.splitext(fl)
            if ext == be.dynamicExt:
                if be.compilerRoot == 'gcc' or be.compilerRoot == 'clang':
                    libName = libName.lstrip('lib')
                for lib in be.libs:
                    if lib == libName:
                        p = be.installDirPathShell + '/' + fl
                        try:
                            os.remove(p)
                        except Exception:
                            log.warning(f'failed to remove {p}')
            elif ext == '.exp' or ext == '.ilk' or ext == '.lib' or ext == '.pdb':  # msvc files
                p = be.installDirPathShell + '/' + fl
                try:
                    os.remove(p)
                except Exception:
                    log.warning(f'failed to remove {p}')

    if not utils.pathExists(be.buildDirPathShell):  # canary in the coal mine
        log.info(f'{be.infoStr} already clean')
        return True

    dirCleared = True
    for fl in os.listdir(be.buildDirPathShell):
        p = be.buildDirPathShell + '/' + fl
        try:
            os.remove(p)
        except Exception:
            dirCleared = False
            log.warning(f'failed to remove {p}')
    if dirCleared:
        os.removedirs(be.buildDirPathShell)

    if utils.pathExists(be.installPathShell):
        os.remove(be.installPathShell)
    target, ext = os.path.splitext(be.installPathShell)
    if ext == '.dll':
        try:
            os.remove(target + '.exp')
            os.remove(target + '.lib')
        except Exception:
            pass
    try:
        os.removedirs(be.installDirPathShell)
    except Exception:
        pass

    log.info(f'{be.infoStr} all clean')
    return True


def cleanAll(be = None, builds = None):
    '''
        cleans both the current project and also the dependencies
    '''
    if not be:
        be = getBuildElements()
        if not be:
            return

    buildsRef = builds
    if not buildsRef:
        buildsRef = be.builds
    if type(buildsRef) is not list:
        buildsRef = [buildsRef]

    for build in buildsRef:
        try:
            be.configBuild(currentBuild = build)
        except PybythecError as e:
            log.error(e)
            continue
        except Exception as e:
            log.error(f'unknown exception: {str(e)}\n{traceback.format_exc()}')
            continue
        _clean(be)

        # clean library dependencies
        for libSrcPath in be.libSrcPaths:
            if utils.pathExists(libSrcPath):
                libBe = getBuildElements(osType = be.osType,
                                            compiler = be.compiler,
                                            buildType = be.buildType,
                                            binaryFormat = be.binaryFormat,
                                            projConfig = be.projConfig,
                                            globalConfig = be.globalConfig,
                                            currentBuild = be.currentBuild,
                                            libDir = libSrcPath)
                if not libBe:
                    return
                clean(libBe)  # builds = build)


def _runPreScript(be):
    '''
        looks for a pre-build script and loads it as a module
    '''
    pathRoot = '.'
    if be.libDir:
        pathRoot = be.libDir
    preScriptPath = utils.getShellPath(pathRoot + '/pybythecPre.py')
    if not utils.pathExists(preScriptPath):
        preScriptPath = pathRoot + '/.pybythecPre.py'
    if utils.pathExists(preScriptPath):
        import imp
        m = imp.load_source('', preScriptPath)
        m.run(be)


def _runPostScript(be):
    '''
        looks for a post-build script and loads it as a module
    '''
    pathRoot = '.'
    if be.libDir:
        pathRoot = be.libDir
    postScriptPath = utils.getShellPath(pathRoot + '/pybythecPost.py')
    if not utils.pathExists(postScriptPath):
        postScriptPath = pathRoot + '/.pybythecPost.py'
    if utils.pathExists(postScriptPath):
        import importlib.util
        spec = importlib.util.spec_from_file_location('', postScriptPath)
        if not spec:
            return
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        module.run(be)

        # m = importlib.load_source('', postScriptPath)
        # import imp
        # m = imp.load_source('', postScriptPath)
        # m.run(be)
