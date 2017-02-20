# Copyright 2014-present, Apstra, Inc. All rights reserved.
#
# This source code is licensed under End User License Agreement found in the
# LICENSE file at http://www.apstra.com/community/eula


from copy import copy
import yaml
import json
import contextlib

__all__ = ['ViewHandler']


class ViewHandlerType(type):
    """
    This type is used to metaclass the ViewHandler.  The general purpose
    is so that when someone subclasses ViewHandler, the schema will be
    auto-constructed using the subclass class.
    """
    def __new__(mcs, name, bases, cls_dict):
        new_cls = type.__new__(mcs, name, bases, cls_dict)

        view_schema = cls_dict['View']
        if view_schema:
            view_schema._constructor = lambda **kw: new_cls(**kw)

        return new_cls


class ViewHandler(object):
    __metaclass__ = ViewHandlerType

    Api = None
    Module = None
    View = None

    def __init__(self, **kwargs):
        self.data = copy(kwargs)

    def to_api(self):
        return self.Api.dump(self)

    @classmethod
    def loads(cls, stream):
        return cls.View.load(yaml.load(stream))

    @classmethod
    def load_api(cls, api_item):
        return cls(**cls.View.dump(api_item.value))

    @classmethod
    def load_file(cls, filepath):
        return cls.loads(open(filepath))

    @contextlib.contextmanager
    def api_item(self, session):
        module = getattr(session, self.Module.__name__)
        yield module[getattr(self, self.Module.LABEL)]

    def __str__(self):
        return json.dumps(self.data, indent=2)

    __repr__ = __str__
