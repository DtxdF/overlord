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

import overlord.exceptions

CONFIG = {}

def get_default(value, default=None):
    if value is None:
        return default

    return value

def get_vmName():
    return CONFIG.get("vmName")

def get_makejail():
    return CONFIG.get("makejail")

def get_makejailFromMetadata():
    return CONFIG.get("makejailFromMetadata")

def get_template():
    return CONFIG.get("template")

def get_diskLayout():
    return CONFIG.get("diskLayout")

def get_script():
    return CONFIG.get("script")

def get_metadata():
    metadata = get_default(CONFIG.get("metadata"), [])

    prefix = CONFIG.get("metadataPrefix")

    if prefix is not None:
        metadata = [(prefix + "." + m) for m in metadata]

    return metadata

def get_options():
    return get_default(CONFIG.get("options"), [])

def get_script_environment():
    return get_default(CONFIG.get("script-environment"), [])

def get_start_environment():
    return get_default(CONFIG.get("start-environment"), [])

def get_start_arguments():
    return get_default(CONFIG.get("start-arguments"), [])

def get_build_environment():
    return get_default(CONFIG.get("build-environment"), [])

def get_build_arguments():
    return get_default(CONFIG.get("build-arguments"), [])

def get_cloud_init():
    return get_default(CONFIG.get("cloud-init"), {})

def get_overwrite():
    return get_default(CONFIG.get("overwrite"), False)

def get_datastore():
    return CONFIG.get("datastore")

def get_poweroff():
    return get_default(CONFIG.get("poweroff"), False)

def validate(document):
    global CONFIG

    _name = "<root:vmJail>"
    overlord.error.assert_type(_name, document, dict)

    keys = (
        "kind",
        "datacenters",
        "deployIn",
        "maximumDeployments",
        "vmName",
        "makejail",
        "makejailFromMetadata",
        "template",
        "diskLayout",
        "script",
        "metadata",
        "metadataPrefix",
        "options",
        "script-environment",
        "start-environment",
        "start-arguments",
        "build-environment",
        "build-arguments",
        "cloud-init",
        "overwrite",
        "datastore",
        "poweroff"
    )

    overlord.error.assert_parameter(_name, document, keys)

    validate_vmName(document)
    validate_makejail(document)
    validate_template(document)
    validate_diskLayout(document)
    validate_script(document)
    validate_metadata(document)
    validate_metadataPrefix(document)
    validate_options(document)
    validate_script_environment(document)
    validate_start_environment(document)
    validate_start_arguments(document)
    validate_build_environment(document)
    validate_build_arguments(document)
    validate_cloud_init(document)
    validate_overwrite(document)
    validate_datastore(document)
    validate_poweroff(document)

    CONFIG = document

def validate_poweroff(document):
    overlord.error._validate1(document, "", "poweroff", bool)

def validate_datastore(document):
    overlord.error._validate1(document, "", "datastore", str)

def validate_overwrite(document):
    overlord.error._validate1(document, "", "overwrite", bool)

def validate_cloud_init(document):
    keys = (
        "flags",
        "meta-data",
        "network-config",
        "user-data"
    )

    _value = overlord.error._validate2(document, "", "cloud-init", keys)

    if _value is None:
        return

    validate_cloud_init_flags(_value)
    validate_cloud_init_meta_data(_value)
    validate_cloud_init_network_config(_value)
    validate_cloud_init_user_data(_value)

def validate_cloud_init_user_data(document):
    overlord.error._validate1(document, "cloud-init.", "user-data", dict)

def validate_cloud_init_network_config(document):
    overlord.error._validate1(document, "cloud-init.", "network-config", dict)

def validate_cloud_init_meta_data(document):
    overlord.error._validate1(document, "cloud-init.", "meta-data", dict)

def validate_cloud_init_flags(document):
    overlord.error._validate1(document, "cloud-init.", "flags", str)

def validate_options(document):
    _value = overlord.error._validate1(document, "", "options", list)

    if _value is None:
        return

    overlord.error.assert_item(_value, validate_options_item)

def validate_options_item(options, entry, index):
    opt_index = 0

    for opt_name, opt_value in entry.items():
        overlord.error.assert_type(f"options.<item#{index}>.<item#{opt_index}>", opt_name, str)

        if opt_value is not None:
            overlord.error.assert_type(f"options.<item#{index}>.{opt_name}", opt_value, str)

        opt_index += 1

def validate_script_environment(document):
    _validate_environment(document, "", "script-environment")

def validate_start_environment(document):
    _validate_environment(document, "", "start-environment")

def validate_start_arguments(document):
    _validate_environment(document, "", "start-arguments")

def validate_build_environment(document):
    _validate_environment(document, "", "build-environment")

def validate_build_arguments(document):
    _validate_environment(document, "", "build-arguments")

def _validate_environment(document, prefix, name):
    _value = overlord.error._validate1(document, prefix, name, list)

    if _value is None:
        return

    overlord.error.assert_item(_value, _validate_environment_item, {
        "prefix" : prefix,
        "name" : name
    })

def _validate_environment_item(environment, entry, index, data):
    prefix = data["prefix"]
    document_name = data["name"]

    env_index = 0

    for name, value in entry.items():
        overlord.error.assert_type(f"{prefix}{document_name}.<item#{index}>.<item#{env_index}>", name, str)
        overlord.error.assert_type(f"{prefix}{document_name}.<item#{index}>.{name}", value, str)

        env_index += 1

def validate_vmName(document):
    overlord.error._validate1(document, "", "vmName", str)

def validate_makejail(document):
    makejail = document.get("makejail")
    makejailFromMetadata = document.get("makejailFromMetadata")

    if makejail is None and makejailFromMetadata is None:
        raise overlord.exceptions.InvalidSpec("'makejail' or 'makejailFromMetadata' are required but haven't been specified.")

    elif makejail is not None and makejailFromMetadata is not None:
        raise overlord.exceptions.InvalidSpec("Only 'makejail' or 'makejailFromMetadata' should be specified, but not both.")

    elif makejail is not None:
        overlord.error.assert_type("makejail", makejail, str)

    elif makejailFromMetadata is not None:
        overlord.error.assert_type("makejailFromMetadata", makejailFromMetadata, str)

def validate_template(document):
    _value = overlord.error._validate1(document, "", "template", dict)

    if _value is None:
        return

    overlord.error.assert_item(_value, validate_template_item)

def validate_template_item(template, name, index):
    overlord.error.assert_type(f"template.<item#{index}>", name, str)
    overlord.error.assert_type(f"template.{name}", template[name], str)

def validate_diskLayout(document):
    keys = (
        "driver",
        "size",
        "from",
        "disk",
        "fstab"
    )

    _value = overlord.error._validate2(document, "", "diskLayout", keys)

    if _value is None:
        return

    validate_diskLayout_driver(_value)
    validate_diskLayout_size(_value)
    validate_diskLayout_from(_value)
    validate_diskLayout_disk(_value)
    validate_diskLayout_fstab(_value)

def validate_diskLayout_fstab(document):
    _value = overlord.error._validate1(document, "diskLayout.", "fstab", list)

    if _value is None:
        return

    overlord.error.assert_len("diskLayout.fstab", _value, -1, lambda l, dl: dl > 0, "> 0")
    overlord.error.assert_item(_value, validate_diskLayout_fstab_item)

def validate_diskLayout_fstab_item(fstab, entry, index):
    _name = f"diskLayout.fstab.<item#{index}>"

    keys = (
        "device",
        "mountpoint",
        "type",
        "options",
        "dump",
        "pass"
    )

    overlord.error.assert_type(_name, entry, dict)
    overlord.error.assert_parameter(_name, entry, keys)

    validate_diskLayout_fstab_device(index, entry)
    validate_diskLayout_fstab_mountpoint(index, entry)
    validate_diskLayout_fstab_type(index, entry)
    validate_diskLayout_fstab_options(index, entry)
    validate_diskLayout_fstab_dump(index, entry)
    validate_diskLayout_fstab_pass(index, entry)

def validate_diskLayout_fstab_device(index, document):
    overlord.error._validate1(document, f"diskLayout.fstab.<item#{index}>.", "device", str, required=True)

def validate_diskLayout_fstab_mountpoint(index, document):
    overlord.error._validate1(document, f"diskLayout.fstab.<item#{index}>.", "mountpoint", str, required=True)

def validate_diskLayout_fstab_type(index, document):
    overlord.error._validate1(document, f"diskLayout.fstab.<item#{index}>.", "type", str, required=True)

def validate_diskLayout_fstab_options(index, document):
    overlord.error._validate1(document, f"diskLayout.fstab.<item#{index}>.", "options", str, required=True)

def validate_diskLayout_fstab_dump(index, document):
    dump = overlord.error._validate1(document, f"diskLayout.fstab.<item#{index}>.", "dump", int, required=True)
    overlord.error.assert_value(f"diskLayout.fstab.<item#{index}>.dump", lambda v: v >= 0, dump, ">= 0")

def validate_diskLayout_fstab_pass(index, document):
    pass_ = overlord.error._validate1(document, f"diskLayout.fstab.<item#{index}>.", "pass", int, required=True)
    overlord.error.assert_value(f"diskLayout.fstab.<item#{index}>.pass", lambda v: v >= 0, pass_, ">= 0")

def validate_diskLayout_driver(document):
    driver = overlord.error._validate1(document, f"diskLayout.", "driver", str, required=True)

    if driver != "virtio-blk" \
            and driver != "nvme" \
            and driver != "ahci-hd":
        raise overlord.exceptions.InvalidSpec(f"diskLayout.driver: invalid driver: '{driver}'")

def validate_diskLayout_size(document):
    overlord.error._validate1(document, "diskLayout.", "driver", str, required=True)

def validate_diskLayout_from(document):
    from_ = overlord.error._validate1(document, "diskLayout.", "from", dict, required=True)

    if "type" not in from_:
        overlord.error.assert_required("diskLayout.from.type")

    validate_diskLayout_from_type(from_)

def validate_diskLayout_from_type(document):
    type_ = document.get("type")

    if type_ == "components":
        keys = (
            "type",
            "components",
            "osVersion",
            "osArch",
            "downloadURL"
        )

    elif type_ == "appjailImage":
        keys = (
            "type",
            "entrypoint",
            "imageName",
            "imageArch",
            "imageTag"
        )

    elif type_ == "pkgbase":
        keys = (
            "type",
            "osVersion",
            "osArch",
            "packages",
            "pkgConf",
            "fingerprints"
        )

    elif type_ == "iso":
        keys = (
            "type",
            "isoFile",
            "installed"
        )

    elif type_ == "img":
        keys = (
            "type",
            "imgFile"
        )

    else:
        raise overlord.exceptions.InvalidSpec(f"diskLayout.from.type: invalid type: '{type_}'")

    overlord.error._validate2(document, "diskLayout.", "from", keys)

    if type_ == "components":
        validate_diskLayout_from_components(document)
        validate_diskLayout_from_osVersion(document)
        validate_diskLayout_from_osArch(document)
        validate_diskLayout_from_downloadURL(document)

    elif type_ == "appjailImage":
        validate_diskLayout_from_entrypoint(document)
        validate_diskLayout_from_imageName(document)
        validate_diskLayout_from_imageArch(document)
        validate_diskLayout_from_imageTag(document)

    elif type_ == "pkgbase":
        validate_diskLayout_from_osVersion(document)
        validate_diskLayout_from_osArch(document)
        validate_diskLayout_from_packages(document)
        validate_diskLayout_from_pkgConf(document)
        validate_diskLayout_from_fingerprints(document)

    elif type_ == "iso":
        validate_diskLayout_from_isoFile(document)
        validate_diskLayout_from_installed(document)

    elif type_ == "img":
        validate_diskLayout_from_imgFile(document)
        validate_diskLayout_from_installed(document)

def validate_diskLayout_from_fingerprints(document):
    overlord.error._validate1(document, "diskLayout.from.", "fingerprints", str)

def validate_diskLayout_from_pkgConf(document):
    overlord.error._validate1(document, "diskLayout.from.", "pkgConf", str)

def validate_diskLayout_from_packages(document):
    _value = overlord.error._validate1(document, "diskLayout.from.", "packages", list, required=True)
    overlord.error.assert_item(_value, validate_diskLayout_fstab_item)

def validate_diskLayout_from_packages_item(packages, package, index):
    overlord.error.assert_type(f"diskLayout.from.packages.<item#{index}>", package, str)

def validate_diskLayout_from_imgFile(document):
    overlord.error._validate1(document, "diskLayout.from.", "imgFile", str)

def validate_diskLayout_from_installed(document):
    overlord.error._validate1(document, "diskLayout.from.", "installed", bool)

def validate_diskLayout_from_isoFile(document):
    overlord.error._validate1(document, "diskLayout.from.", "isoFile", str, required=True)

def validate_diskLayout_from_imageTag(document):
    overlord.error._validate1(document, "diskLayout.from.", "imageTag", str, required=True)

def validate_diskLayout_from_imageArch(document):
    overlord.error._validate1(document, "diskLayout.from.", "imageArch", str, required=True)

def validate_diskLayout_from_imageName(document):
    overlord.error._validate1(document, "diskLayout.from.", "imageName", str, required=True)

def validate_diskLayout_from_components(document):
    _value = overlord.error._validate1(document, "diskLayout.from.", "components", list, required=True)
    overlord.error.assert_item(_value, validate_diskLayout_from_components_item)

def validate_diskLayout_from_components_item(components, component, index):
    overlord.error.assert_type(f"diskLayout.from.components.<item#{index}>", component, str)

def validate_diskLayout_from_osVersion(document):
    overlord.error._validate1(document, "diskLayout.from.", "osVersion", str, required=True)

def validate_diskLayout_from_osArch(document):
    overlord.error._validate1(document, "diskLayout.from.", "osArch", str, required=True)

def validate_diskLayout_from_downloadURL(document):
    overlord.error._validate1(document, "diskLayout.from.", "downloadURL", str)

def validate_diskLayout_from_entrypoint(document):
    overlord.error._validate1(document, "diskLayout.from.", "entrypoint", str, required=True)

def validate_diskLayout_disk(document):
    keys = (
        "scheme",
        "partitions",
        "bootcode"
    )

    _value = overlord.error._validate2(document, "diskLayout.", "disk", keys)

    if _value is None:
        return

    validate_diskLayout_disk_scheme(_value)
    validate_diskLayout_disk_partitions(_value)
    validate_diskLayout_disk_bootcode(_value)

def validate_diskLayout_disk_scheme(document):
    scheme = overlord.error._validate1(document, "diskLayout.disk.", "scheme", str, required=True)

    if scheme != "gpt":
        raise overlord.exceptions.InvalidSpec(f"diskLayout.disk.scheme: invalid scheme: '{scheme}'.")

def validate_diskLayout_disk_partitions(document):
    _value = overlord.error._validate1(document, "diskLayout.disk.", "partitions", list)

    if _value is None:
        return

    overlord.error.assert_len("diskLayout.disk.partitions", _value, -1, lambda l, dl: dl > 0, "> 0")
    overlord.error.assert_item(_value, validate_diskLayout_disk_partitions_item)

def validate_diskLayout_disk_partitions_item(partitions, partition, index):
    validate_diskLayout_disk_partition(index, partition)

def validate_diskLayout_disk_partition(index, partition):
    _name = f"diskLayout.disk.partitions.<item#{index}>"

    keys = (
        "type",
        "alignment",
        "start",
        "size",
        "label",
        "format"
    )

    overlord.error.assert_type(_name, partition, dict)
    overlord.error.assert_parameter(_name, partition, keys)

    validate_diskLayout_disk_partition_type(index, partition)
    validate_diskLayout_disk_partition_alignment(index, partition)
    validate_diskLayout_disk_partition_start(index, partition)
    validate_diskLayout_disk_partition_size(index, partition)
    validate_diskLayout_disk_partition_label(index, partition)
    validate_diskLayout_disk_partition_format(index, partition)

def validate_diskLayout_disk_partition_type(index, partition):
    overlord.error._validate1(partition, f"diskLayout.disk.partitions.<item#{index}>.", "type", str, required=True)

def validate_diskLayout_disk_partition_alignment(index, partition):
    overlord.error._validate1(partition, f"diskLayout.disk.partitions.<item#{index}>.", "alignment", str)

def validate_diskLayout_disk_partition_start(index, partition):
    overlord.error._validate1(partition, f"diskLayout.disk.partitions.<item#{index}>.", "start", str)

def validate_diskLayout_disk_partition_size(index, partition):
    overlord.error._validate1(partition, f"diskLayout.disk.partitions.<item#{index}>.", "size", str)

def validate_diskLayout_disk_partition_label(index, partition):
    overlord.error._validate1(partition, f"diskLayout.disk.partitions.<item#{index}>.", "label", str)

def validate_diskLayout_disk_partition_format(index, partition):
    keys = (
        "flags",
        "script"
    )

    format_ = overlord.error._validate2(partition, f"diskLayout.disk.partitions.<item#{index}>.", "format", keys)

    if format_ is None:
        return

    if "flags" in format_ and "script" in format_:
        raise overlord.exceptions.InvalidSpec("Only 'flags' or 'script' should be specified, but not both.")

    elif "flags" in format_:
        flags = format_.get("flags")

        overlord.error.assert_type(f"diskLayout.disk.partitions.<item#{index}>.format.flags", flags, str)

    elif "script" in format_:
        script = format_.get("script")

        overlord.error.assert_type(f"diskLayout.disk.partitions.<item#{index}>.format.script", script, str)

def validate_diskLayout_disk_bootcode(document):
    keys = (
        "bootcode",
        "partcode",
        "index"
    )

    _value = overlord.error._validate2(document, "diskLayout.disk.", "bootcode", keys)

    if _value is None:
        return

    validate_diskLayout_disk_bootcode_bootcode(_value)
    validate_diskLayout_disk_bootcode_partcode(_value)

def validate_diskLayout_disk_bootcode_bootcode(document):
    overlord.error._validate1(document, "diskLayout.disk.bootcode.", "bootcode", str)

def validate_diskLayout_disk_bootcode_partcode(document):
    partcode = document.get("partcode")
    index = document.get("index")

    if partcode is None and index is None:
        return

    if (partcode is None and index is not None) \
            or (partcode is not None and index is None):
        raise overlord.exceptions.InvalidSpec(f"Both 'diskLayout.disk.bootcode.partcode' and 'diskLayout.disk.bootcode.index' must be specified at the same time.")

    overlord.error.assert_type("diskLayout.disk.bootcode.partcode", partcode, str)
    overlord.error.assert_type("diskLayout.disk.bootcode.index", index, int)
    overlord.error.assert_value("diskLayout.disk.bootcode.index", lambda v: v >= 0, index, ">= 0")

def validate_script(document):
    overlord.error._validate1(document, "", "script", str)

def validate_metadataPrefix(document):
    overlord.error._validate1(document, "", "metadataPrefix", str)

def validate_metadata(document):
    _value = overlord.error._validate1(document, "", "metadata", list)

    if _value is None:
        return

    overlord.error.assert_item(_value, validate_metadata_item)

def validate_metadata_item(metadata, name, index):
    overlord.error.assert_type(f"metadata.<item#{index}>", name, str)
    overlord.error.assert_value(f"metadata.<item#{index}>",
        overlord.metadata.check_keyname, name, overlord.metadata.REGEX_KEY)
