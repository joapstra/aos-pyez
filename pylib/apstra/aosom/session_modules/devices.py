# Copyright 2014-present, Apstra, Inc. All rights reserved.
#
# This source code is licensed under End User License Agreement found in the
# LICENSE file at http://www.apstra.com/community/eula

import requests
import retrying

from apstra.aosom.exc import SessionRqstError
from apstra.aosom.collection import Collection, CollectionItem

__all__ = ['DeviceManager']


class DeviceItem(CollectionItem):

    @property
    def state(self):
        return self.value['status']['state']

    @property
    def is_approved(self):
        return bool(self.id in self.collection.approved.ids)

    @property
    def user_config(self):
        self.read()
        return self.value.get('user_config')

    @user_config.setter
    def user_config(self, value):
        got = requests.put(
            self.url, headers=self.api.headers,
            json=dict(user_config=value))

        if not got.ok:
            raise SessionRqstError(
                message='unable to set user_config',
                resp=got)

    def approve(self, location=None):

        if self.state != 'OOS-QUARANTINED':
            return False

        self.user_config = dict(
            admin_state='normal',
            aos_hcl_model=self.value['facts']['aos_hcl_model'],
            location=location or '')

        self.collection.approved.update([self.id])

        return True


class Approved(object):
    def __init__(self, api):
        self.api = api
        self.url = '%s/resources/device-pools/default_pool' % self.api.url

    @property
    def ids(self):
        return [item['id'] for item in self.get_devices()]

    def get(self):
        got = requests.get(self.url, headers=self.api.headers)
        if not got.ok:
            raise SessionRqstError(got)

        return got.json()

    def get_devices(self):
        got = requests.get(self.url, headers=self.api.headers)
        if not got.ok:
            raise SessionRqstError(got)

        return got.json()['devices']

    def update(self, device_keys):
        has_devices = self.get_devices()

        has_ids = set([dev['id'] for dev in has_devices])
        should_ids = has_ids | set(device_keys)
        diff_ids = has_ids ^ should_ids

        if not diff_ids:
            return   # nothing to add

        # need to append to what's already in the pool,
        # since this is a PUT action

        for new_id in diff_ids:
            has_devices.append(dict(id=new_id))

        timeout = 3000

        @retrying.retry(wait_fixed=1000, stop_max_delay=timeout)
        def put_updated():
            got = requests.put(self.url, headers=self.api.headers,
                               json=dict(display_name='Default Pool',
                                         devices=has_devices))

            if not got.ok:
                raise SessionRqstError(
                    message='unable to update approved list: %s' % got.text,
                    resp=got)

        put_updated()


class DeviceManager(Collection):
    RESOURCE_URI = 'systems'
    DISPLAY_NAME = 'device_key'
    Item = DeviceItem

    def __init__(self, owner):
        super(DeviceManager, self).__init__(owner)
        self.approved = Approved(owner.api)
