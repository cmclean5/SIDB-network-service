# --------------------------------------
# Colin.D.Mclean@ed.ac.uk (09/10/2018)
# Importing HP Ontology to Neo4J server using the python neo4j.v1 driver package
# Using phython 3, i.e. > python3 HPOobo2NEO4J_v4.py
# EXAMPLES: https://blog.pursuitofzen.com/what-i-learned-about-neo4j/
#           https://neo4j.com/docs/developer-manual/current/drivers/sessions-transactions/
# --------------------------------------
# from __future__ import print_function

# --- python import statements
import pkg_resources
import numpy as np
import pandas as pd
import networkx as nx

from network.model import node
from network.model import relationship

FNAME = "patient_dataset.csv"
THRES = 0.2

# --- probably make this a more general class, to read pateient data
class patient(object):

    # ---This class creates an instance of the test patient dataset, and
    #    constructs an network object from the data.
    def __init__(self):
        #self.dataDIR = pkg_resources.resource_filename('SIDB-network-service.tests', 'data')
        self.dataDIR = pkg_resources.resource_filename('tests', 'data')
        self.data    = None
        self.data_CN = None
        self.cdata   = []
        self.gg      = nx.Graph()
        self.N       = 0
        self.ss      = None
        self.sim     = None

    def load_data(self, fname=FNAME, fsep=','):
        self.data    = None
        self.data_CN = None
        ## load patient data
        self.data = pd.read_csv("%s/%s" % (self.dataDIR, fname), sep=fsep, header='infer')
        self.data = pd.DataFrame(self.data)

        self.data.fillna(value='', inplace=True)

        ## load patient data column names
        # self.data.columns.str.split(',') #.str.replace(' ','_')
        self.data.rename(columns={'PatientID': 'id', 'EntrezIDs': 'EntrezIDs', 'HGNCIDs': 'HGNCIDs', 'HP terms': 'HPterms', 'GO terms': 'GOterms'}, inplace=True)
        self.data_CN = self.data.columns


    def get_data(self):
        if self.data is not None:
            return self.data
        else:
            print("Error: no data file")


    def get_column_data(self, colname='EntrezIDs', csep=';'):

        if self.data_CN.contains(colname):
           # reset column data vector and get column data
           temp = []
           temp = list(self.data[colname])

           # separate each row, of column data vector, into its induvidual elements
           for i in range(len(temp)):
              for j in str.split(temp[i], csep):
                  self.cdata.append(j)

           # get unique set elements in column's data vector
           self.cdata = list(set(self.cdata))


    def get_nodes(self):

        if self.data is not None:
            self.N = len(self.data)

            if self.N > 0:

                self.Nodes = []

                for rk, rv in self.data.iterrows():
                    rkeys = list(rv.keys())
                    rvals = list(rv.values)
                    att_map = {}
                    for rkeys, rvals in zip(rkeys, rvals):
                        att_map.setdefault(rkeys, rvals)
                        #att_map.setdefault(rkeys, []).append(rvals) #.split(';')
                    #att_map.update({'nodeID': [(rk+1)]})
                    att_map['name']     = 'John Smith v%s' %( str(rk))
                    att_map['label']    = 'Patient'
                    att_map['category'] = 'Patient'
                    self.gg.add_node(rk, att_map)

    def patientHPsim(self):

        if self.data is not None:
            self.N = len(self.data)

            if self.N > 0:

                self.sim = np.zeros([self.N, self.N], dtype=np.double)

            for i in range(self.N):
                s1 = self.data['HPterms'][i]
                #if not np.isnan(s1):
                s1 = set(str.split(s1, ';'))
                for j in range(self.N):
                    if j > i:
                        s2 = self.data['HPterms'][j]
                        #if not np.isnan(s2):
                        s2 = set(str.split(s2, ';'))
                        sint = s1.intersection(s2)
                        suin = s1.union(s2)
                        val = len(sint) / len(suin)
                        self.sim[i, j] = val
                        self.sim[j, i] = val
                        # print(sim[i,j])


    def patientHPsim_edges(self, threshold=THRES):

        if self.sim is not None:

            dim = self.sim.shape

            if (dim[0] == dim[1]) and dim[0] > 0:

                self.ss = []

            for i in range(dim[0]):
                for j in range(dim[0]):
                    if j > i:
                        if self.sim[i, j] >= threshold:
                            self.ss.append([i, j, round(self.sim[i, j], 3)])


    def get_edges(self):

        if (self.ss is not None) and (self.gg.number_of_nodes() > 0):
            dim = len(self.ss)

            if dim > 0:

                patient_rel = relationship.relationship()

                edge_label = "Shared_HP_terms"

                for i in range(len(self.ss)):
                    U  = self.ss[i][0]
                    V  = self.ss[i][1]
                    We = self.ss[i][2]

                    patient_rel.__init__()
                    patient_rel.create(objID='Pe:{}'.format(i),
                                       objLABEL=edge_label,
                                       soID=self.gg.node[U]['id'],
                                       siID=self.gg.node[V]['id'],
                                       soLABEL=self.gg.node[U]['label'],
                                       siLABEL=self.gg.node[V]['label'],
                                       dir="",
                                       we=str(We),# fix
                                       meth="HP_Jacard_Sim",
                                       _type=edge_label,
                                       _pred=edge_label
                                       )

                    self.gg.add_edge(u=U,v=V, attr_dict=patient_rel.att_map)
