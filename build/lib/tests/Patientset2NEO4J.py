#--------------------------------------
# Colin.D.Mclean@ed.ac.uk (09/10/2018)
# Importing HP Ontology to Neo4J server using the python neo4j.v1 driver package
# Using phython 3, i.e. > python3 HPOobo2NEO4J_v4.py
# EXAMPLES: https://blog.pursuitofzen.com/what-i-learned-about-neo4j/
#           https://neo4j.com/docs/developer-manual/current/drivers/sessions-transactions/
#--------------------------------------
from __future__ import print_function

#--- python import statements
from   neo4j.v1 import GraphDatabase, basic_auth
import sys
import time   as t
import numpy  as np
import obonet as ob
import networkx as nx
import csv
import os

#--- probably make this a more general class, to read/import/extract 
#    ontology .obo files into neo4j. 
class importPatient(object):
 
 #--- This imports the py2neo Graph class and creates a instance bound to
 #    the default Neo4j server URI =""bolt://129.215.164.31:443", passing the 
 #    user name and password
 def __init__(self, uri, user, password):
    self._driver = GraphDatabase.driver(uri,auth=basic_auth(user,password))
    self.session = self._driver.session()
    self.X='P:2'#----query example for HP term
 
 def close(self):
    self._driver.close()
 
 def delete_graph(self):
    ret = self.session.run("""MATCH (n:Patient) DETACH DELETE n""")
 
 
 #@classmethod
 def create_nodes(self, batch):
    with self.session.begin_transaction() as tx:
         tx.run("""UNWIND {batch} AS row
                   MERGE (n:Patient {id: row.id})
                   ON CREATE SET n.name = row.name, n.HPterms = row.HPterms
                   ON MATCH SET n.name = row.name, n.HPterms = row.HPterms
                   """, {"batch": batch})
         tx.commit()
 
 #@classmethod 
 def create_relations(self, batch):
    with self.session.begin_transaction() as tx:
           tx.run("""UNWIND {batch} AS row
                     MATCH (a:Patient {id: row.so}),
                     (b:Patient {id: row.si})
                      MERGE (a)-[r:ASSOCIATED_TO {weight:row.sim}]-(b)""",{"batch": batch})
           tx.commit()
 
 
 def node_index(self):
    #--- create constraint to make sure no 
    #    multiple instances of a node appears,
    #    and also create accompanying indexing 
    ret = self.session.run(
          """CREATE CONSTRAINT ON (n:Patient)
          ASSERT n.id IS UNIQUE""")
 
 def runExample1(self):
  print("-----------")
  print("Example 1:") 
  print("Get name of terms for %s"%(self.X))
  
  #--- query 1
  query = """
  MATCH (n:Patient)
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
  print("Get nearest neigbours of %s"%(self.X))
 
  #--- query 2
  query = """
  MATCH (n:Patient)--(m:Patient)
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
 
 N          = 0
 thres      = 0.2
 data       = []
 ss         = []
 batchNODES = []
 batchEDGES = []
 sim        = np.zeros([N,N],dtype=np.double)
 
 #--- test patient dataset   
 file = os.path.join("/home/colin/annotation_data","patientset.csv")
 pat = importPatient(uri, user, psswd)
    
 #--- we'll remove patient network before starting
 pat.delete_graph()

 #--- read patient data
 print("read test patient dataset...")
 with open(file) as infile:
  reader = csv.DictReader(infile)
  for row in reader:
    data.append(row)
 
 print("done!\n")
 
 N = len(data)
  
 if N > 0:
  
  for i in range(N):
     name = "Patient_%d"%((i+1))
     batchNODES.append({"id":data[i].get('PatientID'),'name':name,'HPterms':str.split(data[i].get('HP terms'),';')})
  
  
  sim = np.zeros([N,N],dtype=np.double)
     
  for i in range(N):
    for j in range(N):
      if j > i:
        s1 = set(str.split(data[i].get('HP terms'),';'))
        s2 = set(str.split(data[j].get('HP terms'),';'))
        sint = s1.intersection(s2)
        suin = s1.union(s2)
        val  = len(sint) / len(suin)
        sim[i,j] = val
        sim[j,i] = val
        #print(sim[i,j])
  
  for i in range(N):
     for j in range(N):
        if j > i:
          if sim[i,j] >= thres:
            ss.append([i,j,round(sim[i,j],3)])
  
  
  for i in range(len(ss)):
     batchEDGES.append({"so":batchNODES[ss[i][0]].get('id'),"si":batchNODES[ss[i][1]].get('id'),"sim":ss[i][2]})
  
  #--- load nodes into neo4j graph
  t0 = t.time()
  print("import %d Patient nodes into neo4j..."%(len(batchNODES)))
  pat.create_nodes( batchNODES )
  t1 = t.time()
  print("done!\n")
  print("elapsed time ",t1-t0,"\n")
  
  
  #---create indexes
  pat.node_index()
  
  #--- load relationships into neo4j
  t0 = t.time()
  print("import %d Patient relationships into neo4j..."%(len(batchEDGES)))
  pat.create_relations( batchEDGES )   
  t1 = t.time()
  print("done!\n")
  print("elapsed time ",t1-t0,"\n")
  
  
  #---- run tests
  pat.runExample1()
  pat.runExample2()
  
  #---- close the session
  pat.close()
  
 
 
 #--- execute main method
if __name__ == "__main__": main()
