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

import pyaml_env

import overlord.error
import overlord.exceptions
import overlord.metadata

CONFIG = {}

def get_metadata():
    metadata = CONFIG.get("metadata")

    prefix = CONFIG.get("metadataPrefix")

    if prefix is not None:
        _metadata = {}

        for key, value in metadata.items():
            _metadata[prefix + "." + key] = value

        metadata = _metadata

    return metadata

def get_namespace():
    namespace = CONFIG.get("namespace")

    if namespace is None:
        return

    prefix = CONFIG.get("metadataPrefix")

    if prefix is not None:
        mapping = namespace.get("mapping")

        for item in mapping:
            if "prefix" in item:
                file_prefix = item["prefix"]

                del item["prefix"]

            else:
                file_prefix = prefix

            if "file" in item:
                (metadata, file_) = item["file"]

                if file_prefix:
                    if isinstance(file_prefix, bool):
                        if file_prefix:
                            metadata = prefix + "." + metadata

                    else:
                        metadata = file_prefix + "." + metadata

                item["file"] = (metadata, file_)

    return namespace

def validate(document):
    global CONFIG

    _name = "<root:metadata>"
    overlord.error.assert_type(_name, document, dict)

    keys = (
        "kind",
        "datacenters",
        "deployIn",
        "maximumDeployments",
        "metadata",
        "metadataPrefix",
        "namespace",
        "include"
    )

    overlord.error.assert_parameter(_name, document, keys)

    validate_metadata(document)
    validate_metadataPrefix(document)
    validate_namespace(document)

    CONFIG = document

def validate_namespace(document):
    keys = (
        "name",
        "mapping"
    )

    _value = overlord.error._validate2(document, "", "namespace", keys)

    if _value is None:
        return

    validate_namespace_name(_value)
    validate_namespace_mapping(_value)

def validate_namespace_name(document):
    overlord.error._validate1(document, "namespace.", "name", str, required=True)

def validate_namespace_mapping(document):
    _value = overlord.error._validate1(document, "namespace.", "mapping", list, required=True)
    overlord.error.assert_len("namespace.mapping", _value, -1, lambda l, dl: dl > 0, "> 0")
    overlord.error.assert_item(_value, validate_namespace_mapping_item)

def validate_namespace_mapping_item(mapping, entry, index):
    _name = f"namespace.mapping.<item#{index}>"
    overlord.error.assert_type(_name, entry, dict)

    keys = (
        "file",
        "directory",
        "owner",
        "group",
        "mode",
        "umask",
        "prefix"
    )

    overlord.error.assert_parameter(_name, entry, keys)

    if "file" not in entry and "directory" not in entry:
        raise overlord.exceptions.InvalidSpec(f"'{_name}.file' or '{_name}.directory' is required but hasn't been specified.")

    if "file" in entry and "directory" in entry:
        raise overlord.exceptions.InvalidSpec(f"'{_name}' specifies both 'file' and 'directory' but only one should be specified.")

    if "file" in entry:
        validate_namespace_mapping_file(index, entry)

    else:
        validate_namespace_mapping_directory(index, entry)

    validate_namespace_mapping_prefix(index, entry)
    validate_namespace_mapping_owner(index, entry)
    validate_namespace_mapping_group(index, entry)
    validate_namespace_mapping_mode(index, entry)
    validate_namespace_mapping_umask(index, entry)

def validate_namespace_mapping_prefix(index, document):
    overlord.error._validate1(document, f"namespace.mapping.<item#{index}>.", "prefix", (str, bool),
        multiple=True)

def validate_namespace_mapping_file(index, document):
    _prefix = f"namespace.mapping.<item#{index}>"
    _value = overlord.error._validate1(document, f"{_prefix}.", "file", (str, tuple, list),
        multiple=True)

    if isinstance(_value, str):
        _value = _value.split(":", 1)

    if len(_value) != 2:
        raise overlord.exceptions.InvalidSpec(f"'{_prefix}.file' must specify both the metadata and the mapping file.")

    document["file"] = tuple(_value)

def validate_namespace_mapping_directory(index, document):
    overlord.error._validate1(document, f"namespace.mapping.<item#{index}>.", "directory", str)

def validate_namespace_mapping_owner(index, document):
    overlord.error._validate1(document, f"namespace.mapping.<item#{index}>.", "owner", (int, str),
        multiple=True)

def validate_namespace_mapping_group(index, document):
    overlord.error._validate1(document, f"namespace.mapping.<item#{index}>.", "group", (int, str),
        multiple=True)

def validate_namespace_mapping_mode(index, document):
    overlord.error._validate1(document, f"namespace.mapping.<item#{index}>.", "mode", int)

def validate_namespace_mapping_umask(index, document):
    overlord.error._validate1(document, f"namespace.mapping.<item#{index}>.", "umask", int)

def validate_metadataPrefix(document):
    overlord.error._validate1(document, "", "metadataPrefix", str)

def validate_metadata(document):
    metadata = document.get("metadata")

    if metadata is None:
        metadata = {}

    overlord.error.assert_type("metadata", document, dict)

    include = document.get("include")

    if include is None:
        include = []

    overlord.error.assert_type("include", include, list)

    for index, file_ in enumerate(include):
        overlord.error.assert_type(f"include.<item#{index}>", file_, str)

        data = pyaml_env.parse_config(file_, default_value="")

        overlord.error.assert_type(f"include.<item#{index}:metadata>", data, dict)

        metadata.update(data)

    if len(metadata) > 0:
        overlord.error.assert_item(metadata, validate_metadata_item)

def validate_metadata_item(metadata, name, index):
    overlord.error.assert_type(f"metadata.<item#{index}>", name, str)
    overlord.error.assert_value(f"metadata.{name}",
        overlord.metadata.check_keyname, name, overlord.metadata.REGEX_KEY)
    overlord.error.assert_type(f"metadata.{name}", metadata[name], str)
