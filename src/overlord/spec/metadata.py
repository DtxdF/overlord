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

import overlord.exceptions

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
            if "file" in item:
                (metadata, file_) = item["file"]

                metadata = prefix + "." + metadata

                item["file"] = (metadata, file_)

    return namespace

def validate(document):
    global CONFIG

    if not isinstance(document, dict):
        raise overlord.exceptions.InvalidSpec("The document is invalid.")

    keys = (
        "kind",
        "datacenters",
        "deployIn",
        "maximumDeployments",
        "metadata",
        "metadataPrefix",
        "namespace"
    )

    for key in document:
        if key not in keys:
            raise overlord.exceptions.InvalidSpec(f"{key}: this key is invalid.")

    validate_metadata(document)
    validate_metadataPrefix(document)
    validate_namespace(document)

    CONFIG = document

def validate_namespace(document):
    namespace = document.get("namespace")

    if namespace is None:
        return

    if not isinstance(namespace, dict):
        raise overlord.exceptions.InvalidSpec("'namespace' is invalid.")

    keys = (
        "name",
        "mapping"
    )

    for key in namespace:
        if key not in keys:
            raise overlord.exceptions.InvalidSpec(f"namespace.{key}: this key is invalid.")

    validate_namespace_name(namespace)
    validate_namespace_mapping(namespace)

def validate_namespace_name(document):
    name = document.get("name")

    if name is None:
        raise overlord.exceptions.InvalidSpec("'namespace.name' is required but hasn't been specified.")

def validate_namespace_mapping(document):
    mapping = document.get("mapping")

    if mapping is None:
        raise overlord.exceptions.InvalidSpec("'namespace.mapping' is required but hasn't been specified.")

    if not isinstance(mapping, list):
        raise overlord.exceptions.InvalidSpec("'namespace.mapping' is invalid.")

    if len(mapping) == 0:
        raise overlord.exceptions.InvalidSpec("'namespace.mapping': at least one mapping must be specified.")

    for index, entry in enumerate(mapping):
        if not isinstance(entry, dict):
            raise overlord.exceptions.InvalidSpec(f"{entry}: invalid value type for 'namespace.mapping.{index}'")

        keys = (
            "file",
            "directory",
            "owner",
            "group",
            "mode",
            "umask"
        )

        for key in entry:
            if key not in keys:
                raise overlord.exceptions.InvalidSpec(f"namespace.mapping.{index}.{key}: this key is invalid.")

        if "file" not in entry and "directory" not in entry:
            raise overlord.exceptions.InvalidSpec(f"'namespace.mapping.{index}.file' or 'namespace.mapping.{index}.directory' is required but hasn't been specified.")

        if "file" in entry and "directory" in entry:
            raise overlord.exceptions.InvalidSpec(f"'namespace.mapping.{index}' specifies both 'file' and 'directory' but only one should be specified.")

        if "file" in entry:
            validate_namespace_mapping_file(index, entry)

        else:
            validate_namespace_mapping_directory(index, entry)

        validate_namespace_mapping_owner(index, entry)
        validate_namespace_mapping_group(index, entry)
        validate_namespace_mapping_mode(index, entry)
        validate_namespace_mapping_umask(index, entry)

def validate_namespace_mapping_file(index, document):
    file_ = document.get("file")

    if file_ is None:
        return

    if not isinstance(file_, str) and not isinstance(file_, tuple) and not isinstance(file_, list):
        raise overlord.exceptions.InvalidSpec(f"{file_}: invalid value type for 'namespace.mapping.{index}.file'")

    if isinstance(file_, str):
        file_ = file_.split(":", 1)

    if len(file_) != 2:
        raise overlord.exceptions.InvalidSpec(f"{file_}: 'namespace.mapping.{index}.file' must specify both the metadata and the mapping file.")

    document["file"] = tuple(file_)

def validate_namespace_mapping_directory(index, document):
    directory = document.get("directory")

    if directory is None:
        return

    if not isinstance(directory, str):
        raise overlord.exceptions.InvalidSpec(f"{directory}: invalid value type for 'namespace.mapping.{index}.directory'")

def validate_namespace_mapping_owner(index, document):
    owner = document.get("owner")

    if owner is None:
        return

    if not isinstance(owner, int) and not isinstance(owner, str):
        raise overlord.exceptions.InvalidSpec(f"{owner}: invalid value type for 'namespace.mapping.{index}.owner'")

def validate_namespace_mapping_group(index, document):
    group = document.get("group")

    if group is None:
        return

    if not isinstance(group, int) and not isinstance(group, str):
        raise overlord.exceptions.InvalidSpec(f"{group}: invalid value type for 'namespace.mapping.{index}.group'")

def validate_namespace_mapping_mode(index, document):
    mode = document.get("mode")

    if mode is None:
        return

    if not isinstance(mode, int):
        raise overlord.exceptions.InvalidSpec(f"{mode}: invalid value type for 'namespace.mapping.{index}.mode'")

def validate_namespace_mapping_umask(index, document):
    umask = document.get("umask")

    if umask is None:
        return

    if not isinstance(umask, int):
        raise overlord.exceptions.InvalidSpec(f"{umask}: invalid value type for 'namespace.mapping.{index}.umask'")

def validate_metadataPrefix(document):
    metadataPrefix = document.get("metadataPrefix")

    if metadataPrefix is None:
        return

    if not isinstance(metadataPrefix, str):
        raise overlord.exceptions.InvalidSpec(f"{metadataPrefix}: invalid value type for 'metadataPrefix'")

def validate_metadata(document):
    metadata = document.get("metadata")

    if metadata is None:
        raise overlord.exceptions.InvalidSpec("'metadata' is required but hasn't been specified.")

    if not isinstance(metadata, dict):
        raise overlord.exceptions.InvalidSpec("'metadata' is invalid.")

    for metadata_name, metadata_value in metadata.items():
        if not isinstance(metadata_name, str) \
                or not isinstance(metadata_value, str):
            raise overlord.exceptions.InvalidSpec(f"Invalid metadata name (metadata.{metadata_name}) or value (metadata.{metadata_value}).")
