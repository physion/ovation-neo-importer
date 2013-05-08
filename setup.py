#!/usr/bin/env python

from setuptools import setup

LONG_DESCRIPTION = """This packages provides Ovation importers for common electrophysiology formats.
It uses the Neo IO libraries to read compatible data files.

An ovation.io account and the ovation-python library is required for use.
"""

setup(name='Ovation Neo IO importer',
      version='1.0',
      description='Ovation import tools for Neo IO compatible data',
      long_description=LONG_DESCRIPTION,
      author='Physion',
      author_email='info@physion.us',
      url='http://ovation.io',
      packages=['ovation_neo'],
      install_requires=['numpy>=1.7.1',
                        'quantities>=0.10.1',
                        'neo==0.2.1.1'],
      tests_require=['nose==1.3.0'],
      classifiers=[
          'Development Status :: 4 - Beta',
          'Environment :: Console',
          'Intended Audience :: End Users/Desktop',
          'Intended Audience :: Science/Research',
          'Intended Audience :: Developers',
          'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
          'Operating System :: MacOS :: MacOS X',
          'Operating System :: Microsoft :: Windows',
          'Operating System :: POSIX',
          'Programming Language :: Python',
      ],
)
