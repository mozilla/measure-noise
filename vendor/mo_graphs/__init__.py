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

from collections import namedtuple

Edge = namedtuple("Edge", ["parent", "child"])


class BaseGraph(object):

    __slots__ = []

    def vertices(self):
        raise NotImplementedError()

    def add_edge(self, edge):
        raise NotImplementedError()

    def add_edges(self, edges):
        raise NotImplementedError()

    def get_children(self, node):
        raise NotImplementedError()

    def get_parents(self, node):
        raise NotImplementedError()

    def get_edges(self, node):
        return {
                   (node, child)
                   for child in self.get_children(node)
               } | {
                   (parent, node)
                   for parent in self.get_parents(node)
               }

    def get_family(self, node):
        return self.get_children(node) | self.get_parents(node)

