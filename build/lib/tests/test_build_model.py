#--------------------------------------
# Colin.D.Mclean@ed.ac.uk (09/10/2018)
# Build a model, i.e. patient network with relationships to disired network objects, i.e. ontologies (HP, DOID, GO), PPI network model etc.
# (built using python 3.7)
# 1) load the patient network
#    - import in our graphical db
# 2) loop over each network object
#    - record each relationship between patient network and network object (NOTE: we should make use of Relational Ontology (RO) here)
#    - (optional) import each network object into graphical db (we might only want to import a setset of this network object??)
#    - delete network object
# 3) import relationships between the patient network and network objects into graphical db.
# 4) (to do) build and import relationships between network objects
#--------------------------------------
# from __future__ import print_function

import os
import networkx

from network.patient_service import patient

#from . import patient_service
# from . import ontology_service
# from . import graphical_db_service

class build_model(object):

    def __init__(self):
        self.pn = None
        self.on = None

    # This (and patient_service) will change, but for moment
    # load our patient network
    def patient_network(self):
        temp = patient_service.patient()
        temp.load_data()
        temp.get_nodes()
        temp.patientHPsim()
        temp.patientHPsim_edges()
        temp.get_edges()
        self.pn = temp.gg
