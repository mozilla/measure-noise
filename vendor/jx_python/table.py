# encoding: utf-8
#
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Contact: Kyle Lahnakoski (kyle@lahnakoski.com)
#
from __future__ import absolute_import, division, unicode_literals

import jx_base
from mo_dots import Data


class Table(jx_base.Table):

    __slots__ = ['header', 'data', 'meta']


    def __init__(self, header=None, data=None):
        self.header = header

        self.data = data
        self.meta = Data()

    def groupby(self, keys):
        pass


