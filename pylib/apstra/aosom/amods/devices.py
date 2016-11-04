# Copyright 2014-present, Apstra, Inc. All rights reserved.
#
# This source code is licensed under End User License Agreement found in the
# LICENSE file at http://www.apstra.com/community/eula

import requests

from apstra.aosom.exc import SessionRqstError
from apstra.aosom.collection import Collection, CollectionItem

__all__ = ['DeviceManager']


class DeviceItem(CollectionItem):
    @property
    def user_config(self):
        return None

    @user_config.setter
    def user_config(self, value):
        got = requests.put(
            self.url, headers=self.api.headers,
            json=dict(user_config=value))

        if not got.ok:
            raise SessionRqstError(resp=got)


class Approved(object):
    def __init__(self, api):
        self.api = api
        self.url = '%s/resources/device-pools/default_pool' % self.api.url

    def get(self):
        got = requests.get(self.url, headers=self.api.headers)
        if not got.ok:
            raise SessionRqstError(got)

        return got.json()['devices']

    def update(self, device_keys):
        has_devices = self.get()

        has_ids = set([dev['id'] for dev in has_devices])
        should_ids = has_ids | set(device_keys)
        diff_ids = has_ids ^ should_ids

        if not diff_ids:
            return   # nothing to add

        # keep what's already in the pool, since this is a PUT

        for new_id in diff_ids:
            has_devices.append(dict(id=new_id))

        got = requests.put(self.url, headers=self.api.headers,
                           json=dict(display_name='Default Pool',
                                     devices=has_devices))
        if not got.ok:
            raise SessionRqstError(got)


class DeviceManager(Collection):
    RESOURCE_URI = 'systems'
    DISPLAY_NAME = 'device_key'
    Item = DeviceItem

    def __init__(self, api):
        super(DeviceManager, self).__init__(api)
        self.approved = Approved(api)
