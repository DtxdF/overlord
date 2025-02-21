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
import re
import shutil

import overlord.config
import overlord.process

logger = logging.getLogger(__name__)

def check_dependency():
    return shutil.which("appjail")

def check_jail_name(name):
    return re.match(r"^[a-zA-Z0-9_][a-zA-Z0-9_-]*$", name)

def get_jail_path(jail):
    proc = overlord.process.run(["appjail", "cmd", "local", jail, "realpath", "."])

    value = None

    for output in proc:
        if "rc" in output:
            rc = output["rc"]

            if rc != 0:
                return (rc, value)

        elif "stderr" in output:
            stderr = output["stderr"]
            stderr = stderr.rstrip()

            logger.warning("stderr: %s", stderr)

        elif "line" in output:
            value = output["line"]
            value = value.strip()

    return (rc, value)

def get_list():
    proc = overlord.process.run(["appjail", "jail", "list", "-eHIpt", "name"])

    rc = 0

    jails = []

    for output in proc:
        if "rc" in output:
            rc = output["rc"]

            if rc != 0:
                return (rc, jails)

        elif "stderr" in output:
            stderr = output["stderr"]
            stderr = stderr.rstrip()

            logger.warning("stderr: %s", stderr)

        elif "line" in output:
            jail = output["line"]
            jail = jail.strip()

            jails.append(jail)

    return (rc, jails)

def status(jail):
    proc = overlord.process.run(["appjail", "status", "-q", jail])

    rc = 0

    for output in proc:
        if "rc" in output:
            rc = output["rc"]

    return rc

def get_value(jail, keyword):
    proc = overlord.process.run(["appjail", "jail", "get", "-I", "--", jail, keyword])

    rc = 0

    value = None

    for output in proc:
        if "rc" in output:
            rc = output["rc"]

            if rc != 0:
                return (rc, value)

        elif "stderr" in output:
            stderr = output["stderr"]
            stderr = stderr.rstrip()

            logger.warning("stderr: %s", stderr)

        elif "line" in output:
            value = output["line"]
            value = value.strip()

    return (rc, value)

def get_stat(jail, keyword):
    proc = overlord.process.run(["appjail", "limits", "stats", "-heHIpt", "--", jail, keyword])

    rc = 0

    value = None

    for output in proc:
        if "rc" in output:
            rc = output["rc"]

            if rc != 0:
                return (rc, value)

        elif "stderr" in output:
            stderr = output["stderr"]
            stderr = stderr.rstrip()

            logger.warning("stderr: %s", stderr)

        elif "line" in output:
            value = output["line"]
            value = value.strip()
            value = int(value)

    return (rc, value)

def get_cpuset(jail):
    proc = overlord.process.run(["appjail", "cpuset", jail])

    rc = 0

    value = None

    for output in proc:
        if "rc" in output:
            rc = output["rc"]

            if rc != 0:
                return (rc, value)

        elif "stderr" in output:
            stderr = output["stderr"]
            stderr = stderr.rstrip()

            logger.warning("stderr: %s", stderr)

        elif "line" in output:
            value = output["line"]
            value = value.strip()

    return (rc, value)

def get_devfs_nros(jail):
    data = []

    proc = overlord.process.run(["appjail", "devfs", "list", "-eHIpt", "--", jail, "nro"])

    rc = 0

    for output in proc:
        if "rc" in output:
            rc = output["rc"]

            if rc != 0:
                return (rc, data)

        elif "stderr" in output:
            stderr = output["stderr"]
            stderr = stderr.rstrip()

            logger.warning("stderr: %s", stderr)

        elif "line" in output:
            value = output["line"]
            value = value.strip()
            value = int(value)

            data.append(value)

    return (rc, data)

def get_devfs(jail, nro, keyword):
    value = None

    rc = 0

    proc = overlord.process.run(["appjail", "devfs", "get", "-I", "-n", f"{nro}", "--", jail, keyword])

    for output in proc:
        if "rc" in output:
            rc = output["rc"]

            if rc != 0:
                return (rc, value)

        elif "stderr" in output:
            stderr = output["stderr"]
            stderr = stderr.rstrip()

            logger.warning("stderr: %s", stderr)

        elif "line" in output:
            value = output["line"]
            value = value.strip()

    return (rc, value)

def list_devfs(jail, nro):
    data = {}

    rc = 0

    keywords = overlord.config.get_polling_keywords_devfs()

    if len(keywords) == 0:
        return (rc, data)

    for keyword in keywords:
        (rc, value) = get_devfs(jail, nro, keyword)

        if rc != 0:
            return (rc, data)

        data[keyword] = value

    data.update({ "nro" : nro })

    return (rc, data)

def get_expose_nros(jail):
    data = []

    proc = overlord.process.run(["appjail", "expose", "list", "-eHIpt", "--", jail, "nro"])

    rc = 0

    for output in proc:
        if "rc" in output:
            rc = output["rc"]

            if rc != 0:
                return (rc, data)

        elif "stderr" in output:
            stderr = output["stderr"]
            stderr = stderr.rstrip()

            logger.warning("stderr: %s", stderr)

        elif "line" in output:
            value = output["line"]
            value = value.strip()
            value = int(value)

            data.append(value)

    return (rc, data)

def get_expose(jail, nro, keyword):
    value = None

    rc = 0

    proc = overlord.process.run(["appjail", "expose", "get", "-I", "-n", f"{nro}", "--", jail, keyword])

    for output in proc:
        if "rc" in output:
            rc = output["rc"]

            if rc != 0:
                return (rc, value)

        else:
            value = output["line"]
            value = value.strip()

    return (rc, value)

def list_expose(jail, nro):
    data = {}

    rc = 0

    keywords = overlord.config.get_polling_keywords_expose()

    if len(keywords) == 0:
        return (rc, data)

    for keyword in keywords:
        (rc, value) = get_expose(jail, nro, keyword)

        if rc != 0:
            return (rc, data)

        data[keyword] = value

    data.update({ "nro" : nro })

    return (rc, data)

def get_healthcheck_nros(jail):
    data = []

    proc = overlord.process.run(["appjail", "healthcheck", "list", "-eHIpt", "--", jail, "nro"])

    rc = 0

    for output in proc:
        if "rc" in output:
            rc = output["rc"]

            if rc != 0:
                return (rc, data)

        elif "stderr" in output:
            stderr = output["stderr"]
            stderr = stderr.rstrip()

            logger.warning("stderr: %s", stderr)

        elif "line" in output:
            value = output["line"]
            value = value.strip()
            value = int(value)

            data.append(value)

    return (rc, data)

def get_healthcheck(jail, nro, keyword):
    value = None

    rc = 0

    proc = overlord.process.run(["appjail", "healthcheck", "get", "-I", "-n", f"{nro}", "--", jail, keyword])

    for output in proc:
        if "rc" in output:
            rc = output["rc"]

            if rc != 0:
                return (rc, value)

        elif "stderr" in output:
            stderr = output["stderr"]
            stderr = stderr.rstrip()

            logger.warning("stderr: %s", stderr)

        elif "line" in output:
            value = output["line"]
            value = value.strip()

    return (rc, value)

def list_healthcheck(jail, nro):
    data = {}

    rc = 0

    keywords = overlord.config.get_polling_keywords_healthcheck()

    if len(keywords) == 0:
        return (rc, data)

    for keyword in keywords:
        (rc, value) = get_healthcheck(jail, nro, keyword)

        if rc != 0:
            return (rc, data)

        data[keyword] = value

    data.update({ "nro" : nro })

    return (rc, data)

def get_limits_nros(jail):
    data = []

    proc = overlord.process.run(["appjail", "limits", "list", "-eHIpt", "--", jail, "nro"])

    rc = 0

    for output in proc:
        if "rc" in output:
            rc = output["rc"]

            if rc != 0:
                return (rc, data)

        elif "stderr" in output:
            stderr = output["stderr"]
            stderr = stderr.rstrip()

            logger.warning("stderr: %s", stderr)

        elif "line" in output:
            value = output["line"]
            value = value.strip()
            value = int(value)

            data.append(value)

    return (rc, data)

def get_limits(jail, nro, keyword):
    value = None

    rc = 0

    proc = overlord.process.run(["appjail", "limits", "get", "-I", "-n", f"{nro}", "--", jail, keyword])

    for output in proc:
        if "rc" in output:
            rc = output["rc"]

            if rc != 0:
                return (rc, value)

        elif "stderr" in output:
            stderr = output["stderr"]
            stderr = stderr.rstrip()

            logger.warning("stderr: %s", stderr)

        elif "line" in output:
            value = output["line"]
            value = value.strip()

    return (rc, value)

def list_limits(jail, nro):
    data = {}

    rc = 0

    keywords = overlord.config.get_polling_keywords_limits()

    if len(keywords) == 0:
        return (rc, data)

    for keyword in keywords:
        (rc, value) = get_limits(jail, nro, keyword)

        if rc != 0:
            return (rc, data)

        data[keyword] = value

    data.update({ "nro" : nro })

    return (rc, data)

def get_fstab_nros(jail):
    data = []

    proc = overlord.process.run(["appjail", "fstab", "jail", jail, "list", "-eHIpt", "nro"])

    rc = 0

    for output in proc:
        if "rc" in output:
            rc = output["rc"]

            if rc != 0:
                return (rc, data)

        elif "stderr" in output:
            stderr = output["stderr"]
            stderr = stderr.rstrip()

            logger.warning("stderr: %s", stderr)

        elif "line" in output:
            value = output["line"]
            value = value.strip()
            value = int(value)

            data.append(value)

    return (rc, data)

def get_fstab(jail, nro, keyword):
    value = None

    rc = 0

    proc = overlord.process.run(["appjail", "fstab", "jail", jail, "get", "-I", "-n", f"{nro}", "--", keyword])

    for output in proc:
        if "rc" in output:
            rc = output["rc"]

            if rc != 0:
                return (rc, value)

        elif "stderr" in output:
            stderr = output["stderr"]
            stderr = stderr.rstrip()

            logger.warning("stderr: %s", stderr)

        elif "line" in output:
            value = output["line"]
            value = value.strip()

    return (rc, value)

def list_fstab(jail, nro):
    data = {}

    rc = 0

    keywords = overlord.config.get_polling_keywords_fstab()

    if len(keywords) == 0:
        return (rc, data)

    for keyword in keywords:
        (rc, value) = get_fstab(jail, nro, keyword)

        if rc != 0:
            return (rc, data)

        data[keyword] = value

    data.update({ "nro" : nro })

    return (rc, data)

def get_labels(jail):
    data = []

    proc = overlord.process.run(["appjail", "label", "list", "-eHIpt", "--", jail, "name"])

    rc = 0

    for output in proc:
        if "rc" in output:
            rc = output["rc"]

            if rc != 0:
                return (rc, data)

        elif "stderr" in output:
            stderr = output["stderr"]
            stderr = stderr.rstrip()

            logger.warning("stderr: %s", stderr)

        elif "line" in output:
            value = output["line"]
            value = value.rstrip("\n")

            data.append(value)

    return (rc, data)

def get_label(jail, label, keyword):
    value = None

    rc = 0

    proc = overlord.process.run(["appjail", "label", "get", "-I", "-l", f"{label}", "--", jail, keyword])

    for output in proc:
        if "rc" in output:
            rc = output["rc"]

            if rc != 0:
                return (rc, value)

        elif "stderr" in output:
            stderr = output["stderr"]
            stderr = stderr.rstrip()

            logger.warning("stderr: %s", stderr)

        elif "line" in output:
            value = output["line"]
            value = value.rstrip("\n")

    return (rc, value)

def list_label(jail, label):
    data = {}

    rc = 0

    keywords = overlord.config.get_polling_keywords_label()

    if len(keywords) == 0:
        return (rc, data)

    for keyword in keywords:
        (rc, value) = get_label(jail, label, keyword)

        if rc != 0:
            return (rc, data)

        data[keyword] = value

    data.update({ "name" : label })

    return (rc, data)

def get_nat_networks(jail):
    data = []

    proc = overlord.process.run(["appjail", "nat", "list", "jail", "-eHIpt", "--", jail, "network"])

    rc = 0

    for output in proc:
        if "rc" in output:
            rc = output["rc"]

            if rc != 0:
                return (rc, data)

        elif "stderr" in output:
            stderr = output["stderr"]
            stderr = stderr.rstrip()

            logger.warning("stderr: %s", stderr)

        elif "line" in output:
            value = output["line"]
            value = value.rstrip("\n")

            data.append(value)

    return (rc, data)

def get_nat(jail, network, keyword):
    value = None

    rc = 0

    proc = overlord.process.run(["appjail", "nat", "get", "jail", "-I", "-n", f"{network}", "--", jail, keyword])

    for output in proc:
        if "rc" in output:
            rc = output["rc"]

            if rc != 0:
                return (rc, value)

        elif "stderr" in output:
            stderr = output["stderr"]
            stderr = stderr.rstrip()

            logger.warning("stderr: %s", stderr)

        elif "line" in output:
            value = output["line"]
            value = value.rstrip("\n")

    return (rc, value)

def list_nat(jail, network):
    data = {}

    rc = 0

    keywords = overlord.config.get_polling_keywords_nat()

    if len(keywords) == 0:
        return (rc, data)

    for keyword in keywords:
        (rc, value) = get_nat(jail, network, keyword)

        if rc != 0:
            return (rc, data)

        data[keyword] = value

    data.update({ "network" : network })

    return (rc, data)

def get_volumes(jail):
    data = []

    proc = overlord.process.run(["appjail", "volume", "list", "-eHIpt", "--", jail, "name"])

    rc = 0

    for output in proc:
        if "rc" in output:
            rc = output["rc"]

            if rc != 0:
                return (rc, data)

        elif "stderr" in output:
            stderr = output["stderr"]
            stderr = stderr.rstrip()

            logger.warning("stderr: %s", stderr)

        elif "line" in output:
            value = output["line"]
            value = value.rstrip("\n")

            data.append(value)

    return (rc, data)

def get_volume(jail, volume, keyword):
    value = None

    rc = 0

    proc = overlord.process.run(["appjail", "volume", "get", "-I", "-v", f"{volume}", "--", jail, keyword])

    for output in proc:
        if "rc" in output:
            rc = output["rc"]

            if rc != 0:
                return (rc, value)

        elif "stderr" in output:
            stderr = output["stderr"]
            stderr = stderr.rstrip()

            logger.warning("stderr: %s", stderr)

        elif "line" in output:
            value = output["line"]
            value = value.rstrip("\n")

    return (rc, value)

def list_volume(jail, volume):
    data = {}

    rc = 0

    keywords = overlord.config.get_polling_keywords_volume()

    if len(keywords) == 0:
        return (rc, data)

    for keyword in keywords:
        (rc, value) = get_volume(jail, volume, keyword)

        if rc != 0:
            return (rc, data)

        data[keyword] = value

    data.update({ "name" : volume })

    return (rc, data)

def info(jail):
    data = {}

    rc = 0

    keywords = overlord.config.get_polling_keywords_jail()

    for keyword in keywords:
        (rc, value) = get_value(jail, keyword)

        if rc != 0:
            return (rc, data)

        data[keyword] = value

    return (rc, data)

def stats(jail):
    data = {}

    rc = 0

    keywords = overlord.config.get_polling_keywords_stats()

    for keyword in keywords:
        (rc, value) = get_stat(jail, keyword)

        if rc != 0:
            return (rc, data)

        data[keyword] = value
        
    return (rc, data)
