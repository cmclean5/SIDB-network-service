#--------------------------------------
# Colin.D.Mclean@ed.ac.uk (09/10/2018)
# Service to batch importing network objects to Neo4J server
# using the python neo4j driver package
# Using phython 3.7, i.e. > python3 HPOobo2NEO4J_v4.py
# EXAMPLES: https://blog.pursuitofzen.com/what-i-learned-about-neo4j/
#           https://neo4j.com/docs/developer-manual/current/drivers/sessions-transactions/
#           https://dzone.com/articles/tips-for-fast-batch-updates-of-graph-structures-wi
#--------------------------------------
# from __future__ import print_function

#--- python import statements
from neo4j import GraphDatabase, basic_auth
import sys
import time as t
import numpy  as np
#import obonet as ob
import networkx as nx

#--- probably make this a more general class, to read/import/extract
#    ontology .obo files into neo4j.
class graphical_db(object):

 #--- This imports the Graph class and creates a instance bound to
 #    the default Neo4j server URI =""bolt://129.215.164.31:443", passing the
 #    user name and password
 def __init__(self, uri, user, password):
    self._driver = GraphDatabase.driver(uri,auth=basic_auth(user,password))
    self.session = self._driver.session()
    #self.tx      = self.session.begin_transaction()
    #self.X='HP:0007759'#----query example for HP term

 def close(self):
    self._driver.close()

 def delete_graph(self):
    ret = self.session.run("""MATCH (n:HPO) DETACH DELETE n""")


 #@classmethod
 def create_nodes(self, batch):
    with self.session.begin_transaction() as tx:
         tx.run("""UNWIND {batch} AS row
                   MERGE (n:HPO {id: row.id})
                   ON CREATE SET n.name = row.name
                   ON MATCH SET n.name = row.name
                   """, {"batch": batch})
         tx.commit()

 #@classmethod
 def create_relations(self, batch):
    with self.session.begin_transaction() as tx:
           tx.run("""UNWIND {batch} AS row
                     MATCH (a:HPO {id: row.Pterm}),
                     (b:HPO {id: row.Cterm})
                      MERGE (a)-[r:IS_A]->(b)""",{"batch": batch})
           tx.commit()


 def node_index(self):
    #--- create constraint to make sure no
    #    multiple instances of a node appears,
    #    and also create accompanying indexing
    ret = self.session.run(
          """CREATE CONSTRAINT ON (n:HPO)
          ASSERT n.id IS UNIQUE""")

 def runExample1(self):
  print("-----------")
  print("Example 1:")
  print("Get name of terms for %s"%(self.X))

  #--- query 1
  query = """
  MATCH (n:HPO)
  WHERE n.id = {name}
  RETURN n.id AS ID, n.name AS NAME
  """

