===============================
pybythec
===============================

.. image:: https://img.shields.io/pypi/v/pybythec.svg
        :target: https://pypi.python.org/pypi/pybythec

.. image:: https://img.shields.io/travis/glowtree/pybythec.svg
        :target: https://travis-ci.org/glowtree/pybythec

..  .. image:: https://readthedocs.org/projects/pybythec/badge/?version=latest
..          :target: https://readthedocs.org/projects/pybythec/?badge=latest
..          :alt: Documentation Status


a lightweight python build system for c/c++

* Free software: ISC license
* Documentation: https://github.com/glowtree/pybythec
..  * Documentation: https://pybythec.readthedocs.org.


Install
--------

pip install pybythec


Usage
--------

In your project directory create a pybythec.json file (or .pybythec.json).

Look in the example directory in the github repository to see what to add.


Then from the command line run:

pybythec


Clean your project with:

pybythec -cl


Clean your project and all it's dependencies with:

pybythec -cla


Better documentation to come!!!


Credits
---------

Tools used in rendering this package:

*  Cookiecutter_
*  `cookiecutter-pypackage`_

.. _Cookiecutter: https://github.com/audreyr/cookiecutter
.. _`cookiecutter-pypackage`: https://github.com/audreyr/cookiecutter-pypackage
