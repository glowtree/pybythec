
import pybythec
import argparse

def main():

  parser = argparse.ArgumentParser(formatter_class = argparse.RawTextHelpFormatter)
  parser.add_argument('-v', '--version', action = 'store_true', help = 'the version')
  parser.add_argument('-c', '--compiler', help = 'any variation of gcc, clang, or msvc ie g++-4.4, msvc-110')  # metavar = 'compiler', 
  parser.add_argument('-os', '--osType', help = 'operating system: currently linux, osx, or windows')
  parser.add_argument('-b', '--buildType', help = 'debug release etc')
  parser.add_argument('-bf', '--binaryFormat', help = '32bit, 64bit etc')
  parser.add_argument('-pc', '--projectConfig', help = 'path to a pybythec project config file (json)')
  parser.add_argument('-gc', '--globalConfig', help = 'path to a pybythec global config file (json)')
  parser.add_argument('-ck', '--customKeys', help = 'custom keys that you want this build to use (comma delineated, no spaces ie foo,bar)')
  parser.add_argument('-cl', '--clean', action = 'store_true', help = 'clean the build')
  parser.add_argument('-cla', '--cleanAll', action = 'store_true', help = 'clean the build and the builds of all library dependencies')
  args = parser.parse_args()

  return pybythec.build(
      version = args.version,
      compiler = args.compiler,
      osType = args.osType,
      buildType = args.buildType,
      binaryFormat = args.binaryFormat,
      projConfigPath = args.projectConfig,
      globalConfigPath = args.globalConfig,
      customKeys = args.customKeys.split(',') if args.customKeys else None,
      clean = args.clean,
      cleanAll = args.cleanAll)
