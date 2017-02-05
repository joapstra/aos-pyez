# Copyright 2014-present, Apstra, Inc. All rights reserved.
#
# This source code is licensed under End User License Agreement found in the
# LICENSE file at http://www.apstra.com/community/eula

import retrying

from apstra.aosom.collection import Collection, CollectionItem
from apstra.aosom.exc import SessionRqstError
from apstra.aosom.dynmodldr import DynamicModuleOwner

__all__ = [
    'Blueprints'
]


class BlueprintCollectionItem(CollectionItem, DynamicModuleOwner):
    """
    This class provides :class:`Blueprint` item instance management.
    """
    DYNMODULEDIR = '.blueprint_modules'

    def __init__(self, *vargs, **kwargs):
        super(BlueprintCollectionItem, self).__init__(*vargs, **kwargs)
#        self.params = BlueprintItemParamsCollection(self)

    # =========================================================================
    #
    #                             PROPERTIES
    #
    # =========================================================================

    # -------------------------------------------------------------------------
    # PROPERTY: contents
    # -------------------------------------------------------------------------

    @property
    def contents(self):
        """
        Property accessor to blueprint contents.

        :getter: returns the current blueprint data :class:`dict`
        :deletter: removes the blueprint from AOS-server

        Raises:
            SessionRqstError: upon issue with HTTP requests

        """
        got = self.api.requests.get(self.url)
        if not got.ok:
            raise SessionRqstError(
                message='unable to get blueprint contents',
                resp=got)

        return got.json()

    @contents.deleter
    def contents(self):
        """
        When the `del` operation is applied to this property, then this
        action will attempt to delete the blueprint from AOS-server.  For
        example:

        # >>> del my_blueprint.contents

        Another way to do the same as:

        # >>> my_blueprint.delete()
        """
        self.delete()

    # -------------------------------------------------------------------------
    # PROPERTY: build_errors
    # -------------------------------------------------------------------------

    @property
    def build_errors(self):
        """
        Property accessor to any existing blueprint build errors.

        Raises:
            SessionReqstError: upon error with obtaining the blueprint contents

        Returns:
            - either the `dict` of existing errors within the blueprint contents
            - `None` if no errors
        """
        return self.contents.get('errors')

    # =========================================================================
    #
    #                             PUBLIC METHODS
    #
    # =========================================================================

    def create(self, design_template_id, reference_arch, blocking=True):
        data = dict(
            display_name=self.name,
            template_id=design_template_id,
            reference_architecture=reference_arch)

        super(BlueprintCollectionItem, self).create(data)

        if not blocking:
            return True

        @retrying.retry(wait_fixed=1000, stop_max_delay=10000)
        def wait_for_blueprint():
            assert self.id

        # noinspection PyBroadException
        try:
            wait_for_blueprint()
        except:
            return False

        return True

    def await_build_ready(self, timeout=5000):
        """
        Wait a specific amount of `timeout` for the blueprint build status
        to return no errors.  The waiting polling interval is fixed at 1sec.

        Args:
            timeout (int): timeout to wait in miliseconds

        Returns:
            True: when the blueprint contains to build errors
            False: when the blueprint contains build errors, even after waiting `timeout`

        """
        @retrying.retry(wait_fixed=1000, stop_max_delay=timeout)
        def wait_for_no_errors():
            assert not self.build_errors

        # noinspection PyBroadException
        try:
            wait_for_no_errors()
        except:
            return False

        return True


class Blueprints(Collection):
    """
    Blueprints collection class provides management of AOS blueprint instances.
    """
    URI = 'blueprints'
    Item = BlueprintCollectionItem
