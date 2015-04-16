"""This module has base class for libcloudlet
"""

__docformat__ = 'reStructuredText'



class CloudletException(Exception):
    """Abstract Exception class for libcloudlet
    """
    pass


class HandoffException(CloudletException):
    """Handoff exception
    """
    pass


class ProvisioningException(CloudletException):
    """Provisioning exception
    """
    pass

class CreateBaseVMException(CloudletException):
    """Exception in creating Base VM
    """
    pass

class CreateVMOverlayException(CloudletException):
    """Exception in creating VM overlay
    """
    pass

class DiscoveryService(object):
    """Abstract class defining minimal methods for cloudlet discovery service.
    """

    def __init__(self, **kwargs):
        """
        """
        pass

    def discover(self, account=None, key=None, 
                 cloud_URL=None, client=None, application=None, **kwargs):
        """Discover a list of cloudlets by sending query to directory server.

        :param cloud_URL: IP address or domain name of a cloud directory server
        :type cloud_URL: string
        :param account: account for directory server
        :type account: string
        :param key: access key for directory server
        :type key: string
        :param client: data structure saving client information
        :type client: :class:`MobileClient`
        :param application: data structure saving application information
        :type application: :class:`Application`

        :return: list of selected cloudlet object using client and application\
            infomation
        :rtype: list of :class:`Cloudlet` object


        """
        pass


class MobileClient(object):
    """Data structure for information of the mobile client

    This data structure is designed to save attributes for describing
    the mobile client. Arbitrary key, value paris can be saved and these will
    eventually be passed to the cloudlet using REST API.

    :param GPS_latitude: GPS coordinate latitude of the mobile device
    :param GPS_longitude: GPS longitude of a mobile device
    :param network_type: Type of the network of a mobile client. Either 'cellular' or 'WiFi'
    :param **kwargs: dictionary to save mobile client related information using
      key-value format
    :type GPS_latitude: str of decimal degree
    :type GPS_longitude: str of decimal degree
    :type ip_addr: str
    :type network_type: str
    :type **kwargs: dictionary
    """

    def __init__(self, GPS_latitude=None, GPS_longitude=None, network_type=None, **kwargs):
        pass


class Application(object):
    """Data structure for the mobile application.

    This data structure is designed to save attributes for describing
    the application. Arbitrary key, value paris can be saved and these will
    eventually be passed to the cloudlet using REST API.

    :param UUID: UUID string of the mobile application
    :param max_RTT_ms: maximum allowed latency (RTT) for offloading
    :param min_CPU_clock_MHz: minimal CPU clock speed required for offloading
    :param cache_URL_list: necessary cached URLs
    :param cache_file_list: ncessary cached files
    :param **kwargs: dictionary to save app related information using
      key-value format
    :type UUID: str
    :type max_RTT_ms: int
    :type min_CPU_clock_MHz: int
    :type cache_URL_list: list of str
    :type cache_file_list: list of str
    :type **kwargs: dictionary

    """

    def __init__(self, UUID, max_RTT_ms=None, min_CPU_clock_MHz=None, cache_URL_list=None, cache_file_list=None, **kwargs):
        pass


class Cloudlet(object):
    """Represent a single cloudlet

    :param URL: IP address or domain name of the cloudlet
    :type URL: str
    :param access_token: authentication token to access Cloudlet
    :type access_token: str
    """

    def __init__(URL, access_token, **kwargs):
        pass

    def associate(self):
        """ Connect and associate with a cloudlet

        return: associated cloudlet
        rtype: :class:`VM`
        """
        pass

    def disassociate(self):
        """
        Disassociate with a cloudlet, and terminate all VMs that a user
        was using.

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
        :return: a provisioned VM information
        :rtype: :class:`VM`

        :raises: :class:`ProvisioningException` when provisioning fails.
        """
        pass


class VM(object):
    """Represent a virtual mahince instance at cloudlet

    :param UUID: an UUID of the virtual machine instance assigned by cloudlet
    :type UUID: str
    """

    def __init__(self, UUID, **kwargs):
        pass

    def handoff (dest_cloudlet, **kwargs):
        """Migrate this VM instance from the current cloudlet to the destination
        cloudlet.

        :param dest_cloudlet: Handoff destination cloudlet.\
            It contains access information to the cloudlet.
        :type dest_cloudlet: :class:`Cloudlet`
        :return: A VM instance at the destination :class:`Cloudlet`
        :rtype: :class:`VM`

        :raises: :class:`HandoffException` when handoff fails.
        """
        pass

    def create_base_VM(base_VM_name, **kwargs):
        """Create a base VM image of the VM. The VM will be shutdown
        after this operation.

        :param base_VM_name: a new name for the base VM
        :type base_VM_name: str
        :return: UUID of created base VM image
        :rtype: str

        :raises: :class:`CreateBaseVMException` when fails.
        """
        pass

    def create_VM_overlay(VM_overlay_name, **kwargs):
        """create VM overlay of the running VM

        :param VM_overlay_name: a new name for the VM overlay
        :type VM_overlay_name: str
        :return: UUID of created VM overlay image
        :rtype: str

        :raises: :class:`CreateVMOverlayException` when fails.
        """
        pass

    def resume(self, **kwargs):
        """Resume the VM instance if it's not active.

        :return: True if successfully resumed
        :rtype: bool
        """
        pass

    def assign_IP(self, **kwargs):
        """Assign IP address to the VM to be accessible

        :return: assigned IP address
        :rtype: str
        """
        pass

