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
import sys

import overlord.config
import overlord.process
import overlord.metadata

logger = logging.getLogger(__name__)

def check_vm_name(name):
    return re.match(r"[a-zA-Z0-9][.a-zA-Z0-9_-]{0,229}[a-zA-Z0-9]", name) is not None

def is_done(jail_path):
    done_file = os.path.join(jail_path, ".done")

    return os.path.isfile(done_file)

def write_done(jail_path):
    done_file = os.path.join(jail_path, ".done")

    with open(done_file, "w"):
        pass

def install_from_components(jail, download_url, components_path, components):
    args = []

    args.append(os.path.join(sys.prefix, "libexec/overlord/safe-exc.sh"))
    args.append(os.path.join(sys.prefix, "libexec/overlord/vm-install-from-components.sh"))
    args.extend(["-c", components_path])
    args.extend(["-j", jail])
    args.extend(["-u", download_url])
    args.append("--")
    args.extend(components)

    proc = overlord.process.run(args)

    rc = 0

    lines = []

    for output in proc:
        if "rc" in output:
            rc = output["rc"]

            if rc != 0:
                lines = "\n".join(lines) + "\n"

                return (rc, lines)

        elif "stderr" in output:
            stderr = output["stderr"]
            stderr = stderr.rstrip()

            lines.append(stderr)

            logger.warning("stderr: %s", stderr)

        elif "line" in output:
            value = output["line"]
            value = value.rstrip()

            lines.append(value)

    lines = "\n".join(lines) + "\n"

    return (rc, lines)

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

    proc = overlord.process.run(args)

    rc = 0

    lines = []

    for output in proc:
        if "rc" in output:
            rc = output["rc"]

            if rc != 0:
                lines = "\n".join(lines) + "\n"

                return (rc, lines)

        elif "stderr" in output:
            stderr = output["stderr"]
            stderr = stderr.rstrip()

            lines.append(stderr)

            logger.warning("stderr: %s", stderr)

        elif "line" in output:
            value = output["line"]
            value = value.rstrip()

            lines.append(value)

    lines = "\n".join(lines) + "\n"

    return (rc, lines)

async def write_script(jail_path, content):
    script_path = os.path.join(jail_path, "run.sh")
    
    with open(script_path, "wb", buffering=0) as fd:
        fd.write(content.encode())
        fd.flush()
        os.fsync(fd.fileno())

    os.chmod(script_path, 0o555)

async def write_partitions(jail_path, scheme, partitions, bootcode):
    await _write_metadata(jail_path, "overlord.diskLayout.disk.scheme", scheme)

    for index, partition in enumerate(partitions, 1):
        for key, value in partition.items():
            if key == "format":
                key = "format.flags"
                value = value.get("flags")

                if value is None:
                    continue

            await _write_metadata(jail_path, f"overlord.diskLayout.disk.partitions.{index}.{key}", value)

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

def create(jail, name, datastore=None, template=None, size=None):
    args = ["appjail", "cmd", "jexec", jail, "vm", "create"]

    if datastore is not None:
        args.extend(["-d", datastore])

    if template is not None:
        args.extend(["-t", template])

    if size is not None:
        args.extend(["-s", size])

    args.append(name)

    proc = overlord.process.run(args)

    rc = 0

    lines = []

    for output in proc:
        if "rc" in output:
            rc = output["rc"]

            if rc != 0:
                lines = "\n".join(lines) + "\n"

                return (rc, lines)

        elif "stderr" in output:
            stderr = output["stderr"]
            stderr = stderr.rstrip()

            lines.append(stderr)

            logger.warning("stderr: %s", stderr)

        elif "line" in output:
            value = output["line"]
            value = value.rstrip()

            lines.append(value)

    lines = "\n".join(lines) + "\n"

    return (rc, lines)
