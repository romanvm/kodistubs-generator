# Kodistubs Generator

Script for generating [Kodistubs](https://github.com/romanvm/Kodistubs).

## Description

This script generates stub files for Kodi Python API and respective Sphinx
autodoc .rst file for API documentation. Generated stub files still need
post-editing to fix formatting issues like line length, tables etc.

``kodistubs-generator`` is created for using on Linux and similar platforms
and was tested on Linux Ubuntu.

## Usage

* Clone Kodi sources and install all build prerequisites for your
  platform. Make sure you have installed **Doxygen** documentation generator.
* Run ``cmake .`` to generate project Makefile.
* Run ``make python_binding`` to generate SWIG XML definitions for
  Kodi Python API.
* Clone this repository, create a virtual environment with Python 3, activate
  this environment and install all requirements.
* Go to the directory where you have cloned ``kodistubs-denerator`` and run
  the script: ``python generator.py <path to Kodi soruces>`` from the virtual
  environment you have created on the previous step.
  Generated stub files will be located in ``/build`` subdirectory
  of your working directory.

## License

GPL v.3
