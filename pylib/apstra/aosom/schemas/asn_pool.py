# Copyright 2014-present, Apstra, Inc. All rights reserved.
#
# This source code is licensed under End User License Agreement found in the
# LICENSE file at http://www.apstra.com/community/eula


from lollipop import types as lt
from lollipop import validators as lv

__all__ = ['AsnPool']


_valid_asn_value = lv.Range(
    min=1, max=2**16 - 1,
    error="Invalid ASN value {data}, must be [{min} .. {max}]")


def _valid_asn_range(asn_r):
    if not asn_r['first'] <= asn_r['last']:
        raise lv.ValidationError(
            "first={} must be <= last={}".format(
                asn_r['first'], asn_r['last']))


AsnPool = lt.Object({
    'display_name': lt.String(),
    'ranges': lt.List(lt.Dict({
        'first': lt.Integer(validate=_valid_asn_value),
        'last': lt.Integer(validate=_valid_asn_value)
    }, validate=_valid_asn_range))
})
