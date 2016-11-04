# Copyright 2014-present, Apstra, Inc. All rights reserved.
#
# This source code is licensed under End User License Agreement found in the
# LICENSE file at http://www.apstra.com/community/eula

from apstra.aosom.collection import Collection

__all__ = ['DeviceManager']


class DeviceManager(Collection):
    RESOURCE_URI = 'systems'
    DISPLAY_NAME = 'device_key'
