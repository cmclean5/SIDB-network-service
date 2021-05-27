#--------------------------------------
# Colin.D.Mclean@ed.ac.uk (09/10/2018)
# Service to batch importing network objects to Neo4J server
# using the python neo4j driver package
# Using phython 3.7, i.e. > python3 HPOobo2NEO4J_v4.py
# This class will accept a networkx object, to be imported into neo4j via bolt.
# We will have to:
# 1)
# EXAMPLES:
#  1)      Please look at the nxneo4j package (for importing networkx graph data into neo4j using bolt):
#          https://github.com/neo4j-graph-analytics/networkx-neo4j/tree/master/nxneo4j
#  2)      and the neonx package, for formatting networkx data into that which we can use in (1):
#          https://github.com/ducky427/neonx/tree/master/neonx
#
# MATERIAL:
#          https://blog.pursuitofzen.com/what-i-learned-about-neo4j/
#          https://neo4j.com/docs/developer-manual/current/drivers/sessions-transactions/
#          https://dzone.com/articles/tips-for-fast-batch-updates-of-graph-structures-wi
#          https://learnxinyminutes.com/docs/cypher/
#--------------------------------------
# from __future__ import print_function

#--- python import statements
from neo4j import GraphDatabase, basic_auth
#import sys
#import time as t
#import numpy  as np
#import obonet as ob
import networkx as nx

from network.utils import utils

#--- Let's use kgx's NeoTransformer class (we'll rename graphical_db),
#    if the kgx class doesn't work, lets fall back to our verison, i.e. this old
#    graphical_db class.

#--- probably make this a more general class, to read/import/extract
#    ontology .obo files into neo4j.
class graphical_db(object):

    #--- This imports the Graph class and creates a instance bound to
    #    the default Neo4j server URI =""bolt://129.215.164.31:443", passing the
    #    user name and password
    def __init__(self, uri, user, password):
        #self._driver        = GraphDatabase.driver(uri,auth=basic_auth(user,password))
        #self.session        = self._driver.session()
        self.gg              = nx.Graph()
        self.nodeLabel       = None
        self.nodeSourceLabel = None
        self.nodeTargetLabel = None
        self.relLabel        = None
        self.relSourceLabel  = None
        self.relTargetLabel  = None
        self.node_att_keys   = []
        self.edge_att_keys   = []

    def get_node(self, properties, sep=';'):

        temp = {}
        for i in self.node_att_keys:
            values = properties[i]
            if not isinstance(values, dict):
                temp[i] = utils.get_values(values=values, sep=sep)

        return temp

    # for the moment this is same as get_node function above
    def get_edge(self, properties, sep=';'):

        temp = {}
        for i in self.edge_att_keys:
            values = properties[i]
            if not isinstance(values, dict):
                temp[i] =utils.get_values(values=values, sep=sep)

        return temp


    def find_node_att_keys(self):
        if self.gg.number_of_nodes() > 0:
            data = self.gg.nodes(data=True)
            (nid, att) = data[0]
            self.node_att_keys = list(att.keys())

    def find_edge_att_keys(self):
        if self.gg.number_of_edges() > 0:
            data = self.gg.edges(data=True)
            (eid_so, eid_si, att) = data[0]
            self.edge_att_keys = list(att.keys())

    def load_graph(self, graph=nx.Graph(), _nodeSourceLabel=None, _nodeTargetLabel=None, _relLabel=None, _relSourceLabel='source', _relTargetLabel='target'):

        self.gg.clear()
        self.gg              = graph
        self.nodeLabel       = _nodeSourceLabel
        self.nodeSourceLabel = _nodeSourceLabel
        self.nodeTargetLabel = _nodeSourceLabel
        self.relLabel        = _relLabel
        self.relSourceLabel  = _relSourceLabel
        self.relTargetLabel  = _relTargetLabel

        if _nodeTargetLabel is not None:
            self.nodeTargetLabel = _nodeTargetLabel

        self.find_node_att_keys()
        self.find_edge_att_keys()

    def remove_att_key(self, _key=None, _map=[]):

        if (_key is not None) and (len(_map) > 0):
            if _key in _map:
                _map.remove(_key)
                return(_map)

        return(_map)

    def add_entity_properties(self, _MIN=0, _MAX=0, _MAP=None):

        temp = ""

        if _MAP is not None:

            for i in range(_MIN, _MAX):
                temp += "%s: value.%s, "%(_MAP[i], _MAP[i])

        return(temp)

    def build_node_query(self):
        query = []
        query.append("UNWIND {values} AS value MERGE (n:%s {%s: value.%s } ) "%(self.nodeLabel,"id","id"))

        t_node_att_keys = self.node_att_keys.copy()
        t_node_att_keys = self.remove_att_key(_key="id", _map=t_node_att_keys)
        #t_node_att_keys.remove('id')

        N = (len(t_node_att_keys)-1)

        if N > 0 :
            query.append("ON CREATE SET n {")

            query.append(self.add_entity_properties(_MIN=0, _MAX=N, _MAP=t_node_att_keys))
            query.append("%s: value.%s}"%(t_node_att_keys[N], t_node_att_keys[N]))

            query.append("ON MATCH SET n {")

            query.append(self.add_entity_properties(_MIN=0, _MAX=N, _MAP=t_node_att_keys))
            query.append("%s: value.%s}" % (t_node_att_keys[N], t_node_att_keys[N]))

        return ' '.join(query)


    def build_edge_query(self):
        query = []

        query.append("UNWIND {values} AS value")
        query.append("MATCH (a:%s {id: value.%s}), (b:%s {id: value.%s})"
                     %(self.nodeSourceLabel, self.relSourceLabel, self.nodeTargetLabel, self.relTargetLabel))

        t_edge_att_keys = self.edge_att_keys.copy()
        t_edge_att_keys = self.remove_att_key(_key=self.relSourceLabel, _map=t_edge_att_keys)
        t_edge_att_keys = self.remove_att_key(_key=self.relTargetLabel, _map=t_edge_att_keys)
        t_edge_att_keys = self.remove_att_key(_key=self.relLabel, _map=t_edge_att_keys)

        N = (len(t_edge_att_keys)-1)

        query.append("DO {")
        # add edge
        if N <= 0:
            query.append("MERGE (a)-[r:value.%s]->(b)" % (self.relLabel))
            # check if graph is not directed
            if not self.gg.is_directed():
                query.append("MERGE (b)-[r:value.%s]->(a)" % (self.relLabel))
        else:
            query.append("MERGE (a)-[r:value.%s {"%(self.relLabel))
            query.append(self.add_entity_properties(_MIN=0, _MAX=N, _MAP=t_edge_att_keys))
            query.append("%s: value.%s}" % (t_edge_att_keys[N], t_edge_att_keys[N]))
            query.append("]->(b)")

            # check if graph is not directed
            if not self.gg.is_directed():
                query.append("MERGE (b)-[r:value.%s {"%(self.relLabel))
                query.append(self.add_entity_properties(_MIN=0, _MAX=N, _MAP=t_edge_att_keys))
                query.append("%s: value.%s}" % (t_edge_att_keys[N], t_edge_att_keys[N]))
                query.append("]->(a)")

        query.append("}")

        return ' '.join(query)


    def import_nodes(self):

        entities = []

        for i, (nid, properties) in enumerate(self.gg.nodes(data=True)):
            entities.append(self.get_node(properties=properties))

        with self.session.begin_transaction() as tx:
            query = self.build_node_query()
            tx.run(query, {"values": entities})
            tx.commit()


    def import_edges(self):

        entities = []

        for i, (eid_so, eid_si, properties) in enumerate(self.gg.edges(data=True)):
            entities.append(self.get_edge(properties=properties))

        with self.session.begin_transaction() as tx:
            query = self.build_edge_query()
            tx.run(query, {"values": entities})
            tx.commit()


    def close(self):
        self._driver.close()


    def delete_graph(self):
            ret = self.session.run("MATCH (n:%s) DETACH DELETE n"%(self.nodeLabel))


    def create_node_index(self):
       #--- create constraint to make sure no
       #    multiple instances of a node appears,
       #    and also create accompanying indexing
       ret = self.session.run(
                              """CREATE CONSTRAINT ON (n:%s)
                              ASSERT n.id IS UNIQUE"""%(self.nodeLabel))

    #def runExample1(self):
    #    print("-----------")
    #    print("Example 1:")
    #    print("Get name of terms for %s"%(self.X))

  #--- query 1
  #query = """
  #MATCH (n:HPO)
  #WHERE n.id = {name}
  #RETURN n.id AS ID, n.name AS NAME
  #"""

