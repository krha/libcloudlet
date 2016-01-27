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


class CloudletQueryingThread(threading.Thread):
    def __init__(self, cloudlet_info, app_info=None):
        self.cloudlet_info = cloudlet_info
        self.url = "http://%s:%d%s" % (
                cloudlet_info['ip_address'],
                cloudlet_info['rest_api_port'],
                cloudlet_info['rest_api_url'])
        self.app_info = app_info
        threading.Thread.__init__(self, target=self.get_info)

    def get_info(self):
        try:
            _LOG.info("Connecting to cloudlet at %s" % self.url)
            end_point = urlparse(self.url)
            if self.app_info:
                params = json.dumps(self.app_info.__dict__)
            else:
                params = json.dumps({})
            headers = {"Content-type": "application/json"}
            conn = httplib.HTTPConnection(end_point.hostname, \
                    end_point.port, timeout=10)
            _LOG.debug("Query parameter:")
            _LOG.debug((pprint.pformat(json.loads(params))))
            conn.request("GET", "%s" % end_point[2], params, headers)
            data = conn.getresponse().read()
            json_data = json.loads(data)
            self.cloudlet_info.update(json_data)
        except socket.error as e:
            _LOG.error(str(e) + "\n")


class DiscoveryService(object):
    """Abstract class defining minimal methods for cloudlet discovery service.
    """
    REST_API_URL        =   "/api/v1/Cloudlet/search/"

    def __init__(self, **kwargs):
        """
        """
        pass

    @staticmethod
    def _preprocess_URL(cloud_URL):
        if cloud_URL.endswith('/'):
            cloud_URL = cloud_URL[:-1]
        return cloud_URL

    @staticmethod
    def discover(cloud_URL=None, cloudlet_provider_list=None,
                 client_info=None, app_info=None, n_ret_clodulet=3, **kwargs):
        """Discover a list of cloudlets by sending query to directory server.

        :param cloud_URL: IP address or domain name of a cloud directory server
        :type cloud_URL: string
        :param cloudlet_provider_list: list of cloudlet provider
        :type cloudlet_provider_list: list of string
        :param client_info: data structure saving client information
        :type client_info: :class:`MobileClient`
        :param app_info: data structure saving application information
        :type app_info: :class:`Application`

        :return: list of selected cloudlet object using client and application\
            infomation
        :rtype: list of :class:`Cloudlet` object
        """
        # proprocessing cloud_URL
        cloud_URL = DiscoveryService._preprocess_URL(cloud_URL)
        time_cloud_conn = time.time()
        # get cloudlet list from central cloud directory server
        latitude = getattr(app_info, 'GPS_latitude', None)
        longitude = getattr(app_info, 'GPS_longitude', None)
        client_ip = getattr(app_info, 'client_ip', None)
        if latitude and longitude:
            end_point = urlparse("%s%s?n=%d&latitude=%s&longitude=%s" % \
                    (cloud_URL, DiscoveryService.REST_API_URL, \
                    n_max, latitude, longitude))
        elif client_ip:
            # search by IP address
            end_point = urlparse("%s%s?n=%d&client_ip=%s" % \
                    (cloud_URL, DiscoveryService.REST_API_URL, \
                    n_max, str(client_ip)))
        else:
            end_point = urlparse("%s%s?n=%d" % \
                    (cloud_URL, DiscoveryService.REST_API_URL, \
                    n_ret_clodulet))
        try:
            cloudlet_list = []
            cloudlets = DiscoveryService.http_get(end_point)
            for cloudlet in cloudlets:
                ipaddr = cloudlet.get('ip_address', '')
                rest_api_url = cloudlet.get('rest_api_url', '')
                if len(ipaddr) != 0 and len(rest_api_url) != 0:
                    cloudlet_list.append(cloudlet)
        except socket.error as e:
            CloudletException("Cannot connect to %s" % str(e))

        # second level search to each cloudlet
        time_cloudlet_conn = time.time()
        DiscoveryService._get_cloudlet_infos(cloudlet_list, app_info)
        time_cloudlet_ret = time.time()

        cloudlet = DiscoveryService._find_best_cloudlet(cloudlet_list, app_info)
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
    def _get_cloudlet_infos(cloudlet_list, app_info):
        thread_list = list()
        for cloudlet in cloudlet_list:
            new_thread = CloudletQueryingThread(cloudlet, app_info)
            thread_list.append(new_thread)
        for th in thread_list:
            th.start()
        for th in thread_list:
            th.join()

    @staticmethod
    def _find_best_cloudlet(cloudlet_list, app_info=None):
        # pre-screening conditions
        item_len = len(cloudlet_list)
        if item_len == 0:
            msg = "No available cloudlet at the list\n"
            raise DiscoveryException(msg)
        if item_len == 1:
            _LOG.info("Only one cloudlet is available")
            return cloudlet_list[0]

        # filterout using required conditions
        filtered_cloudlet = list(cloudlet_list)
        for cloudlet in cloudlet_list:
            # check CPU min
            required_clock_speed = getattr(app_info, AppInfo.REQUIRED_MIN_CPU_CLOCK, None)
            cloudlet_cpu_speed = cloudlet.get(ResourceConst.CLOCK_SPEED)
            if required_clock_speed is not None:
                if cloudlet_cpu_speed < required_clock_speed:
                    filtered_cloudlet.remove(cloudlet)
            # check rtt
            #required_rtt = getattr(app_info, AppInfo.REQUIRED_RTT, None)
            #cloudlet_rtt = getattr(cloudlet, ResourceConst.RTT_BETWEEN_CLIENT, None)
            #if required_rtt is not None:
            #    if cloudlet_rtt < required_rtt:
            #        filtered_cloudlet.append(cloudlet)
        if len(filtered_cloudlet) == 0:
            _LOG.warning("No available cloudlet after filtering out")
            return None

        # check cache
        max_cache_score = float(-1)
        max_cache_cloudlet = None
        for cloudlet in filtered_cloudlet:
            cache_score = cloudlet.get(ResourceConst.APP_CACHE_TOTAL_SCORE, None)
            if cache_score is not None and cache_score > max_cache_score:
                max_cache_score = cache_score
                max_cache_cloudlet = cloudlet
        if max_cache_cloudlet is not None:
            return max_cache_cloudlet
        else:
            return filtered_cloudlet[0]


        # check application preference
        #weight_rtt = getattr(app_info, AppInfo.KEY_WEIGHT_CACHE, None)
        #weight_cache = getattr(app_info, AppInfo.KEY_WEIGHT_CACHE, None)
        #weight_resource = getattr(app_info, AppInfo.KEY_WEIGHT_CACHE, None)
        #if weight_rtt is None or weight_cache is None or \
        #        weight_resource is None:
        #    index = random.randint(0, item_len-1)
        #    return cloudlet_list[index]

    @staticmethod
    def http_get(end_point):
        _LOG.info("Connecting to %s" % (end_point.geturl()))
        params = urllib.urlencode({})
        headers = {"Content-type":"application/json"}
        end_string = "%s?%s" % (end_point[2], end_point[4])

        conn = httplib.HTTPConnection(end_point[1])
        conn.request("GET", end_string, params, headers)
        data = conn.getresponse().read()
        response_list = json.loads(data).get('cloudlet', list())
        conn.close()
        return response_list



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
        for k, v in kwargs.iteritems():
            setattr(self, k, v)


class Cloudlet(object):
    """Represent a single cloudlet

    :param URL: IP address or domain name of the cloudlet
    :type URL: str
    :param auth_token: authentication token to access Cloudlet
    :type auth_token: str
    """

    def __init__(URL, auth_token, **kwargs):
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

