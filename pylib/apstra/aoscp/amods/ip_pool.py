from apstra.aoscp.amods.resource import ResourcePool

__all__ = ['IpPool']


class IpPool(ResourcePool):
    RESOURCE_URI = 'resources/ip-pools'
