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

import logging
import os
import re
import shlex
import shutil
import yaml
import sys

import overlord.config
import overlord.process
import overlord.metadata

logger = logging.getLogger(__name__)

def check_vm_name(name):
    return re.match(r"[a-zA-Z0-9][.a-zA-Z0-9_-]{0,229}[a-zA-Z0-9]", name) is not None

def is_done(jail_path):
    # .done is accepted for backward compatibility.
    done_files = (".done", "vm/.done")

    for done_file in done_files:
        done_file = os.path.join(jail_path, done_file)

        if os.path.isfile(done_file):
            return True

    return False

def write_done(jail_path, content=""):
    done_file = os.path.join(jail_path, "vm/.done")

    with open(done_file, "w") as fd:
        fd.write(content)
        fd.flush()
        os.fsync(fd.fileno())

def get_done(jail_path):
    done_file = os.path.join(jail_path, ".done")

    if not os.path.isfile(done_file):
        done_file = os.path.join(jail_path, "vm/.done")

    if not os.path.isfile(done_file):
        return

    with open(done_file) as fd:
        return fd.read()

def install_from_pkgbase(jail, major_version, arch, packages, pkg_conf=None, fingerprints=None):
    args = []

    args.append(os.path.join(sys.prefix, "libexec/overlord/safe-exc.sh"))
    args.append(os.path.join(sys.prefix, "libexec/overlord/vm-install-from-pkgbase.sh"))
    args.extend(["-a", arch])
    if pkg_conf is not None:
        args.extend(["-c", pkg_conf])
    if fingerprints is not None:
        args.extend(["-f", fingerprints])
    args.extend(["-j", jail])
    args.extend(["-v", major_version])
    args.append("--")
    args.extend(packages)

    return _run(args)

def install_from_components(jail, download_url, components_path, components):
    args = []

    args.append(os.path.join(sys.prefix, "libexec/overlord/safe-exc.sh"))
    args.append(os.path.join(sys.prefix, "libexec/overlord/vm-install-from-components.sh"))
    args.extend(["-c", components_path])
    args.extend(["-j", jail])
    args.extend(["-u", download_url])
    args.append("--")
    args.extend(components)

    return _run(args)

def install_from_iso(jail, iso_file):
    args = ["appjail", "cmd", "jexec", jail, "vm", "install", jail, iso_file]

    return _run(args)

def install_from_appjail_image(jail, entrypoint, image_name, image_arch, image_tag):
    imagesdir = overlord.config.get_appjail_images()

    args = []

    args.append(os.path.join(sys.prefix, "libexec/overlord/safe-exc.sh"))
    args.append(os.path.join(sys.prefix, "libexec/overlord/vm-install-from-appjail-image.sh"))
    args.extend(["-a", image_arch])
    args.extend(["-i", imagesdir])
    args.extend(["-I", image_name])
    args.extend(["-e", entrypoint])
    args.extend(["-j", jail])
    args.extend(["-t", image_tag])

    return _run(args)

def start(jail):
    args = []

    args.append(os.path.join(sys.prefix, "libexec/overlord/safe-exc.sh"))
    args.append(os.path.join(sys.prefix, "libexec/overlord/vm-start.sh"))
    args.extend(["-j", jail])

    return _run(args)

async def write_script(jail_path, content):
    script_path = os.path.join(jail_path, "run.sh")
    
    with open(script_path, "wb", buffering=0) as fd:
        fd.write(content.encode())
        fd.flush()
        os.fsync(fd.fileno())

    os.chmod(script_path, 0o555)

async def write_partitions(jail_path, scheme, partitions, bootcode=None):
    await _write_metadata(jail_path, "overlord.diskLayout.disk.scheme", scheme)

    for index, partition in enumerate(partitions, 1):
        for key, value in partition.items():
            if key == "format":
                if "flags" in value:
                    key = "format.flags"
                    value = value.get("flags")

                elif "script" in value:
                    key = "format.script"
                    value = value.get("script")

            await _write_metadata(jail_path, f"overlord.diskLayout.disk.partitions.{index}.{key}", value)

    if bootcode is not None:
        _bootcode = bootcode.get("bootcode")

        if _bootcode is not None:
            await _write_metadata(jail_path, "overlord.diskLayout.disk.bootcode.bootcode", _bootcode)

        partcode = bootcode.get("partcode")
        
        if partcode is not None:
            await _write_metadata(jail_path, "overlord.diskLayout.disk.bootcode.partcode", partcode)

        index = bootcode.get("index")

        if index is not None:
            await _write_metadata(jail_path, "overlord.diskLayout.disk.bootcode.index", "%s" % index)

async def write_fstab(jail_path, fstab):
    for index, entry in enumerate(fstab):
        for key, value in entry.items():
            await _write_metadata(jail_path, f"overlord.diskLayout.disk.fstab.{index}.{key}", "%s" % value)

async def write_metadata(jail_path, metadata):
    if not overlord.metadata.check(metadata):
        return

    content = await overlord.metadata.get(metadata)

    await _write_metadata(jail_path, metadata, content)

async def write_environment(jail_path, environment):
    _environment = []

    for kv in environment:
        for key, value in kv.items():
            _environment.append("export %s" % shlex.quote(f"{key}={value}"))

    _environment.append("\n")

    await _write_metadata(jail_path, "environment", "\n".join(_environment))

async def _write_metadata(jail_path, name, value):
    metadata_dir = os.path.join(jail_path, "metadata")

    os.makedirs(metadata_dir, exist_ok=True)

    metadata_path = os.path.join(metadata_dir, name)

    with open(metadata_path, "wb", buffering=0) as fd:
        fd.write(value.encode())
        fd.flush()
        os.fsync(fd.fileno())

def write_template(jail_path, template_name, template):
    vm_template = []

    for param_name, param_value in template.items():
        param_value = shlex.quote(param_value)

        vm_template.append(f"{param_name}={param_value}")

    vm_template = "\n".join(vm_template)
    vm_template += "\n"
    
    template_path = os.path.join(jail_path, f"vm/.templates/{template_name}.conf")

    with open(template_path, "wb", buffering=0) as fd:
        fd.write(vm_template.encode())
        fd.flush()
        os.fsync(fd.fileno())

def clone_template(jail_path, template_name, vm):
    template_path = os.path.join(jail_path, f"vm/.templates/{template_name}.conf")

    vmconf_path = os.path.join(jail_path, f"vm/{vm}/{vm}.conf")

    shutil.copy(template_path, vmconf_path)

def write_seed(jail_path, flags, datastore):
    cidir = os.path.join(jail_path, "cloud-init")

    os.makedirs(cidir, exist_ok=True)

    meta_data = datastore.get("meta-data")

    if meta_data is not None:
        meta_data_file = os.path.join(cidir, "meta-data")

        meta_data = yaml.dump(meta_data)

        with open(meta_data_file, "w") as fd:
            fd.write(meta_data)

    user_data = datastore.get("user-data")

    if user_data is not None:
        user_data_file = os.path.join(cidir, "user-data")

        user_data = "#cloud-config" + "\n" + yaml.dump(user_data)

        with open(user_data_file, "w") as fd:
            fd.write(user_data)

    network_config = datastore.get("network-config")

    if network_config is not None:
        network_config_file = os.path.join(cidir, "network-config")

        network_config = yaml.dump(network_config)

        with open(network_config_file, "w") as fd:
            fd.write(network_config)

    seed_file = os.path.join(jail_path, "seed.iso")

    if flags is None:
        flags = "-o R,L=cidata"

    flags = shlex.split(flags)

    args = ["makefs", "-t", "cd9660"] + flags + ["--", seed_file, cidir]

    return _run(args)

def create(jail, name, datastore=None, template=None, size=None, image=None):
    args = ["appjail", "cmd", "jexec", jail, "vm", "create"]

    if datastore is not None:
        args.extend(["-d", datastore])

    if template is not None:
        args.extend(["-t", template])

    if size is not None:
        args.extend(["-s", size])

    if image is not None:
        args.extend(["-i", image])

    args.append(name)

    return _run(args)

def poweroff(jail, name):
    args = ["appjail", "cmd", "jexec", jail, "vm", "poweroff", "-f", name]

    return _run(args)

def _run(args):
    (rc, stdout, stderr) = overlord.process.run_proc(args, merge_output=True)

    if stderr:
        logger.warning("(rc:%d, args:%s, stderr:1): %s", rc, repr(args), stderr.rstrip())

    output = stdout + stderr

    return (rc, output)
