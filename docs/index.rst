.. aos-pyez doc master file

********
AOS PyEZ
********

Release version |version|. (:ref:`Changelog <changelog>`)

The aos-pyez library is a Pythonic interface to the Apstra AOS-Server API.  The complete AOS-Server API documentation
is available directly from the AOS-Server User Interface, as shown:

    .. image:: static/aos-api-reference.png

The aos-pyez library is designed to work with AOS version 1.1.  At present, the aos-pyez library exposes some, but
not all functionality provided by the AOS-Server.  The aos-pyez library, does however, provide you the means to
access any aspect of the API, as described in the :ref:`session_requests` guide.  With the current aos-pyez, you
will be able to use the Design, Resource, and Blueprint Build features.  Additional features will be continuously
added.  If you'd like to get involved, please post your requests/bugs on the github repo.

Guide
=====

.. toctree::
    :maxdepth: 1

    install
    quickstart
    session
    devices
    collections
    resources
    design
    blueprints


.. _api_reference:

API Reference
=============
.. toctree::
    :maxdepth: 1

    apidoc/session
    apidoc/devices
    apidoc/collections
    apidoc/blueprints


Other information
=================

.. toctree::
    :maxdepth: 1

    changelog
    license


Indices and Tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
