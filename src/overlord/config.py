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

import logging.config
import re

import pyaml_env

import overlord.chains
import overlord.default
import overlord.exceptions

CONFIG = {}

def load(file):
    global CONFIG

    document = pyaml_env.parse_config(file, default_value="")

    if document is None:
        return

    validate(document)

    CONFIG = document

def get_config():
    config = {
        "port" : get_port(),
        "debug" : get_debug(),
        "compress_response" : get_compress_response(),
        "polling" : {
            "jail_stats" : get_polling_jail_stats(),
            "jail_info" : get_polling_jail_info(),
            "projects" : get_polling_projects(),
            "jails" : get_polling_jails(),
            "jail_extras" : get_polling_jail_extras(),
            "project_info" : get_polling_project_info(),
            "skew" : get_polling_skew(),
            "keywords" : {
                "stats" : get_polling_keywords_stats(),
                "jail" : get_polling_keywords_jail(),
                "devfs" : get_polling_keywords_devfs(),
                "expose" : get_polling_keywords_expose(),
                "healthcheck" : get_polling_keywords_healthcheck(),
                "label" : get_polling_keywords_label(),
                "limits" : get_polling_keywords_limits(),
                "nat" : get_polling_keywords_nat(),
                "volume" : get_polling_keywords_volume(),
                "fstab" : get_polling_keywords_fstab()
            }
        },
        "memcache" : {
            "connections" : get_memcache_connections(),
            "max_pool_size" : get_memcache_max_pool_size(),
            "pool_idle_timeout" : get_memcache_pool_idle_timeout(),
            "retry_attempts" : get_memcache_retry_attempts(),
            "retry_timeout" : get_memcache_retry_timeout(),
            "dead_timeout" : get_memcache_dead_timeout(),
            "connect_timeout" : get_memcache_connect_timeout(),
            "timeout" : get_memcache_timeout(),
            "no_delay" : get_memcache_no_delay(),
            "id" : get_memcache_id()
        },
        "secret_key" : get_secret_key(),
        "log_config" : get_log_config(),
        "chains" : {},
        "labels" : get_labels(),
        "director" : {
            "logs" : get_director_logs()
        },
        "appjail" : {
            "logs" : get_appjail_logs()
        },
        "beanstalkd_addr" : get_beanstalkd_addr(),
        "execution_time" : get_execution_time(),
        "dataplaneapi" : {
            "serverid" : get_dataplaneapi_serverid(),
            "entrypoint" : get_dataplaneapi_entrypoint(),
            "auth" : {
                "username" : get_dataplaneapi_auth_username(),
                "password" : get_dataplaneapi_auth_password()
            },
            "timeout" : get_dataplaneapi_timeout(),
            "read_timeout" : get_dataplaneapi_read_timeout(),
            "write_timeout" : get_dataplaneapi_write_timeout(),
            "connect_timeout" : get_dataplaneapi_connect_timeout(),
            "pool_timeout" : get_dataplaneapi_pool_timeout(),
            "max_keepalive_connections" : get_dataplaneapi_max_keepalive_connections(),
            "max_connections" : get_dataplaneapi_max_connections(),
            "keepalive_expiry" : get_dataplaneapi_keepalive_expiry()
        },
        "skydns" : {
            "serverid" : get_skydns_serverid(),
            "path" : get_skydns_path(),
            "zone" : get_skydns_zone()
        },
        "etcd" : {},
        "max_watch_projects" : get_max_watch_projects(),
        "metadata" : {
            "location" : get_metadata_location(),
            "size" : get_metadata_size()
        }
    }

    for host in list_etcd_hosts():
        config["etcd"][host] = {
            "port" : get_etcd_port(host),
            "protocol" : get_etcd_protocol(host),
            "ca_cert" : get_etcd_ca_cert(host),
            "cert_key" : get_etcd_cert_key(host),
            "timeout" : get_etcd_timeout(host),
            "api_path" : get_etcd_api_path(host)
        }

    for chain in list_chains():
        config["chains"][chain] = {
            "entrypoint" : get_chain_entrypoint(chain),
            "access_token" : get_chain_access_token(chain),
            "timeout" : get_chain_timeout(chain),
            "read_timeout" : get_chain_read_timeout(chain),
            "write_timeout" : get_chain_write_timeout(chain),
            "connect_timeout" : get_chain_connect_timeout(chain),
            "pool_timeout" : get_chain_pool_timeout(chain),
            "max_keepalive_connections" : get_chain_max_keepalive_connections(chain),
            "max_connections" : get_chain_max_connections(chain),
            "keepalive_expiry" : get_chain_keepalive_expiry(chain)
        }

    return config

def get_default(value, default=None):
    if value is None:
        return default

    return value

def get_execution_time():
    return CONFIG.get("execution_time", overlord.default.EXECUTION_TIME)

def get_beanstalkd_addr():
    return get_default(CONFIG.get("beanstalkd_addr"), overlord.default.BEANSTALKD_ADDR)

def get_director():
    return get_default(CONFIG.get("director"), overlord.default.DIRECTOR)

def get_director_logs():
    director = get_director()

    return get_default(director.get("logs"), overlord.default.DIRECTOR["logs"])

def get_appjail():
    return get_default(CONFIG.get("appjail"), overlord.default.APPJAIL)

def get_appjail_logs():
    appjail = get_appjail()

    return get_default(appjail.get("logs"), overlord.default.APPJAIL["logs"])

def get_labels():
    return get_default(CONFIG.get("labels"), overlord.default.LABELS)

def get_port():
    return get_default(CONFIG.get("port"), overlord.default.PORT)

def get_debug():
    return get_default(CONFIG.get("debug"), overlord.default.DEBUG)

def get_compress_response():
    return get_default(CONFIG.get("compress_response"), overlord.default.COMPRESS_RESPONSE)

def get_polling():
    return get_default(CONFIG.get("polling"), overlord.default.POLLING)

def get_polling_jail_stats():
    polling = get_polling()

    return get_default(polling.get("jail_stats"), overlord.default.POLLING["jail_stats"])

def get_polling_jail_info():
    polling = get_polling()

    return get_default(polling.get("jail_info"), overlord.default.POLLING["jail_info"])

def get_polling_projects():
    polling = get_polling()

    return get_default(polling.get("projects"), overlord.default.POLLING["projects"])

def get_polling_jails():
    polling = get_polling()

    return get_default(polling.get("jails"), overlord.default.POLLING["jails"])

def get_polling_jail_extras():
    polling = get_polling()

    return get_default(polling.get("jail_extras"), overlord.default.POLLING["jail_extras"])

def get_polling_project_info():
    polling = get_polling()

    return get_default(polling.get("project_info"), overlord.default.POLLING["project_info"])

def get_polling_skew():
    polling = get_polling()

    return get_default(polling.get("skew"), overlord.default.POLLING["skew"])

def get_polling_keywords():
    polling = get_polling()

    return get_default(polling.get("keywords"), overlord.default.POLLING["keywords"])

def get_polling_keywords_stats():
    polling_keywords = get_polling_keywords()

    return get_default(polling_keywords.get("stats"), overlord.default.POLLING["keywords"]["stats"])

def get_polling_keywords_jail():
    polling_keywords = get_polling_keywords()

    return get_default(polling_keywords.get("jail"), overlord.default.POLLING["keywords"]["jail"])

def get_polling_keywords_devfs():
    polling_keywords = get_polling_keywords()

    return get_default(polling_keywords.get("devfs"), overlord.default.POLLING["keywords"]["devfs"])

def get_polling_keywords_expose():
    polling_keywords = get_polling_keywords()

    return get_default(polling_keywords.get("expose"), overlord.default.POLLING["keywords"]["expose"])

def get_polling_keywords_healthcheck():
    polling_keywords = get_polling_keywords()

    return get_default(polling_keywords.get("healthcheck"), overlord.default.POLLING["keywords"]["healthcheck"])

def get_polling_keywords_label():
    polling_keywords = get_polling_keywords()

    return get_default(polling_keywords.get("label"), overlord.default.POLLING["keywords"]["label"])

def get_polling_keywords_limits():
    polling_keywords = get_polling_keywords()

    return get_default(polling_keywords.get("limits"), overlord.default.POLLING["keywords"]["limits"])

def get_polling_keywords_nat():
    polling_keywords = get_polling_keywords()

    return get_default(polling_keywords.get("nat"), overlord.default.POLLING["keywords"]["nat"])

def get_polling_keywords_volume():
    polling_keywords = get_polling_keywords()

    return get_default(polling_keywords.get("volume"), overlord.default.POLLING["keywords"]["volume"])

def get_polling_keywords_fstab():
    polling_keywords = get_polling_keywords()

    return get_default(polling_keywords.get("fstab"), overlord.default.POLLING["keywords"]["fstab"])

def get_memcache():
    return get_default(CONFIG.get("memcache"), overlord.default.MEMCACHE)

def get_memcache_connections():
    memcache = get_memcache()

    return get_default(memcache.get("connections"), overlord.default.MEMCACHE["connections"])

def get_memcache_max_pool_size():
    memcache = get_memcache()

    return get_default(memcache.get("max_pool_size"), overlord.default.MEMCACHE["max_pool_size"])

def get_memcache_pool_idle_timeout():
    memcache = get_memcache()

    return get_default(memcache.get("pool_idle_timeout"), overlord.default.MEMCACHE["retry_attempts"])

def get_memcache_retry_attempts():
    memcache = get_memcache()

    return get_default(memcache.get("retry_attempts"), overlord.default.MEMCACHE["retry_attempts"])

def get_memcache_retry_timeout():
    memcache = get_memcache()

    return get_default(memcache.get("retry_timeout"), overlord.default.MEMCACHE["retry_timeout"])

def get_memcache_dead_timeout():
    memcache = get_memcache()

    return get_default(memcache.get("dead_timeout"), overlord.default.MEMCACHE["dead_timeout"])

def get_memcache_connect_timeout():
    memcache = get_memcache()

    return get_default(memcache.get("connect_timeout"), overlord.default.MEMCACHE["connect_timeout"])

def get_memcache_timeout():
    memcache = get_memcache()

    return get_default(memcache.get("timeout"), overlord.default.MEMCACHE["timeout"])

def get_memcache_no_delay():
    memcache = get_memcache()

    return get_default(memcache.get("no_delay"), overlord.default.MEMCACHE["no_delay"])

def get_memcache_id():
    memcache = get_memcache()

    return get_default(memcache.get("id"), overlord.default.MEMCACHE["id"])

def get_secret_key():
    return get_default(CONFIG.get("secret_key"), overlord.default.SECRET_KEY)

def get_log_config():
    return get_default(CONFIG.get("log_config"), overlord.default.LOG_CONFIG)

def get_chains():
    return get_default(CONFIG.get("chains"), overlord.default.CHAINS)

def list_chains():
    return list(get_chains().keys())

def get_chain(chain):
    return get_chains().get(chain)

def get_chain_entrypoint(chain):
    chain_conf = get_chain(chain)

    if chain_conf is None:
        return

    entrypoint = chain_conf.get("entrypoint")

    return entrypoint

def get_chain_access_token(chain):
    chain_conf = get_chain(chain)

    if chain_conf is None:
        return

    access_token = chain_conf.get("access_token")

    return access_token

def get_chain_timeout(chain):
    chain_conf = get_chain(chain)

    if chain_conf is None:
        return

    timeout = get_default(chain_conf.get("timeout"), overlord.default.CHAIN_TIMEOUT)

    if timeout < 0:
        timeout = None

    elif timeout == 0:
        pass # ignore

    return timeout

def get_chain_read_timeout(chain):
    chain_conf = get_chain(chain)

    if chain_conf is None:
        return

    read_timeout = get_default(chain_conf.get("read_timeout"), overlord.default.CHAIN_READ_TIMEOUT)

    if read_timeout < 0:
        read_timeout = None

    elif read_timeout == 0:
        pass # ignore

    return read_timeout

def get_chain_write_timeout(chain):
    chain_conf = get_chain(chain)

    if chain_conf is None:
        return

    write_timeout = get_default(chain_conf.get("write_timeout"), overlord.default.CHAIN_WRITE_TIMEOUT)

    if write_timeout < 0:
        write_timeout = None

    elif write_timeout == 0:
        pass # ignore

    return write_timeout

def get_chain_connect_timeout(chain):
    chain_conf = get_chain(chain)

    if chain_conf is None:
        return

    connect_timeout = get_default(chain_conf.get("connect_timeout"), overlord.default.CHAIN_CONNECT_TIMEOUT)

    if connect_timeout < 0:
        connect_timeout = None

    elif connect_timeout == 0:
        pass # ignore

    return connect_timeout

def get_chain_pool_timeout(chain):
    chain_conf = get_chain(chain)

    if chain_conf is None:
        return

    pool_timeout = get_default(chain_conf.get("pool_timeout"), overlord.default.CHAIN_POOL_TIMEOUT)

    if pool_timeout < 0:
        pool_timeout = None

    elif pool_timeout == 0:
        pass # ignore

    return pool_timeout

def get_chain_max_keepalive_connections(chain):
    chain_conf = get_chain(chain)

    if chain_conf is None:
        return

    max_keepalive_connections = get_default(chain_conf.get("max_keepalive_connections"), overlord.default.CHAIN_MAX_KEEPALIVE_CONNECTIONS)

    return max_keepalive_connections

def get_chain_max_connections(chain):
    chain_conf = get_chain(chain)

    if chain_conf is None:
        return

    max_connections = get_default(chain_conf.get("max_connections"), overlord.default.CHAIN_MAX_CONNECTIONS)

    return max_connections

def get_chain_keepalive_expiry(chain):
    chain_conf = get_chain(chain)

    if chain_conf is None:
        return

    keepalive_expiry = get_default(chain_conf.get("keepalive_expiry"), overlord.default.CHAIN_KEEPALIVE_EXPIRY)

    return keepalive_expiry

def get_dataplaneapi():
    return get_default(CONFIG.get("dataplaneapi"), {})

def get_dataplaneapi_serverid():
    dataplaneapi = get_dataplaneapi()

    return dataplaneapi.get("serverid")

def get_dataplaneapi_entrypoint():
    dataplaneapi = get_dataplaneapi()

    return dataplaneapi.get("entrypoint")

def get_dataplaneapi_auth():
    dataplaneapi = get_dataplaneapi()

    return get_default(dataplaneapi.get("auth"), {})

def get_dataplaneapi_auth_username():
    auth = get_dataplaneapi_auth()

    return auth.get("username")

def get_dataplaneapi_auth_password():
    auth = get_dataplaneapi_auth()

    return auth.get("password")

def get_dataplaneapi_timeout():
    dataplaneapi = get_dataplaneapi()

    timeout = get_default(dataplaneapi.get("timeout"), overlord.default.CHAIN_TIMEOUT)

    if timeout < 0:
        timeout = None

    elif timeout == 0:
        pass # ignore

    return timeout

def get_dataplaneapi_read_timeout():
    dataplaneapi = get_dataplaneapi()

    read_timeout = get_default(dataplaneapi.get("read_timeout"), overlord.default.CHAIN_READ_TIMEOUT)

    if read_timeout < 0:
        read_timeout = None

    elif read_timeout == 0:
        pass # ignore

    return read_timeout

def get_dataplaneapi_write_timeout():
    dataplaneapi = get_dataplaneapi()

    write_timeout = get_default(dataplaneapi.get("write_timeout"), overlord.default.CHAIN_WRITE_TIMEOUT)

    if write_timeout < 0:
        write_timeout = None

    elif write_timeout == 0:
        pass # ignore

    return write_timeout

def get_dataplaneapi_connect_timeout():
    dataplaneapi = get_dataplaneapi()

    connect_timeout = get_default(dataplaneapi.get("connect_timeout"), overlord.default.CHAIN_CONNECT_TIMEOUT)

    if connect_timeout < 0:
        connect_timeout = None

    elif connect_timeout == 0:
        pass # ignore

    return connect_timeout

def get_dataplaneapi_pool_timeout():
    dataplaneapi = get_dataplaneapi()

    pool_timeout = get_default(dataplaneapi.get("pool_timeout"), overlord.default.CHAIN_POOL_TIMEOUT)

    if pool_timeout < 0:
        pool_timeout = None

    elif pool_timeout == 0:
        pass # ignore

    return pool_timeout

def get_dataplaneapi_max_keepalive_connections():
    dataplaneapi = get_dataplaneapi()

    max_keepalive_connections = get_default(dataplaneapi.get("max_keepalive_connections"), overlord.default.CHAIN_MAX_KEEPALIVE_CONNECTIONS)

    return max_keepalive_connections

def get_dataplaneapi_max_connections():
    dataplaneapi = get_dataplaneapi()

    max_connections = get_default(dataplaneapi.get("max_connections"), overlord.default.CHAIN_MAX_CONNECTIONS)

    return max_connections

def get_dataplaneapi_keepalive_expiry():
    dataplaneapi = get_dataplaneapi()

    keepalive_expiry = get_default(dataplaneapi.get("keepalive_expiry"), overlord.default.CHAIN_KEEPALIVE_EXPIRY)

    return keepalive_expiry

def get_skydns():
    return get_default(CONFIG.get("skydns"), overlord.default.SKYDNS)

def get_skydns_serverid():
    skydns = get_skydns()

    return skydns.get("serverid")

def get_skydns_path():
    skydns = get_skydns()

    return get_default(skydns.get("path"), overlord.default.SKYDNS["path"])

def get_skydns_zone():
    skydns = get_skydns()

    return get_default(skydns.get("zone"), overlord.default.SKYDNS["zone"])

def get_etcd():
    return get_default(CONFIG.get("etcd"), overlord.default.ETCD)

def list_etcd_hosts():
    etcd = get_etcd()

    return list(etcd)

def get_etcd_host(host):
    etcd = get_etcd()

    return etcd.get(host)

def get_etcd_port(host):
    etcd_host = get_etcd_host(host)

    if etcd_host is None:
        return

    return get_default(etcd_host.get("port"), overlord.default.ETCD_PORT)

def get_etcd_protocol(host):
    etcd_host = get_etcd_host(host)
    
    if etcd_host is None:
        return

    return get_default(etcd_host.get("protocol"), overlord.default.ETCD_PROTOCOL)

def get_etcd_ca_cert(host):
    etcd_host = get_etcd_host(host)

    if etcd_host is None:
        return

    return etcd_host.get("ca_cert")

def get_etcd_cert_key(host):
    etcd_host = get_etcd_host(host)

    if etcd_host is None:
        return

    return etcd_host.get("cert_key")

def get_etcd_timeout(host):
    etcd_host = get_etcd_host(host)

    if etcd_host is None:
        return

    return etcd_host.get("timeout")

def get_etcd_api_path(host):
    etcd_host = get_etcd_host(host)

    if etcd_host is None:
        return

    return etcd_host.get("api_path")

def get_max_watch_projects():
    return get_default(CONFIG.get("max_watch_projects"), overlord.default.CPU_COUNT)

def get_metadata():
    return get_default(CONFIG.get("metadata"), {})

def get_metadata_location():
    metadata = get_metadata()

    return get_default(metadata.get("location"), overlord.default.METADATA["location"])

def get_metadata_size():
    metadata = get_metadata()

    return get_default(metadata.get("size"), overlord.default.METADATA["size"])

def validate(document):
    if not isinstance(document, dict):
        raise overlord.exceptions.InvalidSpec("The configuration is invalid.")

    keys = (
        "port",
        "debug",
        "compress_response",
        "polling",
        "memcache",
        "secret_key",
        "log_config",
        "chains",
        "labels",
        "director",
        "appjail",
        "beanstalkd_addr",
        "execution_time",
        "dataplaneapi",
        "skydns",
        "etcd",
        "max_watch_projects",
        "metadata"
    )

    for key in document:
        if key not in keys:
            raise overlord.exceptions.InvalidSpec(f"{key}: this key is invalid.")

    validate_port(document)
    validate_debug(document)
    validate_compress_response(document)
    validate_polling(document)
    validate_memcache(document)
    validate_secret_key(document)
    validate_log_config(document)
    validate_chains(document)
    validate_labels(document)
    validate_director(document)
    validate_appjail(document)
    validate_beanstalkd_addr(document)
    validate_execution_time(document)
    validate_dataplaneapi(document)
    validate_skydns(document)
    validate_etcd(document)
    validate_max_watch_projects(document)
    validate_metadata(document)

def validate_metadata(document):
    metadata = document.get("metadata")

    if metadata is None:
        return

    if not isinstance(metadata, dict):
        raise overlord.exceptions.InvalidSpec("'metadata' is invalid.")

    keys = (
        "location",
        "size"
    )

    for key in metadata.keys():
        if key not in keys:
            raise overlord.exceptions.InvalidSpec(f"metadata.{key}: this key is invalid.")

    validate_metadata_location(metadata)
    validate_metadata_size(metadata)

def validate_metadata_size(document):
    size = document.get("size")

    if size is None:
        return

    if not isinstance(size, int):
        raise overlord.exceptions.InvalidSpec(f"{size}: invalid value type for 'metadata.size'")

    if size < overlord.default.METADATA_MAX_SIZE:
        raise ValueError(f"{size}: invalid value for 'metadata.size'")

def validate_metadata_location(document):
    location = document.get("location")

    if location is None:
        return

    if not isinstance(location, str):
        raise overlord.exceptions.InvalidSpec(f"{location}: invalid value type for 'metadata.location'")

def validate_max_watch_projects(document):
    max_watch_projects = document.get("max_watch_projects")

    if max_watch_projects is None:
        return

    if not isinstance(max_watch_projects, int):
        raise overlord.exceptions.InvalidSpec(f"{max_watch_projects}: invalid value type for 'max_watch_projects'")

    if max_watch_projects <= 0:
        raise ValueError(f"{max_watch_projects}: invalid value for 'max_watch_projects'.")

def validate_etcd(document):
    etcd = document.get("etcd")

    if etcd is None:
        return

    if not isinstance(etcd, dict):
        raise overlord.exceptions.InvalidSpec("'etcd' is invalid.")

    for index, host in enumerate(etcd):
        if not isinstance(host, str):
            raise overlord.exceptions.InvalidSpec(f"{host}: invalid value type for 'etcd.{index}'")

        validate_etcd_host(etcd, host)

def validate_etcd_host(etcd, host):
    if not isinstance(etcd[host], dict):
        raise overlord.exceptions.InvalidSpec(f"'etcd.{host}' is invalid.")

    keys = (
        "port",
        "protocol",
        "ca_cert",
        "cert_key",
        "timeout",
        "api_path"
    )

    for key in etcd[host]:
        if key not in keys:
            raise overlord.exceptions.InvalidSpec(f"etcd.{host}.{key}: this key is invalid.")

    validate_etcd_port(etcd, host)
    validate_etcd_protocol(etcd, host)
    validate_etcd_ca_cert(etcd, host)
    validate_etcd_cert_key(etcd, host)
    validate_etcd_timeout(etcd, host)
    validate_etcd_api_path(etcd, host)

def validate_etcd_port(etcd, host):
    port = etcd[host].get("port")

    if port is None:
        return

    if not isinstance(port, int):
        raise overlord.exceptions.InvalidSpec(f"{port}: invalid value type for 'etcd.{host}.port'")

    if port < 0 or port > 65535:
        raise ValueError(f"{port}: invalid port.")

def validate_etcd_protocol(etcd, host):
    protocol = etcd[host].get("protocol")

    if protocol is None:
        return

    if not isinstance(protocol, str):
        raise overlord.exceptions.InvalidSpec(f"{protocol}: invalid value type for 'etcd.{host}.protocol'")

def validate_etcd_ca_cert(etcd, host):
    ca_cert = etcd[host].get("ca_cert")

    if ca_cert is None:
        return

    if not isinstance(ca_cert, str):
        raise overlord.exceptions.InvalidSpec(f"{ca_cert}: invalid value type for 'etcd.{host}.ca_cert'")

def validate_etcd_cert_key(etcd, host):
    cert_key = etcd[host].get("cert_key")

    if cert_key is None:
        return

    if not isinstance(cert_key, str):
        raise overlord.exceptions.InvalidSpec(f"{cert_key}: invalid value type for 'etcd.{host}.cert_key'")

def validate_etcd_timeout(etcd, host):
    timeout = etcd[host].get("timeout")

    if timeout is None:
        return

    if not isinstance(timeout, int):
        raise overlord.exceptions.InvalidSpec(f"{timeout}: invalid value type for 'etcd.{host}.timeout'")

def validate_etcd_api_path(etcd, host):
    api_path = etcd[host].get("api_path")

    if api_path is None:
        return

    if not isinstance(api_path, str):
        raise overlord.exceptions.InvalidSpec(f"{api_path}: invalid value type for 'etcd.{host}.api_path'")

def validate_skydns(document):
    skydns = document.get("skydns")

    if skydns is None:
        return

    if not isinstance(skydns, dict):
        raise overlord.exceptions.InvalidSpec("'skydns' is invalid.")

    keys = (
        "serverid",
        "path",
        "zone"
    )

    for key in skydns:
        if key not in keys:
            raise overlord.exceptions.InvalidSpec(f"skydns.{key}: this key is invalid.")

    validate_skydns_serverid(skydns)
    validate_skydns_path(skydns)
    validate_skydns_zone(skydns)

def validate_skydns_serverid(document):
    serverid = document.get("serverid")

    if serverid is None:
        raise overlord.exceptions.InvalidSpec("'skydns.serverid' is required but hasn't been specified.")

    if not isinstance(serverid, str):
        raise overlord.exceptions.InvalidSpec(f"{serverid}: invalid value type for 'skydns.serverid'")

    match = re.match(r"^[a-zA-Z_-][a-zA-Z\d_-]+$", serverid)

    if not match:
        raise overlord.exceptions.InvalidSpec(f"{serverid}: invalid server ID for 'skydns.serverid'")

    serverid = serverid[match.start():match.end()]
    serverid = serverid.lower()

    document["serverid"] = serverid

def validate_skydns_path(document):
    path = document.get("path")

    if path is None:
        return

    if not isinstance(path, str):
        raise overlord.exceptions.InvalidSpec(f"{path}: invalid value type for 'skydns.path'")

def validate_skydns_zone(document):
    zone = document.get("zone")

    if zone is None:
        return

    if not isinstance(zone, str):
        raise overlord.exceptions.InvalidSpec(f"{zone}: invalid value type for 'skydns.zone'")

def validate_dataplaneapi(document):
    dataplaneapi = document.get("dataplaneapi")

    if dataplaneapi is None:
        return

    if not isinstance(dataplaneapi, dict):
        raise overlord.exceptions.InvalidSpec("'dataplaneapi' is invalid.")

    keys = (
        "serverid",
        "entrypoint",
        "auth",
        "timeout",
        "read_timeout",
        "write_timeout",
        "connect_timeout",
        "pool_timeout",
        "max_keepalive_connections",
        "max_connections",
        "keepalive_expiry"
    )

    for key in dataplaneapi:
        if key not in keys:
            raise overlord.exceptions.InvalidSpec(f"dataplaneapi.{key}: this key is invalid.")

    validate_dataplaneapi_serverid(dataplaneapi)
    validate_dataplaneapi_entrypoint(dataplaneapi)
    validate_dataplaneapi_auth(dataplaneapi)
    validate_dataplaneapi_timeout(dataplaneapi)
    validate_dataplaneapi_read_timeout(dataplaneapi)
    validate_dataplaneapi_write_timeout(dataplaneapi)
    validate_dataplaneapi_connect_timeout(dataplaneapi)
    validate_dataplaneapi_pool_timeout(dataplaneapi)
    validate_dataplaneapi_max_keepalive_connections(dataplaneapi)
    validate_dataplaneapi_max_connections(dataplaneapi)
    validate_dataplaneapi_keepalive_expiry(dataplaneapi)

def validate_dataplaneapi_serverid(document):
    serverid = document.get("serverid")

    if serverid is None:
        raise overlord.exceptions.InvalidSpec("'dataplaneapi.serverid' is required but hasn't been specified.")

    if not isinstance(serverid, str):
        raise overlord.exceptions.InvalidSpec(f"{serverid}: invalid value type for 'dataplaneapi.serverid'")

def validate_dataplaneapi_entrypoint(document):
    entrypoint = document.get("entrypoint")

    if entrypoint is None:
        raise overlord.exceptions.InvalidSpec("'dataplaneapi.entrypoint' is required but hasn't been specified.")

    if not isinstance(entrypoint, str):
        raise overlord.exceptions.InvalidSpec(f"{entrypoint}: invalid value type for 'dataplaneapi.entrypoint'")

def validate_dataplaneapi_auth(document):
    auth = document.get("auth")

    if auth is None:
        raise overlord.exceptions.InvalidSpec("'dataplaneapi.auth' is required but hasn't been specified.")

    if not isinstance(auth, dict):
        raise overlord.exceptions.InvalidSpec("'dataplaneapi.auth' is invalid.")

    keys = (
        "username",
        "password"
    )

    for key in auth:
        if key not in keys:
            raise overlord.exceptions.InvalidSpec(f"dataplaneapi.auth.{key}: this key is invalid.")

    validate_dataplaneapi_auth_username(auth)
    validate_dataplaneapi_auth_password(auth)

def validate_dataplaneapi_auth_username(document):
    username = document.get("username")

    if username is None:
        raise overlord.exceptions.InvalidSpec("'dataplaneapi.auth.username' is required but hasn't been specified.")

    if not isinstance(username, str):
        raise overlord.exceptions.InvalidSpec(f"{username}: invalid value type for 'dataplaneapi.auth.username'")

def validate_dataplaneapi_auth_password(document):
    password = document.get("password")

    if password is None:
        raise overlord.exceptions.InvalidSpec("'dataplaneapi.auth.password' is required but hasn't been specified.")

    if not isinstance(password, str):
        raise overlord.exceptions.InvalidSpec(f"{password}: invalid value type for 'dataplaneapi.auth.password'")

def validate_dataplaneapi_timeout(document):
    timeout = document.get("timeout")

    if timeout is None:
        return

    if not isinstance(timeout, int):
        raise overlord.exceptions.InvalidSpec(f"{timeout}: invalid value type for 'dataplaneapi.timeout'")

def validate_dataplaneapi_read_timeout(document):
    read_timeout = document.get("read_timeout")

    if read_timeout is None:
        return

    if not isinstance(read_timeout, int):
        raise overlord.exceptions.InvalidSpec(f"{read_timeout}: invalid value type for 'dataplaneapi.read_timeout'")

def validate_dataplaneapi_write_timeout(document):
    write_timeout = document.get("write_timeout")

    if write_timeout is None:
        return

    if not isinstance(write_timeout, int):
        raise overlord.exceptions.InvalidSpec(f"{write_timeout}: invalid value type for 'dataplaneapi.write_timeout'")

def validate_dataplaneapi_connect_timeout(document):
    connect_timeout = document.get("connect_timeout")

    if connect_timeout is None:
        return

    if not isinstance(connect_timeout, int):
        raise overlord.exceptions.InvalidSpec(f"{connect_timeout}: invalid value type for 'dataplaneapi.connect_timeout'")

def validate_dataplaneapi_pool_timeout(document):
    pool_timeout = document.get("pool_timeout")

    if pool_timeout is None:
        return

    if not isinstance(pool_timeout, int):
        raise overlord.exceptions.InvalidSpec(f"{pool_timeout}: invalid value type for 'dataplaneapi.pool_timeout'")

def validate_dataplaneapi_max_keepalive_connections(document):
    max_keepalive_connections = document.get("max_keepalive_connections")

    if max_keepalive_connections is None:
        return

    if not isinstance(max_keepalive_connections, int):
        raise overlord.exceptions.InvalidSpec(f"{max_keepalive_connections}: invalid value type for 'dataplaneapi.max_keepalive_connections'")

def validate_dataplaneapi_max_connections(document):
    max_connections = document.get("max_connections")

    if max_connections is None:
        return

    if not isinstance(max_connections, int):
        raise overlord.exceptions.InvalidSpec(f"{max_connections}: invalid value type for 'dataplaneapi.max_connections'")

def validate_dataplaneapi_keepalive_expiry(document):
    keepalive_expiry = document.get("keepalive_expiry")

    if keepalive_expiry is None:
        return

    if not isinstance(keepalive_expiry, int):
        raise overlord.exceptions.InvalidSpec(f"{keepalive_expiry}: invalid value type for 'dataplaneapi.keepalive_expiry'")

def validate_execution_time(document):
    execution_time = document.get("execution_time")

    if execution_time is None:
        return

    if not isinstance(execution_time, int):
        raise overlord.exceptions.InvalidSpec(f"{execution_time}: invalid value type for 'execution_time'")

def validate_beanstalkd_addr(document):
    beanstalkd_addr = document.get("beanstalkd_addr")

    if beanstalkd_addr is None:
        return

    if not isinstance(beanstalkd_addr, str):
        raise overlord.exceptions.InvalidSpec(f"{beanstalkd_addr}: invalid value type for 'beanstalkd_addr'")

    parsed = beanstalkd_addr.split(":", 1)

    if len(parsed) == 1:
        addr = (parsed, 11300)

    else:
        if parsed[0] == "unix":
            addr = parsed[1]

        else:
            addr = (parsed[0], int(parsed[1]))

    document["beanstalkd_addr"] = addr

def validate_director(document):
    director = document.get("director")

    if director is None:
        return

    if not isinstance(director, dict):
        raise overlord.exceptions.InvalidSpec("'director' is invalid.")

    keys = (
        "logs"
    )

    for key in director.keys():
        if key not in keys:
            raise overlord.exceptions.InvalidSpec(f"director.{key}: this key is invalid.")

    validate_director_logs(director)

def validate_director_logs(document):
    logs = document.get("logs")

    if logs is None:
        return

    if not isinstance(logs, str):
        raise overlord.exceptions.InvalidSpec(f"{logs}: invalid value type for 'director.logs'")

def validate_appjail(document):
    appjail = document.get("appjail")

    if appjail is None:
        return

    if not isinstance(appjail, dict):
        raise overlord.exceptions.InvalidSpec("'appjail' is invalid.")

    keys = (
        "logs"
    )

    for key in appjail.keys():
        if key not in keys:
            raise overlord.exceptions.InvalidSpec(f"appjail.{key}: this key is invalid.")

    validate_appjail_logs(appjail)

def validate_appjail_logs(document):
    logs = document.get("logs")

    if logs is None:
        return

    if not isinstance(logs, str):
        raise overlord.exceptions.InvalidSpec(f"{logs}: invalid value type for 'appjail.logs'")

def validate_port(document):
    port = document.get("port")

    if port is None:
        return

    if not isinstance(port, int):
        raise overlord.exceptions.InvalidSpec(f"{port}: invalid value type for 'port'")

    if port < 0 or port > 65535:
        raise ValueError(f"{port}: invalid port.")

def validate_debug(document):
    debug = document.get("debug")

    if debug is None:
        return

    if not isinstance(debug, bool):
        raise overlord.exceptions.InvalidSpec(f"{debug}: invalid value type for 'debug'")

def validate_compress_response(document):
    compress_response = document.get("compress_response")

    if compress_response is None:
        return

    if not isinstance(compress_response, bool):
        raise overlord.exceptions.InvalidSpec(f"{compress_response}: invalid value type for 'compress_response'")

def validate_polling(document):
    polling = document.get("polling")

    if polling is None:
        return

    if not isinstance(polling, dict):
        raise overlord.exceptions.InvalidSpec("'polling' is invalid.")

    keys = (
        "jail_stats",
        "jail_info",
        "projects",
        "jails",
        "jail_extras",
        "project_info",
        "skew",
        "keywords"
    )

    for key in polling.keys():
        if key not in keys:
            raise overlord.exceptions.InvalidSpec(f"polling.{key}: this key is invalid.")

    validate_polling_jail_stats(polling)
    validate_polling_jail_info(polling)
    validate_polling_projects(polling)
    validate_polling_jails(polling)
    validate_polling_jail_extras(polling)
    validate_polling_project_info(polling)
    validate_polling_skew(polling)
    validate_polling_keywords(polling)

def validate_polling_jail_stats(document):
    interval = document.get("jail_stats")

    if interval is None:
        return

    if not isinstance(interval, int):
        raise overlord.exceptions.InvalidSpec(f"{interval}: invalid value type for 'polling.stats'")

    if interval < 0:
        raise ValueError(f"{interval}: invalid value for 'polling.stats'")

def validate_polling_jail_info(document):
    interval = document.get("jail_info")

    if interval is None:
        return

    if not isinstance(interval, int):
        raise overlord.exceptions.InvalidSpec(f"{interval}: invalid value type for 'polling.info'")

    if interval < 0:
        raise ValueError(f"{interval}: invalid value for 'polling.info'")

def validate_polling_projects(document):
    interval = document.get("projects")

    if interval is None:
        return

    if not isinstance(interval, int):
        raise overlord.exceptions.InvalidSpec(f"{interval}: invalid value type for 'polling.projects'")

    if interval < 0:
        raise ValueError(f"{interval}: invalid value for 'polling.projects'")

def validate_polling_jails(document):
    interval = document.get("jails")

    if interval is None:
        return

    if not isinstance(interval, int):
        raise overlord.exceptions.InvalidSpec(f"{interval}: invalid value type for 'polling.jails'")

    if interval < 0:
        raise ValueError(f"{interval}: invalid value for 'polling.jails'")

def validate_polling_jail_extras(document):
    interval = document.get("jail_extras")

    if interval is None:
        return

    if not isinstance(interval, int):
        raise overlord.exceptions.InvalidSpec(f"{interval}: invalid value type for 'polling.jail_extras'")

    if interval < 0:
        raise ValueError(f"{interval}: invalid value for 'polling.jail_extras'")

def validate_polling_project_info(document):
    interval = document.get("project_info")

    if interval is None:
        return

    if not isinstance(interval, int):
        raise overlord.exceptions.InvalidSpec(f"{interval}: invalid value type for 'polling.project_info'")

    if interval < 0:
        raise ValueError(f"{interval}: invalid value for 'polling.project_info'")

def validate_polling_skew(document):
    skew = document.get("skew")

    if skew is None:
        return

    if not isinstance(skew, list):
        raise overlord.exceptions.InvalidSpec(f"{skew}: invalid value type for 'polling.skew'")

    if len(skew) != 2:
        raise overlord.exceptions.InvalidSpec(f"{skew}: invalid value length for 'polling.skew'")

    begin = skew[0]

    if not isinstance(begin, int) \
            or begin < 0:
        raise overlord.exceptions.InvalidSpec(f"{skew}: invalid value for 'polling.skew.0'")

    end = skew[1]

    if not isinstance(end, int) \
            or end < 0:
        raise overlord.exceptions.InvalidSpec(f"{skew}: invalid value for 'polling.skew.1'")

    if begin > end:
        raise overlord.exceptions.InvalidSpec(f"{skew}: 'polling.skew.1' must be greater than 'polling.skew.0'")

def validate_polling_keywords(document):
    keywords = document.get("keywords")

    if keywords is None:
        return

    if not isinstance(keywords, dict):
        raise overlord.exceptions.InvalidSpec("'polling.keywords' is invalid.")

    keys = (
        "jail",
        "stats",
        "devfs",
        "expose",
        "healthcheck",
        "label",
        "limits",
        "nat",
        "volume",
        "fstab"
    )

    for key in keywords.keys():
        if key not in keys:
            raise overlord.exceptions.InvalidSpec(f"polling.keywords.{key}: this key is invalid.")

    validate_polling_keywords_jail(keywords)
    validate_polling_keywords_stats(keywords)
    validate_polling_keywords_devfs(keywords)
    validate_polling_keywords_expose(keywords)
    validate_polling_keywords_healthcheck(keywords)
    validate_polling_keywords_label(keywords)
    validate_polling_keywords_limits(keywords)
    validate_polling_keywords_nat(keywords)
    validate_polling_keywords_volume(keywords)
    validate_polling_keywords_fstab(keywords)

def validate_polling_keywords_jail(document):
    jail = document.get("jail")

    if jail is None:
        return

    if not isinstance(jail, list):
        raise overlord.exceptions.InvalidSpec("'polling.keywords.jail' is invalid.")

    for index, entry in enumerate(jail):
        if not isinstance(entry, str):
            raise overlord.exceptions.InvalidSpec(f"{entry}: invalid value type for 'polling.keywords.jail.{index}'")

    keys = overlord.default.POLLING["keywords"]["jail"]

    for key in jail:
        if key not in keys:
            raise overlord.exceptions.InvalidSpec(f"polling.keywords.jail.{key}: this key is invalid.")

def validate_polling_keywords_stats(document):
    stats = document.get("stats")

    if stats is None:
        return

    if not isinstance(stats, list):
        raise overlord.exceptions.InvalidSpec("'polling.keywords.stats' is invalid.")

    for index, entry in enumerate(stats):
        if not isinstance(entry, str):
            raise overlord.exceptions.InvalidSpec(f"{entry}: invalid value type for 'polling.keywords.stats.{index}'")

    keys = overlord.default.POLLING["keywords"]["stats"]

    for key in stats:
        if key not in keys:
            raise overlord.exceptions.InvalidSpec(f"polling.keywords.stats.{key}: this key is invalid.")

def validate_polling_keywords_devfs(document):
    devfs = document.get("devfs")

    if devfs is None:
        return

    if not isinstance(devfs, list):
        raise overlord.exceptions.InvalidSpec("'polling.keywords.devfs' is invalid.")

    for index, entry in enumerate(devfs):
        if not isinstance(entry, str):
            raise overlord.exceptions.InvalidSpec(f"{entry}: invalid value type for 'polling.keywords.devfs.{index}'")

    keys = overlord.default.POLLING["keywords"]["devfs"]

    for key in devfs:
        if key not in keys:
            raise overlord.exceptions.InvalidSpec(f"polling.keywords.devfs.{key}: this key is invalid.")

def validate_polling_keywords_expose(document):
    expose = document.get("expose")

    if expose is None:
        return

    if not isinstance(expose, list):
        raise overlord.exceptions.InvalidSpec("'polling.keywords.expose' is invalid.")

    for index, entry in enumerate(expose):
        if not isinstance(entry, str):
            raise overlord.exceptions.InvalidSpec(f"{entry}: invalid value type for 'polling.keywords.expose.{index}'")

    keys = overlord.default.POLLING["keywords"]["expose"]

    for key in expose:
        if key not in keys:
            raise overlord.exceptions.InvalidSpec(f"polling.keywords.expose.{key}: this key is invalid.")

def validate_polling_keywords_healthcheck(document):
    healthcheck = document.get("healthcheck")

    if healthcheck is None:
        return

    if not isinstance(healthcheck, list):
        raise overlord.exceptions.InvalidSpec("'polling.keywords.healthcheck' is invalid.")

    for index, entry in enumerate(healthcheck):
        if not isinstance(entry, str):
            raise overlord.exceptions.InvalidSpec(f"{entry}: invalid value type for 'polling.keywords.healthcheck.{index}'")

    keys = overlord.default.POLLING["keywords"]["healthcheck"]

    for key in healthcheck:
        if key not in keys:
            raise overlord.exceptions.InvalidSpec(f"polling.keywords.healthcheck.{key}: this key is invalid.")

def validate_polling_keywords_label(document):
    label = document.get("label")

    if label is None:
        return

    if not isinstance(label, list):
        raise overlord.exceptions.InvalidSpec("'polling.keywords.label' is invalid.")

    for index, entry in enumerate(label):
        if not isinstance(entry, str):
            raise overlord.exceptions.InvalidSpec(f"{entry}: invalid value type for 'polling.keywords.label.{index}'")

    keys = overlord.default.POLLING["keywords"]["label"]

    for key in label:
        if key not in keys:
            raise overlord.exceptions.InvalidSpec(f"polling.keywords.label.{key}: this key is invalid.")

def validate_polling_keywords_limits(document):
    limits = document.get("limits")

    if limits is None:
        return

    if not isinstance(limits, list):
        raise overlord.exceptions.InvalidSpec("'polling.keywords.limits' is invalid.")

    for index, entry in enumerate(limits):
        if not isinstance(entry, str):
            raise overlord.exceptions.InvalidSpec(f"{entry}: invalid value type for 'polling.keywords.limits.{index}'")

    keys = overlord.default.POLLING["keywords"]["limits"]

    for key in limits:
        if key not in keys:
            raise overlord.exceptions.InvalidSpec(f"polling.keywords.limits.{key}: this key is invalid.")

def validate_polling_keywords_nat(document):
    nat = document.get("nat")

    if nat is None:
        return

    if not isinstance(nat, list):
        raise overlord.exceptions.InvalidSpec("'polling.keywords.nat' is invalid.")

    for index, entry in enumerate(nat):
        if not isinstance(entry, str):
            raise overlord.exceptions.InvalidSpec(f"{entry}: invalid value type for 'polling.keywords.nat.{index}'")

    keys = overlord.default.POLLING["keywords"]["nat"]

    for key in nat:
        if key not in keys:
            raise overlord.exceptions.InvalidSpec(f"polling.keywords.nat.{key}: this key is invalid.")

def validate_polling_keywords_volume(document):
    volume = document.get("volume")

    if volume is None:
        return

    if not isinstance(volume, list):
        raise overlord.exceptions.InvalidSpec("'polling.keywords.volume' is invalid.")

    for index, entry in enumerate(volume):
        if not isinstance(entry, str):
            raise overlord.exceptions.InvalidSpec(f"{entry}: invalid value type for 'polling.keywords.volume.{index}'")

    keys = overlord.default.POLLING["keywords"]["volume"]

    for key in volume:
        if key not in keys:
            raise overlord.exceptions.InvalidSpec(f"polling.keywords.volume.{key}: this key is invalid.")

def validate_polling_keywords_fstab(document):
    fstab = document.get("fstab")

    if fstab is None:
        return

    if not isinstance(fstab, list):
        raise overlord.exceptions.InvalidSpec("'polling.keywords.fstab' is invalid.")

    for index, entry in enumerate(fstab):
        if not isinstance(entry, str):
            raise overlord.exceptions.InvalidSpec(f"'polling.keywords.fstab.{index}'")

    keys = overlord.default.POLLING["keywords"]["fstab"]

    for key in fstab:
        if key not in keys:
            raise overlord.exceptions.InvalidSpec(f"polling.keywords.fstab.{key}: this key is invalid.")

def validate_memcache(document):
    memcache = document.get("memcache")

    if memcache is None:
        return

    if not isinstance(memcache, dict):
        raise overlord.exception.InvalidSpec("'memcache' is invalid.")

    keys = (
        "connections",
        "max_pool_size",
        "pool_idle_timeout",
        "retry_attempts",
        "retry_timeout",
        "dead_timeout",
        "connect_timeout",
        "timeout",
        "no_delay",
        "id"
    )

    for key in memcache:
        if key not in keys:
            raise overlord.exceptions.InvalidSpec(f"{key}: this key is invalid.")

    validate_memcache_connections(memcache)
    validate_memcache_max_pool_size(memcache)
    validate_memcache_pool_idle_timeout(memcache)
    validate_memcache_retry_attempts(memcache)
    validate_memcache_retry_timeout(memcache)
    validate_memcache_dead_timeout(memcache)
    validate_memcache_connect_timeout(memcache)
    validate_memcache_timeout(memcache)
    validate_memcache_no_delay(memcache)
    validate_memcache_id(memcache)

def validate_memcache_no_delay(document):
    no_delay = document.get("no_delay")

    if no_delay is None:
        return

    if not isinstance(no_delay, bool):
        raise overlord.exceptions.InvalidSpec(f"{no_delay}: invalid value type for 'memcache.no_delay'")

def validate_memcache_timeout(document):
    timeout = document.get("timeout")

    if timeout is None:
        return

    if not isinstance(timeout, int) \
            or timeout < 1:
        raise overlord.exceptions.InvalidSpec(f"{timeout}: invalid value type for 'memcache.timeout'")

def validate_memcache_connect_timeout(document):
    connect_timeout = document.get("connect_timeout")

    if connect_timeout is None:
        return

    if not isinstance(connect_timeout, int) \
            or connect_timeout < 1:
        raise overlord.exceptions.InvalidSpec(f"{connect_timeout}: invalid value type for 'memcache.connect_timeout'")

def validate_memcache_dead_timeout(document):
    dead_timeout = document.get("dead_timeout")

    if dead_timeout is None:
        return

    if not isinstance(dead_timeout, int) \
            or dead_timeout < 1:
        raise overlord.exceptions.InvalidSpec(f"{dead_timeout}: invalid value type for 'memcache.dead_timeout'")

def validate_memcache_retry_timeout(document):
    retry_timeout = document.get("retry_timeout")

    if retry_timeout is None:
        return

    if not isinstance(retry_timeout, int) \
            or retry_timeout < 1:
        raise overlord.exceptions.InvalidSpec(f"{retry_timeout}: invalid value type for 'memcache.retry_timeout'")

def validate_memcache_retry_attempts(document):
    retry_attempts = document.get("retry_attempts")

    if retry_attempts is None:
        return

    if not isinstance(retry_attempts, int) \
            or retry_attempts < 1:
        raise overlord.exceptions.InvalidSpec(f"{retry_attempts}: invalid value type for 'memcache.retry_attempts'")

def validate_memcache_pool_idle_timeout(document):
    pool_idle_timeout = document.get("pool_idle_timeout")

    if pool_idle_timeout is None:
        return

    if not isinstance(pool_idle_timeout, int) \
            or pool_idle_timeout < 0:
        raise overlord.exceptions.InvalidSpec(f"{pool_idle_timeout}: invalid value type for 'memcache.pool_idle_timeout'")

def validate_memcache_max_pool_size(document):
    max_pool_size = document.get("max_pool_size")

    if max_pool_size is None:
        return

    if not isinstance(max_pool_size, int) \
            or max_pool_size < 1:
        raise overlord.exceptions.InvalidSpec(f"{max_pool_size}: invalid value type for 'memcache.max_pool_size'")

def validate_memcache_connections(document):
    connections = document.get("connections")

    if connections is None:
        return

    if not isinstance(connections, list):
        raise overlord.exceptions.InvalidSpec("'memcache.connections' is invalid.")

    for index, connection in enumerate(connections):
        if not isinstance(connection, str):
            raise overlord.exceptions.InvalidSpec(f"{connection}: invalid value type for 'memcache.connections.{index}'")

def validate_memcache_id(document):
    id = document.get("id")

    if id is None:
        return

    if not isinstance(id, str):
        raise overlord.exceptions.InvalidSpec(f"{id}: invalid value type for 'memcache.id'")

def validate_secret_key(document):
    secret_key = document.get("secret_key")

    if secret_key is None:
        return

    if not isinstance(secret_key, str):
        raise overlord.exceptions.InvalidSpec(f"{secret_key}: invalid value type for 'secret_key'")

def validate_log_config(document):
    log_config = document.get("log_config")

    if log_config is None:
        return

    if not isinstance(log_config, dict):
        raise overlord.exceptions.InvalidSpec("'log_config' is invalid.")

    logging.config.dictConfig(log_config)

def validate_chains(document):
    chains = document.get("chains")

    if chains is None:
        return

    if not isinstance(chains, dict):
        raise overlord.exceptions.InvalidSpec("'chains' is invalid.")

    for index, chain in enumerate(chains):
        if not isinstance(chain, str):
            raise overlord.exceptions.InvalidSpec(f"{chain}: invalid value type for 'chains.{index}'")

        if not overlord.chains.check_chain_name(chain):
            raise overlord.exceptions.InvalidSpec(f"'chains.{chain}': chain name is invalid.")

        validate_chain(chains, chain)

def validate_chain(chains, chain):
    if not isinstance(chains[chain], dict):
        raise overlord.exceptions.InvalidSpec(f"'chains.{chain}' is invalid.")

    keys = (
        "entrypoint",
        "access_token",
        "timeout",
        "read_timeout",
        "write_timeout",
        "connect_timeout",
        "pool_timeout",
        "max_keepalive_connections",
        "max_connections",
        "keepalive_expiry"
    )

    for key in chains[chain]:
        if key not in keys:
            raise overlord.exceptions.InvalidSpec(f"chains.{chain}.{key}: this key is invalid.")

    validate_chain_entrypoint(chains, chain)
    validate_chain_access_token(chains, chain)
    validate_chain_timeout(chains, chain)
    validate_chain_read_timeout(chains, chain)
    validate_chain_write_timeout(chains, chain)
    validate_chain_connect_timeout(chains, chain)
    validate_chain_pool_timeout(chains, chain)
    validate_chain_max_keepalive_connections(chains, chain)
    validate_chain_max_connections(chains, chain)
    validate_chain_keepalive_expiry(chains, chain)

def validate_chain_entrypoint(chains, chain):
    entrypoint = chains[chain].get("entrypoint")

    if entrypoint is None:
        raise overlord.exceptions.InvalidSpec(f"'chains.{chain}.entrypoint' is required but hasn't been specified.")

    if not isinstance(entrypoint, str):
        raise overlord.exceptions.InvalidSpec(f"{entrypoint}: invalid value type for 'chains.{chain}.entrypoint'")

def validate_chain_access_token(chains, chain):
    access_token = chains[chain].get("access_token")

    if access_token is None:
        raise overlord.exceptions.InvalidSpec(f"'chains.{chain}.access_token' is required but hasn't been specified.")

    if not isinstance(access_token, str):
        raise overlord.exceptions.InvalidSpec(f"{access_token}: invalid value type for 'chains.{chain}.access_token'")

def validate_chain_timeout(chains, chain):
    timeout = chains[chain].get("timeout")

    if timeout is None:
        return

    if not isinstance(timeout, int):
        raise overlord.exceptions.InvalidSpec(f"{timeout}: invalid value type for 'chains.{chain}.timeout'")

def validate_chain_read_timeout(chains, chain):
    read_timeout = chains[chain].get("read_timeout")

    if read_timeout is None:
        return

    if not isinstance(read_timeout, int):
        raise overlord.exceptions.InvalidSpec(f"{read_timeout}: invalid value type for 'chains.{chain}.read_timeout'")

def validate_chain_write_timeout(chains, chain):
    write_timeout = chains[chain].get("write_timeout")

    if write_timeout is None:
        return

    if not isinstance(write_timeout, int):
        raise overlord.exceptions.InvalidSpec(f"{write_timeout}: invalid value type for 'chains.{chain}.write_timeout'")

def validate_chain_connect_timeout(chains, chain):
    connect_timeout = chains[chain].get("connect_timeout")

    if connect_timeout is None:
        return

    if not isinstance(connect_timeout, int):
        raise overlord.exceptions.InvalidSpec(f"{connect_timeout}: invalid value type for 'chains.{chain}.connect_timeout'")

def validate_chain_pool_timeout(chains, chain):
    pool_timeout = chains[chain].get("pool_timeout")

    if pool_timeout is None:
        return

    if not isinstance(pool_timeout, int):
        raise overlord.exceptions.InvalidSpec(f"{pool_timeout}: invalid value type for 'chains.{chain}.pool_timeout'")

def validate_chain_max_keepalive_connections(chains, chain):
    max_keepalive_connections = chains[chain].get("max_keepalive_connections")

    if max_keepalive_connections is None:
        return

    if not isinstance(max_keepalive_connections, int):
        raise overlord.exceptions.InvalidSpec(f"{max_keepalive_connections}: invalid value type for 'chains.{chain}.max_keepalive_connections'")

def validate_chain_max_connections(chains, chain):
    max_connections = chains[chain].get("max_connections")

    if max_connections is None:
        return

    if not isinstance(max_connections, int):
        raise overlord.exceptions.InvalidSpec(f"{max_connections}: invalid value type for 'chains.{chain}.max_connections'")

def validate_chain_keepalive_expiry(chains, chain):
    keepalive_expiry = chains[chain].get("keepalive_expiry")

    if keepalive_expiry is None:
        return

    if not isinstance(keepalive_expiry, int):
        raise overlord.exceptions.InvalidSpec(f"{keepalive_expiry}: invalid value type for 'chains.{chain}.keepalive_expiry'")

def validate_labels(document):
    labels = document.get("labels")

    if labels is None:
        return

    if not isinstance(labels, list):
        raise overlord.exceptions.InvalidSpec("'labels' is invalid.")

    for index, entry in enumerate(labels):
        if not isinstance(entry, str):
            raise overlord.exceptions.InvalidSpec(f"{entry}: invalid value type for 'labels.{index}'")

        if not overlord.chains.check_chain_label(entry):
            raise overlord.exceptions.InvalidSpec(f"'labels.{index}.{entry}': invalid label.")

    length = len(labels)

    if length < 1:
        raise overlord.exceptions.InvalidSpec("'labels': at least one label must be specified.")
