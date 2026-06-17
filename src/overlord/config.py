# BSD 3-Clause License
#
# Copyright (c) 2025-2026, Jesús Daniel Colmenares Oviedo <DtxdF@disroot.org>
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
import overlord.error
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
        "serverid" : get_serverid(),
        "port" : get_port(),
        "tls" : {
            "keyfile" : get_tls_keyfile(),
            "certfile" : get_tls_certfile(),
            "port" : get_tls_port()
        },
        "debug" : get_debug(),
        "compress_response" : get_compress_response(),
        "polling" : {
            "adaptive" : {
                "poll_window" : get_polling_adaptive_poll_window(),
                "max_idle" : get_polling_adaptive_max_idle(),
                "idle_penalty" : get_polling_adaptive_idle_penalty(),
                "max_idle_penalty" : get_polling_adaptive_max_idle_penalty()
            },
            "jail_stats" : get_polling_jail_stats(),
            "jail_info" : get_polling_jail_info(),
            "projects" : get_polling_projects(),
            "jails" : get_polling_jails(),
            "jail_extras" : get_polling_jail_extras(),
            "project_info" : get_polling_project_info(),
            "autoscale" : get_polling_autoscale(),
            "heartbeat" : get_polling_heartbeat(),
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
            "no_delay" : get_memcache_no_delay()
        },
        "secret_key" : get_secret_key(),
        "secret_keyfile" : get_secret_keyfile(),
        "log_config" : get_log_config(),
        "chains" : {},
        "labels" : get_labels(),
        "director" : {
            "logs" : get_director_logs()
        },
        "appjail" : {
            "jails" : get_appjail_jails(),
            "logs" : get_appjail_logs(),
            "images" : get_appjail_images()
        },
        "beanstalkd_addr" : get_beanstalkd_addr(),
        "beanstalkd_secret" : get_beanstalkd_secret(),
        "execution_time" : get_execution_time(),
        "dataplaneapi" : {
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
            "keepalive_expiry" : get_dataplaneapi_keepalive_expiry(),
            "cacert" : get_dataplaneapi_cacert()
        },
        "haproxy_stats" : {
            "entrypoint" : get_haproxy_stats_entrypoint(),
            "auth" : {
                "username" : get_haproxy_stats_auth_username(),
                "password" : get_haproxy_stats_auth_password()
            },
            "timeout" : get_haproxy_stats_timeout(),
            "read_timeout" : get_haproxy_stats_read_timeout(),
            "write_timeout" : get_haproxy_stats_write_timeout(),
            "connect_timeout" : get_haproxy_stats_connect_timeout(),
            "pool_timeout" : get_haproxy_stats_pool_timeout(),
            "max_keepalive_connections" : get_haproxy_stats_max_keepalive_connections(),
            "max_connections" : get_haproxy_stats_max_connections(),
            "keepalive_expiry" : get_haproxy_stats_keepalive_expiry(),
            "cacert" : get_haproxy_stats_cacert()
        },
        "skydns" : {
            "path" : get_skydns_path(),
            "zone" : get_skydns_zone()
        },
        "etcd" : {},
        "max_watch_commands" : get_max_watch_commands(),
        "metadata" : {
            "location" : get_metadata_location(),
            "size" : get_metadata_size(),
            "namespaces" : get_namespaces()
        },
        "components" : get_components(),
        "autodisable" : {
            "enabled" : get_autodisable_enabled(),
            "failures" : get_autodisable_failures(),
            "interval" : get_autodisable_interval(),
            "increase" : get_autodisable_increase(),
            "max-increase" : get_autodisable_max_increase(),
            "strict" : get_autodisable_strict()
        },
        "max_autoscale_logs" : get_max_autoscale_logs(),
        "autoscale_logs_expire_time" : get_autoscale_logs_expire_time()
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
            "keepalive_expiry" : get_chain_keepalive_expiry(chain),
            "disable" : get_chain_disable(chain),
            "cacert" : get_chain_cacert(chain),
            "retry" : {
                "total" : get_chain_retry_total(chain),
                "max_backoff_wait" : get_chain_retry_max_backoff_wait(chain),
                "backoff_factor" : get_chain_retry_backoff_factor(chain),
                "respect_retry_after_header" : get_chain_retry_respect_retry_after_header(chain),
                "backoff_jitter" : get_chain_retry_backoff_jitter(chain)
            }
        }

    return config

def get_default(value, default=None):
    if value is None:
        return default

    return value

def get_autoscale_logs_expire_time():
    return get_default(CONFIG.get("autoscale_logs_expire_time"), overlord.default.AUTOSCALE_LOGS_EXPIRE_TIME)

def get_max_autoscale_logs():
    return get_default(CONFIG.get("max_autoscale_logs"), overlord.default.MAX_AUTOSCALE_LOGS)

def get_autodisable():
    return get_default(CONFIG.get("autodisable"), overlord.default.AUTODISABLE)

def get_autodisable_enabled():
    autodisable = get_autodisable()

    return get_default(autodisable.get("enabled"), overlord.default.AUTODISABLE["enabled"])

def get_autodisable_failures():
    autodisable = get_autodisable()

    return get_default(autodisable.get("failures"), overlord.default.AUTODISABLE["failures"])

def get_autodisable_interval():
    autodisable = get_autodisable()

    return get_default(autodisable.get("interval"), overlord.default.AUTODISABLE["interval"])

def get_autodisable_increase():
    autodisable = get_autodisable()

    return get_default(autodisable.get("increase"), overlord.default.AUTODISABLE["increase"])

def get_autodisable_max_increase():
    autodisable = get_autodisable()

    return get_default(autodisable.get("max-increase"), overlord.default.AUTODISABLE["max-increase"])

def get_autodisable_strict():
    autodisable = get_autodisable()

    return get_default(autodisable.get("strict"), overlord.default.AUTODISABLE["strict"])

def get_components():
    return CONFIG.get("components", overlord.default.COMPONENTS)

def get_serverid():
    return CONFIG.get("serverid", overlord.default.SERVERID)

def get_execution_time():
    return CONFIG.get("execution_time", overlord.default.EXECUTION_TIME)

def get_beanstalkd_addr():
    return get_default(CONFIG.get("beanstalkd_addr"), overlord.default.BEANSTALKD_ADDR)

def get_beanstalkd_secret():
    return get_default(CONFIG.get("beanstalkd_secret"), overlord.default.BEANSTALKD_SECRET)

def get_director():
    return get_default(CONFIG.get("director"), overlord.default.DIRECTOR)

def get_director_logs():
    director = get_director()

    return get_default(director.get("logs"), overlord.default.DIRECTOR["logs"])

def get_appjail():
    return get_default(CONFIG.get("appjail"), overlord.default.APPJAIL)

def get_appjail_jails():
    appjail = get_appjail()

    return get_default(appjail.get("jails"), overlord.default.APPJAIL["jails"])

def get_appjail_logs():
    appjail = get_appjail()

    return get_default(appjail.get("logs"), overlord.default.APPJAIL["logs"])

def get_appjail_images():
    appjail = get_appjail()

    return get_default(appjail.get("images"), overlord.default.APPJAIL["images"])

def get_labels():
    return get_default(CONFIG.get("labels"), overlord.default.LABELS)

def get_port():
    return get_default(CONFIG.get("port"), overlord.default.PORT)

def get_tls():
    return get_default(CONFIG.get("tls"), overlord.default.TLS)

def get_tls_keyfile():
    tls = get_tls()

    keyfile = tls.get("keyfile")

    return keyfile

def get_tls_certfile():
    tls = get_tls()

    certfile = tls.get("certfile")

    return certfile

def get_tls_port():
    tls = get_tls()

    port = get_default(tls.get("port"), overlord.default.TLS["port"])

    return port

def get_debug():
    return get_default(CONFIG.get("debug"), overlord.default.DEBUG)

def get_compress_response():
    return get_default(CONFIG.get("compress_response"), overlord.default.COMPRESS_RESPONSE)

def get_polling():
    return get_default(CONFIG.get("polling"), overlord.default.POLLING)

def get_polling_adaptive():
    polling = get_polling()

    return get_default(polling.get("adaptive"), overlord.default.POLLING["adaptive"])

def get_polling_adaptive_poll_window():
    polling_adaptive = get_polling_adaptive()

    return get_default(polling_adaptive.get("poll_window"), overlord.default.POLLING["adaptive"]["poll_window"])

def get_polling_adaptive_max_idle():
    polling_adaptive = get_polling_adaptive()

    return get_default(polling_adaptive.get("max_idle"), overlord.default.POLLING["adaptive"]["max_idle"])

def get_polling_adaptive_idle_penalty():
    polling_adaptive = get_polling_adaptive()

    return get_default(polling_adaptive.get("idle_penalty"), overlord.default.POLLING["adaptive"]["idle_penalty"])

def get_polling_adaptive_max_idle_penalty():
    polling_adaptive = get_polling_adaptive()

    return get_default(polling_adaptive.get("max_idle_penalty"), overlord.default.POLLING["adaptive"]["max_idle_penalty"])

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

def get_polling_autoscale():
    polling = get_polling()

    return get_default(polling.get("autoscale"), overlord.default.POLLING["autoscale"])

def get_polling_heartbeat():
    polling = get_polling()

    return get_default(polling.get("heartbeat"), overlord.default.POLLING["heartbeat"])

def get_polling_skew():
    polling = get_polling()

    return get_default(polling.get("skew"), overlord.default.POLLING["skew"])

def get_polling_keywords():
    polling = get_polling()

    return get_default(polling.get("keywords"), overlord.default.VALID_KEYWORDS)

def get_polling_keywords_stats():
    polling_keywords = get_polling_keywords()

    return get_default(polling_keywords.get("stats"), overlord.default.VALID_KEYWORDS["stats"])

def get_polling_keywords_jail():
    polling_keywords = get_polling_keywords()

    return get_default(polling_keywords.get("jail"), overlord.default.VALID_KEYWORDS["jail"])

def get_polling_keywords_devfs():
    polling_keywords = get_polling_keywords()

    return get_default(polling_keywords.get("devfs"), overlord.default.VALID_KEYWORDS["devfs"])

def get_polling_keywords_expose():
    polling_keywords = get_polling_keywords()

    return get_default(polling_keywords.get("expose"), overlord.default.VALID_KEYWORDS["expose"])

def get_polling_keywords_healthcheck():
    polling_keywords = get_polling_keywords()

    return get_default(polling_keywords.get("healthcheck"), overlord.default.VALID_KEYWORDS["healthcheck"])

def get_polling_keywords_label():
    polling_keywords = get_polling_keywords()

    return get_default(polling_keywords.get("label"), overlord.default.VALID_KEYWORDS["label"])

def get_polling_keywords_limits():
    polling_keywords = get_polling_keywords()

    return get_default(polling_keywords.get("limits"), overlord.default.VALID_KEYWORDS["limits"])

def get_polling_keywords_nat():
    polling_keywords = get_polling_keywords()

    return get_default(polling_keywords.get("nat"), overlord.default.VALID_KEYWORDS["nat"])

def get_polling_keywords_volume():
    polling_keywords = get_polling_keywords()

    return get_default(polling_keywords.get("volume"), overlord.default.VALID_KEYWORDS["volume"])

def get_polling_keywords_fstab():
    polling_keywords = get_polling_keywords()

    return get_default(polling_keywords.get("fstab"), overlord.default.VALID_KEYWORDS["fstab"])

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

def get_secret_key():
    return get_default(CONFIG.get("secret_key"), overlord.default.SECRET_KEY)

def get_secret_keyfile():
    return get_default(CONFIG.get("secret_keyfile"), overlord.default.SECRET_KEYFILE)

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

def get_chain_disable(chain):
    chain_conf = get_chain(chain)

    if chain_conf is None:
        return

    disable = get_default(chain_conf.get("disable"), overlord.default.CHAIN_DISABLE)

    return disable

def get_chain_cacert(chain):
    chain_conf = get_chain(chain)

    if chain_conf is None:
        return

    cacert = chain_conf.get("cacert")

    return cacert

def get_chain_retry(chain):
    chain_conf = get_chain(chain)

    if chain_conf is None:
        return

    retry_conf = get_default(chain_conf.get("retry"), overlord.default.RETRY_POLICY)

    return retry_conf

def get_chain_retry_total(chain):
    retry_conf = get_chain_retry(chain)

    if retry_conf is None:
        return

    total = get_default(retry_conf.get("total"), overlord.default.RETRY_POLICY["total"])

    return total

def get_chain_retry_max_backoff_wait(chain):
    retry_conf = get_chain_retry(chain)

    if retry_conf is None:
        return

    max_backoff_wait = get_default(retry_conf.get("max_backoff_wait"), overlord.default.RETRY_POLICY["max_backoff_wait"])

    return max_backoff_wait

def get_chain_retry_backoff_factor(chain):
    retry_conf = get_chain_retry(chain)

    if retry_conf is None:
        return

    backoff_factor = get_default(retry_conf.get("backoff_factor"), overlord.default.RETRY_POLICY["backoff_factor"])

    return backoff_factor

def get_chain_retry_respect_retry_after_header(chain):
    retry_conf = get_chain_retry(chain)

    if retry_conf is None:
        return

    respect_retry_after_header = get_default(retry_conf.get("respect_retry_after_header"), overlord.default.RETRY_POLICY["respect_retry_after_header"])

    return respect_retry_after_header

def get_chain_retry_backoff_jitter(chain):
    retry_conf = get_chain_retry(chain)

    if retry_conf is None:
        return

    backoff_jitter = get_default(retry_conf.get("backoff_jitter"), overlord.default.RETRY_POLICY["backoff_jitter"])

    return backoff_jitter

def get_dataplaneapi():
    return get_default(CONFIG.get("dataplaneapi"), {})

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

    timeout = get_default(dataplaneapi.get("timeout"), overlord.default.DATAPLANEAPI_TIMEOUT)

    if timeout < 0:
        timeout = None

    elif timeout == 0:
        pass # ignore

    return timeout

def get_dataplaneapi_read_timeout():
    dataplaneapi = get_dataplaneapi()

    read_timeout = get_default(dataplaneapi.get("read_timeout"), overlord.default.DATAPLANEAPI_READ_TIMEOUT)

    if read_timeout < 0:
        read_timeout = None

    elif read_timeout == 0:
        pass # ignore

    return read_timeout

def get_dataplaneapi_write_timeout():
    dataplaneapi = get_dataplaneapi()

    write_timeout = get_default(dataplaneapi.get("write_timeout"), overlord.default.DATAPLANEAPI_WRITE_TIMEOUT)

    if write_timeout < 0:
        write_timeout = None

    elif write_timeout == 0:
        pass # ignore

    return write_timeout

def get_dataplaneapi_connect_timeout():
    dataplaneapi = get_dataplaneapi()

    connect_timeout = get_default(dataplaneapi.get("connect_timeout"), overlord.default.DATAPLANEAPI_CONNECT_TIMEOUT)

    if connect_timeout < 0:
        connect_timeout = None

    elif connect_timeout == 0:
        pass # ignore

    return connect_timeout

def get_dataplaneapi_pool_timeout():
    dataplaneapi = get_dataplaneapi()

    pool_timeout = get_default(dataplaneapi.get("pool_timeout"), overlord.default.DATAPLANEAPI_POOL_TIMEOUT)

    if pool_timeout < 0:
        pool_timeout = None

    elif pool_timeout == 0:
        pass # ignore

    return pool_timeout

def get_dataplaneapi_max_keepalive_connections():
    dataplaneapi = get_dataplaneapi()

    max_keepalive_connections = get_default(dataplaneapi.get("max_keepalive_connections"), overlord.default.DATAPLANEAPI_MAX_KEEPALIVE_CONNECTIONS)

    return max_keepalive_connections

def get_dataplaneapi_max_connections():
    dataplaneapi = get_dataplaneapi()

    max_connections = get_default(dataplaneapi.get("max_connections"), overlord.default.DATAPLANEAPI_MAX_CONNECTIONS)

    return max_connections

def get_dataplaneapi_keepalive_expiry():
    dataplaneapi = get_dataplaneapi()

    keepalive_expiry = get_default(dataplaneapi.get("keepalive_expiry"), overlord.default.DATAPLANEAPI_KEEPALIVE_EXPIRY)

    return keepalive_expiry

def get_dataplaneapi_cacert():
    dataplaneapi = get_dataplaneapi()

    cacert = dataplaneapi.get("cacert")

    return cacert

def get_haproxy_stats():
    return get_default(CONFIG.get("haproxy_stats"), {})

def get_haproxy_stats_entrypoint():
    haproxy_stats = get_haproxy_stats()

    return haproxy_stats.get("entrypoint")

def get_haproxy_stats_auth():
    haproxy_stats = get_haproxy_stats()

    return get_default(haproxy_stats.get("auth"), {})

def get_haproxy_stats_auth_username():
    auth = get_haproxy_stats_auth()

    return auth.get("username")

def get_haproxy_stats_auth_password():
    auth = get_haproxy_stats_auth()

    return auth.get("password")

def get_haproxy_stats_timeout():
    haproxy_stats = get_haproxy_stats()

    timeout = get_default(haproxy_stats.get("timeout"), overlord.default.DATAPLANEAPI_TIMEOUT)

    if timeout < 0:
        timeout = None

    elif timeout == 0:
        pass # ignore

    return timeout

def get_haproxy_stats_read_timeout():
    haproxy_stats = get_haproxy_stats()

    read_timeout = get_default(haproxy_stats.get("read_timeout"), overlord.default.DATAPLANEAPI_READ_TIMEOUT)

    if read_timeout < 0:
        read_timeout = None

    elif read_timeout == 0:
        pass # ignore

    return read_timeout

def get_haproxy_stats_write_timeout():
    haproxy_stats = get_haproxy_stats()

    write_timeout = get_default(haproxy_stats.get("write_timeout"), overlord.default.DATAPLANEAPI_WRITE_TIMEOUT)

    if write_timeout < 0:
        write_timeout = None

    elif write_timeout == 0:
        pass # ignore

    return write_timeout

def get_haproxy_stats_connect_timeout():
    haproxy_stats = get_haproxy_stats()

    connect_timeout = get_default(haproxy_stats.get("connect_timeout"), overlord.default.DATAPLANEAPI_CONNECT_TIMEOUT)

    if connect_timeout < 0:
        connect_timeout = None

    elif connect_timeout == 0:
        pass # ignore

    return connect_timeout

def get_haproxy_stats_pool_timeout():
    haproxy_stats = get_haproxy_stats()

    pool_timeout = get_default(haproxy_stats.get("pool_timeout"), overlord.default.DATAPLANEAPI_POOL_TIMEOUT)

    if pool_timeout < 0:
        pool_timeout = None

    elif pool_timeout == 0:
        pass # ignore

    return pool_timeout

def get_haproxy_stats_max_keepalive_connections():
    haproxy_stats = get_haproxy_stats()

    max_keepalive_connections = get_default(haproxy_stats.get("max_keepalive_connections"), overlord.default.DATAPLANEAPI_MAX_KEEPALIVE_CONNECTIONS)

    return max_keepalive_connections

def get_haproxy_stats_max_connections():
    haproxy_stats = get_haproxy_stats()

    max_connections = get_default(haproxy_stats.get("max_connections"), overlord.default.DATAPLANEAPI_MAX_CONNECTIONS)

    return max_connections

def get_haproxy_stats_keepalive_expiry():
    haproxy_stats = get_haproxy_stats()

    keepalive_expiry = get_default(haproxy_stats.get("keepalive_expiry"), overlord.default.DATAPLANEAPI_KEEPALIVE_EXPIRY)

    return keepalive_expiry

def get_haproxy_stats_cacert():
    haproxy_stats = get_haproxy_stats()

    cacert = haproxy_stats.get("cacert")

    return cacert

def get_skydns():
    return get_default(CONFIG.get("skydns"), overlord.default.SKYDNS)

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

def get_max_watch_commands():
    return get_default(CONFIG.get("max_watch_commands"), overlord.default.CPU_COUNT)

def get_metadata():
    return get_default(CONFIG.get("metadata"), {})

def get_metadata_location():
    metadata = get_metadata()

    return get_default(metadata.get("location"), overlord.default.METADATA["location"])

def get_metadata_size():
    metadata = get_metadata()

    return get_default(metadata.get("size"), overlord.default.METADATA["size"])

def get_namespaces():
    metadata = get_metadata()

    return get_default(metadata.get("namespaces"), overlord.default.METADATA["namespaces"])

def validate(document):
    _name = "<root>"
    overlord.error.assert_type(_name, document, dict)

    keys = (
        "serverid",
        "port",
        "tls",
        "debug",
        "compress_response",
        "polling",
        "memcache",
        "secret_key",
        "secret_keyfile",
        "log_config",
        "chains",
        "labels",
        "director",
        "appjail",
        "beanstalkd_addr",
        "beanstalkd_secret",
        "execution_time",
        "dataplaneapi",
        "haproxy_stats",
        "skydns",
        "etcd",
        "max_watch_commands",
        "metadata",
        "components",
        "autodisable",
        "max_autoscale_logs",
        "autoscale_logs_expire_time"
    )

    overlord.error.assert_parameter(_name, document, keys)

    validate_serverid(document)
    validate_port(document)
    validate_tls(document)
    validate_debug(document)
    validate_compress_response(document)
    validate_polling(document)
    validate_memcache(document)
    validate_secret_key(document)
    validate_secret_keyfile(document)
    validate_log_config(document)
    validate_chains(document)
    validate_labels(document)
    validate_director(document)
    validate_appjail(document)
    validate_beanstalkd_addr(document)
    validate_beanstalkd_secret(document)
    validate_execution_time(document)
    validate_dataplaneapi(document)
    validate_haproxy_stats(document)
    validate_skydns(document)
    validate_etcd(document)
    validate_max_watch_commands(document)
    validate_metadata(document)
    validate_components(document)
    validate_autodisable(document)
    validate_max_autoscale_logs(document)
    validate_autoscale_logs_expire_time(document)

def validate_autoscale_logs_expire_time(document):
    overlord.error._validate1(document, "", "autoscale_logs_expire_time", int, lambda v: v >= 1, ">= 1")

def validate_max_autoscale_logs(document):
    overlord.error._validate1(document, "", "max_autoscale_log", int, lambda v: v >= 1, ">= 1")

def validate_autodisable(document):
    keys = (
        "enabled",
        "failures",
        "interval",
        "increase",
        "max-increase",
        "strict"
    )

    _value = overlord.error._validate2(document, "", "autodisable", keys)
    
    if _value is None:
        return

    validate_autodisable_enabled(_value)
    validate_autodisable_failures(_value)
    validate_autodisable_interval(_value)
    validate_autodisable_increase(_value)
    validate_autodisable_max_increase(_value)
    validate_autodisable_strict(_value)

def validate_autodisable_strict(document):
    overlord.error._validate1(document, "autodisable.", "strict", bool)

def validate_autodisable_max_increase(document):
    overlord.error._validate1(document, "autodisable.", "max_increase", int, lambda v: v >= 1, ">= 1")

def validate_autodisable_increase(document):
    overlord.error._validate1(document, "autodisable.", "increase", int, lambda v: v >= 1, ">= 1")

def validate_autodisable_interval(document):
    overlord.error._validate1(document, "autodisable.", "interval", int, lambda v: v >= 1, ">= 1")

def validate_autodisable_failures(document):
    overlord.error._validate1(document, "autodisable.", "failures", int, lambda v: v >= 1, ">= 1")

def validate_autodisable_enabled(document):
    overlord.error._validate1(document, "autodisable.", "enabled", bool)

def validate_components(document):
    overlord.error._validate1(document, "", "components", str)

def validate_serverid(document):
    overlord.error._validate1(document, "", "serverid", str)

def validate_metadata(document):
    keys = (
        "location",
        "size",
        "namespaces"
    )

    _value = overlord.error._validate2(document, "", "metadata", keys)
    
    if _value is None:
        return

    validate_metadata_location(_value)
    validate_metadata_size(_value)
    validate_metadata_namespaces(_value)

def validate_metadata_namespaces(document):
    overlord.error._validate1(document, "metadata.", "namespaces", str)

def validate_metadata_size(document):
    max_size = overlord.default.METADATA_MAX_SIZE
    overlord.error._validate1(document, "metadata.", "size", int, lambda v: v >= max_size, f">= {max_size}")

def validate_metadata_location(document):
    overlord.error._validate1(document, "metadata.", "location", str)

def validate_max_watch_commands(document):
    overlord.error._validate1(document, "", "max_watch_commands", int, lambda v: v > 0, f"> 0")

def validate_etcd(document):
    _value = overlord.error._validate1(document, "", "etcd", dict)

    if _value is None:
        return

    overlord.error.assert_item(_value, validate_etcd_host)

def validate_etcd_host(etcd, host, index):
    overlord.error.assert_type(f"etcd.<item#{index}>", host, str)

    keys = (
        "port",
        "protocol",
        "ca_cert",
        "cert_key",
        "timeout",
        "api_path"
    )

    _value = overlord.error._validate2(etcd, "etcd.", host, keys)

    if _value is None:
        return

    validate_etcd_port(etcd, host)
    validate_etcd_protocol(etcd, host)
    validate_etcd_ca_cert(etcd, host)
    validate_etcd_cert_key(etcd, host)
    validate_etcd_timeout(etcd, host)
    validate_etcd_api_path(etcd, host)

def validate_etcd_port(etcd, host):
    document = etcd[host]
    overlord.error._validate1(document, f"etcd.{host}.", "port", int, lambda v: v > 0 and v < 65536, f"> 0 and < 65536")

def validate_etcd_protocol(etcd, host):
    document = etcd[host]
    overlord.error._validate1(document, f"etcd.{host}.", "protocol", str)

def validate_etcd_ca_cert(etcd, host):
    document = etcd[host]
    overlord.error._validate1(document, f"etcd.{host}.", "ca_cert", str)

def validate_etcd_cert_key(etcd, host):
    document = etcd[host]
    overlord.error._validate1(document, f"etcd.{host}.", "cert_key", str)

def validate_etcd_timeout(etcd, host):
    document = etcd[host]
    overlord.error._validate1(document, f"etcd.{host}.", "timeout", int)

def validate_etcd_api_path(etcd, host):
    document = etcd[host]
    overlord.error._validate1(document, f"etcd.{host}.", "api_path", str)

def validate_skydns(document):
    keys = (
        "path",
        "zone"
    )

    _value = overlord.error._validate2(document, "", "skydns", keys)

    if _value is None:
        return

    validate_skydns_path(_value)
    validate_skydns_zone(_value)

def validate_skydns_path(document):
    overlord.error._validate1(document, "skydns.", "path", str)

def validate_skydns_zone(document):
    overlord.error._validate1(document, "skydns.", "zone", str)

def validate_haproxy_stats(document):
    keys = (
        "entrypoint",
        "auth",
        "timeout",
        "read_timeout",
        "write_timeout",
        "connect_timeout",
        "pool_timeout",
        "max_keepalive_connections",
        "max_connections",
        "keepalive_expiry",
        "cacert"
    )

    _value = overlord.error._validate2(document, "", "haproxy_stats", keys)

    if _value is None:
        return

    validate_haproxy_stats_entrypoint(_value)
    validate_haproxy_stats_auth(_value)
    validate_haproxy_stats_timeout(_value)
    validate_haproxy_stats_read_timeout(_value)
    validate_haproxy_stats_write_timeout(_value)
    validate_haproxy_stats_connect_timeout(_value)
    validate_haproxy_stats_pool_timeout(_value)
    validate_haproxy_stats_max_keepalive_connections(_value)
    validate_haproxy_stats_max_connections(_value)
    validate_haproxy_stats_keepalive_expiry(_value)
    validate_haproxy_stats_cacert(_value)

def validate_haproxy_stats_entrypoint(document):
    overlord.error._validate1(document, "haproxy_stats.", "entrypoint", str, required=True)

def validate_haproxy_stats_auth(document):
    keys = (
        "username",
        "password"
    )

    _value = overlord.error._validate2(document, "haproxy_stats.", "auth", keys, required=True)

    validate_haproxy_stats_auth_username(_value)
    validate_haproxy_stats_auth_password(_value)

def validate_haproxy_stats_auth_username(document):
    overlord.error._validate1(document, "haproxy_stats.auth.", "username", str, required=True)

def validate_haproxy_stats_auth_password(document):
    overlord.error._validate1(document, "haproxy_stats.auth.", "password", str, required=True)

def validate_haproxy_stats_timeout(document):
    overlord.error._validate1(document, "haproxy_stats.", "timeout", int)

def validate_haproxy_stats_read_timeout(document):
    overlord.error._validate1(document, "haproxy_stats.", "read_timeout", int)

def validate_haproxy_stats_write_timeout(document):
    overlord.error._validate1(document, "haproxy_stats.", "write_timeout", int)

def validate_haproxy_stats_connect_timeout(document):
    overlord.error._validate1(document, "haproxy_stats.", "connect_timeout", int)

def validate_haproxy_stats_pool_timeout(document):
    overlord.error._validate1(document, "haproxy_stats.", "pool_timeout", int)

def validate_haproxy_stats_max_keepalive_connections(document):
    overlord.error._validate1(document, "haproxy_stats.", "max_keepalive_connections", int)

def validate_haproxy_stats_max_connections(document):
    overlord.error._validate1(document, "haproxy_stats.", "max_connections", int)

def validate_haproxy_stats_keepalive_expiry(document):
    overlord.error._validate1(document, "haproxy_stats.", "keepalive_expiry", int)

def validate_haproxy_stats_cacert(document):
    overlord.error._validate1(document, "haproxy_stats.", "cacert", str)

def validate_dataplaneapi(document):
    keys = (
        "entrypoint",
        "auth",
        "timeout",
        "read_timeout",
        "write_timeout",
        "connect_timeout",
        "pool_timeout",
        "max_keepalive_connections",
        "max_connections",
        "keepalive_expiry",
        "cacert"
    )

    _value = overlord.error._validate2(document, "", "dataplaneapi", keys)
    
    if _value is None:
        return

    validate_dataplaneapi_entrypoint(_value)
    validate_dataplaneapi_auth(_value)
    validate_dataplaneapi_timeout(_value)
    validate_dataplaneapi_read_timeout(_value)
    validate_dataplaneapi_write_timeout(_value)
    validate_dataplaneapi_connect_timeout(_value)
    validate_dataplaneapi_pool_timeout(_value)
    validate_dataplaneapi_max_keepalive_connections(_value)
    validate_dataplaneapi_max_connections(_value)
    validate_dataplaneapi_keepalive_expiry(_value)
    validate_dataplaneapi_cacert(_value)

def validate_dataplaneapi_entrypoint(document):
    overlord.error._validate1(document, "dataplaneapi.", "entrypoint", str)

def validate_dataplaneapi_auth(document):
    keys = (
        "username",
        "password"
    )

    _value = overlord.error._validate2(document, "dataplaneapi.", "auth", keys, required=True)

    validate_dataplaneapi_auth_username(_value)
    validate_dataplaneapi_auth_password(_value)

def validate_dataplaneapi_auth_username(document):
    overlord.error._validate1(document, "dataplaneapi.auth.", "username", str, required=True)

def validate_dataplaneapi_auth_password(document):
    overlord.error._validate1(document, "dataplaneapi.auth.", "password", str, required=True)

def validate_dataplaneapi_timeout(document):
    overlord.error._validate1(document, "dataplaneapi.", "timeout", int)

def validate_dataplaneapi_read_timeout(document):
    overlord.error._validate1(document, "dataplaneapi.", "read_timeout", int)

def validate_dataplaneapi_write_timeout(document):
    overlord.error._validate1(document, "dataplaneapi.", "write_timeout", int)

def validate_dataplaneapi_connect_timeout(document):
    overlord.error._validate1(document, "dataplaneapi.", "connect_timeout", int)

def validate_dataplaneapi_pool_timeout(document):
    overlord.error._validate1(document, "dataplaneapi.", "pool_timeout", int)

def validate_dataplaneapi_max_keepalive_connections(document):
    overlord.error._validate1(document, "dataplaneapi.", "max_keepalive_connections", int)

def validate_dataplaneapi_max_connections(document):
    overlord.error._validate1(document, "dataplaneapi.", "max_connections", int)

def validate_dataplaneapi_keepalive_expiry(document):
    overlord.error._validate1(document, "dataplaneapi.", "keepalive_expiry", int)

def validate_dataplaneapi_cacert(document):
    overlord.error._validate1(document, "dataplaneapi.", "cacert", str)

def validate_execution_time(document):
    overlord.error._validate1(document, "", "execution_time", int)

def validate_beanstalkd_addr(document):
    beanstalkd_addr = overlord.error._validate1(document, "", "beanstalkd_addr", str)

    if beanstalkd_addr is None:
        return

    parsed = beanstalkd_addr.split(":", 1)

    if len(parsed) == 1:
        addr = (parsed, 11300)

    else:
        if parsed[0] == "unix":
            addr = parsed[1]

        else:
            addr = (parsed[0], int(parsed[1]))

    document["beanstalkd_addr"] = addr

def validate_beanstalkd_secret(document):
    overlord.error._validate1(document, "", "beanstalkd_secret", str)

def validate_director(document):
    keys = (
        "logs"
    )

    _value = overlord.error._validate2(document, "", "director", keys)
    
    if _value is None:
        return

    validate_director_logs(_value)

def validate_director_logs(document):
    overlord.error._validate1(document, "director.", "logs", str)

def validate_appjail(document):
    keys = (
        "jails",
        "logs",
        "images"
    )

    _value = overlord.error._validate2(document, "", "appjail", keys)
    
    if _value is None:
        return

    validate_appjail_logs(_value)
    validate_appjail_images(_value)
    validate_appjail_jails(_value)

def validate_appjail_jails(document):
    overlord.error._validate1(document, "appjail.", "jails", str)

def validate_appjail_images(document):
    overlord.error._validate1(document, "appjail.", "images", str)

def validate_appjail_logs(document):
    overlord.error._validate1(document, "appjail.", "logs", str)

def validate_port(document):
    overlord.error._validate1(document, "", "port", int, lambda v: v > 0 and v < 65536, "> 0 and < 65536")

def validate_tls(document):
    keys = (
        "keyfile",
        "certfile",
        "port"
    )

    _value = overlord.error._validate2(document, "", "tls", keys)
    
    if _value is None:
        return

    overlord.error._validate1(_value, "tls.", "port", int, lambda v: v > 0 and v < 65536, "> 0 and < 65536")

    keyfile = _value.get("keyfile")
    certfile = _value.get("certfile")

    if keyfile is None and certfile is None:
        return

    if keyfile is None and certfile is not None \
            or keyfile is not None and certfile is None:
        raise overlord.exceptions.InvalidSpec("'tls.keyfile' and 'tls.certfile' must be specified at the same time.")

    overlord.error.assert_type("tls.keyfile", keyfile, str)
    overlord.error.assert_type("tls.certfile", certfile, str)

def validate_debug(document):
    overlord.error._validate1(document, "", "debug", bool)

def validate_compress_response(document):
    overlord.error._validate1(document, "", "compress_response", bool)

def validate_polling(document):
    keys = (
        "adaptive",
        "jail_stats",
        "jail_info",
        "projects",
        "jails",
        "jail_extras",
        "project_info",
        "autoscale",
        "heartbeat",
        "skew",
        "keywords"
    )

    _value = overlord.error._validate2(document, "", "polling", keys)

    if _value is None:
        return

    validate_polling_adaptive(_value)
    validate_polling_jail_stats(_value)
    validate_polling_jail_info(_value)
    validate_polling_projects(_value)
    validate_polling_jails(_value)
    validate_polling_jail_extras(_value)
    validate_polling_project_info(_value)
    validate_polling_autoscale(_value)
    validate_polling_heartbeat(_value)
    validate_polling_skew(_value)
    validate_polling_keywords(_value)

def validate_polling_adaptive(document):
    keys = (
        "poll_window",
        "max_idle",
        "idle_penalty",
        "max_idle_penalty"
    )

    _value = overlord.error._validate2(document, "polling.", "adaptive", keys)

    if _value is None:
        return

    validate_polling_adaptive_poll_window(_value)
    validate_polling_adaptive_max_idle(_value)
    validate_polling_adaptive_idle_penalty(_value)
    validate_polling_adaptive_max_idle_penalty(_value)

def validate_polling_adaptive_poll_window(document):
    overlord.error._validate1(document, "polling.adaptive.", "poll_window", int, lambda v: v >= 0, ">= 0")

def validate_polling_adaptive_max_idle(document):
    overlord.error._validate1(document, "polling.adaptive.", "max_idle", int, lambda v: v >= 0, ">= 0")

def validate_polling_adaptive_idle_penalty(document):
    overlord.error._validate1(document, "polling.adaptive.", "idle_penalty", int, lambda v: v >= 0, ">= 0")

def validate_polling_adaptive_max_idle_penalty(document):
    overlord.error._validate1(document, "polling.adaptive.", "max_idle_penalty", int, lambda v: v > 0, "> 0")

def validate_polling_jail_stats(document):
    overlord.error._validate1(document, "polling.", "jail_stats", int, lambda v: v >= 0, ">= 0")

def validate_polling_jail_info(document):
    overlord.error._validate1(document, "polling.", "jail_info", int, lambda v: v >= 0, ">= 0")

def validate_polling_projects(document):
    overlord.error._validate1(document, "polling.", "projects", int, lambda v: v >= 0, ">= 0")

def validate_polling_jails(document):
    overlord.error._validate1(document, "polling.", "jails", int, lambda v: v >= 0, ">= 0")

def validate_polling_jail_extras(document):
    overlord.error._validate1(document, "polling.", "jail_extras", int, lambda v: v >= 0, ">= 0")

def validate_polling_project_info(document):
    overlord.error._validate1(document, "polling.", "project_info", int, lambda v: v >= 0, ">= 0")

def validate_polling_autoscale(document):
    overlord.error._validate1(document, "polling.", "autoscale", int, lambda v: v >= 0, ">= 0")

def validate_polling_heartbeat(document):
    overlord.error._validate1(document, "polling.", "heartbeat", int, lambda v: v >= 0, ">= 0")

def validate_polling_skew(document):
    _prefix = "polling."
    _name = "skew"
    _value = document.get(_name)

    if _value is None:
        return

    overlord.error.assert_type(f"{_prefix}{_name}", _value, list)
    overlord.error.assert_len(f"{_prefix}{_name}", _value, 2)

    begin = _value[0]

    overlord.error.assert_type(f"{_prefix}{_name}.<item#0>", begin, int)
    overlord.error.assert_value(f"{_prefix}{_name}.<item#0>", lambda v: v >= 0, begin, ">= 0")

    end = _value[1]

    overlord.error.assert_type(f"{_prefix}{_name}.<item#1>", end, int)
    overlord.error.assert_value(f"{_prefix}{_name}.<item#1>", lambda v: v >= 0, end, ">= 0")

    if begin > end:
        raise overlord.exceptions.InvalidSpec(f"{_prefix}{_name}: '{_prefix}{_name}.<item#0>' is greater than '{_prefix}{_name}.<item#1>'.")

def validate_polling_keywords(document):
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

    _value = overlord.error._validate2(document, "polling.", "keywords", keys)

    if _value is None:
        return

    validate_polling_keywords_jail(_value)
    validate_polling_keywords_stats(_value)
    validate_polling_keywords_devfs(_value)
    validate_polling_keywords_expose(_value)
    validate_polling_keywords_healthcheck(_value)
    validate_polling_keywords_label(_value)
    validate_polling_keywords_limits(_value)
    validate_polling_keywords_nat(_value)
    validate_polling_keywords_volume(_value)
    validate_polling_keywords_fstab(_value)

def validate_polling_keywords_jail(document):
    keys = overlord.default.VALID_KEYWORDS["jail"]
    overlord.error._validate2(document, "polling.keywords.", "jail", keys, type_=list)

def validate_polling_keywords_stats(document):
    keys = overlord.default.VALID_KEYWORDS["stats"]
    overlord.error._validate2(document, "polling.keywords.", "stats", keys, type_=list)

def validate_polling_keywords_devfs(document):
    keys = overlord.default.VALID_KEYWORDS["devfs"]
    overlord.error._validate2(document, "polling.keywords.", "devfs", keys, type_=list)

def validate_polling_keywords_expose(document):
    keys = overlord.default.VALID_KEYWORDS["expose"]
    overlord.error._validate2(document, "polling.keywords.", "expose", keys, type_=list)

def validate_polling_keywords_healthcheck(document):
    keys = overlord.default.VALID_KEYWORDS["healthcheck"]
    overlord.error._validate2(document, "polling.keywords.", "healthcheck", keys, type_=list)

def validate_polling_keywords_label(document):
    keys = overlord.default.VALID_KEYWORDS["label"]
    overlord.error._validate2(document, "polling.keywords.", "label", keys, type_=list)

def validate_polling_keywords_limits(document):
    keys = overlord.default.VALID_KEYWORDS["limits"]
    overlord.error._validate2(document, "polling.keywords.", "limits", keys, type_=list)

def validate_polling_keywords_nat(document):
    keys = overlord.default.VALID_KEYWORDS["nat"]
    overlord.error._validate2(document, "polling.keywords.", "nat", keys, type_=list)

def validate_polling_keywords_volume(document):
    keys = overlord.default.VALID_KEYWORDS["volume"]
    overlord.error._validate2(document, "polling.keywords.", "volume", keys, type_=list)

def validate_polling_keywords_fstab(document):
    keys = overlord.default.VALID_KEYWORDS["fstab"]
    overlord.error._validate2(document, "polling.keywords.", "fstab", keys, type_=list)

def validate_memcache(document):
    keys = (
        "connections",
        "max_pool_size",
        "pool_idle_timeout",
        "retry_attempts",
        "retry_timeout",
        "dead_timeout",
        "connect_timeout",
        "timeout",
        "no_delay"
    )

    _value = overlord.error._validate2(document, "", "memcache", keys)

    if _value is None:
        return

    validate_memcache_connections(_value)
    validate_memcache_max_pool_size(_value)
    validate_memcache_pool_idle_timeout(_value)
    validate_memcache_retry_attempts(_value)
    validate_memcache_retry_timeout(_value)
    validate_memcache_dead_timeout(_value)
    validate_memcache_connect_timeout(_value)
    validate_memcache_timeout(_value)
    validate_memcache_no_delay(_value)

def validate_memcache_no_delay(document):
    overlord.error._validate1(document, "memcache.", "no_delay", bool)

def validate_memcache_timeout(document):
    overlord.error._validate1(document, "memcache.", "timeout", int, lambda v: v > 0, "> 0")

def validate_memcache_connect_timeout(document):
    overlord.error._validate1(document, "memcache.", "connect_timeout", int, lambda v: v > 0, "> 0")

def validate_memcache_dead_timeout(document):
    overlord.error._validate1(document, "memcache.", "dead_timeout", int, lambda v: v > 0, "> 0")

def validate_memcache_retry_timeout(document):
    overlord.error._validate1(document, "memcache.", "retry_timeout", int, lambda v: v > 0, "> 0")

def validate_memcache_retry_attempts(document):
    overlord.error._validate1(document, "memcache.", "retry_attempts", int, lambda v: v > 0, "> 0")

def validate_memcache_pool_idle_timeout(document):
    overlord.error._validate1(document, "memcache.", "pool_idle_timeout", int, lambda v: v >= 0, ">= 0")

def validate_memcache_max_pool_size(document):
    overlord.error._validate1(document, "memcache.", "max_pool_size", int, lambda v: v > 0, "> 0")

def validate_memcache_connections(document):
    overlord.error._validate2(document, "memcache.", "connections", type_=list)

def validate_secret_key(document):
    overlord.error._validate1(document, "", "secret_key", str)

def validate_secret_keyfile(document):
    overlord.error._validate1(document, "", "secret_keyfile", str)

def validate_log_config(document):
    _value = overlord.error._validate1(document, "", "log_config", dict)
    logging.config.dictConfig(_value)

def validate_chains(document):
    _value = overlord.error._validate1(document, "", "chains", dict)

    if _value is None:
        return

    overlord.error.assert_item(_value, validate_chain)

def validate_chain(chains, chain, index):
    overlord.error.assert_type(f"chains.<item#{index}>", chain, str)
    overlord.error.assert_value(f"chains.<item#{index}>",
        overlord.chains.check_chain_name, chain, overlord.chains.REGEX_CHAIN_NAME)

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
        "keepalive_expiry",
        "disable",
        "cacert",
        "retry"
    )

    _value = overlord.error._validate2(chains, "chains.", chain, keys)

    if _value is None:
        return

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
    validate_chain_disable(chains, chain)
    validate_chain_cacert(chains, chain)
    validate_chain_retry(chains, chain)

def validate_chain_retry(chains, chain):
    document = chains[chain]

    keys = (
        "total",
        "max_backoff_wait",
        "backoff_factor",
        "respect_retry_after_header",
        "backoff_jitter"
    )

    _value = overlord.error._validate2(document, f"chains.{chain}.", "retry", keys)

    if _value is None:
        return

    validate_chain_retry_total(chains, chain)
    validate_chain_retry_max_backoff_wait(chains, chain)
    validate_chain_retry_backoff_factor(chains, chain)
    validate_chain_retry_respect_retry_after_header(chains, chain)
    validate_chain_retry_backoff_jitter(chains, chain)

def validate_chain_retry_total(chains, chain):
    document = chains[chain]["retry"]
    _name = "total"
    _value = document.get(_name)

    if _value is None:
        return

    if isinstance(_value, int):
        _value = float(_value)

    overlord.error.assert_type(f"chains.{chain}.retry.{_name}", _value, float)

def validate_chain_retry_max_backoff_wait(chains, chain):
    document = chains[chain]["retry"]
    _name = "max_backoff_wait"
    _value = document.get(_name)

    if _value is None:
        return

    if isinstance(_value, int):
        _value = float(_value)

    overlord.error.assert_type(f"chains.{chain}.retry.{_name}", _value, float)

def validate_chain_retry_backoff_factor(chains, chain):
    document = chains[chain]["retry"]
    _name = "backoff_factor"
    _value = document.get(_name)

    if _value is None:
        return

    if isinstance(_value, int):
        _value = float(_value)

    overlord.error.assert_type(f"chains.{chain}.retry.{_name}", _value, float)

def validate_chain_retry_backoff_jitter(chains, chain):
    document = chains[chain]["retry"]
    _name = "backoff_jitter"
    _value = document.get(_name)

    if _value is None:
        return

    if isinstance(_value, int):
        _value = float(_value)

    overlord.error.assert_type(f"chains.{chain}.retry.{_name}", _value, float)

def validate_chain_retry_respect_retry_after_header(chains, chain):
    document = chains[chain]["retry"]
    _name = "respect_retry_after_header"
    _value = document.get(_name)

    if _value is None:
        return

    overlord.error.assert_type(f"chains.{chain}.retry.{_name}", _value, bool)

def validate_chain_cacert(chains, chain):
    document = chains[chain]
    overlord.error._validate1(document, f"chains.{chain}.", "cacert", str)

def validate_chain_disable(chains, chain):
    document = chains[chain]
    overlord.error._validate1(document, f"chains.{chain}.", "disable", bool)

def validate_chain_entrypoint(chains, chain):
    document = chains[chain]
    overlord.error._validate1(document, f"chains.{chain}.", "entrypoint", str, required=True)

def validate_chain_access_token(chains, chain):
    document = chains[chain]
    overlord.error._validate1(document, f"chains.{chain}.", "access_token", str, required=True)

def validate_chain_timeout(chains, chain):
    document = chains[chain]
    overlord.error._validate1(document, f"chains.{chain}.", "timeout", int)

def validate_chain_read_timeout(chains, chain):
    document = chains[chain]
    overlord.error._validate1(document, f"chains.{chain}.", "read_timeout", int)

def validate_chain_write_timeout(chains, chain):
    document = chains[chain]
    overlord.error._validate1(document, f"chains.{chain}.", "write_timeout", int)

def validate_chain_connect_timeout(chains, chain):
    document = chains[chain]
    overlord.error._validate1(document, f"chains.{chain}.", "connect_timeout", int)

def validate_chain_pool_timeout(chains, chain):
    document = chains[chain]
    overlord.error._validate1(document, f"chains.{chain}.", "pool_timeout", int)

def validate_chain_max_keepalive_connections(chains, chain):
    document = chains[chain]
    overlord.error._validate1(document, f"chains.{chain}.", "max_keepalive_connections", int)

def validate_chain_max_connections(chains, chain):
    document = chains[chain]
    overlord.error._validate1(document, f"chains.{chain}.", "max_connections", int)

def validate_chain_keepalive_expiry(chains, chain):
    document = chains[chain]
    overlord.error._validate1(document, f"chains.{chain}.", "keepalive_expiry", int)

def validate_labels(document):
    _value = overlord.error._validate1(document, "", "labels", list)

    if _value is None:
        return

    overlord.error.assert_len("labels", _value, -1, lambda l, dl: dl > 0, "> 0")
    overlord.error.assert_item(_value, validate_label)

def validate_label(labels, label, index):
    overlord.error.assert_type(f"labels.<item#{index}>", label, str)
    overlord.error.assert_value(f"labels.<item#{index}>",
        overlord.chains.check_chain_label, label, overlord.chains.REGEX_LABEL)
