===============================
pybythec
===============================

A lightweight cross-platform build system for c/c++, written in python

.. image:: https://img.shields.io/pypi/v/pybythec.svg
  :target: https://pypi.python.org/pypi/pybythec

.. image:: https://img.shields.io/travis/glowtree/pybythec.svg?label=linux_macOs
  :target: https://travis-ci.org/glowtree/pybythec

.. image:: https://img.shields.io/appveyor/ci/glowtree/pybythec.svg?label=windows
  :target: https://ci.appveyor.com/project/glowtree/pybythec

Install
============

pip install pybythec

Source
======

Find the latest version on github: https://github.com/glowtree/pybythec

Usage
============

Create a pybythec.json file (or .pybythec.json) in the same directory as your c / c++ files.

Here's an example of what would be declared in pybythec.json if you were building an executable called Simple::

    {  
      "target": "Simple",
      "binaryType": "exe",
      "sources": "main.cpp",
      "installPath": "."
    }


Then from the command line run::

  pybythec

Clean your project with::

  pybythec -cl

Clean your project and all it's dependencies with::

  pybythec -cla

Look at other exmples in the './example' directory to see how to build a static library, a dynamic library, and also an executable with library dependencies.

pybythec assumes your already have the compiler / linker you want to use installed on your machine, currently gcc, clang and msvc are supported.

When you install pybythec with pip it will add a file called .pybythecGlobals.json to your home directory.  
This is a master file that declares all of your compiler and linker configurations.  
You can edit this as needed for system-wide configuration.
If you want to move this file just be sure to have an environment variable called PYBYTHEC_GLOBALS point to the new location, for example::

  export PYBYTHEC_GLOBALS=/Users/user/dev/.myPybythecGlobals.json

or for windows powershell::

  $env:PYBYTHEC_GLOBALS="C:/Users/user/dev/.myPybythecGlobals.json"

There are up to 3 configuration files for any given build: global, project and local, where project overrides global, and local overrides both global and project.

You can point pybythec to the project configuration file with the environment variable PYBYTHEC_PROJECT, for example::

  export PYBYTHEC_PROJECT=/Users/user/dev/myProject/.myProjectConfig.json

pybythec will always look for your local file in your current directoy, and it must be called pybythec.json or .pybythec.json.

You don't need all 3 to build, in fact you could even put everything into one of those 3 files if you really wanted to.

The configuration files allow for nested declarations so that you can get specific for your building needs.  

For example if I want a preprocessor declaration that's project wide but only used when building on OS X for gcc, I can add the 
following to my project level config file::

  "defines":
  {
    "macOs": {
      "gcc" : "SOME_DEFINE"
    }
  }

You can use environmet variables in your configuration files simply by prepending with $, for example::

  "libPaths": "$SHARED/lib"


You can have a python script automatically run after the build finishes, just be sure it's called pybythecPost.py or .pybythecPost.py.


Currently pybythec supports gcc/g++, clang/clang++ and msvc 

More documentation to come!!!

License
=======

See LICENSE



