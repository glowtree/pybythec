
import pybythec
import argparse


log = pybythec.utils.Logger('pybythec')

def main():

  parser = argparse.ArgumentParser(formatter_class = argparse.RawTextHelpFormatter)
  parser.add_argument('-v', '--version', action = 'store_true', help = 'the version')
  parser.add_argument('-c', '--compiler', help = 'any variation of gcc, clang, or msvc ie g++-4.4, msvc-110')  # metavar = 'compiler'
  parser.add_argument('-os', '--osType', help = 'operating system: currently linux, macOs, or windows')
  parser.add_argument('-b', '--buildType', help = 'debug release etc')
  parser.add_argument('-bf', '--binaryFormat', help = '32bit, 64bit etc')
  parser.add_argument('-pc', '--projectConfig', help = 'path to a pybythec project config file (json)')
  parser.add_argument('-gc', '--globalConfig', help = 'path to a pybythec global config file (json)')
  parser.add_argument('-bd', '--builds', help = 'list of builds: each one generates a seperate build (comma delineated, no spaces ie foo,bar)')
  parser.add_argument('-cl', '--clean', action = 'store_true', help = 'clean the build')
  parser.add_argument('-cla', '--cleanAll', action = 'store_true', help = 'clean the build and the builds of all library dependencies')
  args = parser.parse_args()

  if args.version:
    print('version: ' + pybythec.__version__)
    return

  be = pybythec.getBuildElements(
      osType = args.osType,
      compiler = args.compiler,
      buildType = args.buildType,
      binaryFormat = args.binaryFormat,
      projConfigPath = args.projectConfig,
      globalConfigPath = args.globalConfig)
  if not be:
    return

  builds = args.builds.split(',') if args.builds else None

  if args.cleanAll:
    return pybythec.cleanAll(be, builds)
  elif args.clean:
    return pybythec.clean(be, builds)
  else:
    return pybythec.build(be, builds)
