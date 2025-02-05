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

import ipaddress
import logging
import os
import random
import re
import uuid

import ifaddr

import overlord.config
import overlord.exceptions

logger = logging.getLogger(__name__)

SERVERID = None

def get_skew():
    (skew_begin, skew_end) = overlord.config.get_polling_skew()
    skew = random.randint(skew_begin, skew_end)

    return skew

def sansi(content):
    lines = []

    for line in content.splitlines():
        line = re.sub(r"(\x9B|\x1B\[)[0-?]*[ -\/]*[@-~]", "", line)

        lines.append(line)

    return "\n".join(lines)

def get_error(err):
    info = {
        "type" : err.__class__.__name__,
        "message" : str(err)
    }

    return info

def iface2ip(interface, netaddr):
    adapters = ifaddr.get_adapters()
    adapters = adapters.mapping

    adapter = adapters.get(interface)

    if adapter is None:
        raise overlord.exceptions.InterfaceNotFound(f"{interface}: Interface not found.")

    for ip_info in adapter.ips:
        if isinstance(ip_info.ip, str):
            ip = ip_info.ip

        elif isinstance(ip_info.ip, tuple):
            (ip, _, _) = ip_info.ip

        if netaddr is None:
            return ip

        if ipaddress.ip_address(ip) in ipaddress.ip_network(netaddr, strict=False):
            return ip

        else:
            logger.debug("%s not in %s", ip, netaddr)

def get_serverid():
    global SERVERID

    if SERVERID is not None:
        return SERVERID

    serverid_file = overlord.config.get_serverid()

    serverid = ""

    if os.path.isfile(serverid_file):
        with open(serverid_file) as fd:
            serverid = fd.read().strip()

    if len(serverid) == 0:
        serverid_dir = os.path.dirname(serverid_file)

        if len(serverid_dir) > 0:
            os.makedirs(serverid_dir, exist_ok=True)

        serverid = "%s" % uuid.uuid4()

        with open(serverid_file, "wb", buffering=0) as fd:
            fd.write(serverid.encode())
            fd.flush()
            os.fsync(fd.fileno())

    SERVERID = serverid

    return serverid
