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

import pymemcache

import overlord.config
import overlord.util

CLIENT = None

def connect():
    global CLIENT

    if CLIENT is not None:
        return CLIENT

    settings = {
        "max_pool_size" : overlord.config.get_memcache_max_pool_size(),
        "pool_idle_timeout" : overlord.config.get_memcache_pool_idle_timeout(),
        "retry_attempts" : overlord.config.get_memcache_retry_attempts(),
        "retry_timeout" : overlord.config.get_memcache_retry_timeout(),
        "dead_timeout" : overlord.config.get_memcache_dead_timeout(),
        "connect_timeout" : overlord.config.get_memcache_connect_timeout(),
        "timeout" : overlord.config.get_memcache_timeout(),
        "no_delay" : overlord.config.get_memcache_no_delay(),
        "use_pooling" : True
    }

    memcache_connections = overlord.config.get_memcache_connections()

    CLIENT = pymemcache.HashClient(memcache_connections, **settings)

    return CLIENT

def _get_key(key):
    id = overlord.util.get_serverid()

    if id is not None:
        key = "%s_%s" % (id, key)

    return key

def save(key, value, *args, **kwargs):
    key = _get_key(key)

    conn = connect()

    result = conn.set(key, json.dumps(value), *args, **kwargs)

    conn.quit()

    return result

def get(key):
    key = _get_key(key)

    conn = connect()

    data = conn.get(key)

    if data is None:
        result = None
    else:
        result = json.loads(data)

    conn.quit()

    return result

def delete(key):
    key = _get_key(key)

    conn = connect()

    result = conn.delete(key)

    conn.quit()

    return result

def save_jails(jails):
    return save("overlord_jails", jails)

def save_jail_stats(jail, stats):
    return save(f"overlord_jail_stats_{jail}", stats)

def save_jail_info(jail, info):
    return save(f"overlord_jail_info_{jail}", info)

def save_jail_cpuset(jail, cpuset):
    return save(f"overlord_jail_cpuset_{jail}", cpuset)

def save_jail_devfs(jail, devfs):
    return save(f"overlord_jail_devfs_{jail}", devfs)

def save_jail_expose(jail, expose):
    return save(f"overlord_jail_expose_{jail}", expose)

def save_jail_healthcheck(jail, healthcheck):
    return save(f"overlord_jail_healthcheck_{jail}", healthcheck)

def save_jail_limits(jail, limits):
    return save(f"overlord_jail_limits_{jail}", limits)

def save_jail_fstab(jail, fstab):
    return save(f"overlord_jail_fstab_{jail}", fstab)

def save_jail_label(jail, label):
    return save(f"overlord_jail_label_{jail}", label)

def save_jail_nat(jail, nat):
    return save(f"overlord_jail_nat_{jail}", nat)

def save_jail_volume(jail, volume):
    return save(f"overlord_jail_volume_{jail}", volume)

def save_jail_fstab(jail, fstab):
    return save(f"overlord_jail_fstab_{jail}", fstab)

def save_projects(projects):
    return save("overlord_projects", projects)

def save_project_info(project, info):
    return save(f"overlord_project_info_{project}", info)

def save_project_status_up(project, status):
    return save(f"overlord_project_status_up_{project}", status)

def save_project_status_down(project, status):
    return save(f"overlord_project_status_down_{project}", status)

def save_vm_status(vm, status):
    return save(f"overlord_vm_status_{vm}", status)

def save_project_status_autoscale(project, status):
    expire_time = 60 * 10 # 10 minutes

    return save(f"overlord_project_status_autoscale_{project}", status, expire=expire_time)

def get_jails():
    data = get("overlord_jails")

    if data is None:
        return []

    return data

def get_jail_stats(jail):
    data = get(f"overlord_jail_stats_{jail}")

    if data is None:
        return {}

    return data

def get_jail_info(jail):
    data = get(f"overlord_jail_info_{jail}")

    if data is None:
        return {}

    return data

def get_jail_cpuset(jail):
    data = get(f"overlord_jail_cpuset_{jail}")

    if data is None:
        return

    return data

def get_jail_devfs(jail):
    data = get(f"overlord_jail_devfs_{jail}")

    if data is None:
        return {}

    return data

def get_jail_expose(jail):
    data = get(f"overlord_jail_expose_{jail}")

    if data is None:
        return {}

    return data

def get_jail_healthcheck(jail):
    data = get(f"overlord_jail_healthcheck_{jail}")

    if data is None:
        return {}

    return data

def get_jail_limits(jail):
    data = get(f"overlord_jail_limits_{jail}")

    if data is None:
        return {}

    return data

def get_jail_fstab(jail):
    data = get(f"overlord_jail_fstab_{jail}")

    if data is None:
        return {}

    return data

def get_jail_label(jail):
    data = get(f"overlord_jail_label_{jail}")

    if data is None:
        return {}

    return data

def get_jail_nat(jail):
    data = get(f"overlord_jail_nat_{jail}")

    if data is None:
        return {}

    return data

def get_jail_volume(jail):
    data = get(f"overlord_jail_volume_{jail}")

    if data is None:
        return {}

    return data

def get_jail_fstab(jail):
    data = get(f"overlord_jail_fstab_{jail}")

    if data is None:
        return {}

    return data

def get_projects():
    data = get("overlord_projects")

    if data is None:
        return []

    return data

def get_project_info(project):
    data = get(f"overlord_project_info_{project}")

    if data is None:
        return {}

    return data

def get_project_status_up(project):
    data = get(f"overlord_project_status_up_{project}")

    if data is None:
        return {}

    return data

def get_project_status_down(project):
    data = get(f"overlord_project_status_down_{project}")

    if data is None:
        return {}

    return data

def get_vm_status(vm):
    data = get(f"overlord_vm_status_{vm}")

    if data is None:
        return {}

    return data

def get_project_status_autoscale(project):
    data = get(f"overlord_project_status_autoscale_{project}")

    if data is None:
        return {}

    return data

def remove_jail(jail):
    for keyword in ("info", "stats", "cpuset", "devfs", "expose", "healthcheck", "limits", "fstab", "label", "nat", "volume", "fstab"):
        delete(f"overlord_jail_{keyword}_{jail}")

    delete(f"overlord_vm_status_{jail}")

def remove_jail_stats(jail):
    delete(f"overlord_jail_stats_{jail}")

def remove_project(project):
    for keyword in ("info", "status_up", "status_down", "status_autoscale"):
        delete(f"overlord_project_{keyword}_{project}")

def gc_jails(jails):
    new = set(jails)
    old = set(get_jails())
    diff = old - new

    for jail in diff:
        remove_jail(jail)

    return save_jails(jails)

def gc_projects(projects):
    new = set(projects)
    old = set(get_projects())
    diff = old - new

    for project in diff:
        remove_project(project)

    return save_projects(projects)

def check_jail(jail):
    jails = get_jails()

    return jail in jails

def check_project(project):
    projects = get_projects()

    return project in projects
