"""This module has base class for libcloudlet
"""

__docformat__ = 'reStructuredText'



class CloudletException(Exception):
    pass


class HandoffException(CloudletException):
    pass


class ProvisioningException(CloudletException):
    pass


class DiscoveryService(object):
    """Abstrace class defining minimal methods for cloudlet discovery service.
    """

    def __init__(self, **kwargs):
        """
        """
        pass

    def discover(self, cloud_URL=None, client=None, application=None, **kwargs):
        """Discover a list of cloudlets by sending query to a cloud directory 
        service.

        :param cloud_URL: IP address or domain name of a cloud directory server
        :param client: data structure saving client information
        :param application: data structure saving application information
        :type cloud_URL: string
        :type client: :class:`MobileClient`
        :type application: :class:`Application`
        :return: list of :class:`Cloudlet` object
        :rtype: list

        """
        pass


class MobileClient(object):
    """Data structure for information of the mobile client

    :param GPS_latitude: GPS coordinate latitude of the mobile device
    :param GPS_longitude: GPS longitude of a mobile device using Decimal Degree
    :param ip_v4: ipv4 of a mobile device
    :param network_type: Type of the network of a mobile client. Either 'cellular' or 'WiFi'
    :type GPS_latitude: Decimal degree
    :type GPS_longitude: Decimal degree
    :type ip_v4: string
    :type network_type: string
    """

    def __init__(self, GPS_latitude=None, GPS_longitude=None, ip_v4=None, network_type=None, **kwargs):
        pass


class Application(object):
    """Data structure for the mobile application

    :param UUID: UUID string of the mobile application
    :param min_RTT_ms: minimum required latency (RTT) for offloading
    :param min_CPU_clock_MHz: minimal required CPU clock speed for offloading
    :param cache_URL_list: required cached URL list
    :param cache_file_list: required cached file list
    :type UUID: str
    :type min_RTT_ms: int
    :type min_CPU_clock_MHz: int
    :type cache_URL_list: list of str
    :type cache_file_list: list of str

    """

    def __init__(self, UUID, min_RTT_ms=None, min_CPU_clock_MHz=None, cache_URL_list=None, cache_file_list=None, **kwargs):
        pass


class Cloudlet(object):
    """Represent a single cloudlet

    :param URL: IP address or domain name of the cloudlet
    :param access_account: access account of the cloudlet
    :param access_key: access key of the cloudlet
    :type URL: str
    :type access_account: str
    :type access_key: str
    """

    def __init__(URL, access_account, access_key=None, **kwargs):
        pass

    def associate(self):
        """ Associate with a Cloudlet
        return: :class:`VM`
        """
        pass

    def disassociate(self):
        """
        Disassociate with a Cloudlet,
        and terminate all VMs that a user was using.

        return: None
        """
        pass

    def provision(self, overlay_URL, overlay_account=None, overlay_key=None, start_VM=False, assign_IP=True, **kwargs):
        """Provision a VM overlay to Cloudlet

        :param overlay_URL: Downloadable URL of the VM overlay
        :param overlay_account: access account to the URL of VM overlay
        :param overlay_key: access key to the URL of VM overlay
        :param start_VM: start the VM after the provisioning
        :param assign_IP: True to assign an accessible IP address to the VM
        :type overlay_URL: str
        :type overlay_account: str
        :type overlay_key: str
        :type start_VM: bool
        :type assign_IP: bool
        :return: a VM object
        :rtype: :class:`VM`

        :raises: :class:`ProvisioningException` if provisioning fails.
        """
        pass


class VM(object):
    """Represent a virtual mahince instance

    :param UUID: an UUID of the virtual machine instance assigned by cloudlet
    :type UUID: str
    """

    def __init__(self, UUID, **kwargs):
        pass

    def handoff (dest_cloudlet, **kwargs):
        """Migrate a server from the current cloudlet to destination cloudlet.

        :param dest_cloudlet: Handoff destination :class:`Cloudlet`.
                            This contains access information to the Cloudlet.
        :type dest_cloudlet: :class:`Cloudlet`
        :return: A VM object at the destination :class:`Cloudlet`
        :rtype: :clas:`VM`

        :raises: :class:`HandoffException` if handoff fails.

        """
        pass

    def create_base_VM(base_VM_name, **kwargs):
        """Create base VM of the running VM

        :param base_VM_name: a new name for the base VM
        :type base_VM_name: str
        :return UUID of created base VM image
        :rtype:str
        """
        pass

    def create_VM_overlay(VM_overlay_name, **kwargs):
        """create VM overlay of the running VM

        :param VM_overlay_name: a new name for the VM overlay
        :type VM_overlay_name: str
        :return UUID of created VM overlay image
        :rtype:str
        """
        pass



