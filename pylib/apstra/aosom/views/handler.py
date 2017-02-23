# Copyright 2014-present, Apstra, Inc. All rights reserved.
#
# This source code is licensed under End User License Agreement found in the
# LICENSE file at http://www.apstra.com/community/eula


import yaml

__all__ = [
    'FileView',
    'ApiView',
    'ViewBroker'
]


class FileView(object):
    Schema = None

    def __init__(self, broker):
        self._broker = broker
        self.import_item = None
        self.export_item = dict()

    def clear(self):
        self.export_item.clear()
        self.import_item = None

    def __getitem__(self, item):
        return self.export_item[item]


class ApiView(object):
    Schema = None

    def __init__(self, broker):
        self._broker = broker
        self.import_item = dict()
        self.export_item = None

    def clear(self):
        self.import_item.clear()
        self.export_item = None

    def __getitem__(self, item):
        return self.export_item.value[item]


class _ViewBroker(object):

    def __init__(self):
        self.api_view = self.Api(self)
        self.file_view = self.File(self)

    def clear(self):
        self.file_view.clear()
        self.api_view.clear()

    def from_file(self, filepath):
        # import the data and validate it
        data = yaml.load(open(filepath))
        self.file_view.Schema.validate(data)

        # setup the import/export view data
        self.file_view.export_item.clear()
        self.file_view.export_item.update(data)
        self.api_view.import_item = self.file_view.export_item

    def from_api(self, api_item):
        # we are not currently validating the data
        # received from the AOS server; presumes that the Schema written
        # by aos-pyez is correct.
        self.api_view.export_item = api_item
        self.file_view.import_item = self.api_view.export_item.value

    def to_file(self):
        return self.file_view.Schema.dump(self.file_view)

    def to_api(self):
        return self.api_view.Schema.dump(self.api_view)


class ViewBroker(type):
    def __new__(mcs, name, file_view, api_view):
        return type.__new__(type, name, (_ViewBroker,), {
            'Api': api_view,
            'File': file_view
        })
