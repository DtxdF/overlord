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

import enum

import pyaml_env

import overlord.chains
import overlord.default
import overlord.exceptions
import overlord.spec.director_project

CONFIG = {}

class OverlordKindTypes(enum.Enum):
    PROJECT = "directorProject"

def load(file):
    global CONFIG

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
    return CONFIG.get("datacenters", {})

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

    timeout = get_default(datacenter.get("timeout"), overlord.default.CHAIN_TIMEOUT)

    if timeout < 0:
        timeout = None

    elif timeout == 0:
        pass # ignore

    return timeout

def get_datacenter_read_timeout(datacenter):
    datacenter = get_datacenter(datacenter)

    if datacenter is None:
        return

    read_timeout = get_default(datacenter.get("read_timeout"), overlord.default.CHAIN_READ_TIMEOUT)

    if read_timeout < 0:
        read_timeout = None

    elif read_timeout == 0:
        pass # ignore

    return read_timeout

def get_datacenter_write_timeout(datacenter):
    datacenter = get_datacenter(datacenter)

    if datacenter is None:
        return

    write_timeout = get_default(datacenter.get("write_timeout"), overlord.default.CHAIN_WRITE_TIMEOUT)

    if write_timeout < 0:
        write_timeout = None

    elif write_timeout == 0:
        pass # ignore

    return write_timeout

def get_datacenter_connect_timeout(datacenter):
    datacenter = get_datacenter(datacenter)

    if datacenter is None:
        return

    connect_timeout = get_default(datacenter.get("connect_timeout"), overlord.default.CHAIN_CONNECT_TIMEOUT)
    
    if connect_timeout < 0:
        connect_timeout = None

    elif connect_timeout == 0:
        pass # ignore

    return connect_timeout

def get_datacenter_pool_timeout(datacenter):
    datacenter = get_datacenter(datacenter)

    if datacenter is None:
        return

    pool_timeout = get_default(datacenter.get("pool_timeout"), overlord.default.CHAIN_POOL_TIMEOUT)

    if pool_timeout < 0:
        pool_timeout = None

    elif pool_timeout == 0:
        pass # ignore

    return pool_timeout

def get_datacenter_max_keepalive_connections(datacenter):
    datacenter = get_datacenter(datacenter)

    if datacenter is None:
        return

    return get_default(datacenter.get("max_keepalive_connections"), overlord.default.CHAIN_MAX_KEEPALIVE_CONNECTIONS)

def get_datacenter_max_connections(datacenter):
    datacenter = get_datacenter(datacenter)

    if datacenter is None:
        return

    return get_default(datacenter.get("max_connections"), overlord.default.CHAIN_MAX_CONNECTIONS)

def get_datacenter_keepalive_expiry(datacenter):
    datacenter = get_datacenter(datacenter)

    if datacenter is None:
        return

    return get_default(datacenter.get("keepalive_expiry"), overlord.default.CHAIN_KEEPALIVE_EXPIRY)

def get_deployIn():
    return CONFIG.get("deployIn", {})

def get_deployIn_entrypoints():
    return get_deployIn().get("entrypoints", list_datacenters())

def get_deployIn_labels():
    return get_deployIn().get("labels", [])

def get_deployIn_exclude():
    return get_deployIn().get("exclude", [])

def get_maximumDeployments():
    return get_default(CONFIG.get("maximumDeployments"), overlord.default.MAXIMUM_DEPLOYMENTS)

def validate(document):
    if not isinstance(document, dict):
        raise overlord.exceptions.InvalidSpec("The document is invalid.")

    validate_kind(document)
    validate_datacenters(document)
    validate_deployIn(document)
    validate_maximumDeployments(document)

def validate_kind(document):
    kind = document.get("kind")

    if kind is None:
        raise overlord.exceptions.InvalidSpec("'kind' is required but hasn't been specified.")

    if kind == OverlordKindTypes.PROJECT.value:
        overlord.spec.director_project.validate(document)

    else:
        raise overlord.exceptions.InvalidKind(f"{kind}: Unknown value for 'kind'.")

def validate_datacenters(document):
    datacenters = document.get("datacenters")

    if datacenters is None:
        raise overlord.exceptions.InvalidSpec("'datacenters' is required but hasn't been specified.")

    if not isinstance(datacenters, dict):
        raise overlord.exceptions.InvalidSpec("'datacenters' is invalid.")

    for index, name in enumerate(datacenters):
        if not isinstance(name, str):
            raise overlord.exceptions.InvalidSpec(f"{name}: invalid value type for 'datacenters.{index}'")

        validate_datacenter(datacenters, name)

def validate_datacenter(datacenters, name):
    datacenter = datacenters[name]

    if not isinstance(datacenter, dict):
        raise overlord.exceptions.InvalidSpec(f"'datacenters.{name}' is invalid.")

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

    for key in datacenter:
        if key not in keys:
            raise overlord.exceptions.InvalidSpec(f"datacenters.{name}.{key}: this key is invalid.")

    validate_datacenter_entrypoint(datacenters, name)
    validate_datacenter_access_token(datacenters, name)
    validate_datacenter_timeout(datacenters, name)
    validate_datacenter_read_timeout(datacenters, name)
    validate_datacenter_write_timeout(datacenters, name)
    validate_datacenter_connect_timeout(datacenters, name)
    validate_datacenter_pool_timeout(datacenters, name)
    validate_datacenter_max_keepalive_connections(datacenters, name)
    validate_datacenter_max_connections(datacenters, name)
    validate_datacenter_keepalive_expiry(datacenters, name)

def validate_datacenter_entrypoint(datacenters, name):
    entrypoint = datacenters[name].get("entrypoint")

    if entrypoint is None:
        raise overlord.exceptions.InvalidSpec(f"'datacenters.{name}.entrypoint' is required but hasn't been specified.")

    if not isinstance(entrypoint, str):
        raise overlord.exceptions.InvalidSpec(f"{entrypoint}: invalid value type for 'datacenters.{name}.entrypoint'")

def validate_datacenter_access_token(datacenters, name):
    access_token = datacenters[name].get("access_token")

    if access_token is None:
        raise overlord.exceptions.InvalidSpec(f"'datacenters.{name}.access_token' is required but hasn't been specified.")

    if not isinstance(access_token, str):
        raise overlord.exceptions.InvalidSpec(f"{access_token}: invalid value type for 'datacenters.{name}.access_token'")

def validate_datacenter_timeout(datacenters, name):
    timeout = datacenters[name].get("timeout")

    if timeout is None:
        return

    if not isinstance(timeout, int):
        raise overlord.exceptions.InvalidSpec(f"{timeout}: invalid value type for 'datacenters.{name}.timeout'")

def validate_datacenter_read_timeout(datacenters, name):
    read_timeout = datacenters[name].get("read_timeout")

    if read_timeout is None:
        return

    if not isinstance(read_timeout, int):
        raise overlord.exceptions.InvalidSpec(f"{read_timeout}: invalid value type for 'datacenters.{name}.read_timeout'")

def validate_datacenter_write_timeout(datacenters, name):
    write_timeout = datacenters[name].get("write_timeout")

    if write_timeout is None:
        return

    if not isinstance(write_timeout, int):
        raise overlord.exceptions.InvalidSpec(f"{write_timeout}: invalid value type for 'datacenters.{name}.write_timeout'")

def validate_datacenter_connect_timeout(datacenters, name):
    connect_timeout = datacenters[name].get("connect_timeout")

    if connect_timeout is None:
        return

    if not isinstance(connect_timeout, int):
        raise overlord.exceptions.InvalidSpec(f"{connect_timeout}: invalid value type for 'datacenters.{name}.connect_timeout'")

def validate_datacenter_pool_timeout(datacenters, name):
    pool_timeout = datacenters[name].get("pool_timeout")

    if pool_timeout is None:
        return

    if not isinstance(pool_timeout, int):
        raise overlord.exceptions.InvalidSpec(f"{pool_timeout}: invalid value type for 'datacenters.{name}.pool_timeout'")

def validate_datacenter_max_keepalive_connections(datacenters, name):
    max_keepalive_connections = datacenters[name].get("max_keepalive_connections")

    if max_keepalive_connections is None:
        return

    if not isinstance(max_keepalive_connections, int):
        raise overlord.exceptions.InvalidSpec(f"{max_keepalive_connections}: invalid value type for 'datacenters.{name}.max_keepalive_connections'")

def validate_datacenter_max_connections(datacenters, name):
    max_connections = datacenters[name].get("max_connections")

    if max_connections is None:
        return

    if not isinstance(max_connections, int):
        raise overlord.exceptions.InvalidSpec(f"{max_connections}: invalid value type for 'datacenters.{name}.max_connections'")

def validate_datacenter_keepalive_expiry(datacenters, name):
    keepalive_expiry = datacenters[name].get("keepalive_expiry")

    if keepalive_expiry is None:
        return

    if not isinstance(keepalive_expiry, int):
        raise overlord.exceptions.InvalidSpec(f"{keepalive_expiry}: invalid value type for 'datacenters.{name}.keepalive_expiry'")

def validate_deployIn(document):
    deployIn = document.get("deployIn")

    if deployIn is None:
        raise overlord.exceptions.InvalidSpec("'deployIn' is required but hasn't been specified.")

    if not isinstance(deployIn, dict):
        raise overlord.exceptions.InvalidSpec("'deployIn' is invalid.")

    keys = (
        "entrypoints",
        "labels",
        "exclude"
    )

    if len(deployIn) == 0:
        raise overlord.exceptions.InvalidSpec(f"'deployIn': at least one type of deployment must be specified.")

    for key in deployIn:
        if key not in keys:
            raise overlord.exceptions.InvalidSpec(f"deployIn.{key}: this key is invalid.")

    validate_deployIn_entrypoints(deployIn)
    validate_deployIn_labels(deployIn)
    validate_deployIn_exclude(deployIn)

def validate_deployIn_entrypoints(document):
    entrypoints = document.get("entrypoints")

    if entrypoints is None:
        return

    if not isinstance(entrypoints, list):
        raise overlord.exceptions.InvalidSpec("'deployIn.entrypoints' is invalid.")

    for index, entry in enumerate(entrypoints):
        if not isinstance(entry, str):
            raise overlord.exceptions.InvalidSpec(f"{entry}: invalid value type for 'deployIn.entrypoints.{index}'")

        # Check for invalid chains.
        overlord.chains.get_chain(entry)

    length = len(entrypoints)

    if length < 1:
        raise overlord.exceptions.InvalidSpec(f"'deployIn.entrypoints': at least one entrypoint must be specified.")

def validate_deployIn_labels(document):
    labels = document.get("labels")

    if labels is None:
        return

    if not isinstance(labels, list):
        raise overlord.exceptions.InvalidSpec("'deployIn.labels' is invalid.")

    for index, entry in enumerate(labels):
        if not isinstance(entry, str):
            raise overlord.exceptions.InvalidSpec(f"{entry}: invalid value type for 'deployIn.labels.{index}'")

        if not overlord.chains.check_chain_label(entry):
            raise overlord.exceptions.InvalidSpec(f"'deployIn.labels.{index}.{entry}': invalid label.")

    length = len(labels)

    if length < 1:
        raise overlord.exceptions.InvalidSpec("'deployIn.labels': at least one label must be specified.")

def validate_deployIn_exclude(document):
    exclude = document.get("exclude")

    if exclude is None:
        return

    if not isinstance(exclude, list):
        raise overlord.exceptions.InvalidSpec("'deployIn.exclude' is invalid.")

    for index, entry in enumerate(exclude):
        if not isinstance(entry, str):
            raise overlord.exceptions.InvalidSpec(f"{entry}: invalid value type for 'deployIn.exclude.{index}'")

        if not overlord.chains.check_chain_label(entry):
            raise overlord.exceptions.InvalidSpec(f"'deployIn.exclude.{index}.{entry}': invalid label.")

    length = len(exclude)

    if length < 1:
        raise overlord.exceptions.InvalidSpec("'deployIn.exclude': at least one label must be specified.")

def validate_maximumDeployments(document):
    maximumDeployments = document.get("maximumDeployments")
    
    if maximumDeployments is None:
        return

    if not isinstance(maximumDeployments, int) \
            or maximumDeployments < 0:
        raise overlord.exceptions.InvalidSpec(f"{maximumDeployments}: invalid value type for 'maximumDeployments'")
