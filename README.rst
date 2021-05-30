:: SIDB-network-service ::

<!-- <p align="center"> -->
  <img src="image/SIDBneo4j.png" hight="800" width="800" title="">
<!-- </p> -->

:: setup and build environment ::

We'll follow Owen's and Xin's Sargasso package to setup our environment:

1) log onto the nrg server:

2) "Note: as Sargasso has a number of dependencies on other Python packages, it is strongly recommended to install in an isolated environment using the virtualenv tool. The virtualenvwrapper tool makes managing multiple virtual environments easier."
   i.e. make sure virtualenv and virtualenvwrapper are installed for python3.7 on nrg:
   pip3 install virtualenv
   pip3 install virtualenvwrapper
   

 3) then set within .bashrc (linux):
     - #--- setup VIRTUALENVWRAPPER_PYTHON for python3.7
     - export VIRTUALENVWRAPPER_PYTHON="/usr/local/bin/python3"
     - export VIRTUALENVWRAPPER_VIRTUALENV="/usr/local/bin/virtualenv"
     - source /usr/local/bin/virtualenvwrapper.sh
     - export WORKON_HOME="${HOME}/.virtualenvs"
     - export PROJECT_HOME="${HOME}/PROJECTS"

 4) source .bashrc

 5) "After setting up virtualenv and virtualenvwrapper, create and work in a virtual environment for Sargasso using the virtualenvwrapper tool:"
     i.e.
      - mkdir PROJECTS/
      - cd PROJECTS/
      - mkproject SIDBAutism (or workon SIDBAutism)
      - cd SIDBAutism
      - git clone https://github.com/statbio/SIDBAutism.git

 6) make sure external packages are installed within our virtual environment:
      - pip3 install ontobio
      - pip3 install neonx
      - pip3 install git+https://github.com/neo4j-graph-analytics/networkx-neo4j.git#egg=networkx-neo4j
      - pip3 install obonet

 7) cd ~/PROJECTS/SIDBAutism/SIDB-network-service/
      - python3 setup.py build
      - pip3 install -e .
