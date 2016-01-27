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


class AppInfoConst(object):
    APPLICATION     = "application"
    APP_ID          = "app-id"
    REQUIRED_RTT             = "required-RTT"
    REQUIRED_CACHE_FILES     = "required-files"
    REQUIRED_CACHE_URLS      = "required-URLs"
    REQUIRED_MIN_CPU_CLOCK   = "required-cpu-clocks"

    WEIGHT_RTT      = "weight-RTT"
    WEIGHT_CACHE    = "weight-cache"
    WEIGHT_RESOURCE = "weight-resource"

    def __init__(self, *args, **kwargs):
        self.__dict__.update(kwargs)

    def __getitem__(self, name):
        return self.__dict__.get(name, None)

    def get_info(self):
        return {self.APPLICATION: self.__dict__}


class ResourceInfoConst(object):
    # static resource
    TOTAL_CPU_NUMBER    =   "total_cpu_num"
    TOTAL_MEM_MB        =   "total_mem_mb"
    CLOCK_SPEED         =   "cpu_clock_speed_mhz"

    # dynamic resource
    TOTAL_CPU_PERCENT   = "total_cpu_usage_percent"
    TOTAL_MEM_FREE_MB   = "total_free_memory_mb"
    RTT_BETWEEN_CLIENT  = "dynamic_RTT"


    # cache status
    APP_CACHE_FILES                 =   "app_cache_files"
    APP_CACHE_URLS                  =   "app_cache_urls"
    APP_CACHE_TOTAL_SCORE           =   "app_cache_total_score"


class Util(object):
    @staticmethod
    def get_ip(iface = 'eth0'):
        import socket
        import struct
        import fcntl
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sockfd = sock.fileno()
        SIOCGIFADDR = 0x8915

        ifreq = struct.pack('16sH14s', iface, socket.AF_INET, '\x00' * 14)
        try:
            res = fcntl.ioctl(sockfd, SIOCGIFADDR, ifreq)
        except:
            return None
        ip = struct.unpack('16sH2x4s8x', res)[2]
        return socket.inet_ntoa(ip)


