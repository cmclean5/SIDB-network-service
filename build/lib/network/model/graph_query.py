"""
The classes in this file are for aiding the building of filtered cypher queries
in NeoTransformer.
"""

from enum import Enum
from typing import Union, Tuple

class QueryLocation(Enum):
    SUBJECT='subject'
    OBJECT='object'
    EDGE='edge'
    NODE='node'

    @staticmethod
    def values():
        return [x.value for x in QueryLocation]

class QueryType(Enum):
    LABEL='label'
    CATEGORY='category'
    PROPERTY='property'

    @staticmethod
    def values():
        return [x.value for x in QueryType]


class Query(object):
    """
    Represents a cypher Query in :py:class:src.graphical_db
    """
    def __init__(self, target:str, value:Union[str, Tuple[str, str]]):
        query_local, query_type = target.split('_')
        self.target = target
        self.query_local = QueryLocation(query_local)
        self.query_type = QueryType(query_type)
        self.value = value

        if self.query_type is QueryType.PROPERTY:
            assert isinstance(value, tuple) and len(value) == 2, 'Property filter values must be a tuple of length 2'

    def __str__(self):
        """
        A human readable string representation of a Filter object
        types:
            subject_category
            object_category
            node_category
            edge_label

            subject_property
            object_property
            node_property
            edge_property
        """
        return 'Query[target={}, value={}]'.format(self.target, self.value)

    @staticmethod
    def build(query_local:QueryLocation, query_type:QueryType, value):
        """
        A factory method for building a Filter using the given enums

        Only edges should have the target "edge_label", and edges should not be
        combined with the "category" location.
        """
        assert not (query_type is QueryType.LABEL and query_local is not QueryLocation.EDGE)
        assert not (query_local is QueryLocation.EDGE and query_type is QueryType.CATEGORY)

        return Query('{}_{}'.format(query_local.value, query_type.value), value)

    @staticmethod
    def targets():
        targets = []
        for query_type in QueryType:
            for query_local in QueryLocation:
                try:
                    targets.append(
                        Query.build(query_type=query_type, query_local=query_local, value=(None, None)).target
                    )
                except:
                    continue
        return targets

if __name__ == '__main__':
    print(Query('subject_label', 'gene'))
    print(Query.build(QueryLocation.EDGE, QueryType.PROPERTY, ('property_name', 'property_value')))
    print(Query.targets())
