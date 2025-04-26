# BSD 3-Clause License
#
# Copyright (c) 2025, Jesús Daniel Colmenares Oviedo <DtxdF@disroot.org>
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice, this
#    list of conditions and the following disclaimer.
#
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
#
# 3. Neither the name of the copyright holder nor the names of its
#    contributors may be used to endorse or promote products derived from
#    this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import os
import sys

CONFIG = ".overlord.yml"
PORT = 8888
DEBUG = False
ENV_FILE = ".env"
COMPRESS_RESPONSE = True
DATABASE = ".overlord.db"
VALID_KEYWORDS = {
    "jail" : {
        "appjail_version",
        "arch",
        "boot",
        "container",
        "container_boot",
        "container_image",
        "container_pid",
        "created",
        "devfs_ruleset",
        "dirty",
        "hostname",
        "inet",
        "inet6",
        "ip4",
        "ip6",
        "is_container",
        "locked",
        "name",
        "network_ip4",
        "networks",
        "path",
        "priority",
        "ports",
        "release_name",
        "status",
        "type",
        "version",
        "version_extra"
    },
    "stats" : {
        "cputime",
        "datasize",
        "stacksize",
        "coredumpsize",
        "memoryuse",
        "memorylocked",
        "maxproc",
        "openfiles",
        "vmemoryuse",
        "pseudoterminals",
        "swapuse",
        "nthr",
        "msgqqueued",
        "msgqsize",
        "nmsgq",
        "nsem",
        "nsemop",
        "nshm",
        "shmsize",
        "wallclock",
        "pcpu",
        "readbps",
        "writebps",
        "readiops",
        "writeiops"
    },
    "devfs" : {
        "enabled",
        "name",
        "rule"
    },
    "expose" : {
        "enabled",
        "name",
        "network_name",
        "hport",
        "jport",
        "protocol",
        "rule"
    },
    "healthcheck" : {
        "enabled",
        "health_cmd",
        "health_type",
        "interval",
        "kill_after",
        "name",
        "recover_cmd",
        "recover_kill_after",
        "recover_timeout",
        "recover_timeout_signal",
        "recover_total",
        "recover_type",
        "retries",
        "start_period",
        "status",
        "timeout",
        "timeout_signal"
    },
    "label" : {
        "value"
    },
    "limits" : {
        "action",
        "enabled",
        "name",
        "per",
        "resource",
        "rule"
    },
    "nat" : {
        "rule"
    },
    "volume" : {
        "name",
        "mountpoint",
        "type",
        "uid",
        "gid",
        "perm"
    },
    "fstab" : {
        "enabled",
        "name",
        "device",
        "mountpoint",
        "type",
        "options",
        "dump",
        "pass"
    }
}
POLLING = {
    "jail_stats" : 12,
    "jail_info" : 8,
    "projects" : 6,
    "jails" : 4,
    "jail_extras" : 6,
    "project_info" : 9,
    "autoscale" : 15,
    "skew" : [6, 10],
    "keywords" : {
        "jail" : [
            "name",
            "network_ip4",
            "ports",
            "status",
            "type",
            "version"
        ],
        "stats" : [
            "cputime",
            "datasize",
            "stacksize",
            "coredumpsize",
            "memoryuse",
            "memorylocked",
            "maxproc",
            "openfiles",
            "vmemoryuse",
            "pseudoterminals",
            "swapuse",
            "nthr",
            "msgqqueued",
            "msgqsize",
            "nmsgq",
            "nsem",
            "nsemop",
            "nshm",
            "shmsize",
            "wallclock",
            "pcpu",
            "readbps",
            "writebps",
            "readiops",
            "writeiops"
        ],
        "devfs" : [
            "enabled",
            "rule",
            "name"
        ],
        "expose" : [
            "enabled",
            "name",
            "network_name",
            "hport",
            "jport",
            "protocol",
            "ext_if",
            "on_if"
        ],
        "healthcheck" : [
            "enabled",
            "name",
            "status",
            "health_cmd",
            "health_type",
            "recover_cmd",
            "recover_type"
        ],
        "label" : [
            "value"
        ],
        "limits" : [
            "enabled",
            "name",
            "rule"
        ],
        "nat" : [
            "rule"
        ],
        "volume" : [
            "mountpoint",
            "type",
            "uid",
            "gid",
            "perm"
        ],
        "fstab" : [
            "enabled",
            "name",
            "device",
            "mountpoint",
            "type",
            "options",
            "dump",
            "pass"
        ]
    }
}
MEMCACHE = {
    "connections" : [
        "127.0.0.1"
    ],
    "max_pool_size" : None,
    "pool_idle_timeout" : 0,
    "retry_attempts" : 2,
    "retry_timeout" : 1,
    "dead_timeout" : 60,
    "connect_timeout" : 5,
    "timeout" : 8,
    "no_delay" : True,
    "id" : None
}
LABELS = ["all"]
SECRET_KEY = None
LOG_CONFIG = None
CHAINS = {}
CHAIN_TIMEOUT = 0
CHAIN_READ_TIMEOUT = 10
CHAIN_WRITE_TIMEOUT = 10
CHAIN_CONNECT_TIMEOUT = 5
CHAIN_POOL_TIMEOUT = 60
CHAIN_MAX_CONNECTIONS = 1024
CHAIN_MAX_KEEPALIVE_CONNECTIONS = 1000
CHAIN_KEEPALIVE_EXPIRY = 60
CHAIN_DISABLE = False
CLIENT_TIMEOUT = 0
CLIENT_READ_TIMEOUT = 120
CLIENT_WRITE_TIMEOUT = 120
CLIENT_CONNECT_TIMEOUT = 10
CLIENT_POOL_TIMEOUT = 60
CLIENT_MAX_CONNECTIONS = 1024
CLIENT_MAX_KEEPALIVE_CONNECTIONS = 1000
CLIENT_KEEPALIVE_EXPIRY = 60
DATAPLANEAPI_TIMEOUT = 0
DATAPLANEAPI_READ_TIMEOUT = 30
DATAPLANEAPI_WRITE_TIMEOUT = 30
DATAPLANEAPI_CONNECT_TIMEOUT = 10
DATAPLANEAPI_POOL_TIMEOUT = 60
DATAPLANEAPI_MAX_CONNECTIONS = 1024
DATAPLANEAPI_MAX_KEEPALIVE_CONNECTIONS = 1000
DATAPLANEAPI_KEEPALIVE_EXPIRY = 60
DIRECTOR = {
    "logs" : os.path.expanduser("~/.director/logs")
}
APPJAIL = {
    "logs" : "/var/log/appjail",
    "images" : "/usr/local/appjail/cache/images",
    "jails" : "/usr/local/appjail/jails"
}
BEANSTALKD_ADDR = ("127.0.0.1", 11300)
EXECUTION_TIME = 60 * 60 * 3
MAXIMUM_DEPLOYMENTS = 0
SKYDNS = {
    "path" : "/skydns",
    "zone" : "."
}
ETCD_PORT = 2379
ETCD_PROTOCOL = "http"
ETCD = {
    "localhost" : {
        "port" : ETCD_PORT,
        "protocol" : ETCD_PROTOCOL
    }
}
DNS = {
    "ttl" : 60,
    "srv" : {
        "priority" : 10,
        "weight" : 100
    }
}
PREFIX = os.path.join(sys.prefix, "overlord")
METADATA = {
    "location" : os.path.join(PREFIX, "metadata"),
    "size" : 2**20 # 1 MiB
}
COMPONENTS = os.path.join(PREFIX, "components")
SERVERID = os.path.join(PREFIX, "serverid")
SECRET_KEYFILE = os.path.join(PREFIX, "keyfile")
METADATA_MAX_SIZE = 2**10 # 1 KiB
CPU_COUNT = os.cpu_count()
SCALE = {
    "replicas" : {
        "min" : 1
    },
    "type" : "any-jail"
}
VM = {
    "from" : {
        "downloadURL" : "https://download.freebsd.org/releases/{ARCH}/{VERSION}"
    }
}
TLS = {
    "port" : PORT + 443
}
AUTODISABLE = {
    "enabled" : True,
    "failures" : 2,
    "interval" : 60, # 1m
    "increase" : 60, # 1m
    "max-increase" : 1800 # 30m
}
RETRY_POLICY = {
    "total" : 6,
    "max_backoff_wait" : 10.0,
    "backoff_factor" : 0.2,
    "respect_retry_after_header" : True,
    "backoff_jitter" : 1.0
}
