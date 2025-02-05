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

import json
import re

import dns.name
import dns.reversename

import overlord.config
import overlord.etcd
import overlord.util

def _get_serverid():
    serverid = overlord.util.get_serverid()

    if serverid is None:
        raise overlord.exceptions.MissingServerID("'skydns.serverid' is required but missing.")

    return serverid

def _get_zone2path():
    zone = overlord.config.get_skydns_zone()
    zone = dns.name.from_text(zone)

    labels = zone.labels
    labels = list(labels)
    labels.reverse()

    path = b"/".join(labels)
    path = path.decode()

    return path

def _get_group(group):
    match = re.match(r"^[a-zA-Z_-][a-zA-Z\d_-]+$", group)

    if not match:
        raise overlord.exceptions.InvalidSpec(f"{group}: invalid group name.")

    group = group[match.start():match.end()]
    group = group.lower()

    return group

def _get_addr2path(address):
    domain = dns.reversename.from_address(address)

    labels = domain.labels
    labels = list(labels)
    labels.reverse()

    path = b"/".join(labels)
    path = path.decode()

    return path

def update_ptr(address, group):
    group = _get_group(group)
    path = overlord.config.get_skydns_path()
    address_path = _get_addr2path(address)

    etcd_path = f"{path}{address_path}"

    zone = overlord.config.get_skydns_zone()
    zone = dns.name.from_text(zone)
    relative_zone = zone.to_text(omit_final_dot=True)

    target = f"{group}.{relative_zone}"

    data = {
        "host" : target,
        "group" : group
    }

    json_data = json.dumps(data)

    result = overlord.etcd.run_cmd("put", etcd_path, json_data)

    return result

def delete_ptr(address):
    path = overlord.config.get_skydns_path()
    address_path = _get_addr2path(address)

    etcd_path = f"{path}{address_path}"

    result = overlord.etcd.run_cmd("delete", etcd_path)

    return result

def update_address(address, group, ttl):
    group = _get_group(group)
    serverid = _get_serverid()
    path = overlord.config.get_skydns_path()
    zone_path = _get_zone2path()

    etcd_path = f"{path}{zone_path}/{group}/{serverid}/"

    data = {
        "host" : address,
        "ttl" : int(ttl),
        "group" : group
    }

    json_data = json.dumps(data)

    result = overlord.etcd.run_cmd("put", etcd_path, json_data)

    return result

def delete_address(group):
    group = _get_group(group)
    serverid = _get_serverid()
    path = overlord.config.get_skydns_path()
    zone_path = _get_zone2path()

    etcd_path = f"{path}{zone_path}/{group}/{serverid}/"

    result = overlord.etcd.run_cmd("delete", etcd_path)

    return result

def update_srv(group, service, proto, port, priority, weight, ttl):
    group = _get_group(group)
    serverid = _get_serverid()
    path = overlord.config.get_skydns_path()
    zone_path = _get_zone2path()

    etcd_path = f"{path}{zone_path}/{group}/_{proto}/_{service}/{serverid}/"

    zone = overlord.config.get_skydns_zone()
    zone = dns.name.from_text(zone)
    relative_zone = zone.to_text(omit_final_dot=True)

    target = f"{serverid}.{group}.{relative_zone}"

    data = {
        "host" : target,
        "port" : int(port),
        "priority" : int(priority),
        "weight" : int(weight),
        "ttl" : int(ttl),
        "group" : group
    }

    json_data = json.dumps(data)

    result = overlord.etcd.run_cmd("put", etcd_path, json_data)

    return result

def delete_srv(group, service, proto):
    serverid = _get_serverid()
    path = overlord.config.get_skydns_path()
    zone_path = _get_zone2path()

    etcd_path = f"{path}{zone_path}/{group}/_{proto}/_{service}/{serverid}/"

    result = overlord.etcd.run_cmd("delete", etcd_path)

    return result
