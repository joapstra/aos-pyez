# Copyright 2014-present, Apstra, Inc. All rights reserved.
#
# This source code is licensed under End User License Agreement found in the
# LICENSE file at http://www.apstra.com/community/eula

import retrying

from apstra.aosom.exc import SessionRqstError
from apstra.aosom.collection import Collection, CollectionItem

__all__ = ['DeviceManager']


class DeviceItem(CollectionItem):
    @property
    def state(self):
        """
        Returns
        -------
        str
            current AOS management state value, e.g. "IS-ACTIVE", meaning "In service, Active".
        """
        return self.value['status']['state']

    @property
    def is_approved(self):
        """
        Returns
        -------
        True if this device is approved
        False otherwise
        """
        return bool(self.id in self.collection.approved.ids)

    @property
    def user_config(self):
        """
        As a **getter** returns the current `user_config` dictionary of values.
        As a **setter** provides the ability to set the `user_config` values.

        Returns
        -------
        dict
            The 'user_config' dictionary of values

        Raises
        ------
        SessionRqstError
            when error occurs in setting the `user_config` value
        """
        self.read()
        return self.value.get('user_config')

    @user_config.setter
    def user_config(self, value):
        got = self.api.requests.put(
            self.url,
            json=dict(user_config=value))

        if not got.ok:
            raise SessionRqstError(
                message='unable to set user_config',
                resp=got)

    def approve(self, location=None):
        """
        Approves this device for use by the AOS system.  If the device is already approved, then this
        method will return False.

        Parameters
        ----------
        location : str
            optional User value that can be used to identify where this device is located in the network.

        Returns
        -------
        True if the device is approved
        False if the device does not need to be approved

        Raises
        ------
        SessionRqstError
            An error has occurred attempting to make the approve request with the AOS Server API
        """
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
        got = self.api.requests.get(self.url)
        if not got.ok:
            raise SessionRqstError(got)

        return got.json()

    def get_devices(self):
        return self.get()['devices']

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
            got = self.api.requests.put(
                self.url, json=dict(display_name='Default Pool',
                                    devices=has_devices))

            if not got.ok:
                raise SessionRqstError(
                    message='unable to update approved list: %s' % got.text,
                    resp=got)

        put_updated()


class DeviceManager(Collection):
    URI = 'systems'
    LABEL = 'device_key'
    Item = DeviceItem

    def __init__(self, owner):
        super(DeviceManager, self).__init__(owner)
        self.approved = Approved(owner.api)
