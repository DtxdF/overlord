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

import time
import logging

import etcd3gw

import overlord.config
import overlord.exceptions
import overlord.util

logger = logging.getLogger(__name__)

HOSTS = {}

def gen_hosts():
    for host in overlord.config.list_etcd_hosts():
        HOSTS[host] = 0

def run_cmd(cmd, *args, **kwargs):
    if len(HOSTS) == 0:
        gen_hosts()

    for host, blacklisted in HOSTS.items():
        if blacklisted > 0:
            wait_time = len(HOSTS) * 2

            current_time = time.time()

            if current_time-blacklisted < wait_time:
                continue

        HOSTS[host] = 0

        settings = {
            "host" : host,
            "port" : overlord.config.get_etcd_port(host),
            "protocol" : overlord.config.get_etcd_protocol(host),
            "ca_cert" : overlord.config.get_etcd_ca_cert(host),
            "cert_key" : overlord.config.get_etcd_cert_key(host),
            "timeout" : overlord.config.get_etcd_timeout(host),
            "api_path" : overlord.config.get_etcd_api_path(host)
        }

        conn = etcd3gw.client(**settings)

        try:
            return getattr(conn, cmd)(*args, **kwargs)

        except Exception as err:
            error = overlord.util.get_error(err)
            error_type = error.get("type")
            error_message = error.get("message")

            logger.exception("(host:%s, function:%s, exception:%s) %s",
                             host, cmd, error_type, error_message)

            HOSTS[host] = time.time()

    raise overlord.exceptions.EtcdException("All etcd instances do not seem to work correctly.")
