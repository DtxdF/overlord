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
import shutil

import overlord.config
import overlord.process
import overlord.util

logger = logging.getLogger(__name__)

def check_dependency():
    return shutil.which("appjail")

def check_jail_name(name):
    return re.match(r"^[a-zA-Z0-9_][a-zA-Z0-9_-]*$", name)

def get_jail_path(jail):
    jailsdir = overlord.config.get_appjail_jails()
    jaildir = os.path.join(jailsdir, jail, "jail")

    if not os.path.isdir(jaildir):
        return

    return jaildir

def get_list():
    jailsdir = overlord.config.get_appjail_jails()

    if not os.path.isdir(jailsdir):
        logger.warning("(dir:%s) can't find jails directory!", jailsdir)

        return None

    jails = os.listdir(jailsdir)

    return jails

def status(jail):
    args = ["appjail", "status", "-q", jail]

    (rc, _, _) = overlord.process.run_proc(args)

    return rc

def get_value(jail, keyword):
    args = ["appjail", "jail", "get", "-I", "--", jail, keyword]

    return _get_value(args)

def get_cpuset(jail):
    args = ["appjail", "cpuset", jail]

    return _get_value(args)

def get_devfs_nros(jail):
    ids = _list_ids(jail, "boot/devfs")
    
    if ids is None:
        return

    ids = [int(id) for id in ids]

    return ids

def get_devfs(jail, nro, keyword):
    value = _read(jail, f"boot/devfs/{nro}", keyword)

    return value

def list_devfs(jail, nro):
    keywords = overlord.config.get_polling_keywords_devfs()

    data = _list(jail, "nro", f"{nro}", get_devfs, keywords)
    
    return data

def get_expose_nros(jail):
    ids = _list_ids(jail, "boot/expose")
    
    if ids is None:
        return

    ids = [int(id) for id in ids]

    return ids

def get_expose(jail, nro, keyword):
    value = _read(jail, f"boot/expose/{nro}", keyword)

    return value

def list_expose(jail, nro):
    keywords = overlord.config.get_polling_keywords_expose()

    data = _list(jail, "nro", f"{nro}", get_expose, keywords)
    
    return data

def get_healthcheck_nros(jail):
    ids = _list_ids(jail, "boot/health")
    
    if ids is None:
        return

    ids = [int(id) for id in ids]

    return ids

def get_healthcheck(jail, nro, keyword):
    value = _read(jail, f"boot/health/{nro}", keyword)

    return value

def list_healthcheck(jail, nro):
    keywords = overlord.config.get_polling_keywords_healthcheck()

    data = _list(jail, "nro", f"{nro}", get_healthcheck, keywords)

    return data

def get_limits_nros(jail):
    ids = _list_ids(jail, "boot/limits")
    
    if ids is None:
        return

    ids = [int(id) for id in ids]

    return ids

def get_limits(jail, nro, keyword):
    value = _read(jail, f"boot/limits/{nro}", keyword)

    return value

def list_limits(jail, nro):
    keywords = overlord.config.get_polling_keywords_limits()

    data = _list(jail, "nro", f"{nro}", get_limits, keywords)

    return data

def get_fstab_nros(jail):
    ids = _list_ids(jail, "boot/fstab")

    if ids is None:
        return

    ids = [int(id) for id in ids]

    return ids

def get_fstab(jail, nro, keyword):
    if keyword == "device":
        keyword = "fs_spec"

    elif keyword == "mountpoint":
        keyword = "fs_file"

    elif keyword == "type":
        keyword = "fs_vfstype"

    elif keyword == "options":
        keyword = "fs_mntops"

    elif keyword == "dump":
        keyword = "fs_freq"

    elif keyword == "pass":
        keyword == "fs_passno"

    value = _read(jail, f"boot/fstab/{nro}", keyword)

    return value

def list_fstab(jail, nro):
    keywords = overlord.config.get_polling_keywords_fstab()

    data = _list(jail, "nro", f"{nro}", get_fstab, keywords)

    return data

def get_labels(jail):
    ids = _list_ids(jail, "labels")

    if ids is None:
        return

    return ids

def get_label(jail, label, keyword):
    value = _read(jail, f"labels/{label}", keyword)

    return value

def list_label(jail, label):
    keywords = overlord.config.get_polling_keywords_label()

    data = _list(jail, "name", label, get_label, keywords)

    return data

def get_nat_networks(jail):
    ids = _list_ids(jail, "boot/nat")

    if ids is None:
        return

    return ids

def get_nat(jail, network, keyword):
    value = None

    if keyword == "rule":
        # pf
        value = _read(jail, f"boot/nat/{network}", "pf-nat.conf")

    return value

def list_nat(jail, network):
    keywords = overlord.config.get_polling_keywords_nat()

    data = _list(jail, "network", network, get_nat, keywords)

    return data

def get_volumes(jail):
    ids = _list_ids(jail, "volumes")

    if ids is None:
        return

    return ids

def get_volume(jail, volume, keyword):
    value = _read(jail, f"volumes/{volume}", keyword)

    return value

def list_volume(jail, volume):
    keywords = overlord.config.get_polling_keywords_volume()

    data = _list(jail, "name", volume, get_volume, keywords)

    return data

def info(jail):
    data = {}

    rc = 0

    keywords = overlord.config.get_polling_keywords_jail()

    for keyword in keywords:
        (rc, value) = get_value(jail, keyword)

        if rc != 0:
            return (rc, None)

        data[keyword] = value

    return (rc, data)

def stats(jail):
    rc = 0
    data = {}
    
    keywords = overlord.config.get_polling_keywords_stats()

    if len(keywords) == 0:
        return (rc, data)

    args = ["rctl", "-u", f"jail:{jail}"]

    (rc, stdout, stderr) = overlord.process.run_proc(args)

    if rc != 0:
        logger.warning("(rc:%d, stderr:1): %s", rc, stderr.rstrip())

        return (rc, None)

    raw = stdout.splitlines()

    for raw_line in raw:
        (key, value) = raw_line.split("=", 1)

        key = key.strip()

        if key not in keywords:
            continue

        value = int(value)

        data[key] = value
        
    return (rc, data)

def _get_nros(args):
    (rc, stdout, stderr) = overlord.process.run_proc(args)

    if rc != 0:
        logger.warning("(rc:%d, args:%s, stderr:1): %s", rc, repr(args), stderr.rstrip())

        return (rc, None)

    nros = stdout.splitlines()
    nros = [int(nro) for nro in nros]

    return (rc, nros)

def _get_values(args):
    (rc, stdout, stderr) = overlord.process.run_proc(args)

    if rc != 0:
        logger.warning("(rc:%d, args:%s, stderr:1): %s", rc, repr(args), stderr.rstrip())

        return (rc, None)

    values = stdout.splitlines()
    values = [value.strip() for value in values]

    return (rc, values)

def _get_value(args):
    (rc, stdout, stderr) = overlord.process.run_proc(args)

    if rc != 0:
        logger.warning("(rc:%d, args:%s, stderr:1): %s", rc, repr(args), stderr.rstrip())

        return (rc, None)

    if len(stdout) > 0 and stdout[-1] == "\n":
        value = stdout[:-1]

    else:
        value = stdout

    return (rc, value)

def _list(jail, key, index, callback, keywords):
    data = {}

    if len(keywords) == 0:
        return data

    for keyword in keywords:
        value = callback(jail, index, keyword)

        data[keyword] = value

    data.update({ key : index })

    return data

def _list_ids(jail, namespace):
    jailsdir = overlord.config.get_appjail_jails()
    basedir = os.path.join(jailsdir, jail, f"conf/{namespace}")

    if not os.path.isdir(basedir):
        return

    values = os.listdir(basedir)

    return values

def _read(jail, namespace, keyword):
    jailsdir = overlord.config.get_appjail_jails()
    basedir = os.path.join(jailsdir, jail, f"conf/{namespace}")
    key = os.path.join(basedir, keyword)

    if not os.path.isfile(key):
        return

    value = None

    try:
        with open(key) as fd:
            value = fd.read()

            if value[-1] == "\n":
                value = value[:-1]

            if len(value) == 0:
                value = None

    except:
        error = overlord.util.get_error(err)
        error_type = error.get("type")
        error_message = error.get("message")

        logger.exception("(exception:%s) %s:", error_type, error_message)

    return value
