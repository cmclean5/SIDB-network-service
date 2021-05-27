#--------------------------------------
# Colin.D.Mclean@ed.ac.uk (09/10/2018)
# Service to load ontology network objects using Monarch's ontobio package
# Using phython 3.7, i.e. > python3 HPOobo2NEO4J_v4.py
# EXAMPLES: The ontobio package will handle any ontoloy in the OLS (https://www.ebi.ac.uk/ols/ontologies), i.e
#            HP  = Human Pheontype Ontology
#           DOID = Human Disease Ontology
#           GO   = Gene Ontology
# We can also load 'local' ontologies from file, for example in the OBO .json graph format, i.e.
#   SIDB-network-service/test/data/local_ontologies/ASDPhenotypeOntology_Public.json (ASDPTO)
#   SIDB-network-service/test/data/local_ontologies/autism-merged.json               (ADAR)
#
#--------------------------------------
# from __future__ import print_function

import os
import shutil
import pkg_resources
import tarfile
from nested_lookup import nested_lookup, get_all_keys
from ontobio.ontol_factory import OntologyFactory
from ontobio.slimmer import get_minimal_subgraph
from ontobio.ontol import Ontology
#from ontobio.assocmodel import AssociationSet


from network.model.node import node
from network.model.relationship import relationship

from network.utils import utils

#OBOname='hp'
#ONTpref='HP'
#OBOrels='subClassOf'

FNAME  ='local_ontologies.tar.gz'
LOCALname = ['asdpto', 'adar']
LOCALfile = ['ASDPhenotypeOntology_Public.json', 'autism-merged.json']

class ontology(object):

    def __init__(self):
        #self.dataDIR = pkg_resources.resource_filename('SIDB-network-service.tests', 'data')
        self.dataDIR = pkg_resources.resource_filename('tests','data')
        self.ofa               = None
        self.OBOname           = None
        self.ONTpref           = None
        self.OBOrels           = None
        self.local_onto_member = None
        self.local_onto_file   = None
        self.ont               = None
        self.gg                = None
        self.obs               = None

    # For the moment we just want to return the ontology,
    # in a networkx format.
    def load(self, name='hp', pref='HP', rels='subClassOf', rm_obs_terms=True):

        # set new ontology factory
        self.ofa = OntologyFactory()
        self.OBOname = name
        self.ONTpref = pref
        self.OBOrels = rels

        # check if we want to load a local ontology
        if self.OBOname in LOCALname:
            self.open_local_onto(self.OBOname)
            if self.local_onto_file is not None:
                self.ont = self.ofa.create(handle=self.local_onto_file)
                self.gg  = self.ont.get_filtered_graph()#relations=rels, prefix=ONTpref)
                self.rm_json_file()
        else:
            # build an ontology (HP, DOID, GO etc) using ontobio, might take ~10s first time an ontology is loaded
            self.ont = self.ofa.create(handle=self.OBOname)

            # filter ontology object for only 'is_a' relationships
            # ont = ont.subontology(relations=rels)

            # there's a lot going on inside (i.e. relationships and terms) ontobio's OntologyFactory object,
            # for the moment let's just extract the OBOname prefix ontology terms, and OBOrels relationship types.
            self.gg = self.ont.get_filtered_graph(relations=self.OBOrels, prefix=self.ONTpref)

        # store terms in ontology which are labeled obsolete
        self.obs = self.ont.all_obsoletes()

        if rm_obs_terms:
            self.remove_obsolete_terms()

    def remove_obsolete_terms(self):

        if (self.obs is not None) and (self.gg.number_of_nodes() > 0):
            self.gg.remove_nodes_from(self.obs)

    def open_local_onto(self, handle=None):
        tf = None
        tf = tarfile.open("%s/%s" %(self.dataDIR, FNAME), mode="r:gz")

        if tf is not None:
            indx = None
            indx = LOCALname.index(handle)
            if indx is not None:
                self.local_onto_file = self.find_json_file(tf, LOCALfile[indx])
        tf.close()

    def find_json_file(self, tf, json_file):
        for members in tf.getmembers():
            if os.path.split(members.name)[1] == json_file:
                self.local_onto_member = members
                tf.extract(member=members, path=os.fspath(self.dataDIR))
                return "%s/%s" %(os.fspath(self.dataDIR), members.path)

    def rm_json_file(self):
        if self.local_onto_member is not None:
            local_dir = "%s/%s"%(self.dataDIR, os.path.split(self.local_onto_member.path)[0])
            if os.path.isdir(local_dir):
                shutil.rmtree(path=local_dir)

    def insert_node_template(self, _nid=None, _properties=None, sep=';'):

        node_label = self.ONTpref

        ont_node = node()
        ont_node.__init__()

        ont_node.create(objID=_nid,
                        objLABEL=node_label,
                        objCATEGORY=node_label,
                        objNAME='',
                        objXREFS='')

        att_map = ont_node.att_map

        keys = get_all_keys(_properties)

        for k in keys:
            if k is not 'synonyms':
                values = utils.unlist(nested_lookup(k, _properties))
                values = utils.check_None(values)
                values = utils.set_values(values, sep)
                att_map = utils.append_values(key=k, values=values, _map=att_map, sep=';')

        return(att_map)

    def insert_edge_template(self, _eid_so=None, _eid_si=None, _properties=None, sep=';'):

        edge_label = self.OBOrels
        node_label = self.ONTpref

        ont_rel = relationship()
        ont_rel.__init__()

        ont_rel.create(soID=_eid_so,
                       siID=_eid_si,
                       soLABEL=node_label,
                       siLABEL=node_label,
                       objLABEL=edge_label,
                         we=1.0,
                      _type=edge_label,
                       _pred=edge_label)

        att_map = ont_rel.att_map

        keys = get_all_keys(_properties)

        for k in keys:
            if k is not 'synonyms':
                values = utils.unlist(nested_lookup(k, _properties))
                values = utils.check_None(values)
                values = utils.set_values(values, sep)
                att_map = utils.append_values(key=k, values=values, _map=att_map, sep=';')

        return(att_map)

    # If we're going to add an ontology to our graphical db, then will needed
    # to reformat the networkx graph's nodes and edges to follow the same basic template,
    # as provided in /model/
    def insert_model_template(self, rm_obs_terms=True):

        # do we have a network object to format
        if self.gg is not None:
            # make sure we've removed obsolete nodes from graph
            if rm_obs_terms:
                self.remove_obsolete_terms()

            t_gg = self.gg.copy()
            self.gg.clear()

            # format nodes
            nodes = {}
            for i, (nid, properties) in enumerate(t_gg.nodes(data=True)):
                att_map = self.insert_node_template(_nid=nid, _properties=properties)
                nodes[nid] = i
                self.gg.add_node(i, att_map)

            # format edges
            for i, (eid_so, eid_si, properties) in enumerate(t_gg.edges(data=True)):
                att_map = self.insert_edge_template(_eid_so=eid_so, _eid_si=eid_si, _properties=properties)
                U = nodes.get(eid_so)
                V = nodes.get(eid_si)
                self.gg.add_edge(u=U, v=V, attr_dict=att_map)
                #    clip = None


    # def get_slim_ontology(self,subset=None):
    #    if subset is not None:
    #        g    = self.ont.get_graph()
    #        clip = get_minimal_subgraph(g, subset)
    #    return clip
