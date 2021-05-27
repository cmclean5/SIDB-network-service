# --------------------------------------
# Colin.D.Mclean@ed.ac.uk (09/10/2018)
# A basic template class to hold various variables associated
# with different network relationship types (i.e. patient, ontology, PPI etc)
# Using phython 3, i.e. > python3 HPOobo2NEO4J_v4.py
#
# --------------------------------------
# from __future__ import print_function

from network.utils import utils

class relationship(object):

    def __init__(self):
        self.object_ID    = None
        self.object_NAME  = None
        self.object_LABEL = None
        self.source_ID    = None
        self.source_NAME  = None
        self.source_LABEL = None
        self.target_ID    = None
        self.target_NAME  = None
        self.target_LABEL = None
        self.directed     = None
        self.weight       = None
        self.method       = None
        self.type         = None
        self.pred         = None
        self.RO_ID        = None
        self.RO_NAME      = None
        self.att_map      = {}

    def create(self, objID = '', objNAME  = '', objLABEL = '',
                     soID  = '', soNAME   = '', soLABEL = '',
                     siID  = '', siNAME   = '', siLABEL = '',
                     dir   = '', we       = '', _pred='', _type = '', meth = '',
                    _RO_ID = '', _RO_NAME = '' ):

        self.object_ID    = objID
        self.object_NAME  = objNAME
        self.object_LABEL = objLABEL
        self.source_ID    = soID
        self.source_NAME  = soNAME
        self.source_LABEL = soLABEL
        self.target_ID    = siID
        self.target_NAME  = siNAME
        self.target_LABEL = siLABEL
        self.directed     = dir
        self.weight       = we
        self.method       = meth
        self.type         = _type
        self.pred         = _pred
        self.RO_ID        = _RO_ID
        self.RO_NAME      = _RO_NAME

        self.build_map()

    def build_map(self):

        t_att_map = {
            "id":            self.object_ID,
            "name":          self.object_NAME,
            "label":         self.object_LABEL,
            #"source": self.source_ID,
            #"source_name": self.source_NAME,
            #"source_label": self.source_LABEL,
            "subject":       self.source_ID,
            "subject_name":  self.source_NAME,
            "subject_label": self.source_LABEL,
            #"target": self.target_ID,
            #"target_name": self.target_NAME,
            #"target_label": self.target_LABEL,
            "object":        self.target_ID,
            "object_name":   self.target_NAME,
            "object_label":  self.target_LABEL,
            "directed":      self.directed,
            "weight":        self.weight,
            "method":        self.method,
            "Relationship":  self.type,
            "predicate":     self.pred,
            "RO_id":         self.RO_ID,
            "RO_label":      self.RO_NAME
        }

        self.att_map = {k: str(utils.set_values(v)) for k, v in t_att_map.items()}# if v is not None}
        #self.att_map = t_att_map


    #def reset(self):
    #    self.att_map = {}

    def print_properties(self):
        for k,v in self.att_map.items():
            print("%s : %s \n"%(str(k), str(v)))
