# Copyright 2014-present, Apstra, Inc. All rights reserved.
#
# This source code is licensed under End User License Agreement found in the
# LICENSE file at http://www.apstra.com/community/eula

from lollipop import types as lt

__all__ = ['IpPool']


IpPool = lt.Object({
    'display_name': lt.String(),
    'subnets': lt.List(lt.Dict({
        'network': lt.String(),
        'status': lt.DumpOnly(lt.String())
    }))
})
