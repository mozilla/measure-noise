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

from mo_graphs import BaseGraph


class NaiveGraph(BaseGraph):
    """
    SIMPLE IMPLEMENTATION OF A GRAPH
    """

    def __init__(self, node_type=None):
        self.nodes = set()
        self.edges = set()
        self.node_type = node_type

    def vertices(self):
        return self.nodes

    def add_edge(self, edge):
        self.nodes |= {edge.parent, edge.child}
        self.edges.add(edge)

    def add_edges(self, edges):
        for edge in edges:
            self.add_edge(edge)

    def remove_children(self, node):
        self.edges = set(e for e in self.edges if e.parent != node)

    def get_children(self, node):
        # FIND THE REVISION
        return set(c for p, c in self.edges if p==node)

    def get_parents(self, node):
        return set(p for p, c in self.edges if c==node)

    def get_edges(self, node):
        return set(e for e in self.edges if e.parent == node or e.child == node)

    def get_family(self, node):
        """
        RETURN ALL ADJACENT NODES
        """
        return set(p if c == node else c for p, c in self.get_edges(node))

