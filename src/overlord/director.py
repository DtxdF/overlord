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

import json
import logging
import os
import re
import shutil

import overlord.process

logger = logging.getLogger(__name__)

def check_dependency():
    return shutil.which("appjail-director")

def check_project_name(name):
    return re.match(r"^[a-zA-Z0-9._-]+$", name) is not None

def get_list():
    proc = overlord.process.run("appjail-director ls | tail -n +2 | cut -d' ' -f3-")

    rc = 0

    projects = []

    for output in proc:
        if "rc" in output:
            rc = output["rc"]

        elif "stderr" in output:
            stderr = output["stderr"]
            stderr = stderr.rstrip()

            logger.warning("stderr: %s", stderr)

        elif "line" in output:
            project = output["line"]
            project = project.strip()

            projects.append(project)

    return (rc, projects)

def describe(project):
    proc = overlord.process.run(["appjail-director", "describe", "-p", project])

    rc = 0

    data = []

    for output in proc:
        if "rc" in output:
            rc = output["rc"]

        elif "stderr" in output:
            stderr = output["stderr"]
            stderr = stderr.rstrip()

            logger.warning("stderr: %s", stderr)

        elif "line" in output:
            value = output["line"]
            
            data.append(value)

    if data:
        project_info = json.loads("".join(data))

        last_log = project_info.get("last_log")

        if last_log is not None:
            last_log = last_log.split("/")[-1]

            project_info["last_log"] = last_log

    else:
        project_info = {}

    return (rc, project_info)

def up(name, director_file, env=None, cwd=None):
    proc = overlord.process.run(["appjail-director", "up", "-j", "-f", director_file, "-p", name], env=env, cwd=cwd)

    rc = 0

    data = []

    for output in proc:
        if "rc" in output:
            rc = output["rc"]

        elif "stderr" in output:
            stderr = output["stderr"]
            stderr = stderr.rstrip()

            logger.warning("stderr: %s", stderr)
        
        elif "line" in output:
            value = output["line"]

            data.append(value)

    if data:
        result = json.loads("".join(data))

    else:
        result = {}

    return (rc, result)

def down(name, destroy=False, ignore_failed=False, ignore_services=False, env=None, cwd=None):
    cmd = ["appjail-director", "down", "-j"]

    if destroy:
        cmd.append("-d")

    if ignore_failed:
        cmd.append("--ignore-failed")

    if ignore_services:
        cmd.append("--ignore-services")

    cmd.extend(["-p", name])

    proc = overlord.process.run(cmd, env=env, cwd=cwd)

    rc = 0

    data = []

    for output in proc:
        if "rc" in output:
            rc = output["rc"]

        elif "stderr" in output:
            stderr = output["stderr"]
            stderr = stderr.rstrip()

            logger.warning("stderr: %s", stderr)

        elif "line" in output:
            value = output["line"]

            data.append(value)

    if data:
        result = json.loads("".join(data))

    else:
        result = {}

    return (rc, result)

def check(project):
    proc = overlord.process.run(["appjail-director", "check", "-p", project])

    rc = 0

    for output in proc:
        if "rc" in output:
            rc = output["rc"]

    return rc == 0
