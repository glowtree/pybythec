# import json
import shutil
import subprocess
import platform
import sys
import os

LINUX_ROOT = ''
if 'microsoft-standard' in platform.uname(
).release:  # check if it's windows subsystem for linux
    LINUX_ROOT = '/mnt'

LINEAR_PROCESS = 0
MULTI_THREAD = 1
MULTI_PROCESS = 2


class PybythecError(Exception):
    def __init__(self, msg):
        super(PybythecError, self).__init__(msg)


class Logger:
    def __init__(self, name = None, debug = False, filepath = None):
        self.name = name
        if self.name:
            self.name += ': '
        else:
            self.name = ''
        self._debug = debug
        self.wf = sys.stdout
        if filepath:
            self.toFile = True
            self.wf = open(filepath, 'w')
        else:
            self.toFile = False

    def __del__(self):
        if self.toFile:
            self.wf.close()

    def debug(self, s):
        if self._debug:
            self.wf.write(f'debug: {self.name}{s}\n')
            self.wf.flush()

    def info(self, s):
        self.wf.write(f'{self.name}{s}\n')
        self.wf.flush()

    def warning(self, s):
        self.wf.write(f'warning: {self.name}{s}\n')
        self.wf.flush()

    def error(self, s):
        if self.toFile:
            self.wf.write(f'error: {self.name}{s}\n')
            self.wf.flush()
        else:
            sys.stderr.write(f'error: {self.name}{s}\n')
            sys.stderr.flush()

    def raw(self, s):
        sys.stdout.write(s)

    # shorthands
    def d(self, s):
        self.debug(s)

    def i(self, s):
        self.info(s)

    def w(self, s):
        self.warning(s)

    def e(self, s):
        self.error(s)

    def r(self, s):
        self.raw(s)


log = Logger()  # singleton


def srcNewer(srcPath, dstPath):
    if int(os.stat(srcPath).st_mtime) > int(os.stat(dstPath).st_mtime):
        return True
    return False


def checkTimestamps(incPaths, src, timestamp):
    '''
    finds the newest timestamp of everything upstream of the src file, including the src file
  '''
    srcPath = getShellPath(src)
    if not os.path.exists(srcPath):
        log.warning(f'checkTimestamps: {srcPath} doesn\'t exist')
        return

    srcTimeStamp = float(os.stat(srcPath).st_mtime)
    if srcTimeStamp > timestamp[0]:
        timestamp[0] = srcTimeStamp

    fileCopy = str()
    srcFile = open(srcPath, 'r')
    for line in srcFile:
        fileCopy += line
    srcFile.close()

    for line in fileCopy.split('\n'):
        if line.startswith('#include'):
            filename = line.lstrip('#include')
            filename = filename.strip()
            if (filename[0] == '"'):
                filename = filename.strip('"')
                for dir in incPaths:
                    filepath = f'{dir}/{filename}'
                    if os.path.exists(filepath):
                        checkTimestamps(incPaths, filepath, timestamp)


def sourceNeedsBuilding(incPaths, src, objTimestamp):
    '''
    determines whether a source file needs to be built or not
  '''
    timestamp = [0]  # [] so it's passed as a reference
    checkTimestamps(incPaths, src, timestamp)

    if timestamp[0] > objTimestamp:
        return True

    return False


def getLibPath(libName, libPath, compiler, libExt):
    '''
      get the lib path with the os / compiler specific prefix and file extension
  '''
    libPath += '/'
    if compiler.startswith('gcc') or compiler.startswith('clang'):
        libPath += 'lib'
    libPath += libName + libExt
    return libPath


def isWindowsPath(path):
    '''
    path: assume it's an absolute path ie C:/hi
  '''
    if len(path) < 3:
        return False
    if path[0].isalpha() and path[1] == ':' and (path[2] == '/'
                                                 or path[2] == '\\'):
        return True
    return False


def windowsToLinux(p):
    '''
  '''
    np = p.replace('\\', '/')
    driveLetter = np[0].lower()
    return f'{LINUX_ROOT}/{driveLetter}{np[2:]}'


def linuxToWindows(p):
    '''
  '''
    np = p[len(LINUX_ROOT) + 1:]
    return np[0].upper() + ':' + np[1:]


def getShellPath(path):
    '''
    path: assume absolute path
    returns the usable path for the current shell
  '''
    if not isWindowsPath(path):
        return path
    if platform.system() == 'Linux' or platform.system() == 'Darwin':
        return windowsToLinux(path)
    return path


def pathExists(path):
    '''
  '''
    return os.path.exists(getShellPath(path))


def getPath(path, osType):
    '''
    gets the path based on the requested os type ie windows, linux
  '''
    isWin = isWindowsPath(path)
    if osType == 'windows':
        if isWin:
            return path
        return linuxToWindows(path)
    # otherwise linux
    if isWin:
        return windowsToLinux(path)
    return path


def getShellOsType():
    '''
  '''
    if platform.system() == 'Linux':
        return 'linux'
    elif platform.system() == 'Darwin':
        return 'macOs'
    elif platform.system() == 'Windows':
        return 'windows'
    else:
        raise PybythecError('os needs to be linux, macOs or windows')


def _getAbsPath(cwDir, path):
    '''
  '''
    _cwDir = cwDir.replace('\\', '/')
    if not _cwDir.endswith('/'):
        _cwDir += '/'
    _path = path.replace('\\', '/')
    if len(path) < 2:
        if path[0] == '.':
            return _cwDir.rstrip('/')
    if _path[0] == '.' and path[1].isalpha():  # ie .pybythec
        return _cwDir + _path
    return os.path.normpath(os.path.join(cwDir, './' + path)).replace('\\', '/')
    # TODO: handle the case when it's ./.pybythec
    # return _cwDir + _path.lstrip('./\\')


def getAbsPath(cwDir, path):
    '''
    cwDir: current working dir path
    path: may be relative or absolute
    returns absolute path
  '''
    if isWindowsPath(path):
        return path.replace('\\', '/')
    if os.path.isabs(path):
        return path
    return _getAbsPath(cwDir, path)


def resolvePaths(cwDir, paths, osType):
    '''
    '''
    i = 0
    for path in paths:
        p = getAbsPath(cwDir, path)
        paths[i] = getPath(p, osType)
        i += 1


def createDirs(path):
    '''
        recursively goes up the path heiarchy creating the necessary directories along the way
        similar to os.makedirs except doesn't throw an exception if a directory's already exists
        also os.makedirs throws the same exception whether the directory already exists or it couldn't create it, not ideal
    '''
    if path is None or not len(path):
        log.warning('createDirs: empty path')
        return

    # in case path ends with a '/'
    path = path.rstrip('/')

    if os.path.exists(path):
        return

    # if the path above the current one doesn't exist, create it
    abovePath = os.path.dirname(path)
    if not os.path.exists(abovePath):
        createDirs(abovePath)

    try:
        os.mkdir(path)
    except Exception:  # OSError:
        # log.warning('failed to make {0} because {1}', path, e)
        pass


def copyfile(srcPath, dstDir):
    '''
        copies srcPath to dstPath, creating the directory structure if necessary for the destination
        srcPath: absolute file path
        dstDir:  absolute directory path
    '''

    if not os.path.exists(srcPath):
        return False

    dstPath = f'{dstDir}/{os.path.basename(srcPath)}'

    if os.path.exists(dstPath):
        if not srcNewer(srcPath, dstPath):
            return

    # in case the path doesn't already exist
    createDirs(dstDir)

    shutil.copy2(srcPath, dstDir)

    log.debug(f'{srcPath} copied to {dstPath}')

    return True


# def loadJsonFile(jsonPath):
#     '''
#     load a json config file
#     NOTE: no check for existence of the path so that logging warnings can be controlled elsewhere
#   '''
#     if os.path.splitext(jsonPath)[1] != '.json':
#         # raise PybythecError(f'{jsonPath} is not a json file')
#         return None
#     if not os.path.exists(jsonPath):
#         raise PybythecError(f'{jsonPath} doesn\'t exist')
#     try:
#         with open(jsonPath) as f:
#             return json.loads(removeComments(f))
#     except Exception as e:
#         raise PybythecError(f'failed to parse {jsonPath}: {e}')

# def removeComments(f):
#     '''
#     removes // style comments from a file, num of lines stays the same
#   '''
#     sansComments = ''
#     inQuotes = False
#     for l in f:
#         i = 0
#         for c in l:
#             if c == '"':
#                 inQuotes = not inQuotes
#             elif c == '/' and l[i + 1] == '/' and not inQuotes:
#                 sansComments += '\n'
#                 break
#             i += 1
#             sansComments += c
# return sansComments


def runCmd(cmd):
    '''
    runs a command and blocks until it's done, returns the output
  '''
    try:
        p = subprocess.Popen(cmd,
                             stdout = subprocess.PIPE,
                             stderr = subprocess.PIPE)
    except subprocess.CalledProcessError as e:
        return f'cmd failed: {" ".join(cmd)} because: {e.output}'
    except Exception:
        return f'cmd failed: {" ".join(cmd)}'
    stdout, stderr = p.communicate()
    output = ''
    if len(stderr):
        output += stderr.decode('utf-8')
    if len(stdout):
        output += stdout.decode('utf-8')
    return output


# testing
if __name__ == '__main__':

    print(
        getAbsPath(
            'C:\\Users\\tom\\work_offline\\repos\\pybythec/example/shared/src\\DynamicLib',
            '../../include'))
