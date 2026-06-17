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

import overlord.chains
import overlord.metadata
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

def get_autoScale_economy():
    autoScale = get_autoScale()

    return get_default(autoScale.get("economy"), {})

def get_autoScale_labels():
    autoScale = get_autoScale()

    return get_default(autoScale.get("labels"), overlord.default.LABELS)

def get_autoScale_metadata():
    autoScale = get_autoScale()

    return get_default(autoScale.get("metadata"), [])

def get_autoScale_load_balancer():
    autoScale = get_autoScale()

    return get_default(autoScale.get("load-balancer"), {})

def get_reserve_port():
    return get_default(CONFIG.get("reserve_port"), {})

def validate(document):
    global CONFIG

    _name = "<root:directorProject>"
    overlord.error.assert_type(_name, document, dict)

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
        "autoScale",
        "reserve_port"
    )

    overlord.error.assert_parameter(_name, document, keys)

    validate_projectName(document)
    validate_project(document)
    validate_environment(document)
    validate_datacentersEnvironment(document)
    validate_chainsEnvironment(document)
    validate_labelsEnvironment(document)
    validate_environFromMetadata(document)
    validate_autoScale(document)
    validate_reserve_port(document)

    CONFIG = document

def validate_reserve_port(document):
    _value = overlord.error._validate1(document, "", "reserve_port", dict)

    if _value is None:
        return

    overlord.error.assert_item(_value, validate_reserve_port_item)

def validate_reserve_port_item(reserve_port, interface, index):
    overlord.error.assert_type(f"reserve_port.<item#{index}>", interface, str)

    network = reserve_port.get(interface)

    if network is not None:
        overlord.error.assert_type(f"reserve_port.{interface}", network, str)

def validate_autoScale(document):
    keys = (
        "replicas",
        "type",
        "value",
        "rules",
        "economy",
        "labels",
        "metadata",
        "load-balancer"
    )

    _value = overlord.error._validate2(document, "", "autoScale", keys)
    
    if _value is None:
        return

    validate_autoScale_replicas(_value)
    validate_autoScale_type(_value)
    validate_autoScale_rules(_value)
    validate_autoScale_economy(_value)
    validate_autoScale_labels(_value)
    validate_autoScale_metadata(_value)
    validate_autoScale_load_balancer(_value)

def validate_autoScale_load_balancer(document):
    keys = ("frontend", "backend")

    _value = overlord.error._validate2(document, "autoScale.", "load-balancer", keys)
    
    if _value is None:
        return

    overlord.error.assert_item(_value, validate_autoScale_load_balancer_item)

def validate_autoScale_load_balancer_item(data, type_, index):
    _prefix = "autoScale.load-balancer"

    overlord.error.assert_type(f"{_prefix}.<item#{index}>", type_, str)

    _prefix = f"{_prefix}.{type_}"

    document = data[type_]

    name = overlord.error._validate1(document, f"{_prefix}.", "name", str, required=True)

    keys = ("or", "and")
    rules_obj = overlord.error._validate2(document, f"{_prefix}.", "rules", keys, required=True)
    overlord.error.assert_len(f"{_prefix}.rules", rules_obj, -1, lambda l, dl: dl > 0, "> 0")

    index1 = 0
    
    for rule_type, rules in rules_obj.items():
        overlord.error.assert_type(f"{_prefix}.rules.<item#{index1}>", rule_type, str)
        overlord.error.assert_type(f"{_prefix}.rules.{rule_type}", rules, dict)

        index2 = 0

        for rule_name, rule_obj in rules.items():
            overlord.error.assert_type(f"{_prefix}.rules.{rule_type}.<item#{index2}>", rule_name, str)
            keys = ("value", "each")
            rule_obj = overlord.error._validate2(rules, f"{_prefix}.rules.{rule_type}.", rule_name, keys)

            value = overlord.error._validate1(rule_obj, f"{_prefix}.rules.{rule_type}.{rule_name}.",
                "value", (int, str, tuple, list), required=True, multiple=True)

            if isinstance(value, list):
                overlord.error.assert_len(f"{_prefix}.rules.{rule_type}.{rule_name}.value", value, 2)

                begin = value[0]

                overlord.error.assert_type(f"{_prefix}.rules.{rule_type}.{rule_name}.value.<item#0>", begin, int)
                overlord.error.assert_value(f"{_prefix}.rules.{rule_type}.{rule_name}.value.<item#0>", lambda v: v >= 0, begin, ">= 0")

                end = value[1]

                overlord.error.assert_type(f"{_prefix}.rules.{rule_type}.{rule_name}.value.<item#1>", end, int)
                overlord.error.assert_value(f"{_prefix}.rules.{rule_type}.{rule_name}.value.<item#1>", lambda v: v >= 0, end, ">= 0")

                if begin > end:
                    raise overlord.exceptions.InvalidSpec(f"{_prefix}.rules.{rule_type}.{rule_name}.value: '{_prefix}.rules.{rule_type}.{rule_name}.value.<item#0>' is greater than '{_prefix}.rules.{rule_type}.{rule_name}.value.<item#1>'.")

            if "each" in rule_obj:
                overlord.error._validate1(document, f"{_prefix}.rules.{rule_type}.{rule_name}.", "each", int)

            index2 += 1

        index1 += 1

def validate_autoScale_replicas(document):
    keys = ("min", "max")

    _value = overlord.error._validate2(document, "autoScale.", "replicas", keys)
    
    if _value is None:
        return

    validate_autoScale_replicas_min(_value)
    validate_autoScale_replicas_max(_value)

def validate_autoScale_replicas_min(document):
    overlord.error._validate1(document, "autoScale.replicas.", "min", int, lambda v: v > 0, "> 0")

def validate_autoScale_replicas_max(document):
    overlord.error._validate1(document, "autoScale.replicas.", "max", int, lambda v: v > 0, "> 0")

def validate_autoScale_type(document):
    type_ = overlord.error._validate1(document, "autoScale.", "type", str)

    if type_ is None:
        return

    if type_ == "any-jail" \
            or type_ == "any-project" \
            or type_ == "average":
        pass # ignore

    elif type_ == "percent-jail" \
            or type_ == "percent-project":
        overlord.error._validate1(document, "autoScale.", "value", int, required=True)

    else:
        raise overlord.exceptions.InvalidSpec(f"autoScale.type: invalid scale type: '{type_}'.")

def validate_autoScale_economy(document):
    return _validate_autoScale_rules("economy", document)

def validate_autoScale_rules(document):
    return _validate_autoScale_rules("rules", document)

def _validate_autoScale_rules(rules_type, document):
    rules = overlord.error._validate1(document, "autoScale.", rules_type, dict)

    if rules is None:
        return

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

                    document[rules_type][rule] = value

                except Exception as err:
                    raise overlord.exceptions.InvalidSpec(f"{value}: invalid value type for 'autoScale.{rules_type}.{rule}': {err}")

            if not isinstance(value, int) \
                    or value < 0:
                raise overlord.exceptions.InvalidSpec(f"{value}: invalid value type for 'autoScale.{rules_type}.{rule}'")

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
                raise overlord.exceptions.InvalidSpec(f"{value}: invalid value type for 'autoScale.{rules_type}.{rule}'")

        else:
            raise overlord.exceptions.InvalidSpec(f"autoScale.{rules_type}.{rule}: invalid resource.")

def validate_autoScale_labels(document):
    _value = overlord.error._validate1(document, "autoScale.", "labels", list)

    if _value is None:
        return

    overlord.error.assert_len("deployIn.labels", _value, -1, lambda l, dl: dl > 0, "> 0")
    overlord.error.assert_item(_value, validate_autoScale_label)

def validate_autoScale_label(labels, label, index):
    overlord.error.assert_type(f"autoScale.labels.<item#{index}>", label, str)
    overlord.error.assert_value(f"autoScale.labels.<item#{index}>",
        overlord.chains.check_chain_label, label, overlord.chains.REGEX_LABEL)

def validate_autoScale_metadata(document):
    _value = overlord.error._validate1(document, "autoScale.", "metadata", list)

    if _value is None:
        return

    overlord.error.assert_len("autoScale.metadata", _value, -1, lambda l, dl: dl > 0, "> 0")
    overlord.error.assert_item(_value, validate_autoScale_metadata_item)

def validate_autoScale_metadata_item(metadata, name, index):
    overlord.error.assert_type(f"autoScale.metadata.<item#{index}>", name, str)
    overlord.error.assert_value(f"autoScale.metadata.<item#{index}>",
        overlord.metadata.check_keyname, name, overlord.metadata.REGEX_KEY)

def validate_projectName(document):
    overlord.error._validate1(document, "", "projectName", str, required=True)

def validate_project(document):
    projectFile = document.get("projectFile")
    projectFromMetadata = document.get("projectFromMetadata")

    if projectFile is None and projectFromMetadata is None:
        raise overlord.exceptions.InvalidSpec("'projectFile' or 'projectFromMetadata' are required but haven't been specified.")

    elif projectFile is not None and projectFromMetadata is not None:
        raise overlord.exceptions.InvalidSpec("Only 'projectFile' or 'projectFromMetadata' should be specified, but not both.")

    elif projectFile is not None:
        overlord.error.assert_type("projectFile", projectFile, str)

    elif projectFromMetadata is not None:
        overlord.error.assert_type("projectFromMetadata", projectFromMetadata, str)

def validate_environment(document):
    _value = overlord.error._validate1(document, "", "environment", dict)

    if _value is None:
        return

    overlord.error.assert_item(_value, validate_environment_item)

def validate_environment_item(environment, name, index):
    overlord.error.assert_type(f"environment.<item#{index}>", name, str)
    overlord.error.assert_type(f"environment.{name}", environment[name], str)

def validate_datacentersEnvironment(document):
    _value = overlord.error._validate1(document, "", "datacentersEnvironment", dict)

    if _value is None:
        return

    overlord.error.assert_item(_value, validate_datacentersEnvironment_item)

def validate_datacentersEnvironment_item(datacentersEnvironment, datacenter, index):
    overlord.error.assert_type(f"datacentersEnvironment.<item#{index}>", datacenter, str)

    environment = overlord.error._validate1(datacentersEnvironment, "datacentersEnvironment.", datacenter, dict, required=True)

    index = 0

    for name, value in environment.items():
        overlord.error.assert_type(f"datacentersEnvironment.{datacenter}.<item#{index}>", name, str)
        overlord.error.assert_type(f"datacentersEnvironment.{datacenter}.{name}", value, str)

        index += 1

def validate_chainsEnvironment(document):
    _value = overlord.error._validate1(document, "", "chainsEnvironment", dict)

    if _value is None:
        return

    overlord.error.assert_item(_value, validate_chainsEnvironment_item)

def validate_chainsEnvironment_item(chainsEnvironment, chain, index):
    overlord.error.assert_type(f"chainsEnvironment.<item#{index}>", chain, str)
    overlord.error.assert_value(f"chainsEnvironment.{chain}",
        overlord.chains.check_chain_name, chain, overlord.chains.REGEX_CHAIN_NAME)

    environment = overlord.error._validate1(chainsEnvironment, "chainsEnvironment.", chain, dict, required=True)

    index = 0

    for name, value in environment.items():
        overlord.error.assert_type(f"chainsEnvironment.{chain}.<item#{index}>", name, str)
        overlord.error.assert_type(f"chainsEnvironment.{chain}.{name}", value, str)

        index += 1

def validate_labelsEnvironment(document):
    _value = overlord.error._validate1(document, "", "labelsEnvironment", dict)

    if _value is None:
        return

    overlord.error.assert_item(_value, validate_labelsEnvironment_item)

def validate_labelsEnvironment_item(labelsEnvironment, label, index):
    overlord.error.assert_type(f"labelsEnvironment.<item#{index}>", label, str)
    overlord.error.assert_value(f"labelsEnvironment.<item#{index}>",
        overlord.chains.check_chain_label, label, overlord.chains.REGEX_LABEL)

    environment = overlord.error._validate1(labelsEnvironment, "labelsEnvironment.", label, dict, required=True)

    index = 0

    for name, value in environment.items():
        overlord.error.assert_type(f"labelsEnvironment.{label}.<item#{index}>", name, str)
        overlord.error.assert_type(f"labelsEnvironment.{label}.{name}", value, str)

        index += 1

def validate_environFromMetadata(document):
    overlord.error._validate1(document, "", "environmentFromMetadata", str)
