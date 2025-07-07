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

import contextlib
import hmac
import ipaddress
import logging
import os
import random
import re
import secrets
import socket
import uuid

import ifaddr

import overlord.config
import overlord.exceptions

logger = logging.getLogger(__name__)

SERVERID = None
BEANSTALKD_SECRET = None

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

def hmac_hexdigest(secret_key, message):
    hmac_object = hmac.new(secret_key, message, "sha256")

    hexdigest = hmac_object.hexdigest()

    return hexdigest

def hmac_validation(secret_key, message, expected_digest):
    hmac_object = hmac.new(secret_key, message, "sha256")

    hexdigest = hmac_object.hexdigest()

    return hmac.compare_digest(hmac_object.hexdigest(), expected_digest)

def get_beanstalkd_secret():
    global BEANSTALKD_SECRET

    if BEANSTALKD_SECRET is not None:
        return BEANSTALKD_SECRET

    beanstalkd_secret_file = overlord.config.get_beanstalkd_secret()

    keylen = 64
    beanstalkd_secret = ""

    if os.path.isfile(beanstalkd_secret_file):
        with open(beanstalkd_secret_file, "rb") as fd:
            beanstalkd_secret = fd.read()

    if len(beanstalkd_secret) == 0:
        beanstalkd_secret_dir = os.path.dirname(beanstalkd_secret_file)

        if len(beanstalkd_secret_dir) > 0:
            os.makedirs(beanstalkd_secret_dir, exist_ok=True)

        beanstalkd_secret = secrets.token_bytes(keylen)

        with open(beanstalkd_secret_file, "wb", buffering=0) as fd:
            fd.write(beanstalkd_secret)
            fd.flush()
            os.fsync(fd.fileno())

        os.chmod(beanstalkd_secret_file, 0o400)

    BEANSTALKD_SECRET = beanstalkd_secret

    return beanstalkd_secret

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

def get_freeport(interface, port=0, netaddr=None):
    ip = iface2ip(interface, netaddr)

    if ip is None:
        return

    ip_info = ipaddress.ip_address(ip)
    ip_version = ip_info.version

    if ip_version == 4:
        family = socket.AF_INET

    elif ip_version == 6:
        family = socket.AF_INET6

    else:
        raise ValueError("Can't obtain IP address version.")

    with socket.socket(family) as sock_srv:
        sock_srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock_srv.bind((ip, port))
        sock_srv.listen(1)

        sockname = sock_srv.getsockname()

        with socket.socket(family) as sock_cli:
            sock_cli.connect(sockname)
            ephe_sock, _ = sock_srv.accept()

            with contextlib.closing(ephe_sock):
                return sockname[1]
