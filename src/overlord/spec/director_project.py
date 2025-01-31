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

CONFIG = {}

def get_projectName():
    return CONFIG.get("projectName")

def get_projectFile():
    return CONFIG.get("projectFile")

def get_environment(datacenter=None, chain=None, labels=[]):
    environment = CONFIG.get("environment", {})
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
    return CONFIG.get("labelsEnvironment", {})

def get_labelEnvironment(label):
    labelsEnvironment = get_labelsEnvironment()

    return labelsEnvironment.get(label, {})

def list_labelsEnvironment():
    labelsEnvironment = CONFIG.get("labelsEnvironment", {})

    return list(labelsEnvironment)

def get_datacentersEnvironment():
    return CONFIG.get("datacentersEnvironment", {})

def get_datacenterEnvironment(datacenter):
    datacentersEnvironment = get_datacentersEnvironment()

    return datacentersEnvironment.get(datacenter, {})

def list_datacentersEnvironment():
    datacentersEnvironment = CONFIG.get("datacentersEnvironment", {})

    return list(datacentersEnvironment)

def get_chainsEnvironment():
    return CONFIG.get("chainsEnvironment", {})

def get_chainEnvironment(chain):
    chainsEnvironment = get_chainsEnvironment()

    if chain is None:
        chain = "<root>"

    return chainsEnvironment.get(chain, {})

def list_chainsEnvironment():
    chainsEnvironment = CONFIG.get("chainsEnvironment", {})

    return list(chainsEnvironment)

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
        "environment",
        "datacentersEnvironment",
        "chainsEnvironment",
        "labelsEnvironment"
    )

    for key in document:
        if key not in keys:
            raise overlord.exceptions.InvalidSpec(f"{key}: this key is invalid.")

    validate_projectName(document)
    validate_projectFile(document)
    validate_environment(document)
    validate_datacentersEnvironment(document)
    validate_chainsEnvironment(document)
    validate_labelsEnvironment(document)

    CONFIG = document

def validate_projectName(document):
    projectName = document.get("projectName")

    if projectName is None:
        raise overlord.exceptions.InvalidSpec("'projectName' is required but hasn't been specified.")

    if not isinstance(projectName, str):
        raise overlord.exceptions.InvalidSpec(f"{projectName}: invalid value type for 'projectName'")

def validate_projectFile(document):
    projectFile = document.get("projectFile")

    if projectFile is None:
        raise overlord.exceptions.InvalidSpec("'projectFile' is required but hasn't been specified.")

    if not isinstance(projectFile, str):
        raise overlord.exceptions.InvalidSpec(f"{projectFile}: invalid value type for 'projectFile'")

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
