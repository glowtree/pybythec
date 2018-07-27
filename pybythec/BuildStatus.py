
import os
import json
from pybythec import utils
from pybythec.utils import f

log = utils.Logger('pybythec')

class BuildStatus:
  '''
    member variables:
    name: name of target
    path: path to write status.json file to
    status: failed, built, up to date, or locked
    description: what happened
  '''
                                     
  def __init__(self, name, path = ''):
    self.name = name
    self.path = path
    self.status = 'failed'
    self.description = ''
  

  def readFromFile(self, libSrcDir, buildDir, binaryRelfPath):
    '''
      buildPath (in): where to read the status.json file from
    '''

    buildPath = f('{0}/{1}/{2}', libSrcDir, buildDir, binaryRelfPath)

    if not os.path.exists(buildPath):
      # try the other hidden / non-hidden version
      if buildDir[0] == '.':
        buildPath = f('{0}/{1}/{2}', libSrcDir, buildDir.lstrip('.'), binaryRelfPath)
      else:
        buildPath = f('{0}/.{1}/{2}', libSrcDir, buildDir, binaryRelfPath)

    contents = utils.loadJsonFile(buildPath + '/status.json')
    if not contents:
      self.description = 'couldn\'t find contents in ' + buildPath
      log.error('couldn\'t find contents in ' + buildPath)
      return
    if 'status' in contents:
      self.status = contents['status']
    else:
      self.description = 'couldn\'t find the build status in ' + buildPath
      log.error(self.description)
    if 'description' in contents:
      self.description = contents['description']
    else:
      self.description = buildPath + ' doesn\'t contain a description'
      log.warning(self.description)


  def writeInfo(self, status, msg, *args):
    msg = f(msg, *args)
    log.info(msg)
    self.status = status
    self.description = msg
    self._writeToFile()


  def writeError(self, msg, *args):
    msg = f(msg, *args)
    log.error(msg)
    self.description = msg
    self._writeToFile()


  def _writeToFile(self):
    if not os.path.exists(self.path):
      return
    with open(self.path + '/status.json', 'w') as f:
      json.dump({'status': self.status, 'description': self.description}, f, indent = 4)
