# --------------------------------------
# Colin.D.Mclean@ed.ac.uk (09/10/2018)
# A basic template class to hold various variables associated
# with different network node types (i.e. patient data, ontologies etc)
# Using phython 3, i.e. > python3 HPOobo2NEO4J_v4.py
#
# --------------------------------------
# from __future__ import print_function

class node(object):

    def __init__(self):
        self.object_ID       = None
        self.object_LABEL    = None
        self.object_CATEGORY = None
        self.object_NAME     = None
        self.object_XREFS    = None
        self.att_map         = {}

    def create(self, objID= '', objNAME= '', objLABEL= '', objCATEGORY= '', objXREFS= ''):

        self.object_ID       = objID
        self.object_LABEL    = objLABEL
        self.object_CATEGORY = objCATEGORY
        self.object_NAME     = objNAME
        self.object_XREFS    = objXREFS

        self.build_map()

    def build_map(self):

        t_att_map = {
            "id":       self.object_ID,
            "label":    self.object_LABEL,
            "category": self.object_CATEGORY,
            "name":     self.object_NAME,
            "xrefs":    self.object_XREFS
        }

        self.att_map = {k: str(v) for k, v in t_att_map.items()}# if v is not None}
        #self.att_map = t_att_map

    #def reset(self):
    #    self.att_map = {}

    def print_properties(self):
        for k,v in self.att_map.items():
            print("%s : %s \n"%(str(k), str(v)))
