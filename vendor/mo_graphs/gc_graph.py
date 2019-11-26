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

import gc
from collections import defaultdict

from mo_graphs import BaseGraph, Edge


class GCGraph(BaseGraph):
    """
    SHOW THE GC GRAPH VERTICIES AS INTS
    """

    def __init__(self):
        gc.disable()  # OBJECTS CONTINUE TO BLINK IN, AND OUT, OF EXISTENCE
        gc.collect()
        self.id2obj = {id(o): o for o in gc.get_objects()}
        self.parents = defaultdict(set)
        self.children = defaultdict(set)
        self.edges = set()
        for ip, p in self.id2obj.items():
            for c in gc.get_referents(p):
                ic = id(c)
                self.edges.add(Edge(ip, ic))
                self.parents[ic].add(ip)
                self.children[ip].add(ic)
        gc.enable()

    @property
    def vertices(self):
        return set(self.id2obj.keys())

    @property
    def nodes(self):
        return set(self.id2obj.keys())

    def get_children(self, node):
        return self.children[node]

    def get_parents(self, node):
        return self.parents[node]

    def get_edges(self, node):
        return set(
            Edge(node, child)
            for child in self.children[node]
        ) | set(
            Edge(parent, node)
            for parent in self.parents[node]
        )

    def get_family(self, node):
        """
        RETURN ALL ADJACENT NODES
        """
        return self.get_children(node) | self.get_parents(node)

