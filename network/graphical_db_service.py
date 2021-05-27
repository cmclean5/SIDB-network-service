import pandas as pd
import logging, yaml, json
import itertools, uuid, click
import pkg_resources

from network.model.graph_manager import Graph
from network.model.graph_query   import Query, QueryLocation, QueryType

from typing import Union, Dict, List
from collections import defaultdict

from neo4j.v1 import GraphDatabase as bolt_gdb
from neo4j.v1.types import Node, Record

# Nice to have, but we may want to remove this later, as/if only using bolt??
from neo4jrestclient.client import GraphDatabase as http_gdb

neo4j_log = logging.getLogger("neo4j.bolt")
neo4j_log.setLevel(logging.WARNING)

# For the moment, lets see if we can import networkx graphs into neo4j (<- YES WE CAN:
#  Tested .save() and .save_with_unwind() with the Patient network.),
# using kgx's batch queries... the kgx package also has the functionality
# extract graphs from neo4j into a networkx object (test later).
# knowledge graph exchange tools for biolink-compatible graphs
# https://github.com/NCATS-Tangerine/kgx

class graphical_db(Graph):
    """

    We expect a Translator canonical style http://bit.ly/tr-kg-standard
    E.g. predicates are names with underscores, not IDs.

    Does not load from config file if uri and username are provided.

    """

    def __init__(self, graph=None, host=None, ports=None, username=None, password=None, **args):
        super(graphical_db, self).__init__(graph)

        self.bolt_driver = None
        self.http_driver = None

        if ports is None:
            # read from config
            with open(pkg_resources.resource_filename('network', 'config.yml'), 'r') as ymlfile:
                #with open('config.yml', 'r') as ymlfile:
                cfg = yaml.load(ymlfile)
                bolt_uri = "bolt://{}:{}".format(cfg['neo4j']['host'], cfg['neo4j']['ports']['bolt'])
                username = cfg['neo4j']['username']
                password = cfg['neo4j']['password']
                logging.debug("Initializing bolt driver with URI: {}".format(bolt_uri))
                self.bolt_driver = bolt_gdb.driver(bolt_uri, auth=(username, password), **args)

                if 'http_port' in cfg['neo4j']:
                    http_uri = "http://{}:{}".format(cfg['neo4j']['host'], cfg['neo4j']['ports']['http'])
                    logging.debug("Initializing http driver with URI: {}".format(http_uri))
                    self.http_driver = http_gdb(http_uri, username=username, password=password)
                if 'https_port' in cfg['neo4j']:
                    https_uri = "https://{}:{}".format(cfg['neo4j']['host'], cfg['neo4j']['ports']['https'])
                    logging.debug("Initializing https driver with URI: {}".format(https_uri))
                    self.http_driver = http_gdb(https_uri, username=username, password=password)
        else:
            if 'bolt' in ports:
                bolt_uri = "bolt://{}:{}".format(host, ports['bolt'])
                self.bolt_driver = bolt_gdb.driver(bolt_uri, auth=(username, password), **args)
            if 'http' in ports:
                http_uri = "http://{}:{}".format(host, ports['http'])
                self.http_driver = http_gdb(http_uri, username=username, password=password)
            if 'https' in ports:
                https_uri = "https://{}:{}".format(host, ports['https'])
                self.http_driver = http_gdb(https_uri, username=username, password=password)

 
    def build_label(self, label:Union[List[str], str, None]) -> str:
        """
        Takes a potential label and turns it into the string representation
        needed to fill a cypher query.
        """
        if label is None:
            return ''
        elif isinstance(label, str):
            if ' ' in label:
                return f':`{label}`'
            else:
                return f':{label}'
        elif isinstance(label, (list, set, tuple)):
            label = ''.join([self.build_label(l) for l in label])
            return f'{label}'

    def build_properties(self, properties:Dict[str, str]) -> str:
        if properties == {}:
            return ''
        else:
            return ' {{ {properties} }}'.format(properties=self.parse_properties(properties))

    def clean_whitespace(self, s:str) -> str:
        replace = {
            '  ' : ' ',
            '\n' : ''
        }

        while any(k in s for k in replace.keys()):
            for old_value, new_value in replace.items():
                s = s.replace(old_value, new_value)

        return s.strip()

    def build_query_kwargs(self):
        properties = defaultdict(dict)
        labels = defaultdict(list)

        for c in self.querys:
            query_type = c.query_type

            if query_type is QueryType.PROPERTY:
                arg = c.target
                property_name, property_value = c.value
                properties[arg][property_name] = property_value

            elif query_type is QueryType.LABEL or query_type is QueryType.CATEGORY:
                arg = c.target
                labels[arg].append(c.value)

            else:
                assert False

        kwargs = {k : '' for k in Query.targets()}

        for arg, value in properties.items():
            kwargs[arg] = self.build_properties(value)

        for arg, value in labels.items():
            kwargs[arg] = self.build_label(value)

        return kwargs

  
    def save_node(self, tx, obj):
        """
        Load a node into neo4j
        """

        if 'id' not in obj:
            raise KeyError("node does not have 'id' property")
        if 'name' not in obj:
            logging.warning("node does not have 'name' property")

        if 'category' not in obj:
            logging.warning("node does not have 'category' property. Using 'Node' as default")
            label = 'Node'
        else:
            label = obj.pop('category')

        properties = ', '.join('n.{0}=${0}'.format(k) for k in obj.keys())
        query = "MERGE (n:{label} {{id: $id}}) SET {properties}".format(label=label, properties=properties)
        tx.run(query, **obj)

    def save_node_unwind(self, nodes_by_category, property_names):
        """
        Save all nodes into neo4j using the UNWIND cypher clause
        """

        for category in nodes_by_category.keys():
            self.populate_missing_properties(nodes_by_category[category], property_names)
            query = self.generate_unwind_node_query(category, property_names)
            nodes = nodes_by_category[category]
            for i in range(0, len(nodes), 1000):
                end = i + 1000
                subset = nodes[i:end]
                logging.info("nodes subset: {}-{}".format(i, end))
                time_start = self.current_time_in_millis()
                with self.bolt_driver.session() as session:
                    session.run(query, nodes=subset)
                time_end = self.current_time_in_millis()
                logging.debug("time taken to load nodes: {} ms".format(time_end - time_start))

            #with self.bolt_driver.session() as session:
            #    session.run(query, nodes=nodes_by_category[category])

    def save_edge_unwind(self, edges_by_relationship_type, property_names):
        """
        Save all edges into neo4j using the UNWIND cypher clause
        """

        for predicate in edges_by_relationship_type:
            self.populate_missing_properties(edges_by_relationship_type[predicate], property_names)
            subject_label = edges_by_relationship_type[predicate][0]['subject_label']
            object_label  = edges_by_relationship_type[predicate][0]['object_label']
            query = self.generate_unwind_edge_query(predicate, subject_label, object_label, property_names)
            edges = edges_by_relationship_type[predicate]
            for i in range(0, len(edges), 1000):
                end = i + 1000
                subset = edges[i:end]
                logging.info("edges subset: {}-{}".format(i, end))
                time_start = self.current_time_in_millis()
                with self.bolt_driver.session() as session:
                    session.run(query, relationship=predicate, edges=subset)
                time_end = self.current_time_in_millis()
                logging.debug("time taken to load edges: {} ms".format(time_end - time_start))

    def generate_unwind_node_query(self, label, property_names):
        """
        Generate UNWIND cypher clause for a given label and property names (optional)
        """

        ignore_list = ['category']

        properties_dict = {p : p for p in property_names if p not in ignore_list}

        properties = ', '.join('n.{0}=node.{0}'.format(k) for k in properties_dict.keys() if k != 'id')

        query = """
        UNWIND $nodes AS node
        MERGE (n:Node {{id: node.id}})
        SET n:{label}, {properties}
        """.format(label=label, properties=properties)

        query = self.clean_whitespace(query)

        logging.debug(query)

        return query


    def generate_unwind_edge_query(self, relationship, subject_label, object_label, property_names):
        """
        Generate UNWIND cypher clause for a given relationship
        """

        if subject_label is '':
            subject_label = 'Node'

        if object_label is '':
            object_label = 'Node'

        ignore_list = ['subject', 'predicate', 'object', 'subject_label', 'object_label']
        properties_dict = {p : "edge.{}".format(p) for p in property_names if p not in ignore_list}

        properties = ', '.join('r.{0}=edge.{0}'.format(k) for k in properties_dict.keys())

        query="""
        UNWIND $edges AS edge
        MATCH (s:{subject_label} {{id: edge.subject}}), (o:{object_label} {{id: edge.object}})
        MERGE (s)-[r:{edge_label}]->(o)
        SET {properties}
        """.format(subject_label=subject_label, object_label=object_label, properties=properties, edge_label=relationship)

        query = self.clean_whitespace(query)

        logging.debug(query)

        return query

    def save_edge(self, tx, obj):

        """
        Load an edge into neo4j
        """
        label = obj.pop('predicate')
        subject_id = obj.pop('subject')
        object_id = obj.pop('object')

        subject_label = obj.pop('subject_label')
        object_label  = obj.pop('object_label')

        properties = ', '.join('r.{0}=${0}'.format(k) for k in obj.keys())

        q = """
        MATCH (s:{subject_label} {{id:$subject_id}}), (o:{object_label} {{id:$object_id}})
        MERGE (s)-[r:{label}]->(o)
        SET {properties}
        """.format(subject_label=subject_label, object_label=object_label, properties=properties, label=label)

        q = self.clean_whitespace(q)

        tx.run(q, subject_id=subject_id, object_id=object_id, **obj)

    def save_from_csv(self, nodes_filename, edges_filename):
        """
        Load from a CSV to neo4j
        """
        nodes_df = pd.read_csv(nodes_filename)
        edges_df = pd.read_csv(edges_filename)

        with self.bolt_driver.session() as session:
            for index, row in nodes_df.iterrows():
                session.write_transaction(self.save_node, row.to_dict())
            for index, row in edges_df.iterrows():
                session.write_transaction(self.save_edge, row.to_dict())
        self.neo4j_report()

    def save_with_unwind(self, edgesOnly=False):

        """
        Load from a nx graph to neo4j using the UNWIND cypher clause
        """

        nodes_by_category = {}
        node_properties = []
        for n in self.graph.nodes():
            node = self.graph.node[n]
            if 'id' not in node:
                continue

            category = node['category']
            if category not in nodes_by_category:
                nodes_by_category[category] = [node]
            else:
                nodes_by_category[category].append(node)

            node_properties += [x for x in node if x not in node_properties]

        edges_by_relationship_type = {}
        edge_properties = []
        for e, (eso, esi, eattr) in enumerate(self.graph.edges(data=True)):
            predicate = eattr['predicate']
            if predicate not in edges_by_relationship_type:
                edges_by_relationship_type[predicate] = [eattr]
            else:
                edges_by_relationship_type[predicate].append(eattr)
            edge_properties += [x for x in eattr.keys() if x not in edge_properties]

        with self.bolt_driver.session() as session:
            session.write_transaction(self.create_constraints, nodes_by_category.keys())

        if edgesOnly:
            self.save_edge_unwind(edges_by_relationship_type, edge_properties)
        else:
            self.save_node_unwind(nodes_by_category, node_properties)
            self.save_edge_unwind(edges_by_relationship_type, edge_properties)

    def save(self):
        """
        Load from a nx graph to neo4j
        """

        labels = {'Node'}
        for n in self.graph.nodes():
            node = self.graph.node[n]
            if 'category' in node:
                if isinstance(node['category'], list):
                    labels.update(node['category'])
                else:
                    labels.add(node['category'])

        with self.bolt_driver.session() as session:
            session.write_transaction(self.create_constraints, labels)
            for node_id in self.graph.nodes():
                node_attributes = self.graph.node[node_id]
                if 'id' not in node_attributes:
                    node_attributes['id'] = node_id
                session.write_transaction(self.save_node, node_attributes.copy())
            for e, (eso, esi, eattr) in enumerate(self.graph.edges(data=True)):
                session.write_transaction(self.save_edge, eattr.copy())

        self.neo4j_report()

    def save_via_apoc(self, nodes_filename=None, edges_filename=None):
        """
        Load from a nx graph to neo4j, via APOC procedure
        """

        if nodes_filename is None or edges_filename is None:
            prefix = uuid.uuid4()
            nodes_filename = "/tmp/{}_nodes.json".format(prefix)
            edges_filename = "/tmp/{}_edges.json".format(prefix)

        self._save_as_json(nodes_filename, edges_filename)
        self.save_nodes_via_apoc(nodes_filename)
        self.save_edges_via_apoc(edges_filename)
        self.update_node_labels()

    def save_nodes_via_apoc(self, filename):
        """
        Load nodes from a nx graph to neo4j, via APOC procedure
        """
        logging.info("reading nodes from {} and saving to Neo4j via APOC procedure".format(filename))
        start = self.current_time_in_millis()
        query = """
        CALL apoc.periodic.iterate(
            "CALL apoc.load.json('file://""" + filename + """') YIELD value AS jsonValue RETURN jsonValue",
            "MERGE (n:Node {id:jsonValue.id}) set n+=jsonValue",
            {
                batchSize: 10000,
                iterateList: true
            }
        )
        """

        self.http_driver.query(query)
        end = self.current_time_in_millis()
        logging.debug("time taken for APOC procedure: {} ms".format(end - start))

    def save_edges_via_apoc(self, filename):
        """
        Load edges from a nx graph to neo4j, via APOC procedure
        """
        logging.info("reading edges from {} and saving to Neo4j via APOC procedure".format(filename))
        start = self.current_time_in_millis()
        query = """
        CALL apoc.periodic.iterate(
            "CALL apoc.load.json('file://""" + filename + """') YIELD value AS jsonValue return jsonValue",
            "MATCH (a:Node {id:jsonValue.subject})
            MATCH (b:Node {id:jsonValue.object})
            CALL apoc.merge.relationship(a,jsonValue.predicate,{id:jsonValue.id},jsonValue,b) YIELD rel
            RETURN count(*) as relationships",
            {
                batchSize: 10000,
                iterateList: true
            }
        );
        """

        self.http_driver.query(query)
        end = self.current_time_in_millis()
        logging.debug("time taken for APOC procedure: {} ms".format(end - start))

    def update_node_labels(self):
        """
        Update node labels
        """
        logging.info("updating node labels")
        start = self.current_time_in_millis()
        query_string = """
        UNWIND $nodes as node
        MATCH (n:Node {{id: node.id}}) SET n:{node_labels}
        """

        nodes_by_category = {}
        for node in self.graph.nodes(data=True):
            node_data = node[1]
            key = ':'.join(node_data['category'])
            if key in nodes_by_category:
                nodes_by_category[key].append(node_data)
            else:
                nodes_by_category[key] = [node_data]

        for category in nodes_by_category:
            query = query_string.format(node_labels=category)
            with self.bolt_driver.session() as session:
                session.run(query, nodes=nodes_by_category[category])
        end = self.current_time_in_millis()
        logging.debug("time taken to update node labels: {} ms".format(end - start))

    def report(self):
        logging.info("Total number of nodes: {}".format(len(self.graph.nodes())))
        logging.info("Total number of edges: {}".format(len(self.graph.edges())))

    def neo4j_report(self):
        """
        Give a summary on the number of nodes and edges in neo4j database
        """
        with self.bolt_driver.session() as session:
            for r in session.run("MATCH (n) RETURN COUNT(*)"):
                logging.info("Number of Nodes: {}".format(r.values()[0]))
            for r in session.run("MATCH (s)-->(o) RETURN COUNT(*)"):
                logging.info("Number of Edges: {}".format(r.values()[0]))


    def delete_db_data(self, label):
        """"
        Warning: Only use for developmental tasks.
        Delete all nodes and relationships in the database with associated label
        """

        total = 0
        limit = 30000

        with self.bolt_driver.session() as session:
            for r in session.run("MATCH (n:{label}) RETURN COUNT(*)".format(label=label)):
                total = r.values()[0]
                logging.info("Total {} Nodes: {}".format(label, total))

        while total > 0:
            with self.bolt_driver.session() as session:
                for r in session.run("""
                MATCH (n:{label}) 
                WITH n LIMIT {limit}
                DETACH DELETE n
                RETURN COUNT(*)
                """.format(label=label, limit=limit)):
                    subset = r.values()[0]
                    total  = total - subset
                    logging.info("Total {} Nodes: {}".format(label, total))


    def create_constraints(self, tx, labels):
        """
        Create a unique constraint on node 'id' for all labels
        """
        query = "CREATE CONSTRAINT ON (n:{}) ASSERT n.id IS UNIQUE"
        label_set = set()

        for label in labels:
            if ':' in label:
                sub_labels = label.split(':')
                for sublabel in sub_labels:
                    label_set.add(sublabel)
            else:
                label_set.add(label)

        for label in label_set:
            tx.run(query.format(label))


    def _save_as_json(self, node_filename, edge_filename):
        """
        Write a graph as JSON (used internally)
        """
        nodes = self._save_nodes_as_json(node_filename)
        edges = self._save_edges_as_json(edge_filename)

    def _save_nodes_as_json(self, filename):
        """
        Write nodes as JSON (used internally)
        """
        FH = open(filename, "w")
        nodes = []
        for node in self.graph.nodes(data=True):
            nodes.append(node[1])

        FH.write(json.dumps(nodes))
        FH.close()

    def _save_edges_as_json(self, filename):
        """
        Write edges as JSON (used internally)
        """
        FH = open(filename, "w")
        edges = []
        for edge in self.graph.edges_iter(data=True, keys=True):
            edges.append(edge[3])

        FH.write(json.dumps(edges))
        FH.close()

    @staticmethod
    def parse_properties(properties, delim = '|'):
        propertyList = []
        for key in properties:
            if key in ['subject', 'predicate', 'object']:
                continue

            values = properties[key]
            if type(values) == type(""):
                pair = "{}: \"{}\"".format(key, str(values))
            else:
                pair = "{}: {}".format(key, str(values))
            propertyList.append(pair)
        return ','.join(propertyList)

    @staticmethod
    def populate_missing_properties(objs, properties):
        for obj in objs:
            missing_properties = set(properties) - set(obj.keys())
            for property in missing_properties:
                obj[property] = ''