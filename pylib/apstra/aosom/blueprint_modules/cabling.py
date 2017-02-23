# Copyright 2014-present, Apstra, Inc. All rights reserved.
#
# This source code is licensed under End User License Agreement found in the
# LICENSE file at http://www.apstra.com/community/eula

import jmespath
import csv


class Cabling(object):

    class Dialect(csv.excel):
        skipinitialspace = True

    def __init__(self, blueprint):
        self.api = blueprint.api
        self.blueprint = blueprint

    @property
    def links(self):
        # note: this will always fetch the data from the API
        return self.blueprint.contents['system']['links']

    @property
    def names(self):
        return [l['display_name'] for l in self.links]

    @property
    def roles(self):
        return set(jmespath.search('[].role', self.links))

    def find_by_role(self, role, links=None):
        return jmespath.search(
            "[?role=='%s']" % role,
            links or self.links)

    def find_by_node(self, node, links=None):
        return jmespath.search(
            "[?endpoints[?id=='%s']]" % node,
            links or self.links)

    def find_by_nodepair(self, node_1, node_2, links=None):
        return self.find_by_node(
            node_1, links=self.find_by_node(node_2, links))

    @staticmethod
    def get_peer_endpoints(node, links):
        endpoints = jmespath.search(
            "[].endpoints[?id != '%s'][]" % node,
            links)

        peer_nodes = [e['id'] for e in endpoints]

        return peer_nodes, endpoints

    def get_flat_list(self, links=None):
        flat = []
        for link in (links or self.links):
            item = [link['display_name']]

            left, _, right = item[0].partition('<->')
            right, _, _ = right.partition('[')

            item.append(left)
            item.append(right)

            for end in link['endpoints']:
                idx = item.index(end['id'])
                item.insert(idx + 1, end['interface'])

            flat.append(item)

        return flat

    def export_csv(self, fileobj, flat_list=None, links=None):
        if not isinstance(fileobj, file):
            raise ValueError('fileobj is not a file type')

        if links:
            flat_list = self.get_flat_list(links)

        wr = csv.writer(fileobj, csv.excel, self.Dialect)
        wr.writerows(flat_list or self.get_flat_list(links))

    @classmethod
    def import_csv(cls, fileobj):
        if not isinstance(fileobj, file):
            raise ValueError('fileobj is not a file type')

        return list(csv.reader(fileobj, cls.Dialect))
