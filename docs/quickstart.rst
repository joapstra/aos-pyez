.. _quickstart:

Quickstart
==========

This section will guide you through the process of creating a management session with the AOS-Server
and performing a few basic interactions.

Let's start with creating a session: ::

    >>> from apstra.aosom.session import Session
    >>> aos = Session('192.168.59.250', user='admin', passwd='admin)
    >>> aos.login()

.. currentmodule:: apstra.aosom.session

The first parameter is the AOS-server IP address or hostname.  The remaining key/value arguments are documented in
the API reference section.  The `user` and `passwd` both default to *admin* if not provided.

The `login()` method will make the request to authenticate a login and provide back a session token.  If for any
reason the login attempt fails, an exception will be raised.  See :meth:`Session.login` for
details.  You can verify the login session information by examinging the :attr:`Session.session`.

The value of the `aos.session` value looks like: ::

    >>> aos.session
    {'port': 8888,
     'server': 'aos-server',
     'token': u'eyJhbGci<~snip~>MTUiMP0skQ'}

The :class:`Session` then allows you to access other API features.  These features are generally a collection of
similar items.  These features are defined within the :data:`Session.ModuleCatalog`. ::

    ['Blueprints', 'IpPools', 'DesignTemplates', 'ExternalRouters',
     'AsnPools', 'RackTypes', 'LogicalDevices', 'Devices', 'LogicalDeviceMaps']

*   The `Devices` feature allows you to access the Device-Manager features; i.e. access
    inventory management and information about the devices being managed by AOS.

*   The `AsnPools`, `IpPools`, and `ExternalRouters` are resources that you provide to
    AOS so that they can be assigned and used to services that you define within AOS - aka "Blueprints".

*   The `DesignTemplates`, `LogicalDevices`, `LogicalDevicesMaps`, and `RackTypes` are all design
    elements.  You use these design elements to define your Blueprint services.

*   Finally the `Blueprints` are the network services that you are managing with AOS.

To access any of these, simply use the name as an attribute of the aos Session.  By way of example, here is how
you can access the devices under management, and display the Management-IpAddr, Serial-Number, Model as it is known
to AOS, and the OS/version information: ::

    >>> for dev in aos.Devices:
    ...    dev_facts = dev.value['facts']
    ...    print dev_facts['mgmt_ipaddr'], dev_facts['serial_number'], dev_facts['aos_hcl_model'], dev_facts['os_version']
    192.168.60.16 08002737C2C1 Cumulus_VX 3.1.1
    192.168.60.19 080027A71AE6 Arista_vEOS 4.16.6M
    192.168.60.18 0800277025C8 Cumulus_VX 3.1.1
    192.168.60.17 080027AC6320 Cumulus_VX 3.1.1
    192.168.60.15 08002763CBDC Cumulus_VX 3.1.1

