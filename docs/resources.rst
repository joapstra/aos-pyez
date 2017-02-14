.. _resources:

=========
Resources
=========

This version of the aos-pyez supports all AOS 1.1 managed Resources.  Resources are collections of data items
that you use with AOS Blueprints for the purpose assigning values for network services.

    * IP Pools
    * ASN Pools
    * External Routers

IP Pools
--------
When you need to assign IP addresses to an AOS Blueprint you can use IP Pools to instruct AOS to allocate and assign
addresses from these pool rather than explicitly assigning specific individual values.

You can use AOS IP Pools in conjunction with your existing IP Address Management (IPAM) system.
An IPAM system allows you to allocate blocks of IP address ranges.  If you use an IPAM system you know that you
are still responsible for manually assigning specific IP addresses from those ranges when you create your network
services.  When you use AOS, you can create an AOS IP Pool with the IPAM range information, and then assign the IP
Pool to an AOS Blueprint.  By following this approach you let AOS do the specific IP allocation task.

You can access the IP Pools resources via the aos-pyez library by using the :attr:`IpPools` property of the
Session: ::

    >>> aos.IpPools

The IpPools is managed as a Collection/Items, as described in the :ref:`collections` guide documents.  In
addition to the Items properties documented there, the an IpPool item also supports:

    * `in_use` - `True` if the pool is used by an AOS Blueprint, `False` otherwise.

ASN Pools
---------
When you need to assign Autonomous System Numbers (ASNs) to an AOS Blueprint you can use ASN Pools to instruct
AOS to allocate and assign values from these pool rather than explicitly assigning specific individual values.

You can use AOS ASN Pools in conjunction with your existing IP Address Managementq (IPAM) system, presuming it also
supports ASN block management.  Even though an IPAM system allows you to allocate ASN blocks, you are still
responsible for manually assigning specific values to devices when you create your network
services.  When you use AOS, you can create an AOS ASN Pool with the block range information from your IPAM.  You
then assign that ASN Pool into your Blueprint. By following this approach you let AOS do the specific ASN value
assignment task.

You can access the ASN Pools resources via the aos-pyez library by using the :attr:`AsnPools` property of the
Session: ::

    >>> aos.AsnPools

The AsnPools is managed as a Collection/Items, as described in the :ref:`collections` guide documents.  In
addition to the Items properties documented there, the an IpPool item also supports:

    * `in_use` - `True` if the pool is used by an AOS Blueprint, `False` otherwise.

External Routers
----------------
AOS currently does not manage the routers, but AOS Blueprint services need information about those routers.  For
example, when using AOS to manage a L3 Clos , the Blueprint needs external router information to configure the
attached switches and have the necessary information to gather the appropriate telemetry associated with the
BGP session(s).

You can access the External Routers resource via the aos-pyez library using the :attr:`ExternalRouters` property
of the Session: ::

    >>> aos.ExternalRouters

The ExternalRouters is managed as a Collection/Items, as described in the :ref:`collections` guide documents.
