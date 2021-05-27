#--------------------------------------
# Colin.D.Mclean@ed.ac.uk (09/10/2018)
# Importing HP Ontology to Neo4J server using the python neo4j.v1 driver package
# Using phython 3, i.e. > python3 HPOobo2NEO4J_v4.py
# EXAMPLES: https://blog.pursuitofzen.com/what-i-learned-about-neo4j/
#           https://neo4j.com/docs/developer-manual/current/drivers/sessions-transactions/
#           https://dzone.com/articles/tips-for-fast-batch-updates-of-graph-structures-wi
#--------------------------------------
from __future__ import print_function

#--- python import statements
# from neo4j.v1 import GraphDatabase, basic_auth
from neo4j import GraphDatabase, basic_auth
import sys
import time as t
import numpy  as np
import obonet as ob
import networkx as nx

#--- probably make this a more general class, to read/import/extract 
#    ontology .obo files into neo4j. 
class importHPO(object):
 
 #--- This imports the py2neo Graph class and creates a instance bound to
 #    the default Neo4j server URI =""bolt://129.215.164.31:443", passing the 
 #    user name and password
 def __init__(self, uri, user, password):
    self._driver = GraphDatabase.driver(uri,auth=basic_auth(user,password))
    self.session = self._driver.session()
    #self.tx      = self.session.begin_transaction()
    self.X='HP:0007759'#----query example for HP term
 
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
  
  print("run query...")
  res = self.session.run(query, name=self.X)
  
  for r in res:
   print(r)
 
  print("Done.") 
  print("-----------")
 
 
 def runExample2(self): 
  print("-----------")
  print("Example 2:") 
  print("Get children terms for %s"%(self.X))
 
  #--- query 2
  query = """
  MATCH (n:HPO)-->(m:HPO)
  WHERE n.id = {name}
  RETURN m.id AS ID, m.name AS NAME
  """
 
  print("run query...")
  res = self.session.run(query, name=self.X)
 
  for r in res:
   print(r)
  #----
  print("Done.") 
  print("------------")



def main():
 uri   = "bolt://129.215.164.31:443"
 user  = "neo4j"
 psswd = "network"
    
 hpo = importHPO(uri, user, psswd)
    
 #--- we'll remove HPO before starting
 hpo.delete_graph()

 #--- url for HPO's OBO file
 url = 'https://raw.githubusercontent.com/obophenotype/human-phenotype-ontology/master/hp.obo'
        
 #--- read obo file into networkx graph
 print("read HPO obo file...")
 ont = ob.read_obo(url)
 print("done!\n")
    
 #--- extract node information into csv file, load into neo4j and use as indexing for edges
 nodes = list(ont.nodes())
    
 #--- The HPO id <=> HPO name 
 id2name = {id_: data.get('name') for id_, data in ont.nodes(data=True)}
 #--- The HPO node 'IS_A' relationships
 id2term = {id_: data.get('is_a') for id_, data in ont.nodes(data=True)}
 
         
 #--- format nodes into list of dict, [{},{},{}...{}]
 #    this will be unwond into a cyther statement before being committed  
 batchNODES = []
  
 for i in range(len(nodes)):
   id   = str(list(id2name.keys())[i])
   name = str(list(id2name.values())[i])
   batchNODES.append({"id":id,"name":name})


 #--- load nodes into neo4j graph
 t0 = t.time()
 print("import %d HPO nodes into neo4j..."%(len(batchNODES)))
 hpo.create_nodes( batchNODES )
 t1 = t.time()
 print("done!\n")
 print("elapsed time ",t1-t0,"\n")
  
  
 #---create indexes
 hpo.node_index()
 
 #--- format relationships into list of dict, [{},{},{}...{}]
 #    this will be unwond into a cyther statement before being committed  
 batchEDGE = []

 for i in range(len(id2term)):
  Pterm  = list(id2term.keys())[i]
  Cterms = list(id2term.values())[i]
  if Cterms:
    for j in range(len(Cterms)):
      batchEDGE.append({"Pterm":Pterm,"Cterm":Cterms[j]})

 #--- load relationships into neo4j
 t0 = t.time()
 print("import %d HPO relationships into neo4j..."%(len(batchEDGE)))
 hpo.create_relations( batchEDGE )   
 t1 = t.time()
 print("done!\n")
 print("elapsed time ",t1-t0,"\n")
  
 
 #---- run tests
 hpo.runExample1()
 hpo.runExample2()
  
 #---- close the session
 hpo.close()
 
 
 #--- execute main method
if __name__ == "__main__": main()


