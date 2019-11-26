# encoding: utf-8
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Author: Kyle Lahnakoski (kyle@lahnakoski.com)
#

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from collections import defaultdict

from mo_math import UNION

from mo_collections.queue import Queue
from mo_graphs import BaseGraph


class Graph(BaseGraph):
    def __init__(self, node_type=None):
        self.nodes = set()
        self.edges = set()
        self.node_type = node_type
        self.node_parents = defaultdict(set)
        self.node_children = defaultdict(set)

    def vertices(self):
        return self.nodes

    def add_edge(self, edge):
        self.nodes |= {edge.parent, edge.child}
        self.node_parents[edge.child].add(edge.parent)
        self.node_children[edge.parent].add(edge.child)
        self.edges.add(edge)

    def add_edges(self, edges):
        for edge in edges:
            self.add_edge(edge)

    def get_children(self, node):
        # FIND THE REVISION
        return self.node_children[node]

    def get_decendents(self, node):
        output = set()
        cs = self.get_children(node)
        output |= cs
        for c in cs:
            output |= self.get_decendents(c)
        return output

    def get_parents(self, node):
        return self.node_parents[node]

    def get_edges(self, node):
        return [
            (node, child)
            for child in self.get_children(node)
        ] + [
            (parent, node)
            for parent in self.get_parents(node)
        ]

    def get_family(self, node):
        """
        RETURN ALL ADJACENT NODES
        """
        return self.get_children(node) | self.get_parents(node)

