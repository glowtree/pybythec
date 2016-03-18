
import os
import json
import logging
from pybythec import utils

log = logging.getLogger('pybythec')

class BuildStatus:
  '''
    member variables:
    name: name of target
    path: path to write pybythecStatus.json file to
    status: failed, built, up to date, or locked
    description: what happened
  '''
                                     
  def __init__(self, name, path = ''):
    self.name = name
    self.path = path
    self.status = 'failed'
    self.description = ''
  
  
  def readFromFile(self, buildPath):
    '''
      buildPath (in): where to read the pybythecStatus.json file from
    '''
    contents = utils.loadJsonFile(buildPath + '/pybythecStatus.json')
    if not contents:
      self.description = 'couldn\'t find build status in ' + buildPath
      log.error('couldn\'t find build status in ' + self.description)
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


  def writeInfo(self, status, msg):
    log.info(msg)
    self.status = status
    self.description = msg
    self._writeToFile()


  def writeError(self, msg):
    log.error(msg)
    self.description = msg
    self._writeToFile()


  def _writeToFile(self):
    if not os.path.exists(self.path):
      return
    with open(self.path + '/pybythecStatus.json', 'w') as f:
      json.dump({'status': self.status, 'description': self.description}, f, indent = 4)
