# --- python import statements
import pkg_resources
import pandas as pd
import numpy as np
import networkx as nx
from   random import *

# Notes
# nice introduction to python's random number package
# https://docs.python.org/3/library/random.html

DDD     = "DDG2P_3_10_2018.csv"
DDD2GO  = "DDD_EntrezIDS2GOterms.csv"
OUTFILE = "patient_dataset_x.csv"


class PatientDDD(object):

    """
    Class to model/generate a simple patient ASD-related data-set from the DDD csv files [DDG2P_3_10_2018.csv, and DDD_EntrezIDS2GOterms.csv].
    We make the assume that patient associated ASD data, curated from publically available papers, will have:
    1) Had one or two genes sequenced and found associated with observed traits, and
    2) that these genes can be found within the ddd csv file.
    """

    def __init__(self):
        #self.dataDIR = pkg_resources.resource_filename('SIDB-network-service.tests', 'data')
        self.dataDIR = pkg_resources.resource_filename('tests', 'data')

        #--- load ddd csv file as data-frame
        self.ddd_data       = None
        self.ddd_data_CN    = None

        #--- load ddd genes to GO terms csv file as data-frame
        self.ddd2GO_data    = None
        self.ddd2GO_data_CN = None

        #--- save simulated/generated data as data-frame
        self.out_df         = None

        #--- Number of pateints in the model
        self.N              = 0

        #--- Store the each patient ID
        self.pateintID      = list()
        #--- Store the gene-set (used entrez IDs) for each patient
        self.patientGS      = list()
        #--- Store phenotype terms (i.e. HP terms) associated with patient
        self.patientPS      = list()
        #--- Store hgnc IDs associated with patient
        self.hgncIDs        = list()
        #--- Store patient GO terms associated with patient
        self.patientGO      = list()

        self.gg = nx.Graph()


    def load_data(self, sep='\t'):

        self.ddd_data       = None
        self.ddd_data_CN    = None

        self.ddd2GO_data    = None
        self.ddd2GO_data_CN = None

        self.ddd_data    = pd.read_csv("%s/%s" % (self.dataDIR, DDD), sep=sep, header='infer')
        self.ddd_data    = pd.DataFrame(self.ddd_data)
        self.ddd_data    = self.ddd_data.fillna('')
        self.ddd_data_CN = self.ddd_data.columns

        self.ddd2GO_data    = pd.read_csv("%s/%s" % (self.dataDIR, DDD2GO), sep=sep, header='infer')
        self.ddd2GO_data    = pd.DataFrame(self.ddd2GO_data)
        self.ddd2GO_data    = self.ddd2GO_data.fillna('')
        self.ddd2GO_data_CN = self.ddd2GO_data.columns


    def generate_dataset(self, population=100):

        if (self.ddd_data is not None) and (self.ddd2GO_data is not None):

            #--- Number of patients
            if population < 0:
                self.N = 100
            else:
                self.N = population

            #--- set seed for random number generator
            seed()

            #--- rest data-set lists
            self.pateintID = list()
            self.patientGS = list()
            self.patientPS = list()
            self.hgncIDs   = list()
            self.patientGO = list()

            #--- get list of all entrez gene ids from DDD dataset
            self.entrezIDs = list(self.ddd_data['eIDS'])

            #--- generate IDs for each of the N patients
            self.patientID = ['P{}'.format(x + 1) for x in range(0, self.N)]

            #--- generate gene-sets for each of the N patients
            for i in range(0, self.N):

                if random() >= 0.5:
                    self.patientGS.append(list(set(choices(self.entrezIDs, k=2))))
                else:
                    self.patientGS.append(choices(self.entrezIDs, k=1))

            #--- fill data-sets for each of the N patients
            for i in range(0, self.N):

                temp = self.ddd_data.loc[self.ddd_data['eIDS'].isin(self.patientGS[i])]
                self.patientPS.append(set([str.split(x, ';') for x in temp['phenotypes']][0]))
                self.hgncIDs.append(set([x for x in temp['hgnc.id']]))

                temp = self.ddd2GO_data.loc[self.ddd2GO_data['EntrezID'].isin(self.patientGS[i])]
                self.patientGO.append(set([x for x in temp['GO term']]))


    def collapse(self, target: list, sep: str) -> list:
        return [sep.join(map(str, x)) for x in target]


    def save_dataset(self, csep=';', fsep=','):

        datasets = list(zip(self.patientID,
                            self.collapse(target=self.patientGS, sep=csep),
                            self.collapse(target=self.hgncIDs,   sep=csep),
                            self.collapse(target=self.patientPS, sep=csep),
                            self.collapse(target=self.patientGO, sep=csep)))

        columns = ['PatientID', 'EntrezIDs', 'HGNCIDs', 'HP terms', 'GO terms']

        self.out_df = pd.DataFrame(datasets, columns=columns)

        self.out_df.to_csv(path_or_buf='%s/%s' %(self.dataDIR, OUTFILE), sep=fsep, header=True, index=False)
