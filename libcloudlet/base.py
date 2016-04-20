#
# Cloudlet Infrastructure for Mobile Computing
#
#   Author: Kiryong Ha <krha@cmu.edu>
#
#   Copyright (C) 2011-2016 Carnegie Mellon University
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
#

"""This module has base class for libcloudlet
"""

__docformat__ = 'reStructuredText'

import sys
import threading
import urllib
import httplib
import json
import time
import socket
import logging
import pprint
from urlparse import urlparse
from contextlib import closing
from . import const


class CloudletException(Exception):
    """Abstract Exception class for libcloudlet
    """
    pass


class DiscoveryException(CloudletException):
    """Handoff exception
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


# Logging
_LOG = logging.getLogger("discovery")
_LOG.setLevel(logging.DEBUG)
ch = logging.StreamHandler(sys.stdout)
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(levelname)-8s %(message)s')
ch.setFormatter(formatter)
_LOG.addHandler(ch)


class DiscoveryService(object):
    """Abstract class defining minimal methods for cloudlet discovery service.
    """

    def __init__(self, directory_server=None, **kwargs):
        """
        :param directory_server: IP address or domain name of a cloud directory server
        :type directory_server: string
        """
        self.directory_server = directory_server
        if self.directory_server.endswith('/'):
            self.directory_server = self.directory_server[:-1]

    def discover(self, **kwargs):
        """Abstract method to discover a list of cloudlets
        """
        pass


class ElijahCloudletSelection(object):

    @staticmethod
    def select_cloudlet(cloudlet_list, app_info):
        """ Select one cloudlet using application information

        :param cloudlet_list : list of promising cloudlet
        :type cloudlet_list: list of :class:`Cloudlet` object
        :return: selected cloudlet
        :rtype: :class:`Cloudlet` object
        """
        # check pre-conditions
        item_len = len(cloudlet_list)
        if item_len == 0:
            msg = "No available cloudlet at the list\n"
            raise DiscoveryException(msg)
        if item_len == 1:
            _LOG.info("Only one cloudlet is available")
            return cloudlet_list[0]

        # filter out using required conditions
        filtered_cloudlet = []
        for cloudlet in cloudlet_list:
            # get application specific cloudlet info
            cloudlet_info = getattr(cloudlet, app_info.get_appid(), None)
            if not cloudlet_info:
                continue
            # check CPU min
            required_clock_speed = getattr(app_info, const.AppInfoConst.REQUIRED_MIN_CPU_CLOCK, 0.0)
            cloudlet_cpu_speed = cloudlet_info.get(const.ResourceInfoConst.CLOCK_SPEED, 0.0)
            if required_clock_speed:
                if cloudlet_cpu_speed >= required_clock_speed:
                    filtered_cloudlet.append(cloudlet)
            # check rtt
            #required_rtt = getattr(app_info, const.AppInfoConst.REQUIRED_RTT, 0)
            #cloudlet_rtt = cloudlet_info.get(const.ResourceInfoConst.RTT_BETWEEN_CLIENT, 0)
            #if required_rtt:
            #    if cloudlet_rtt < required_rtt:
            #        filtered_cloudlet.append(cloudlet)
        if len(filtered_cloudlet) == 0:
            _LOG.warning("No available cloudlet meeting condition")
            return None

        # check cache
        max_cache_score = 0.0
        max_cache_cloudlet = None
        for cloudlet in filtered_cloudlet:
            # get application specific cloudlet info
            cloudlet_info = getattr(cloudlet, app_info.get_appid(), None)
            if not cloudlet_info:
                continue
            cache_score = cloudlet_info.get(const.ResourceInfoConst.APP_CACHE_TOTAL_SCORE, None)
            if cache_score and cache_score > max_cache_score:
                max_cache_score, max_cache_cloudlet = cache_score, cloudlet
        return max_cache_cloudlet or filtered_cloudlet[0]

        # check application preference
        #weight_rtt = getattr(app_info, const.AppInfoConst.KEY_WEIGHT_CACHE, None)
        #weight_cache = getattr(app_info, const.AppInfoConst.KEY_WEIGHT_CACHE, None)
        #weight_resource = getattr(app_info, const.AppInfoConst.KEY_WEIGHT_CACHE, None)
        #if weight_rtt or weight_cache or weight_resource:
        #    index = random.randint(0, item_len-1)
        #    return cloudlet_list[index]

class ElijahCloudletDiscovery(DiscoveryService):
    _REST_API_URL        =   "/api/v1/Cloudlet/search/"

    def __init__(self, directory_server=None, **kwargs):
        """
        :param directory_server: IP address or domain name of a cloud directory server
        :type directory_server: string
        """
        super(ElijahCloudletDiscovery, self).__init__(directory_server, **kwargs)

    def discover(self, client_info=None, app_info=None,
                 selection_algorithm=None, **kwargs):
        """Discover a list of cloudlets by sending query to directory server.

        :param client_info: data structure saving a mobile client information
        :type client_info: :class:`MobileClient`
        :param app_info: data structure saving an application information
        :type app_info: :class:`Application`
        :param selection_algorithm: custom function for selecting cloudlet
        :type selection_algorithm: function pointer of\
            slection_algorithm(list of :class:`Cloudlet`, app_info)

        :return: list of selected cloudlet object using client and application\
            infomation
        :rtype: :class:`Cloudlet` object
        """

        # first level search to get cloudlet list from central directory server
        time_cloud_conn = time.time()
        cloudlet_list = self._list_cloudlets(self.directory_server, app_info)
        if not cloudlet_list:
            msg = "Cannot find any cloudlet from directory server at %s" % str(end_point)
            raise CloudletException(msg)

        # second level search to each cloudlet
        time_cloudlet_conn = time.time()
        self._get_cloudlet_details(cloudlet_list, app_info)
        time_cloudlet_ret = time.time()

        # select the best one
        if not selection_algorithm:
            selection_algorithm = ElijahCloudletSelection.select_cloudlet
        cloudlet = selection_algorithm(cloudlet_list, app_info)
        time_query_end = time.time()

        # print time measurement
        if True:
            _LOG.debug("Time from get cloudlet list from cloud:\t%f" % \
                       (time_cloudlet_conn-time_cloud_conn))
            _LOG.debug("Time from get detail cloudlet info:\t%f" % \
                       (time_cloudlet_ret-time_cloudlet_conn))
            _LOG.debug("Time to make a decision:\t\t%f" % \
                       (time_query_end-time_cloudlet_ret))
            _LOG.debug("Total time:\t\t\t\t%f" %\
                       (time_query_end-time_cloudlet_ret))
        return cloudlet

    @staticmethod
    def _list_cloudlets(directory_server, app_info, n_ret_cloudlet=3):
        """ get the list of promising cloudlets from the directory server
        :param app_info: data structure saving application information
        :type app_info: :class:`Application`
        :return: cloudlet list
        :rtype: list of :class:`Cloudlet` object
        """
        # set up end point for REST API call
        latitude = getattr(app_info, 'GPS_latitude', None)
        longitude = getattr(app_info, 'GPS_longitude', None)
        client_ip = getattr(app_info, 'client_ip', None)
        if latitude and longitude: # search by given GPS coordinate
            end_point = urlparse("%s%s?n=%d&latitude=%s&longitude=%s" % \
                    (directory_server, ElijahCloudletDiscovery._REST_API_URL, \
                    n_max, latitude, longitude))
        elif client_ip: # search by specified IP address
            end_point = urlparse("%s%s?n=%d&client_ip=%s" % \
                    (directory_server, ElijahCloudletDiscovery._REST_API_URL, \
                    n_max, str(client_ip)))
        else: # search by device's IP address
            end_point = urlparse("%s%s?n=%d" % \
                    (directory_server, ElijahCloudletDiscovery._REST_API_URL, \
                    n_ret_cloudlet))

        # send query and organize results
        ret_data = ElijahCloudletDiscovery._http_get(end_point)
        cloudlets = json.loads(ret_data).get('cloudlet', list())
        if not cloudlets:
            msg = "No cloudlet is active at %s" % str(end_point)
            raise CloudletException(msg)
        cloudlet_list = []
        for cloudlet in cloudlets:
            ipaddr = cloudlet.get('ip_address', None)
            port = cloudlet.get('rest_api_port', None)
            rest_api_url = cloudlet.get('rest_api_url', None)
            if ipaddr and port and rest_api_url:
                endpoint = "http://%s:%d%s" % (ipaddr,
                                               port,
                                               rest_api_url)
                new_cloudlet = Cloudlet(REST_endpoint=endpoint, **cloudlet)
                cloudlet_list.append(new_cloudlet)
        return cloudlet_list

    @staticmethod
    def _get_cloudlet_details(cloudlet_list, app_info):
        """ Get details information of each cloudlet and update :class:`Cloudlet` object

        :param cloudlet_list : list of promising cloudlet
        :type cloudlet_list: list of :class:`Cloudlet` object
        :return: None
        """
        thread_list = list()
        for cloudlet in cloudlet_list:
            new_thread = CloudletQueryingThread(cloudlet, app_info)
            thread_list.append(new_thread)
        for th in thread_list:
            th.start()
        for th in thread_list:
            th.join()


    @staticmethod
    def _http_get(end_point):
        """ Send REST query using HTTP GET method
        :param end_point: end point URL
        :type end_point: string
        :return: HTTP GET result
        :rtype: string
        """
        _LOG.info("Connecting to %s" % (end_point.geturl()))
        params = urllib.urlencode({})
        headers = {"Content-type":"application/json"}
        end_string = "%s?%s" % (end_point[2], end_point[4])
        try:
            with closing(httplib.HTTPConnection(end_point[1])) as conn:
                conn = httplib.HTTPConnection(end_point[1])
                conn.request("GET", end_string, params, headers)
                data = conn.getresponse().read()
                return data
        except socket.error as e:
            msg = "Failed to connect to %s" % str(end_point)
            raise CloudletException(msg)



class MobileClient(object):
    """Data structure for information of the mobile client

    This data structure is designed to save attributes for describing
    the mobile client. Arbitrary key, value paris can be saved and these will
    eventually be passed to the cloudlet.

    :param **kwargs: dictionary to save mobile client related information using
      key-value format
    :type **kwargs: dictionary

    Key and values should be seriealizable to JSON format.
    For example, GPS coordinates can be appended as follows.

    >>> from libcloudlet.base import MobileClient 
    >>> properties = {"GPS_latitude": "40.439722",
                      "GPS_longitude": "-79.976389",
                      "network_type": "cellular"}
    >>> mobile_client = MobileClient(**properties)

    """

    def __init__(self, **kwargs):
        for k, v in kwargs.iteritems():
            setattr(self, k, v)


class Application(object):
    """Data structure for the mobile application.

    This data structure is designed to save attributes for describing
    the application. Arbitrary key, value paris can be saved and these will
    eventually be passed to the cloudlet.

    :param **kwargs: dictionary to save app related information using
      key-value format
    :type **kwargs: dictionary

    App information will be saved using <key, value> pairs passed by
    kwargs parameter. Key and values should be seriealizable to JSON format.
    For example, maximum allowed latency (RTT) and minimal CPU clock speed
    required for offloading can be defined as follows.

    >>> from libcloudlet.base import Application
    >>> properties = {"UUID": "c8727360-e769-11e4-8a00-1681e6b88ec1"
                      "max_RTT_ms": 50,
                      "min_CPU_clock_MHz": 2000}
    >>> speech_recogn_app = Application(**properties)

    """

    def __init__(self, **kwargs):
        self.__dict__[const.AppInfoConst.APP_ID] = ""
        for k, v in kwargs.iteritems():
            setattr(self, k, v)

    def get_appid(self):
        """ return appplication ID
        :return: application ID
        :rtype: string
        """
        return getattr(self, const.AppInfoConst.APP_ID, "")


class Cloudlet(object):
    """Represent a single cloudlet

    :param URL: IP address or domain name of the cloudlet
    :type URL: str
    :param auth_token: authentication token to access Cloudlet
    :type auth_token: str
    """

    def __init__(self, REST_endpoint, auth_token=None, **kwargs):
        self.REST_endpoint = REST_endpoint
        meta_info = {}
        for k, v in kwargs.iteritems():
            meta_info[k] = v
        setattr(self, 'meta_info', meta_info)

    def get_info(self, app_info):
        """ Query cloudlet using application information

        :param app_info: application information
        :type app_info: object of :class:`Application`
        return: None
        """
        _LOG.info("Connecting to cloudlet at %s" % self.REST_endpoint)
        end_point = urlparse(self.REST_endpoint)
        params = json.dumps({'application': app_info.__dict__})
        headers = {"Content-type": "application/json"}
        with closing(httplib.HTTPConnection(end_point.hostname, end_point.port, timeout=10)) as conn:
            _LOG.debug("Query parameter:\n%s" % str(pprint.pformat(json.loads(params))))
            conn.request("GET", "%s" % end_point[2], params, headers)
            data = conn.getresponse().read()
            json_data = json.loads(data)
            setattr(self, app_info.get_appid(), json_data)

    def associate(self):
        """ Connect and associate with a cloudlet

        :return: associated cloudlet
        :rtype: :class:`VM`
        """
        pass

    def disassociate(self):
        """
        Disassociate with a cloudlet, and terminate all VMs that a user
        was using.

        :return: None
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

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        attrs = pprint.pformat(self.__dict__)
        return attrs



class CloudletQueryingThread(threading.Thread):
    """ Thread wrapper to connect multiple cloudlets in parallel
    """

    def __init__(self, cloudlet, app_info=None):
        self.cloudlet = cloudlet
        self.app_info = app_info
        threading.Thread.__init__(self, target=self.run)

    def run(self):
        """ thread main method
        """
        self.cloudlet.get_info(self.app_info)



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
            It contains authentication information to the cloudlet.
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

