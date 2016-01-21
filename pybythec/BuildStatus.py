
import os
import json
import logging
from pybythec import utils

log = logging.getLogger('pybythec')

class BuildStatus:
  '''
    contains the build status integer:
    0 - failed (default)
    1 - built successfully
    2 - up-to-date or locked
    
    and a description of the build
  '''
  def __init__(self, path = '', result = 0, description = ''):
    self.path = path
    self.result = result
    self.description = description
    
  def readFromFile(self, buildPath):
    contents = utils.loadJsonFile(buildPath + '/.pybythecStatus.json')
    if not contents:
      self.description = 'couldn\'t find build status in ' + buildPath
      log.error('couldn\'t find build status in ' + self.description)
      return
    if 'result' in contents:
      self.result = contents['result']
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
    self.result = status
    self.description = msg
    self._writeToFile()
    
  def writeError(self, msg):
    log.error(msg)
    self.description = msg
    self._writeToFile()

  def _writeToFile(self):
    if not os.path.exists(self.path):
      return
    with open(self.path + '/.pybythecStatus.json', 'w') as f:
      json.dump({'result': self.result, 'description': self.description}, f, indent = 4)

