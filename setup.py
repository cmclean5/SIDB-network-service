import os
import sys
import re

# maybe in future will excute c++ code or bash scripts
# import subprocess

from setuptools import setup, find_packages

# package has been developed using python3.7
if sys.version_info.major < 3:
    sys.exit("Error: Python 3 is required")

# get absolute path to package's root
directory = os.path.dirname(os.path.abspath(__file__))

# get version from __init__.py
init_path = os.path.join(directory,'network', '__init__.py')
with open(init_path) as read_file:
    text = read_file.read()
pattern = re.compile(r"^__version__ = ['\"]([^'\"]*)['\"]", re.MULTILINE)
version = pattern.search(text).group(1)

# to do: remove 'obonet'... and also possibly 'neonx'?
requires = [
    'nested-lookup',
    "prefixcommons>=0.1.4",
    'click>=6.7',
    'pandas',
    'numpy',
    'networkx==1.11',
    'obonet',
    'ontobio',
    'neonx',
    'neo4j-driver>=1.5.3',
    'neo4jrestclient',
    'pytest==3.9.1'
]

setup(
    name='SIDB-network-service',
    version=version,
    description='Analysis of Patient network data related to Developmental Disorders and Ontologies, and import/export into graphical db',
    long_description=open("README.rst").read(),
    url='http://github.com//statbio/SIDBAutism',
    author='Colin D Mclean, He Xin',
    author_email='Colin.D.Mclean@ed.ac.uk, Xin.He@ed.ac.uk',
    license='MIT',
    classifiers=[
                 'Intended Audience :: Science/Research',
                 'Topic :: Scientific/Engineering :: Bio-Informatics',
                 'License :: OSI Approved :: MIT License',
                 'Programming Language :: Python :: 3',
                 'Topic :: Scientific/Engineering :: Visualization'
                 ],
    packages=find_packages(),
    include_package_data=True,
    package_data={
        'tests.data': ['*'],
        'network':['config.yml']
    },
    install_requires=requires, 
    test_suite='nose.collector',
    tests_require=['nose'],
    zip_safe=False
)
