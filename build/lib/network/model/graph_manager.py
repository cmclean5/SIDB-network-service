import networkx as nx
import json, time

from typing import Union, List, Dict
from networkx.readwrite import json_graph, gml

from .prefix_manager import PrefixManager
from .graph_query import Query

from network.utils import utils

SimpleValue = Union[List[str], str]

class Graph(object):
    """
    Base class for managing and importing networkx Graph, using the graphical db class:

     - from a source [file] to an in-memory property graph (networkx)
     - from an in-memory property graph (networkx) to a target format or database

    """

    def __init__(self, graph=None):
        """
        Create a new Transformer. This should be called directly on a subclass.

        Optional arg: a Transformer
        """

        if graph is not None:
            self.graph = graph
            #self.flatten_property_values(graph=graph)
        else:
            self.graph = nx.MultiDiGraph()


        self.querys = [] # Type: List[Query]
        self.graph_metadata = {}
        self.prefix_manager = PrefixManager()

    def report(self) -> None:
        g = self.graph
        print('|Nodes|={}'.format(len(g.nodes())))
        print('|Edges|={}'.format(len(g.edges())))

    def is_empty(self) -> bool:
        return len(self.graph.nodes()) == 0 and len(self.graph.edges()) == 0

    def add_query(self, f:Query) -> None:
        self.querys.append(f)

    def set_query(self, target: str, value: SimpleValue) -> None:
        self.querys.append(Query(target, value))

    def checkNodeIDlabel(self) -> bool:

        (nid, data) = self.graph.nodes(data=True)[0]
        if 'id' not in data:
            return False
        else:
            return True

    def addNodeIDlabel(self):

        if not self.checkNodeIDlabel():
            nx.set_node_attributes(self.graph, 'id', "")
            for (nid, data) in self.graph.nodes(data=True):
                self.graph.node[nid]['id'] = str(nid)

    def merge(self, graphs):
        """
        Merge all graphs with self.graph

        - If two nodes with same 'id' exist in two graphs, the nodes will be merged based on the 'id'
        - If two nodes with the same 'id' exists in two graphs and they both have conflicting values
        for a property, then the value is overwritten from left to right
        - If two edges with the same 'key' exists in two graphs, the edge will be merged based on the
        'key' property
        - If two edges with the same 'key' exists in two graphs and they both have one or more conflicting
        values for a property, then the value is overwritten from left to right

        """

        graphs.insert(0, self.graph)
        self.graph = nx.compose_all(graphs, "mergedMultiDiGraph")


    def link_networks(self, internal_key=None, external_graph=None, target_key='id', rel_template=None, sep=';'):

        """
        Return the inter-graph connecting this network, i.e. self.graph, to
        the target network, using this network's key.
        """

        inter_graph = nx.Graph()

        if internal_key in self.find_node_att_keys():

            if (external_graph is not None) and (rel_template is not None):

                ext_node_keys = []
                Nodes         = {}
                for i, (nid, nattr) in enumerate(external_graph.nodes(data=True)):
                    ext_node_keys += [x for x in nattr.keys() if x not in ext_node_keys]
                    if target_key not in ext_node_keys:
                        raise KeyError("external graph node does not have %s property") % (target_key)
                    else:
                        Nodes[nattr[target_key]] = nid

                tally = subject_k = object_k = 0
                for node_id in self.graph.nodes_iter():
                    subject_node  = self.graph.node[node_id]
                    subject_id    = utils.unlist(subject_node['id'])
                    subject_label = utils.unlist(subject_node['category'])

                    if internal_key in list(subject_node.keys()):
                        values = subject_node[internal_key]
                        values = utils.get_values(values)

                    if len(values) > 0:
                        subject_k = tally
                        inter_graph.add_node(subject_k, attr_dict=subject_node)
                        tally += 1

                        for v in values:
                            object_node = Nodes.get(v)
                            if object_node is not None:
                                object_k = tally
                                object_node  = external_graph.node[object_node]
                                object_id    = utils.unlist(object_node['id'])
                                object_label = utils.unlist(object_node['category'])
                                inter_graph.add_node(object_k, attr_dict=object_node)
                                tally += 1
                                rel_template['subject']       = subject_id
                                rel_template['subject_label'] = subject_label
                                rel_template['object']        = object_id
                                rel_template['object_label']  = object_label
                                inter_graph.add_edge(u=subject_k, v=object_k, attr_dict=rel_template)

        return inter_graph

    def remap_node_identifier(self, type, new_property, prefix=None):
        """
        Remap node `id` attribute with value from node `new_property` attribute

        Parameters
        ----------
        type: string
            label referring to nodes whose id needs to be remapped

        new_property: string
            property name from which the new value is pulled from

        prefix: string
            signifies that the value for `new_property` is a list and the `prefix` indicates which value
            to pick from the list

        """
        mapping = {}
        for node_id in self.graph.nodes_iter():
            node = self.graph.node[node_id]
            if type not in node['category']:
                continue
            if new_property in node:
                if prefix:
                    # node[new_property] contains a list of values
                    new_property_values = node[new_property]
                    for v in new_property_values:
                        if prefix in v:
                            # take the first occurring value that contains the given prefix
                            if 'HGNC:HGNC:' in v:
                                # TODO: this is a temporary fix and must be removed later
                                v = ':'.join(v.split(':')[1:])
                            mapping[node_id] = v
                            break
                else:
                    # node[new_property] contains a string value
                    mapping[node_id] = node[new_property]
            else:
                # node does not contain new_property key; fall back to original node 'id'
                mapping[node_id] = node_id

        nx.set_node_attributes(self.graph, values = mapping, name = 'id')
        nx.relabel_nodes(self.graph, mapping, copy=False)

        # update 'subject' of all outgoing edges
        updated_subject_values = {}
        for edge in self.graph.out_edges(keys=True):
            updated_subject_values[edge] = edge[0]
        nx.set_edge_attributes(self.graph, values = updated_subject_values, name = 'subject')

        # update 'object' of all incoming edges
        updated_object_values = {}
        for edge in self.graph.in_edges(keys=True):
            updated_object_values[edge] = edge[1]
        nx.set_edge_attributes(self.graph, values = updated_object_values, name = 'object')

    def remap_node_property(self, type, old_property, new_property):
        """
        Remap the value in node `old_property` attribute with value from node `new_property` attribute

        Parameters
        ----------
        type: string
            label referring to nodes whose property needs to be remapped

        old_property: string
            old property name whose value needs to be replaced

        new_property: string
            new property name from which the value is pulled from

        """
        mapping = {}
        for node_id in self.graph.nodes_iter():
            node = self.graph.node[node_id]
            if type not in node['category']:
                continue
            if new_property in node:
                mapping[node_id] = node[new_property]
            elif old_property in node:
                mapping[node_id] = node[old_property]
        nx.set_node_attributes(self.graph, values = mapping, name = old_property)

    def remap_edge_property(self, type, old_property, new_property):
        """
        Remap the value in edge `old_property` attribute with value from edge `new_property` attribute

        Parameters
        ----------
        type: string
            label referring to edges whose property needs to be remapped

        old_property: string
            old property name whose value needs to be replaced

        new_property: string
            new property name from which the value is pulled from

        """
        mapping = {}
        for edge in self.graph.edges_iter(data=True, keys=True):
            edge_key = edge[0:3]
            edge_data = edge[3]
            if type not in edge_data['edge_label']:
                continue
            if new_property in edge_data:
                mapping[edge_key] = edge_data[new_property]
            else:
                mapping[edge_key] = edge_data[old_property]
        nx.set_edge_attributes(self.graph, values = mapping, name = old_property)


    def find_node_att_keys(self):

        if self.graph.number_of_nodes() > 0:
            data = self.graph.nodes(data=True)
            (nid, att) = data[0]
            return list(att.keys())
        else:
            return None

    def find_edge_att_keys(self):

        if self.graph.number_of_edges() > 0:
            data = self.graph.edges(data=True)
            (eid_so, eid_si, att) = data[0]
            return list(att.keys())
        else:
            return None

    def flatten_property_values(self, graph=None, sep=';'):

        if graph is not None:

            for i, (nid, properties) in enumerate(graph.nodes(data=True)):
                for k, v in properties.items():
                    if isinstance(v, dict):
                        properties.pop(k, None)
                    else:
                        properties[k] = utils.get_values(values=v, sep=sep)

                self.graph.add_node(n=nid, attr_dict=properties)

            for eid, (eso, esi, properties) in enumerate(graph.edges(data=True)):
                for k, v in properties.items():
                    if isinstance(v, dict):
                        properties.pop(k, None)
                    else:
                        properties[k] = utils.get_values(values=v, sep=sep)

                self.graph.add_edge(u=eso, v=esi, attr_dict=properties)


    @staticmethod
    def dump(G):
        """
        Convert nx graph G as a JSON dump
        """
        data = json_graph.node_link_data(G)
        return data

    @staticmethod
    def dump_to_file(G, filename):
        """
        Convert nx graph G as a JSON dump and write to file
        """
        FH = open(filename, "w")
        json_data = Graph.dump(G)
        FH.write(json.dumps(json_data))
        FH.close()
        return json_data

    @staticmethod
    def dump_to_gml(G, filename):
        """
        Write nx graph G to .gml file
        """
        gml.write_gml(G, filename)

    @staticmethod
    def restore_from_gml(filename):
        """
        Create a nx graph G from a .gml file
        """
        G = gml.read_gml(filename)
        return G

    @staticmethod
    def restore(json_data):
        """
        Create a nx graph with the given JSON data
        """
        G = json_graph.node_link_graph(json_data)
        return G

    @staticmethod
    def restore_from_file(filename):
        """
        Create a nx graph with the given JSON data and write to file
        """
        FH = open(filename, "r")
        data = FH.read()
        G = Graph.restore(json.loads(data))
        return G

    @staticmethod
    def current_time_in_millis():
            return int(round(time.time() * 1000))

