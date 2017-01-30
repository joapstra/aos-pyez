# Copyright 2014-present, Apstra, Inc. All rights reserved.
#
# This source code is licensed under End User License Agreement found in the
# LICENSE file at http://www.apstra.com/community/eula


from apstra.aosom.collection import Collection
from apstra.aosom.graphql.alerts import AlertsQuery

__all__ = ['Alerts']


class Alerts(Collection):
    DISPLAY_NAME = 'id'                # no human readable unique name
    URI = 'alerts'

    def __init__(self, owner):
        super(Alerts, self).__init__(owner=owner)
        self.query = AlertsQuery(owner=self)
