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

    if not isinstance(document, dict):
        raise overlord.exceptions.InvalidSpec("The document is invalid.")

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

    for key in document:
        if key not in keys:
            raise overlord.exceptions.InvalidSpec(f"{key}: this key is invalid.")

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
    poweroff = document.get("poweroff")

    if poweroff is None:
        return

    if not isinstance(poweroff, bool):
        raise overlord.exceptions.InvalidSpec(f"{poweroff}: invalid value type for 'poweroff'")

def validate_datastore(document):
    datastore = document.get("datastore")

    if datastore is None:
        return

    if not isinstance(datastore, str):
        raise overlord.exceptions.InvalidSpec(f"{datastore}: invalid value type for 'datastore'")

def validate_overwrite(document):
    overwrite = document.get("overwrite")

    if overwrite is None:
        return

    if not isinstance(overwrite, bool):
        raise overlord.exceptions.InvalidSpec(f"{overwrite}: invalid value type for 'overwrite'")

def validate_cloud_init(document):
    cloud_init = document.get("cloud-init")

    if cloud_init is None:
        return

    keys = (
        "flags",
        "meta-data",
        "network-config",
        "user-data"
    )

    for key in cloud_init:
        if key not in keys:
            raise overlord.exceptions.InvalidSpec(f"cloud-init.{key}: this key is invalid.")

    validate_cloud_init_flags(cloud_init)
    validate_cloud_init_meta_data(cloud_init)
    validate_cloud_init_network_config(cloud_init)
    validate_cloud_init_user_data(cloud_init)

def validate_cloud_init_user_data(document):
    user_data = document.get("user-data")

    if user_data is None:
        return

    if not isinstance(user_data, dict):
        raise overlord.exceptions.InvalidSpec("'cloud-init.user-data' is invalid.")

def validate_cloud_init_network_config(document):
    network_config = document.get("network-config")

    if network_config is None:
        return

    if not isinstance(network_config, dict):
        raise overlord.exceptions.InvalidSpec("'cloud-init.network-config' is invalid.")

def validate_cloud_init_meta_data(document):
    meta_data = document.get("meta-data")

    if meta_data is None:
        return

    if not isinstance(meta_data, dict):
        raise overlord.exceptions.InvalidSpec("'cloud-init.meta-data' is invalid.")

def validate_cloud_init_flags(document):
    flags = document.get("flags")

    if flags is None:
        return

    if not isinstance(flags, str):
        raise overlord.exceptions.InvalidSpec(f"{flags}: invalid value type for 'cloud-init.flags'")

def validate_options(document):
    options = document.get("options")

    if options is None:
        return

    if not isinstance(options, list):
        raise overlord.exceptions.InvalidSpec("'options' is invalid.")

    for index, entry in enumerate(options):
        for opt_name, opt_value in entry.items():
            if not isinstance(opt_name, str):
                raise overlord.exceptions.InvalidSpec(f"Invalid option name (options.{index}.{opt_name}).")

            if opt_value is not None \
                    and not isinstance(opt_value, str):
                raise overlord.exceptions.InvalidSpec(f"Invalid option value (options.{index}.{opt_value}).")

def validate_script_environment(document):
    environment = document.get("script-environment")

    if environment is None:
        return

    if not isinstance(environment, list):
        raise overlord.exceptions.InvalidSpec("'script-environment' is invalid.")

    for index, entry in enumerate(environment):
        for env_name, env_value in entry.items():
            if not isinstance(env_name, str) \
                    or not isinstance(env_value, str):
                raise overlord.exceptions.InvalidSpec(f"Invalid environment name (script-environment.{index}.{env_name}) or value (script-environment.{index}.{env_value}).")

def validate_start_environment(document):
    environment = document.get("start-environment")

    if environment is None:
        return

    if not isinstance(environment, list):
        raise overlord.exceptions.InvalidSpec("'start-environment' is invalid.")

    for index, entry in enumerate(environment):
        for env_name, env_value in entry.items():
            if not isinstance(env_name, str) \
                    or not isinstance(env_value, str):
                raise overlord.exceptions.InvalidSpec(f"Invalid environment name (start-environment.{index}.{env_name}) or value (start-environment.{index}.{env_value}).")

def validate_start_arguments(document):
    arguments = document.get("start-arguments")

    if arguments is None:
        return

    if not isinstance(arguments, list):
        raise overlord.exceptions.InvalidSpec("'start-arguments' is invalid.")

    for index, entry in enumerate(arguments):
        for arg_name, arg_value in entry.items():
            if not isinstance(arg_name, str) \
                    or not isinstance(arg_value, str):
                raise overlord.exceptions.InvalidSpec(f"Invalid arguments name (start-arguments.{index}.{arg_name}) or value (start-arguments.{index}.{arg_value}).")

def validate_build_environment(document):
    environment = document.get("build-environment")

    if environment is None:
        return

    if not isinstance(environment, list):
        raise overlord.exceptions.InvalidSpec("'build-environment' is invalid.")

    for index, entry in enumerate(environment):
        for env_name, env_value in entry.items():
            if not isinstance(env_name, str) \
                    or not isinstance(env_value, str):
                raise overlord.exceptions.InvalidSpec(f"Invalid environment name (build-environment.{index}.{env_name}) or value (build-environment.{index}.{env_value}).")

def validate_build_arguments(document):
    arguments = document.get("build-arguments")

    if arguments is None:
        return

    if not isinstance(arguments, list):
        raise overlord.exceptions.InvalidSpec("'build-arguments' is invalid.")

    for index, entry in enumerate(arguments):
        for arg_name, arg_value in entry.items():
            if not isinstance(arg_name, str) \
                    or not isinstance(arg_value, str):
                raise overlord.exceptions.InvalidSpec(f"Invalid arguments name (build-arguments.{index}.{arg_name}) or value (build-arguments.{index}.{arg_value}).")

def validate_vmName(document):
    vmName = document.get("vmName")

    if vmName is None:
        raise overlord.exceptions.InvalidSpec("'vmName' is required but hasn't been specified.")

    if not isinstance(vmName, str):
        raise overlord.exceptions.InvalidSpec(f"{vmName}: invalid value type for 'vmName'")

def validate_makejail(document):
    makejail = document.get("makejail")
    makejailFromMetadata = document.get("makejailFromMetadata")

    if makejail is None and makejailFromMetadata is None:
        raise overlord.exceptions.InvalidSpec("'makejail' or 'makejailFromMetadata' are required but haven't been specified.")

    elif makejail is not None and makejailFromMetadata is not None:
        raise overlord.exceptions.InvalidSpec("Only 'makejail' or 'makejailFromMetadata' should be specified, but not both.")

    elif makejail is not None:
        if not isinstance(makejail, str):
            raise overlord.exceptions.InvalidSpec(f"{makejail}: invalid value type for 'makejail'")

    elif makejailFromMetadata is not None:
        if not isinstance(makejailFromMetadata, str):
            raise overlord.exceptions.InvalidSpec(f"{makejailFromMetadata}: invalid value type for 'makejailFromMetadata'")

def validate_template(document):
    template = document.get("template")

    if template is None:
        raise overlord.exceptions.InvalidSpec("'template' is required but hasn't been specified.")

    if not isinstance(template, dict):
        raise overlord.exceptions.InvalidSpec("'template' is invalid.")

    for param_name, param_value in template.items():
        if not isinstance(param_name, str) \
                or not isinstance(param_value, str):
            raise overlord.exceptions.InvalidSpec(f"Invalid parameter name (template.{param_name}) or value (template.{param_value}).")

def validate_diskLayout(document):
    diskLayout = document.get("diskLayout")

    if diskLayout is None:
        raise overlord.exceptions.InvalidSpec("'diskLayout' is required but hasn't been specified.")

    if not isinstance(diskLayout, dict):
        raise overlord.exceptions.InvalidSpec("'diskLayout' is invalid.")

    keys = (
        "driver",
        "size",
        "from",
        "disk",
        "fstab"
    )

    for key in diskLayout:
        if key not in keys:
            raise overlord.exceptions.InvalidSpec(f"diskLayout.{key}: this key is invalid.")

    validate_diskLayout_driver(diskLayout)
    validate_diskLayout_size(diskLayout)
    validate_diskLayout_from(diskLayout)
    validate_diskLayout_disk(diskLayout)
    validate_diskLayout_fstab(diskLayout)

def validate_diskLayout_fstab(document):
    fstab = document.get("fstab")

    if fstab is None:
        return

    if not isinstance(fstab, list):
        raise overlord.exceptions.InvalidSpec("'diskLayout.fstab' is invalid.")

    if len(fstab) == 0:
        raise overlord.exceptions.InvalidSpec("'diskLayout.fstab' is required but hasn't been specified.")

    for index, entry in enumerate(fstab):
        keys = (
            "device",
            "mountpoint",
            "type",
            "options",
            "dump",
            "pass"
        )

        for key in entry:
            if key not in keys:
                raise overlord.exceptions.InvalidSpec(f"diskLayout.fstab.{index}.{key}: this key is invalid.")

        validate_diskLayout_fstab_device(index, entry)
        validate_diskLayout_fstab_mountpoint(index, entry)
        validate_diskLayout_fstab_type(index, entry)
        validate_diskLayout_fstab_options(index, entry)
        validate_diskLayout_fstab_dump(index, entry)
        validate_diskLayout_fstab_pass(index, entry)

def validate_diskLayout_fstab_device(index, document):
    device = document.get("device")

    if device is None:
        raise overlord.exceptions.InvalidSpec(f"'diskLayout.fstab.{index}.device' is required but hasn't been specified.")

    if not isinstance(device, str):
        raise overlord.exceptions.InvalidSpec(f"{device}: invalid value type for 'diskLayout.fstab.{index}.device'")

def validate_diskLayout_fstab_mountpoint(index, document):
    mountpoint = document.get("mountpoint")

    if mountpoint is None:
        raise overlord.exceptions.InvalidSpec(f"'diskLayout.fstab.{index}.mountpoint' is required but hasn't been specified.")

    if not isinstance(mountpoint, str):
        raise overlord.exceptions.InvalidSpec(f"{mountpoint}: invalid value type for 'diskLayout.fstab.{index}.mountpoint'")

def validate_diskLayout_fstab_type(index, document):
    type = document.get("type")

    if type is None:
        raise overlord.exceptions.InvalidSpec(f"'diskLayout.fstab.{index}.type' is required but hasn't been specified.")

    if not isinstance(type, str):
        raise overlord.exceptions.InvalidSpec(f"{type}: invalid value type for 'diskLayout.fstab.{index}.type'")

def validate_diskLayout_fstab_options(index, document):
    options = document.get("options")

    if options is None:
        raise overlord.exceptions.InvalidSpec(f"'diskLayout.fstab.{index}.options' is required but hasn't been specified.")

    if not isinstance(options, str):
        raise overlord.exceptions.InvalidSpec(f"{options}: invalid value type for 'diskLayout.fstab.{index}.options'")

def validate_diskLayout_fstab_dump(index, document):
    dump = document.get("dump")

    if dump is None:
        raise overlord.exceptions.InvalidSpec(f"'diskLayout.fstab.{index}.dump' is required but hasn't been specified.")

    if not isinstance(dump, int):
        raise overlord.exceptions.InvalidSpec(f"{dump}: invalid value type for 'diskLayout.fstab.{index}.dump'")

    if dump < 0:
        raise ValueError(f"{dump}: invalid value for 'diskLayout.fstab.{index}.dump'")

def validate_diskLayout_fstab_pass(index, document):
    pass_ = document.get("pass")

    if pass_ is None:
        raise overlord.exceptions.InvalidSpec("'diskLayout.fstab.{index}.pass' is required but hasn't been specified.")

    if not isinstance(pass_, int):
        raise overlord.exceptions.InvalidSpec(f"{pass_}: invalid value type for 'diskLayout.fstab.{index}.pass'")

    if pass_ < 0:
        raise ValueError(f"{pass_}: invalid value for 'diskLayout.fstab.{index}.pass'")

def validate_diskLayout_driver(document):
    driver = document.get("driver")

    if driver is None:
        raise overlord.exceptions.InvalidSpec("'diskLayout.driver' is required but hasn't been specified.")

    if not isinstance(driver, str):
        raise overlord.exceptions.InvalidSpec(f"{driver}: invalid value type for 'diskLayout.driver'")

    if driver != "virtio-blk" \
            and driver != "nvme" \
            and driver != "ahci-hd":
         raise overlord.exceptions.InvalidSpec(f"{driver}: invalid value for 'diskLayout.driver'")

def validate_diskLayout_size(document):
    size = document.get("size")

    if size is None:
        raise overlord.exceptions.InvalidSpec("'diskLayout.size' is required but hasn't been specified.")

    if not isinstance(size, str):
        raise overlord.exceptions.InvalidSpec(f"{size}: invalid value type for 'diskLayout.size'")

def validate_diskLayout_from(document):
    from_ = document.get("from")

    if from_ is None:
        raise overlord.exceptions.InvalidSpec("'diskLayout.from' is required but hasn't been specified.")

    if not isinstance(from_, dict):
        raise overlord.exceptions.InvalidSpec("'diskLayout.from' is invalid.")

    if "type" not in from_:
        raise overlord.exceptions.InvalidSpec("diskLayout.from.type: type is required but hasn't been specified.")

    validate_diskLayout_from_type(from_)

def validate_diskLayout_from_type(document):
    type = document.get("type")

    if type == "components":
        keys = (
            "type",
            "components",
            "osVersion",
            "osArch",
            "downloadURL"
        )

    elif type == "appjailImage":
        keys = (
            "type",
            "entrypoint",
            "imageName",
            "imageArch",
            "imageTag"
        )

    elif type == "iso":
        keys = (
            "type",
            "isoFile",
            "installed"
        )

    elif type == "img":
        keys = (
            "type",
            "imgFile"
        )

    else:
        raise overlord.exceptions.InvalidSpec(f"{type}: invalid value for 'diskLayout.from.type'")

    for key in document:
        if key not in keys:
            raise overlord.exceptions.InvalidSpec(f"diskLayout.from.{key}: this key is invalid.")

    if type == "components":
        validate_diskLayout_from_components(document)
        validate_diskLayout_from_osVersion(document)
        validate_diskLayout_from_osArch(document)
        validate_diskLayout_from_downloadURL(document)

    elif type == "entrypoint":
        validate_diskLayout_from_entrypoint(document)
        validate_diskLayout_from_imageName(document)
        validate_diskLayout_from_imageArch(document)
        validate_diskLayout_from_imageTag(document)

    elif type == "iso":
        validate_diskLayout_from_isoFile(document)
        validate_diskLayout_from_installed(document)

    elif type == "img":
        validate_diskLayout_from_imgFile(document)
        validate_diskLayout_from_installed(document)

def validate_diskLayout_from_imgFile(document):
    imgFile = document.get("imgFile")

    if imgFile is None:
        raise overlord.exceptions.InvalidSpec("'imgFile' is required but hasn't been specified.")

    if not isinstance(imgFile, str):
        raise overlord.exceptions.InvalidSpec(f"{imgFile}: invalid value type for 'imgFile'")

def validate_diskLayout_from_installed(document):
    installed = document.get("installed")

    if installed is None:
        return

    if not isinstance(installed, bool):
        raise overlord.exceptions.InvalidSpec(f"{installed}: invalid value type for 'installed'")

def validate_diskLayout_from_isoFile(document):
    isoFile = document.get("isoFile")

    if isoFile is None:
        raise overlord.exceptions.InvalidSpec("'isoFile' is required but hasn't been specified.")

    if not isinstance(isoFile, str):
        raise overlord.exceptions.InvalidSpec(f"{isoFile}: invalid value type for 'isoFile'")

def validate_diskLayout_from_imageTag(document):
    imageTag = document.get("imageTag")

    if imageTag is None:
        raise overlord.exceptions.InvalidSpec("'imageTag' is required but hasn't been specified.")

    if not isinstance(imageTag, str):
        raise overlord.exceptions.InvalidSpec(f"{imageTag}: invalid value type for 'imageTag'")

def validate_diskLayout_from_imageArch(document):
    imageArch = document.get("imageArch")

    if imageArch is None:
        raise overlord.exceptions.InvalidSpec("'imageArch' is required but hasn't been specified.")

    if not isinstance(imageArch, str):
        raise overlord.exceptions.InvalidSpec(f"{imageArch}: invalid value type for 'imageArch'")

def validate_diskLayout_from_imageName(document):
    imageName = document.get("imageName")

    if imageName is None:
        raise overlord.exceptions.InvalidSpec("'imageName' is required but hasn't been specified.")

    if not isinstance(imageName, str):
        raise overlord.exceptions.InvalidSpec(f"{imageName}: invalid value type for 'imageName'")

def validate_diskLayout_from_components(document):
    components = document.get("components")

    if components is None:
        raise overlord.exceptions.InvalidSpec("'diskLayout.from.components' is required but hasn't been specified.")

    if not isinstance(components, list):
        raise overlord.exceptions.InvalidSpec("'diskLayout.from.components' is invalid.")

def validate_diskLayout_from_osVersion(document):
    osVersion = document.get("osVersion")

    if osVersion is None:
        raise overlord.exceptions.InvalidSpec("'osVersion' is required but hasn't been specified.")

    if not isinstance(osVersion, str):
        raise overlord.exceptions.InvalidSpec(f"{osVersion}: invalid value type for 'osVersion'")

def validate_diskLayout_from_osArch(document):
    osArch = document.get("osArch")

    if osArch is None:
        raise overlord.exceptions.InvalidSpec("'osArch' is required but hasn't been specified.")

    if not isinstance(osArch, str):
        raise overlord.exceptions.InvalidSpec(f"{osArch}: invalid value type for 'osArch'")

def validate_diskLayout_from_downloadURL(document):
    downloadURL = document.get("downloadURL")

    if downloadURL is None:
        return

    if not isinstance(downloadURL, str):
        raise overlord.exceptions.InvalidSpec(f"{downloadURL}: invalid value type for 'downloadURL'")

def validate_diskLayout_from_entrypoint(document):
    entrypoint = document.get("entrypoint")

    if entrypoint is None:
        raise overlord.exceptions.InvalidSpec("'diskLayout.from.entrypoint' is required but hasn't been specified.")

    if not isinstance(entrypoint, str):
        raise overlord.exceptions.InvalidSpec(f"{entrypoint}: invalid value type for 'diskLayout.from.entrypoint'")

def validate_diskLayout_disk(document):
    disk = document.get("disk")

    if disk is None:
        return

    if not isinstance(disk, dict):
        raise overlord.exceptions.InvalidSpec("'diskLayout.disk' is invalid.")

    keys = (
        "scheme",
        "partitions",
        "bootcode"
    )

    for key in disk:
        if key not in keys:
            raise overlord.exceptions.InvalidSpec(f"diskLayout.disk.{key}: this key is invalid.")

    validate_diskLayout_disk_scheme(disk)
    validate_diskLayout_disk_partitions(disk)
    validate_diskLayout_disk_bootcode(disk)

def validate_diskLayout_disk_scheme(document):
    scheme = document.get("scheme")

    if scheme is None:
        raise overlord.exceptions.InvalidSpec("'diskLayout.disk.scheme' is required but hasn't been specified.")

    if not isinstance(scheme, str):
        raise overlord.exceptions.InvalidSpec(f"{scheme}: invalid value type for 'diskLayout.disk.scheme'")

    if scheme != "gpt":
        raise overlord.exceptions.InvalidSpec(f"{scheme}: invalid value for 'diskLayout.disk.scheme'")

def validate_diskLayout_disk_partitions(document):
    partitions = document.get("partitions")

    if partitions is None:
        raise overlord.exceptions.InvalidSpec("'diskLayout.disk.partitions' is required but hasn't been specified.")

    if not isinstance(partitions, list):
        raise overlord.exceptions.InvalidSpec("'diskLayout.disk.partitions' is invalid.")

    if len(partitions) == 0:
        raise overlord.exceptions.InvalidSpec("'diskLayout.disk.partitions' is required but hasn't been specified.")

    for index, partition in enumerate(partitions):
        if not isinstance(partition, dict):
            raise overlord.exceptions.InvalidSpec(f"'diskLayout.disk.partitions.{index}' is invalid.")

        validate_diskLayout_disk_partition(index, partition)

def validate_diskLayout_disk_partition(index, partition):
    keys = (
        "type",
        "alignment",
        "start",
        "size",
        "label",
        "format"
    )

    for key in partition:
        if key not in keys:
            raise overlord.exceptions.InvalidSpec(f"diskLayout.disk.partitions.{index}.{key}: this key is invalid.")

    validate_diskLayout_disk_partition_type(index, partition)
    validate_diskLayout_disk_partition_alignment(index, partition)
    validate_diskLayout_disk_partition_start(index, partition)
    validate_diskLayout_disk_partition_size(index, partition)
    validate_diskLayout_disk_partition_label(index, partition)
    validate_diskLayout_disk_partition_format(index, partition)

def validate_diskLayout_disk_partition_type(index, partition):
    type = partition.get("type")

    if type is None:
        raise overlord.exceptions.InvalidSpec(f"'diskLayout.disk.partitions.{index}.type' is required but hasn't been specified.")

    if not isinstance(type, str):
        raise overlord.exceptions.InvalidSpec(f"{type}: invalid value type for 'diskLayout.disk.partition.{index}.type'")

def validate_diskLayout_disk_partition_alignment(index, partition):
    alignment = partition.get("alignment")

    if alignment is None:
        return

    if not isinstance(alignment, str):
        raise overlord.exceptions.InvalidSpec(f"{alignment}: invalid value type for 'diskLayout.disk.partition.{index}.alignment'")

def validate_diskLayout_disk_partition_start(index, partition):
    start = partition.get("start")

    if start is None:
        return

    if not isinstance(start, str):
        raise overlord.exceptions.InvalidSpec(f"{start}: invalid value type for 'diskLayout.disk.partition.{index}.start'")

def validate_diskLayout_disk_partition_size(index, partition):
    size = partition.get("size")

    if size is None:
        return

    if not isinstance(size, str):
        raise overlord.exceptions.InvalidSpec(f"{size}: invalid value type for 'diskLayout.disk.partition.{index}.size'")

def validate_diskLayout_disk_partition_label(index, partition):
    label = partition.get("label")

    if label is None:
        return

    if not isinstance(label, str):
        raise overlord.exceptions.InvalidSpec(f"{label}: invalid value type for 'diskLayout.disk.partition.{index}.label'")

def validate_diskLayout_disk_partition_format(index, partition):
    format = partition.get("format")

    if format is None:
        return

    if not isinstance(format, dict):
        raise overlord.exceptions.InvalidSpec(f"'diskLayout.disk.partitions.{index}.format' is invalid.")

    keys = (
        "flags"
    )

    for key in format:
        if key not in keys:
            raise overlord.exceptions.InvalidSpec(f"diskLayout.disk.partitions.{index}.{key}: this key is invalid.")

    validate_diskLayout_disk_partition_format_flags(index, format)

def validate_diskLayout_disk_partition_format_flags(index, partition):
    flags = partition.get("flags")

    if flags is None:
        return

    if not isinstance(flags, str):
        raise overlord.exceptions.InvalidSpec(f"{flags}: invalid value type for 'diskLayout.disk.partition.{index}.format.flags'")

def validate_diskLayout_disk_bootcode(document):
    bootcode = document.get("bootcode")

    if bootcode is None:
        return

    if not isinstance(bootcode, dict):
        raise overlord.exceptions.InvalidSpec("'diskLayout.disk.bootcode' is invalid.")

    keys = (
        "bootcode",
        "partcode",
        "index"
    )

    for key in bootcode:
        if key not in keys:
            raise overlord.exceptions.InvalidSpec(f"diskLayout.disk.bootcode.{key}: this key is invalid.")

    validate_diskLayout_disk_bootcode_bootcode(bootcode)
    validate_diskLayout_disk_bootcode_partcode(bootcode)

def validate_diskLayout_disk_bootcode_bootcode(document):
    bootcode = document.get("bootcode")

    if bootcode is None:
        return

    if not isinstance(bootcode, str):
        raise overlord.exceptions.InvalidSpec(f"{bootcode}: invalid value type for 'diskLayout.disk.bootcode.bootcode'")

def validate_diskLayout_disk_bootcode_partcode(document):
    partcode = document.get("partcode")
    index = document.get("index")

    if partcode is None and index is None:
        return

    if (partcode is None and index is not None) \
            or (partcode is not None and index is None):
        raise overlord.exceptions.InvalidSpec(f"Both 'diskLayout.disk.bootcode.partcode' and 'diskLayout.disk.bootcode.index' must be specified at the same time.")

    if not isinstance(partcode, str):
        raise overlord.exceptions.InvalidSpec(f"{partcode}: invalid value type for 'diskLayout.disk.bootcode.partcode'")

    if not isinstance(index, int):
        raise overlord.exceptions.InvalidSpec(f"{index}: invalid value type for 'diskLayout.disk.bootcode.index'")

    if index < 0:
        raise ValueError(f"{index}: invalid value for 'diskLayout.disk.bootcode.index'")

def validate_script(document):
    script = document.get("script")

    if script is None:
        return

    if not isinstance(script, str):
        raise overlord.exceptions.InvalidSpec(f"{script}: invalid value type for 'script'")

def validate_metadataPrefix(document):
    metadataPrefix = document.get("metadataPrefix")

    if metadataPrefix is None:
        return

    if not isinstance(metadataPrefix, str):
        raise overlord.exceptions.InvalidSpec(f"{metadataPrefix}: invalid value type for 'metadataPrefix'")

def validate_metadata(document):
    metadata = document.get("metadata")

    if metadata is None:
        return

    if not isinstance(metadata, list):
        raise overlord.exceptions.InvalidSpec("'metadata' is invalid.")

    for index, name in enumerate(metadata):
        if not isinstance(name, str):
            raise overlord.exceptions.InvalidSpec(f"{metadata}: invalid value type for 'metadata.{index}'")
