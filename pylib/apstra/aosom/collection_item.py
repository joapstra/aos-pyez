# Copyright 2014-present, Apstra, Inc. All rights reserved.
#
# This source code is licensed under End User License Agreement found in the
# LICENSE file at http://www.apstra.com/community/eula

from os import path
from copy import copy
import json


from apstra.aosom.exc import SessionRqstError, NoExistsError, DuplicateError


# #############################################################################
# #############################################################################
#
#                                Collection Item
#
# #############################################################################
# #############################################################################

class CollectionItem(object):
    """
    An item within a given :class:`Collection`.  The following public attributes
    are available:

        * :attr:`name` - the user provided item name
        * :attr:`api` - the instance to the :mod:`Session.Api` instance.

    """
    def __init__(self, collection, name, datum):
        self.name = name
        self.collection = collection
        self.api = collection.api
        self.datum = datum

    # =========================================================================
    #
    #                             PROPERTIES
    #
    # =========================================================================

    # -------------------------------------------------------------------------
    # PROPERTY: id
    # -------------------------------------------------------------------------

    @property
    def id(self):
        """
        Property access for the item AOS unique ID value.

        Returns:
            - id string value if the item exists
            - `None` if the item does not exist.
        """
        return self.datum.get(self.collection.UNIQUE_ID) if self.name in self.collection else None

    # -------------------------------------------------------------------------
    # PROPERTY: url
    # -------------------------------------------------------------------------

    @property
    def url(self):
        """
        Property accessor for item URL.

        :getter: returns the URL string for this specific item
        """

        if not self.exists:
            raise NoExistsError("name=%s, collection=%s" %
                                (self.name, self.collection.url))

        return "%s/%s" % (self.collection.url, self.id)

    # -------------------------------------------------------------------------
    # PROPERTY: exists
    # -------------------------------------------------------------------------

    @property
    def exists(self):
        """
        Property accessor to determine if item exists on the AOS-server.

        Returns:
            - True if the item exists
            - False if the item does not exist
        """
        return bool(self.datum and self.id)

    # -------------------------------------------------------------------------
    # PROPERTY: value
    # -------------------------------------------------------------------------

    @property
    def value(self):
        """
        Property accessor for item value.

        :getter: returns the item data dictionary
        :deletter: deletes the item from the AOS-server

        Raises:
            SessionRqstError: upon any HTTP requests issue.
        """
        return self.datum

    @value.deleter
    def value(self):
        """
        Used to delete the item from the AOS-server.  For example:

        #    >>> del aos.IpPools['Servers-IpAddrs'].value

        Another way to do:

        #    >>> aos.IpPools['Servers-IpAddrs'].delete()
        """
        self.delete()

    # =========================================================================
    #
    #                             PUBLIC METHODS
    #
    # =========================================================================

    def write(self, value=None):
        """
        Used to write the item value back to the AOS-server.

        Raises:
            SessionRqstError: upon HTTP request issue
        """
        if not self.exists:
            return self.create(value=value)

        got = self.api.requests.put(
            self.url, json=value or self.datum)

        if not got.ok:
            raise SessionRqstError(
                message='unable to update: %s' % got.reason,
                resp=got)

        self.read()

    def read(self):
        """
        Retrieves the item value from the AOS-server.

        Raises:
            SessionRqstError: upon REST call error

        Returns: a copy of the item value, usually a :class:`dict`.
        """
        got = self.api.requests.get(self.url)
        if not got.ok:
            raise SessionRqstError(
                resp=got,
                message='unable to get item name: %s' % self.name)

        self.datum = copy(got.json())
        return self.datum

    def create(self, value=None, replace=False):
        """
        Creates a new item using the `value` provided.

        Args:
            value (dict):
                item value dictionary.
            replace (bool):
                determine if this method should replace and
                existing item with the same name.

        Raises:
            - SessionError: upon any HTTP request issue.
            - DuplicateError: attempting to create an existing item

        Returns:
            the instance to the new collection item
        """

        # check to see if this item currently exists, using the name/URI
        # when this instances was instantiated from the collection; *not*
        # from the `value` data.

        def throw_duplicate(name):
            raise DuplicateError("'{}' already exists in collection: {}.".format(
                name, self.collection.URI))

        if self.exists:
            if not replace:
                throw_duplicate(self.name)

            self.delete()

        # the caller can either pass the new data to this method, or they
        # could have already assigned it into the :prop:`datum`.  This
        # latter approach should be discouraged.

        if value is not None:
            self.datum = copy(value)

        # now check to see if the new value/name exists.  if the datum
        # does not include the lable value, we need to auto-set it from
        # the instance name value.

        new_name = self.datum.get(self.collection.LABEL)
        if not new_name:
            self.datum[self.collection.LABEL] = self.name

        if new_name in self.collection:
            throw_duplicate(new_name)

        # at this point we should be good to execute the POST and
        # create the new item in the server

        got = self.api.requests.post(self.collection.url, json=self.datum)

        if not got.ok:
            raise SessionRqstError(
                message='unable to create: %s' % got.reason,
                resp=got)

        body = got.json()
        self.datum[self.collection.UNIQUE_ID] = body[self.collection.UNIQUE_ID]

        # now add this item to the parent collection so it can be used by other
        # invocations

        self.collection += self
        return self

    def delete(self):
        """
        Deletes the item from the AOS server

        Raises:
            SessionRqstError - when API error
            NoExistsError - when item does not actually exist
        """
        got = self.api.requests.delete(self.url)
        if not got.ok:
            raise SessionRqstError(
                message='unable to delete item: %s' % got.reason,
                resp=got)

        self.collection -= self

    def jsonfile_save(self, dirpath=None, filename=None, indent=3):
        """
        Saves the contents of the item to a JSON file.

        Args:
            dirpath:
                The path to the directory to store the file.  If none provided
                then the file will be stored in the current working directory

            filename:
                The name of the file, stored within the `dirpath`.  If
                not provided, then the filename will be the item name.

            indent:
                The indent spacing in the JSON file.

        Raises:
            IOError: for any I/O related error
        """
        ofpath = path.join(dirpath or '.', filename or self.name) + '.json'
        json.dump(self.value, open(ofpath, 'w+'), indent=indent)

    def jsonfile_load(self, filepath):
        """
        Loads the contents of the JSON file, `filepath`, as the item value.

        Args:
            filepath (str): complete path to JSON file

        Raises:
            IOError: for any I/O related error
        """
        self.datum = json.load(open(filepath))

    def __str__(self):
        return json.dumps({
            'name': self.name,
            'id': self.id,
            'value': self.value
        }, indent=3)

    __repr__ = __str__
