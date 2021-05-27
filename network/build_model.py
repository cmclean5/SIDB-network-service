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

#import os
import networkx as nx

from network.patient_service import patient
from network.ontology_service import ontology
from network.graphical_db_service import graphical_db

from network.model.graph_manager import Graph
from network.model.relationship import relationship

from network.utils import utils

from nested_lookup import nested_lookup, get_all_keys
# from .graphical_db_service import

class build_model(object):

    def __init__(self):
        self.manP  = Graph()
        self.manO  = Graph()
        self.manPO = Graph()
        self.ontology_obo_name = ['hp', 'go', 'doid', 'asdpto', 'adar']
        self.ontology_ID       = ['HP', 'GO', 'DOID', 'ASDPTO', 'ADAR']
        self.ontology_rels     = ['subClassOf']

    # This (and patient_service) will change, but for moment
    # load our patient network
    def patient_network(self):
        self.manP = Graph()
        pn = patient()
        pn.load_data()
        pn.get_nodes()
        pn.patientHPsim()
        pn.patientHPsim_edges()
        pn.get_edges()
        self.manP.graph=pn.gg.copy()

    def ontology_network(self, handle=None, rels=None):

        self.manO = Graph()
        # are we given a handle?
        if handle is not None:
            indx = None
            indx = self.ontology_obo_name.index(handle)
            if indx is not None:
                on = ontology()
                on.load(name=self.ontology_obo_name[indx],
                        pref=self.ontology_ID[indx],
                        rels=rels)
                on.insert_model_template()
                self.manO.graph=on.gg.copy()

    # neaten up, but output looks correct
    def patient_ontology_network(self, key='HPterms', label='HAS_A'):

        self.manPO = Graph()

        rel = relationship()
        rel.create()
        rel.att_map['label']        = label
        rel.att_map['predicate']    = label
        rel.att_map['Relationship'] = label

        self.manPO.graph = self.manP.link_networks(internal_key=key, external_graph=self.manO.graph.copy(), rel_template=rel.att_map)


    def import_networks(self):

        print("import Patient Network...\n")

        gdb = graphical_db(graph=self.manP.graph.copy())
        gdb.save_with_unwind()

        print("... done.\n")

        print("import HP Ontology Network...\n")

        gdb = graphical_db(graph=self.manO.graph.copy())
        gdb.save_with_unwind()

        print("... done.\n")

        print("import edges between Patient and HP Ontology Networks...\n")

        gdb = graphical_db(graph=self.manPO.graph.copy())
        gdb.save_with_unwind(edgesOnly=True)

        print("... done.\n")