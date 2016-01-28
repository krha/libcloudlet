#!/usr/bin/env python 
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

import os
import sys
import pprint
from optparse import OptionParser
# for local debugging
if os.path.exists("../libcloudlet") is True:
    sys.path.insert(0, "../")
from libcloudlet.base import *
from libcloudlet.const import *


def process_command_line(argv):
    USAGE = 'Usage: %prog -s directory_server'
    DESCRIPTION = 'Cloudlet register thread'

    parser = OptionParser(usage=USAGE, description=DESCRIPTION)

    parser.add_option(
            '-s', '--directory_server', action='store', dest='directory_server',
            default=None, help='IP address of cloudlet register server')
    parser.add_option(
            '-a', '--latitude', action='store', type='string', dest='latitude',
            default=None, help="Manually set cloudlet's latitude")
    parser.add_option(
            '-o', '--longitude', action='store', type='string', dest='longitude',
            default=None, help="Manually set cloudlet's longitude")
    parser.add_option(
            '-c', '--client-ip', action='store', type='string', dest='client_ip',
            default=None, help="Manually set cloudlet's longitude")
    parser.add_option(
            '-f', '--overlay-file', action='store', type='string', dest='overlay_file',
            default=None, help="Specify the VM overlay file path")
    parser.add_option(
            '-u', '--overlay-URL', action='store', type='string', dest='overlay_url',
            default=None, help="Specify the VM overlay URL")
    settings, args = parser.parse_args(argv)

    if not settings.directory_server:
        msg = "Need URL for register server\n"
        msg += "e.g. python cloudlet_discovery_client -s http://128.2.112.221:8080/"
        parser.error(msg)
    if settings.overlay_file and settings.overlay_url:
        parser.error("You cannot specify both overlay file and overlay URL")

    return settings, args


def main(argv):
    settings, args = process_command_line(sys.argv[1:])

    # set application info
    app_info = Application(**{
        AppInfoConst.APP_ID: "moped",
        AppInfoConst.REQUIRED_RTT: 30,
        AppInfoConst.REQUIRED_MIN_CPU_CLOCK: 1600, # in MHz
        AppInfoConst.REQUIRED_CACHE_URLS:[
            "http://amazon-asia.krha.kr/overlay-webapp-face.zip",
            "http://krha.kr/data/publications/mobisys203-kiryong.pdf",
            ],
        AppInfoConst.REQUIRED_CACHE_FILES:[
            "moped/**/*.xml",
            ]
        })

    # set device info
    m_device_info = None
    if settings.latitude is not None and settings.longitude is not None:
        properties = {"GPS_latitude": str(settings.latitude),
                      "GPS_longitude": str(settings.longitude),
                      "network_type": "wifi"}
    elif settings.client_ip is not None:
        # manually set IP address of mobile device
        properties = {"ip_address": str(settings.client_ip),
                      "network_type": "wifi"}
    else:
        properties = {"ip_address": str(Util.get_ip()),
                      "network_type": "wifi"}
    m_device_info = MobileClient(**properties)

    # find the best cloudlet querying to the registration server
    discovery = DiscoveryService(settings.directory_server)
    cloudlet = discovery.discover(client_info=m_device_info,
                       app_info=app_info)
    sys.stdout.write("Query results:\n")
    sys.stdout.write(pprint.pformat(cloudlet)+"\n")

    # perform cloudlet provisioning using given VM overlay
    if cloudlet and (settings.overlay_file or settings.overlay_url):
        synthesis_client = None
        # provision the back-end server at the Cloudlet
        ip_addr = cloudlet.get("ip_address")
        port = SynthesisClient.CLOUDLET_PORT
        synthesis_option = dict()
        synthesis_option[Protocol.SYNTHESIS_OPTION_DISPLAY_VNC] = False
        synthesis_option[Protocol.SYNTHESIS_OPTION_EARLY_START] = False

        if settings.overlay_file:
            synthesis_client = SynthesisClient(ip_addr, port, overlay_file=settings.overlay_file,
                    app_function=None, synthesis_option=synthesis_option)
        elif settings.overlay_url:
            synthesis_client = SynthesisClient(ip_addr, port, overlay_url=settings.overlay_url,
                    app_function=None, synthesis_option=synthesis_option)

        try:
            synthesis_client.provisioning()
            #synthesis_client.terminate()
            sys.stdout.write("SUCCESS in Provisioning\n")
        except ClientError as e:
            sys.stderr.write(str(e))
        return 1
    return 0

if __name__ == "__main__":
    status = main(sys.argv)
    sys.exit(status)
