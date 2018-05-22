
import os
from setuptools import setup
from setuptools.command.install import install as baseInstall

pybythecGlobals = '''
{
  "binaryFormat": "64bit",
  "buildType": "release",
  "installPath": ".",
  "buildDir": ".pybythec",
  "compiler": {
    "linux": "g++",
    "macOs": "clang++",
    "windows": "msvc-140"
  },
  "filetype": {
    "linux": "elf",
    "macOs": "mach-o",
    "windows": "pe"
  },
  "defines": {
    "msvc": [
      "NOMINMAX",
      "VC_EXTRALEAN",
      "WIN32_LEAN_AND_MEAN"
    ],
    "macOs": "__APPLE__"
  },
  "flags": {
    "gcc": {
      "all": [
        "-Wall",
        "-Wno-deprecated",
        "-fno-gnu-keywords"
      ],
      "debug": "-g",
      "release": "-O3",
      "linux": {
        "static": "-fPIC",
        "dynamic": "-fPIC",
        "plugin": "-fPIC"
      }
    },
    "clang": {
      "all": [
        "-Wall",
        "-Wno-deprecated",
        "-fno-gnu-keywords"
      ],
      "debug": "-g",
      "release": "-O3",
      "linux": {
        "static": "-fPIC",
        "dynamic": "-fPIC",
        "plugin": "-fPIC"
      }
    },
    "macOs": {
      "dynamic": "-fno-common",
      "plugin": "-fno-common"
    },
    "msvc": {
      "all": [
        "/EHsc",
        "/Gy",
        "/nologo",
        "/errorReport:prompt"
      ],
      "debug": {
        "all": [
          "/W1",
          "/RTC1",
          "/Z7",
          "/MDd"
        ]
      },
      "release": {
        "all": [
          "/DNDEBUG",
          "/O2",
          "/GL",
          "/MD"
        ]
      },
      "dynamic": "/LD",
      "plugin": "/LD"
    }
  },
  "linkFlags": {
    "gcc": {
      "all": "-Wall",
      "release": "-O3",
      "exe": "-Wl,-rpath=$ORIGIN/", // so an exe can find shared libraries in the same directory
      "dynamic": "-shared",
      "plugin": "-shared",
      "linux": {
        "dynamic": "-fPIC",
        "plugin": "-fPIC"
      }
    },
    "clang": {
      "all": "-Wall",
      "release": "-O3",
      "linux": {
        "exe": "-Wl,-rpath=$ORIGIN/",
        "dynamic": [
          "-shared",
          "-fPIC"
        ],
        "plugin": [
          "-shared",
          "-fPIC"
        ]
      },
      "macOs": {
        "dynamic": "-dynamiclib",
        "plugin": "-bundle"
      }
    },
    "msvc": {
      "all": [
        "/NODEFAULTLIB:LIBCMT",
        "/NOLOGO",
        "/ERRORREPORT:PROMPT"
      ], //:libc.lib
      "debug": "/DEBUG",
      "release": [
        "/INCREMENTAL:NO",
        "/OPT:REF",
        "/OPT:ICF",
        "/LTCG"
      ]
    }
  },
  "libs": {
    "gcc": "pthread"
    // "msvc": ["user32", "gdi32", "Shell32"]
  },
  "bins": {
    "msvc-090": {
      "all": [
        "C:/Program Files (x86)/Microsoft Visual Studio 9.0/Common7/IDE",
        "C:/Program Files/Microsoft SDKs/Windows/v6.0A/bin"
      ],
      "32bit": "C:/Program Files (x86)/Microsoft Visual Studio 9.0/VC/bin",
      "64bit": [
        "C:/Program Files (x86)/Microsoft Visual Studio 9.0/VC/bin/amd64",
        "C:/Program Files (x86)/Microsoft Visual Studio 9.0/VC/bin/x86_amd64"
      ]
    },
    "msvc-100": {
      "all": [
        "C:/Program Files (x86)/Microsoft Visual Studio 10.0/Common7/IDE",
        "C:/Program Files/Microsoft SDKs/Windows/v7.1/bin"
      ],
      "32bit": "C:/Program Files (x86)/Microsoft Visual Studio 10.0/VC/bin",
      "64bit": [
        "C:/Program Files (x86)/Microsoft Visual Studio 10.0/VC/bin/amd64",
        "C:/Program Files (x86)/Microsoft Visual Studio 10.0/VC/bin/x86_amd64"
      ]
    },
    "msvc-110": {
      "all": [
        "C:/Program Files (x86)/Microsoft Visual Studio 11.0/Common7/IDE",
        "C:/Program Files (x86)/Microsoft SDKs/Windows/v7.1A/bin"
      ],
      "32bit": "C:/Program Files (x86)/Microsoft Visual Studio 11.0/VC/bin",
      "64bit": [
        "C:/Program Files (x86)/Microsoft Visual Studio 11.0/VC/bin/amd64",
        "C:/Program Files (x86)/Microsoft Visual Studio 11.0/VC/bin/x86_amd64"
      ]
    },
    "msvc-140": {
      "all": [
        "C:/Program Files (x86)/Microsoft Visual Studio 14.0/Common7/IDE",
        "C:/Program Files (x86)/Microsoft SDKs/Windows/v10.0A/bin/NETFX 4.6.1 Tools"
      ],
      "32bit": "C:/Program Files (x86)/Microsoft Visual Studio 14.0/VC/bin",
      "64bit": "C:/Program Files (x86)/Microsoft Visual Studio 14.0/VC/bin/amd64"
    }
  },
  "incPaths": {
    "msvc-090": [
      "C:/Program Files (x86)/Microsoft Visual Studio 9.0/VC/include",
      "C:/Program Files/Microsoft SDKs/Windows/v6.0A/Include"
    ],
    "msvc-100": [
      "C:/Program Files (x86)/Microsoft Visual Studio 10.0/VC/include",
      "C:/Program Files/Microsoft SDKs/Windows/v7.1/Include"
    ],
    "msvc-110": [
      "C:/Program Files (x86)/Microsoft Visual Studio 11.0/VC/include",
      "C:/Program Files (x86)/Microsoft SDKs/Windows/v7.1A/Include"
    ],
    "msvc-140": [
      "C:/Program Files (x86)/Microsoft Visual Studio 14.0/VC/include",
      "C:/Program Files (x86)/Windows Kits/10/Include/10.0.14393.0/ucrt",
      "C:/Program Files (x86)/Windows Kits/10/Include/10.0.14393.0/um",
      "C:/Program Files (x86)/Windows Kits/10/Include/10.0.14393.0/shared"
    ]
  },
  "libPaths": {
    "msvc-090": {
      "32bit": [
        "C:/Program Files (x86)/Microsoft Visual Studio 9.0/VC/lib",
        "C:/Program Files/Microsoft SDKs/Windows/v6.0A/Lib"
      ],
      "64bit": [
        "C:/Program Files (x86)/Microsoft Visual Studio 9.0/VC/lib/amd64",
        "C:/Program Files/Microsoft SDKs/Windows/v6.0A/Lib/x64"
      ]
    },
    "msvc-100": {
      "32bit": [
        "C:/Program Files (x86)/Microsoft Visual Studio 10.0/VC/lib",
        "C:/Program Files/Microsoft SDKs/Windows/v7.1/Lib"
      ],
      "64bit": [
        "C:/Program Files (x86)/Microsoft Visual Studio 10.0/VC/lib/amd64",
        "C:/Program Files/Microsoft SDKs/Windows/v7.1/Lib/x64"
      ]
    },
    "msvc-110": {
      "32bit": [
        "C:/Program Files (x86)/Microsoft Visual Studio 11.0/VC/lib",
        "C:/Program Files (x86)/Microsoft SDKs/Windows/v7.1A/Lib"
      ],
      "64bit": [
        "C:/Program Files (x86)/Microsoft Visual Studio 11.0/VC/lib/amd64",
        "C:/Program Files (x86)/Microsoft SDKs/Windows/v7.1A/Lib/x64"
      ]
    },
    "msvc-140": {
      "32bit": [
        "C:/Program Files (x86)/Microsoft Visual Studio 14.0/VC/lib",
        "C:/Program Files (x86)/Windows Kits/10/Lib/10.0.14393.0/ucrt/x86",
        "C:/Program Files (x86)/Windows Kits/10/Lib/10.0.14393.0/um/x86"
      ],
      "64bit": [
        "C:/Program Files (x86)/Microsoft Visual Studio 14.0/VC/lib/amd64",
        "C:/Program Files (x86)/Windows Kits/10/Lib/10.0.14393.0/ucrt/x64",
        "C:/Program Files (x86)/Windows Kits/10/Lib/10.0.14393.0/um/x64"
      ]
    }
  }
}
'''

class installer(baseInstall):

  def run(self):
    globalsPath = os.path.expanduser('~') + '/.pybythecGlobals.json'
    print('installing ' + globalsPath)
    with open(globalsPath, 'w') as f:
      f.write(pybythecGlobals)
    baseInstall.run(self)


description = 'A lightweight cross-platform build system for c/c++, written in python'

setup(
    name = 'pybythec',
    version = '0.9.32',
    author = 'glowtree',
    author_email = 'tom@glowtree.com',
    url = 'https://github.com/glowtree/pybythec',
    description = description,
    long_description = str(open('README.rst', 'r').read()).replace(description, ''),
    packages = ['pybythec'],
    entry_points = {
        'console_scripts': ['pybythec=pybythec.command_line:main'],
    },
    license = 'LICENSE',
    test_suite = 'test',
    cmdclass = {'install': installer}
)