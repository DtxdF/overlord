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

import enum
import os

import pyaml_env

import overlord.chains
import overlord.default
import overlord.error
import overlord.exceptions
import overlord.spec.director_project
import overlord.spec.metadata
import overlord.spec.vm_jail
import overlord.spec.app_config

CONFIG = {}

class OverlordKindTypes(enum.Enum):
    PROJECT = "directorProject"
    METADATA = "metadata"
    VMJAIL = "vmJail"
    READONLY = "readOnly"
    APPCONFIG = "appConfig"

def load(file):
    global CONFIG

    file = os.path.realpath(file)

    os.environ["OVERLORD_WRKDIR"] = os.path.dirname(file)
    os.environ["OVERLORD_FILE"] = file

    document = pyaml_env.parse_config(file, default_value="")

    if document is None:
        return

    validate(document)

    CONFIG = document

def get_config():
    kind = get_kind()

    config = {
        "kind" : kind,
        "datacenters" : get_datacenters(),
        "deployIn" : get_deployIn(),
        "maximumDeployments" : get_maximumDeployments()
    }

    if kind == OverlordKindTypes.PROJECT.value:
        config["projectName"] = overlord.spec.director_project.get_projectName()
        config["projectFile"] = overlord.spec.director_project.get_projectFile()
        config["environment"] = overlord.spec.director_project.get_environment()
        config["labelsEnvironment"] = overlord.spec.director_project.get_labelsEnvironment()
        config["chainsEnvironment"] = overlord.spec.director_project.get_chainsEnvironment()
        config["datacentersEnvironment"] = overlord.spec.director_project.get_datacentersEnvironment()
        config["autoScale"] = overlord.spec.director_project.get_autoScale()
        config["reserve_port"] = overlord.spec.director_project.get_reserve_port()

    elif kind == OverlordKindTypes.METADATA.value:
        config["metadata"] = overlord.spec.metadata.get_metadata()
        config["namespace"] = overlord.spec.metadata.get_namespace()

    elif kind == OverlordKindTypes.VMJAIL.value:
        config["vmName"] = overlord.spec.vm_jail.get_vmName()
        config["makejail"] = overlord.spec.vm_jail.get_makejail()
        config["template"] = overlord.spec.vm_jail.get_template()
        config["diskLayout"] = overlord.spec.vm_jail.get_diskLayout()
        config["script"] = overlord.spec.vm_jail.get_script()
        config["metadata"] = overlord.spec.vm_jail.get_metadata()
        config["options"] = overlord.spec.vm_jail.get_options()
        config["script-environment"] = overlord.spec.vm_jail.get_script_environment()
        config["start-environment"] = overlord.spec.vm_jail.get_start_environment()
        config["start-arguments"] = overlord.spec.vm_jail.get_start_arguments()
        config["build-environment"] = overlord.spec.vm_jail.get_build_environment()
        config["build-arguments"] = overlord.spec.vm_jail.get_build_arguments()
        config["cloud-init"] = overlord.spec.vm_jail.get_cloud_init()
        config["overwrite"] = overlord.spec.vm_jail.get_overwrite()
        config["datastore"] = overlord.spec.vm_jail.get_datastore()
        config["poweroff"] = overlord.spec.vm_jail.get_poweroff()

    elif kind == OverlordKindTypes.APPCONFIG.value:
        config["appName"] = overlord.spec.app_config.get_appName()
        config["appFrom"] = overlord.spec.app_config.get_appFrom()
        config["appConfig"] = overlord.spec.app_config.get_appConfig()

    return config

def get_default(value, default=None):
    if value is None:
        return default

    return value

def get_kind():
    kind = CONFIG.get("kind")

    if kind is None:
        raise overlord.exceptions.KindNotDefined("'kind' is not defined.")

    return kind

def list_datacenters():
    return list(get_datacenters())

def get_datacenters():
    return get_default(CONFIG.get("datacenters"), {})

def get_datacenter(datacenter):
    return get_datacenters().get(datacenter)

def get_datacenter_entrypoint(datacenter):
    datacenter = get_datacenter(datacenter)

    if datacenter is None:
        return

    return datacenter.get("entrypoint")

def get_datacenter_access_token(datacenter):
    datacenter = get_datacenter(datacenter)

    if datacenter is None:
        return

    return datacenter.get("access_token")

def get_datacenter_timeout(datacenter):
    datacenter = get_datacenter(datacenter)

    if datacenter is None:
        return

    timeout = get_default(datacenter.get("timeout"), overlord.default.CLIENT_TIMEOUT)

    if timeout < 0:
        timeout = None

    elif timeout == 0:
        pass # ignore

    return timeout

def get_datacenter_read_timeout(datacenter):
    datacenter = get_datacenter(datacenter)

    if datacenter is None:
        return

    read_timeout = get_default(datacenter.get("read_timeout"), overlord.default.CLIENT_READ_TIMEOUT)

    if read_timeout < 0:
        read_timeout = None

    elif read_timeout == 0:
        pass # ignore

    return read_timeout

def get_datacenter_write_timeout(datacenter):
    datacenter = get_datacenter(datacenter)

    if datacenter is None:
        return

    write_timeout = get_default(datacenter.get("write_timeout"), overlord.default.CLIENT_WRITE_TIMEOUT)

    if write_timeout < 0:
        write_timeout = None

    elif write_timeout == 0:
        pass # ignore

    return write_timeout

def get_datacenter_connect_timeout(datacenter):
    datacenter = get_datacenter(datacenter)

    if datacenter is None:
        return

    connect_timeout = get_default(datacenter.get("connect_timeout"), overlord.default.CLIENT_CONNECT_TIMEOUT)
    
    if connect_timeout < 0:
        connect_timeout = None

    elif connect_timeout == 0:
        pass # ignore

    return connect_timeout

def get_datacenter_pool_timeout(datacenter):
    datacenter = get_datacenter(datacenter)

    if datacenter is None:
        return

    pool_timeout = get_default(datacenter.get("pool_timeout"), overlord.default.CLIENT_POOL_TIMEOUT)

    if pool_timeout < 0:
        pool_timeout = None

    elif pool_timeout == 0:
        pass # ignore

    return pool_timeout

def get_datacenter_max_keepalive_connections(datacenter):
    datacenter = get_datacenter(datacenter)

    if datacenter is None:
        return

    return get_default(datacenter.get("max_keepalive_connections"), overlord.default.CLIENT_MAX_KEEPALIVE_CONNECTIONS)

def get_datacenter_max_connections(datacenter):
    datacenter = get_datacenter(datacenter)

    if datacenter is None:
        return

    return get_default(datacenter.get("max_connections"), overlord.default.CLIENT_MAX_CONNECTIONS)

def get_datacenter_keepalive_expiry(datacenter):
    datacenter = get_datacenter(datacenter)

    if datacenter is None:
        return

    return get_default(datacenter.get("keepalive_expiry"), overlord.default.CLIENT_KEEPALIVE_EXPIRY)

def get_datacenter_cacert(datacenter):
    datacenter = get_datacenter(datacenter)

    if datacenter is None:
        return

    return datacenter.get("cacert")

def get_deployIn():
    return get_default(CONFIG.get("deployIn"), {})

def get_deployIn_entrypoints():
    return get_default(get_deployIn().get("entrypoints"), list_datacenters())

def get_deployIn_labels():
    return get_default(get_deployIn().get("labels"), overlord.default.LABELS)

def get_deployIn_exclude():
    return get_default(get_deployIn().get("exclude"), [])

def get_maximumDeployments():
    return get_default(CONFIG.get("maximumDeployments"), overlord.default.MAXIMUM_DEPLOYMENTS)

def validate(document):
    overlord.error.assert_type("<root>", document, dict)

    validate_kind(document)
    validate_datacenters(document)
    validate_deployIn(document)
    validate_maximumDeployments(document)

def validate_kind(document):
    _name = "kind"
    kind = document.get(_name)

    if kind is None:
        overlord.error.assert_required(_name)

    if kind == OverlordKindTypes.PROJECT.value:
        overlord.spec.director_project.validate(document)

    elif kind == OverlordKindTypes.METADATA.value:
        overlord.spec.metadata.validate(document)

    elif kind == OverlordKindTypes.VMJAIL.value:
        overlord.spec.vm_jail.validate(document)

    elif kind == OverlordKindTypes.READONLY.value:
        pass

    elif kind == OverlordKindTypes.APPCONFIG.value:
        overlord.spec.app_config.validate(document)

    else:
        raise overlord.exceptions.InvalidKind(f"kind: unknown value '{kind}'.")

def validate_datacenters(document):
    _value = overlord.error._validate1(document, "", "datacenters", dict, required=True)

    overlord.error.assert_item(_value, validate_datacenter)

def validate_datacenter(datacenters, datacenter, index):
    overlord.error.assert_type(f"datacenters.<item#{index}>", datacenter, str)

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
        "cacert"
    )

    _value = overlord.error._validate2(datacenters, "datacenters.", datacenter, keys)

    if _value is None:
        return

    validate_datacenter_entrypoint(datacenters, datacenter)
    validate_datacenter_access_token(datacenters, datacenter)
    validate_datacenter_timeout(datacenters, datacenter)
    validate_datacenter_read_timeout(datacenters, datacenter)
    validate_datacenter_write_timeout(datacenters, datacenter)
    validate_datacenter_connect_timeout(datacenters, datacenter)
    validate_datacenter_pool_timeout(datacenters, datacenter)
    validate_datacenter_max_keepalive_connections(datacenters, datacenter)
    validate_datacenter_max_connections(datacenters, datacenter)
    validate_datacenter_keepalive_expiry(datacenters, datacenter)
    validate_datacenter_cacert(datacenters, datacenter)

def validate_datacenter_cacert(datacenters, datacenter):
    document = datacenters[datacenter]
    overlord.error._validate1(document, f"datacenters.{datacenter}.", "cacert", str)

def validate_datacenter_entrypoint(datacenters, datacenter):
    document = datacenters[datacenter]
    overlord.error._validate1(document, f"datacenters.{datacenter}.", "entrypoint", str)

def validate_datacenter_access_token(datacenters, datacenter):
    document = datacenters[datacenter]
    overlord.error._validate1(document, f"datacenters.{datacenter}.", "access_token", str)

def validate_datacenter_timeout(datacenters, datacenter):
    document = datacenters[datacenter]
    overlord.error._validate1(document, f"datacenters.{datacenter}.", "timeout", int)

def validate_datacenter_read_timeout(datacenters, datacenter):
    document = datacenters[datacenter]
    overlord.error._validate1(document, f"datacenters.{datacenter}.", "read_timeout", int)

def validate_datacenter_write_timeout(datacenters, datacenter):
    document = datacenters[datacenter]
    overlord.error._validate1(document, f"datacenters.{datacenter}.", "write_timeout", int)

def validate_datacenter_connect_timeout(datacenters, datacenter):
    document = datacenters[datacenter]
    overlord.error._validate1(document, f"datacenters.{datacenter}.", "connect_timeout", int)

def validate_datacenter_pool_timeout(datacenters, datacenter):
    document = datacenters[datacenter]
    overlord.error._validate1(document, f"datacenters.{datacenter}.", "pool_timeout", int)

def validate_datacenter_max_keepalive_connections(datacenters, datacenter):
    document = datacenters[datacenter]
    overlord.error._validate1(document, f"datacenters.{datacenter}.", "max_keepalive_connections", int)

def validate_datacenter_max_connections(datacenters, datacenter):
    document = datacenters[datacenter]
    overlord.error._validate1(document, f"datacenters.{datacenter}.", "max_connections", int)

def validate_datacenter_keepalive_expiry(datacenters, datacenter):
    document = datacenters[datacenter]
    overlord.error._validate1(document, f"datacenters.{datacenter}.", "keepalive_expiry", int)

def validate_deployIn(document):
    keys = (
        "entrypoints",
        "labels",
        "exclude"
    )

    _value = overlord.error._validate2(document, "", "deployIn", keys, required=True)

    overlord.error.assert_len("deployIn", _value, -1, lambda l, dl: dl > 0, "> 0")

    validate_deployIn_entrypoints(_value)
    validate_deployIn_labels(_value)
    validate_deployIn_exclude(_value)

def validate_deployIn_entrypoints(document):
    _value = overlord.error._validate1(document, "deployIn.", "entrypoints", list)

    if _value is None:
        return

    overlord.error.assert_len("deployIn.entrypoints", _value, -1, lambda l, dl: dl > 0, "> 0")
    overlord.error.assert_item(_value, validate_deployIn_entrypoint)

def validate_deployIn_entrypoint(entrypoints, entrypoint, index):
    overlord.error.assert_type(f"deployIn.entrypoints.<item#{index}>", entrypoint, str)
    overlord.chains.get_chain(entrypoint)

def validate_deployIn_labels(document):
    _value = overlord.error._validate1(document, "deployIn.", "labels", list)

    if _value is None:
        return

    overlord.error.assert_len("deployIn.labels", _value, -1, lambda l, dl: dl > 0, "> 0")
    overlord.error.assert_item(_value, validate_deployIn_label)

def validate_deployIn_label(labels, label, index):
    overlord.error.assert_type(f"deployIn.labels.<item#{index}>", label, str)
    overlord.error.assert_value(f"deployIn.labels.<item#{index}>",
        overlord.chains.check_chain_label, label, overlord.chains.REGEX_LABEL)

def validate_deployIn_exclude(document):
    _value = overlord.error._validate1(document, "deployIn.", "exclude", list)

    if _value is None:
        return

    overlord.error.assert_len("deployIn.exclude", _value, -1, lambda l, dl: dl > 0, "> 0")
    overlord.error.assert_item(_value, validate_deployIn_exclude_item)

def validate_deployIn_exclude_item(labels, label, index):
    overlord.error.assert_type(f"deployIn.exclude.<item#{index}>", label, str)
    overlord.error.assert_value(f"deployIn.exclude.<item#{index}>",
        overlord.chains.check_chain_label, label, overlord.chains.REGEX_LABEL)

def validate_maximumDeployments(document):
    overlord.error._validate1(document, "", "maximumDeployments", int, lambda v: v >= 0, f">= 0")
