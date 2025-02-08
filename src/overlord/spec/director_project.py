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

import copy

import humanfriendly

import overlord.exceptions

CONFIG = {}

def get_default(value, default=None):
    if value is None:
        return default

    return value

def get_projectName():
    return CONFIG.get("projectName")

def get_projectFile():
    return CONFIG.get("projectFile")

def get_projectFromMetadata():
    return CONFIG.get("projectFromMetadata")

def get_environFromMetadata():
    return CONFIG.get("environFromMetadata")

def get_environment(datacenter=None, chain=None, labels=[]):
    environment = get_default(CONFIG.get("environment"), {})
    environment = copy.copy(environment)

    for label in labels:
        labelEnvironment = get_labelEnvironment(label)

        environment.update(labelEnvironment)

    chainEnvironment = get_chainEnvironment(chain)

    environment.update(chainEnvironment)

    if datacenter is not None:
        datacenterEnvironment = get_datacenterEnvironment(datacenter)

        environment.update(datacenterEnvironment)

    return environment

def get_labelsEnvironment():
    return get_default(CONFIG.get("labelsEnvironment"), {})

def get_labelEnvironment(label):
    labelsEnvironment = get_labelsEnvironment()

    return get_default(labelsEnvironment.get(label), {})

def list_labelsEnvironment():
    labelsEnvironment = get_labelsEnvironment()

    return list(labelsEnvironment)

def get_datacentersEnvironment():
    return get_default(CONFIG.get("datacentersEnvironment"), {})

def get_datacenterEnvironment(datacenter):
    datacentersEnvironment = get_datacentersEnvironment()

    return get_default(datacentersEnvironment.get(datacenter), {})

def list_datacentersEnvironment():
    datacentersEnvironment = get_datacentersEnvironment()

    return list(datacentersEnvironment)

def get_chainsEnvironment():
    return get_default(CONFIG.get("chainsEnvironment"), {})

def get_chainEnvironment(chain):
    chainsEnvironment = get_chainsEnvironment()

    if chain is None:
        chain = "<root>"

    return chainsEnvironment.get(chain, {})

def list_chainsEnvironment():
    chainsEnvironment = get_chainsEnvironment()

    return list(chainsEnvironment)

def get_autoScale():
    return get_default(CONFIG.get("autoScale"), {})

def get_autoScale_replicas():
    autoScale = get_autoScale()

    return get_default(autoScale.get("replicas"), overlord.default.SCALE["replicas"])

def get_autoScale_replicas_min():
    replicas = get_autoScale_replicas()

    return get_default(replicas.get("min"), overlord.default.SCALE["replicas"]["min"])

def get_autoScale_replicas_max():
    replicas = get_autoScale_replicas()

    return replicas.get("max")

def get_autoScale_type():
    autoScale = get_autoScale()

    return get_default(autoScale.get("type"), overlord.default.SCALE["type"])

def get_autoScale_value():
    autoScale = get_autoScale()

    return autoScale.get("value")

def get_autoScale_rules():
    autoScale = get_autoScale()

    return get_default(autoScale.get("rules"), {})

def get_autoScale_labels():
    autoScale = get_autoScale()

    return get_default(autoScale.get("labels"), overlord.default.LABELS)

def validate(document):
    global CONFIG

    if not isinstance(document, dict):
        raise overlord.exceptions.InvalidSpec("The document is invalid.")

    keys = (
        "kind",
        "datacenters",
        "deployIn",
        "maximumDeployments",
        "projectName",
        "projectFile",
        "projectFromMetadata",
        "environment",
        "datacentersEnvironment",
        "chainsEnvironment",
        "labelsEnvironment",
        "environFromMetadata",
        "autoScale"
    )

    for key in document:
        if key not in keys:
            raise overlord.exceptions.InvalidSpec(f"{key}: this key is invalid.")

    validate_projectName(document)
    validate_project(document)
    validate_environment(document)
    validate_datacentersEnvironment(document)
    validate_chainsEnvironment(document)
    validate_labelsEnvironment(document)
    validate_environFromMetadata(document)
    validate_autoScale(document)

    CONFIG = document

def validate_autoScale(document):
    autoScale = document.get("autoScale")

    if autoScale is None:
        return

    if not isinstance(autoScale, dict):
        raise overlord.exceptions.InvalidSpec("'autoScale' is invalid.")

    keys = (
        "replicas",
        "type",
        "value",
        "rules",
        "labels"
    )

    for key in autoScale:
        if key not in keys:
            raise overlord.exceptions.InvalidSpec(f"autoScale.{key}: this key is invalid.")

    validate_autoScale_replicas(autoScale)
    validate_autoScale_type(autoScale)
    validate_autoScale_rules(autoScale)
    validate_autoScale_labels(autoScale)

def validate_autoScale_replicas(document):
    replicas = document.get("replicas")

    if replicas is None:
        return

    if not isinstance(replicas, dict):
        raise overlord.exceptions.InvalidSpec("'autoScale.replicas' is invalid.")

    keys = ("min", "max")

    for key in replicas:
        if key not in keys:
            raise overlord.exceptions.InvalidSpec(f"autoScale.replicas.{key}: this key is invalid.")

    validate_autoScale_replicas_min(replicas)
    validate_autoScale_replicas_max(replicas)

def validate_autoScale_replicas_min(document):
    min = document.get("min")

    if min is None:
        return

    if not isinstance(min, int) \
            or min < 1:
        raise overlord.exceptions.InvalidSpec(f"{min}: invalid value type for 'autoScale.replicas.min'")

def validate_autoScale_replicas_max(document):
    max = document.get("max")

    if max is None:
        return

    if not isinstance(max, int) \
            or max < 1:
        raise overlord.exceptions.InvalidSpec(f"{max}: invalid value type for 'autoScale.replicas.max'")

def validate_autoScale_type(document):
    type = document.get("type")

    if type is None:
        return

    if not isinstance(type, str):
        raise overlord.exceptions.InvalidSpec(f"{type}: invalid value type for 'autoScale.type'")

    if type == "any-jail" \
            or type == "any-project" \
            or type == "average":
        pass # ignore

    elif type == "percent-jail" \
            or type == "percent-project":
        value = document.get("value")

        if value is None:
            raise overlord.exceptions.InvalidSpec("'autoScale.value' is required but hasn't been specified.")

        if not isinstance(value, int):
            raise overlord.exceptions.InvalidSpec(f"{value}: invalid value type for 'autoScale.value'")
    else:
        raise overlord.exceptions.InvalidSpec(f"{type}: invalid scale type.")

def validate_autoScale_rules(document):
    rules = document.get("rules")

    if rules is None:
        return

    if not isinstance(rules, dict):
        raise overlord.exceptions.InvalidSpec("'autoScale.rules' is invalid.")

    for rule, value in rules.items():
        if rule == "datasize" \
                or rule == "stacksize" \
                or rule == "coredumpsize" \
                or rule == "memoryuse" \
                or rule == "memorylocked" \
                or rule == "vmemoryuse" \
                or rule == "swapuse" \
                or rule == "shmsize" \
                or rule == "readbps" \
                or rule == "writebps":
            if isinstance(value, str):
                try:
                    value = humanfriendly.parse_size(value, binary=True)

                    document["rules"][rule] = value

                except Exception as err:
                    raise overlord.exceptions.InvalidSpec(f"{value}: invalid value type for 'autoScale.rules.{rule}': {err}")

            if not isinstance(value, int) \
                    or value < 0:
                raise overlord.exceptions.InvalidSpec(f"{value}: invalid value type for 'autoScale.rules.{rule}'")

        elif rule == "cputime" \
                or rule == "maxproc" \
                or rule == "openfiles" \
                or rule == "pseudoterminals" \
                or rule == "nthr" \
                or rule == "msgqqueued" \
                or rule == "nmsgq" \
                or rule == "nsem" \
                or rule == "nsemop" \
                or rule == "nshm" \
                or rule == "wallclock" \
                or rule == "pcpu" \
                or rule == "readiops" \
                or rule == "writeiops":
            if not isinstance(value, int) \
                    or value < 0:
                raise overlord.exceptions.InvalidSpec(f"{value}: invalid value type for 'autoScale.rules.{rule}'")

        else:
            raise overlord.exceptions.InvalidSpec(f"autoScale.rules.{rule}: invalid resource.")

def validate_autoScale_labels(document):
    labels = document.get("labels")

    if labels is None:
        return

    if not isinstance(labels, list):
        raise overlord.exceptions.InvalidSpec("'autoScale.labels' is invalid.")

    for index, entry in enumerate(labels):
        if not isinstance(entry, str):
            raise overlord.exceptions.InvalidSpec(f"{entry}: invalid value type for 'autoScale.labels.{index}'")

        if not overlord.chains.check_chain_label(entry):
            raise overlord.exceptions.InvalidSpec(f"'autoScale.labels.{index}.{entry}': invalid label.")

    length = len(labels)

    if length < 1:
        raise overlord.exceptions.InvalidSpec("'autoScale.labels': at least one label must be specified.")

def validate_projectName(document):
    projectName = document.get("projectName")

    if projectName is None:
        raise overlord.exceptions.InvalidSpec("'projectName' is required but hasn't been specified.")

    if not isinstance(projectName, str):
        raise overlord.exceptions.InvalidSpec(f"{projectName}: invalid value type for 'projectName'")

def validate_project(document):
    projectFile = document.get("projectFile")
    projectFromMetadata = document.get("projectFromMetadata")

    if projectFile is None and projectFromMetadata is None:
        raise overlord.exceptions.InvalidSpec("'projectFile' or 'projectFromMetadata' are required but haven't been specified.")

    elif projectFile is not None and projectFromMetadata is not None:
        raise overlord.exceptions.InvalidSpec("Only 'projectFile' or 'projectFromMetadata' should be specified, but not both.")

    elif projectFile is not None:
        if not isinstance(projectFile, str):
            raise overlord.exceptions.InvalidSpec(f"{projectFile}: invalid value type for 'projectFile'")

    elif projectFromMetadata is not None:
        if not isinstance(projectFromMetadata, str):
            raise overlord.exceptions.InvalidSpec(f"{projectFromMetadata}: invalid value type for 'projectFromMetadata'")

def validate_environment(document):
    environment = document.get("environment")

    if environment is None:
        return

    if not isinstance(environment, dict):
        raise overlord.exceptions.InvalidSpec("'environment' is invalid.")

    for env_name, env_value in environment.items():
        if not isinstance(env_name, str) \
                or not isinstance(env_value, str):
            raise overlord.exceptions.InvalidSpec(f"Invalid environment name (environment.{env_name}) or value (environment.{env_value}).")

def validate_datacentersEnvironment(document):
    datacentersEnvironment = document.get("datacentersEnvironment")

    if datacentersEnvironment is None:
        return

    if not isinstance(datacentersEnvironment, dict):
        raise overlord.exceptions.InvalidSpec("'datacentersEnvironment' is invalid.")

    for datacenter, environment in datacentersEnvironment.items():
        if not isinstance(datacenter, str):
            raise overlord.exceptions.InvalidSpec(f"{datacenter}: invalid value type for 'datacentersEnvironment.{index}'")

        for env_name, env_value in environment.items():
            if not isinstance(env_name, str) \
                    or not isinstance(env_value, str):
                raise overlord.exceptions.InvalidSpec(f"Invalid environment name (datacentersEnvironment.{datacentersEnvironment}.{env_name}) or value (datacentersEnvironment.{datacentersEnvironment}.{env_value}).")

def validate_chainsEnvironment(document):
    chainsEnvironment = document.get("chainsEnvironment")

    if chainsEnvironment is None:
        return

    if not isinstance(chainsEnvironment, dict):
        raise overlord.exceptions.InvalidSpec("'chainsEnvironment' is invalid.")

    for datacenter, environment in chainsEnvironment.items():
        if not isinstance(datacenter, str):
            raise overlord.exceptions.InvalidSpec(f"{datacenter}: invalid value type for 'chainsEnvironment.{index}'")

        for env_name, env_value in environment.items():
            if not isinstance(env_name, str) \
                    or not isinstance(env_value, str):
                raise overlord.exceptions.InvalidSpec(f"Invalid environment name (chainsEnvironment.{chainsEnvironment}.{env_name}) or value (chainsEnvironment.{chainsEnvironment}.{env_value}).")

def validate_labelsEnvironment(document):
    labelsEnvironment = document.get("labelsEnvironment")

    if labelsEnvironment is None:
        return

    if not isinstance(labelsEnvironment, dict):
        raise overlord.exceptions.InvalidSpec("'labelsEnvironment' is invalid.")

    for datacenter, environment in labelsEnvironment.items():
        if not isinstance(datacenter, str):
            raise overlord.exceptions.InvalidSpec(f"{datacenter}: invalid value type for 'labelsEnvironment.{index}'")

        for env_name, env_value in environment.items():
            if not isinstance(env_name, str) \
                    or not isinstance(env_value, str):
                raise overlord.exceptions.InvalidSpec(f"Invalid environment name (labelsEnvironment.{labelsEnvironment}.{env_name}) or value (labelsEnvironment.{labelsEnvironment}.{env_value}).")

def validate_environFromMetadata(document):
    environFromMetadata = document.get("environFromMetadata")

    if environFromMetadata is None:
        return

    if not isinstance(environFromMetadata, str):
        raise overlord.exceptions.InvalidSpec(f"{environFromMetadata}: invalid value type for 'environFromMetadata'")
