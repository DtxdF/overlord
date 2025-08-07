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
    args = "appjail-director ls | tail -n +2 | cut -d' ' -f3-"

    (rc, stdout, stderr) = overlord.process.run_proc(args)

    if rc != 0:
        logger.warning("(rc:%d, args:%s, stderr:1): %s", rc, repr(args), stderr.rstrip())

        return (rc, None)

    projects = stdout.splitlines()
    projects = [project.strip() for project in projects]

    return (rc, projects)

def describe(project):
    args = ["appjail-director", "describe", "-p", project]

    (rc, stdout, stderr) = overlord.process.run_proc(args)

    if rc != 0:
        logger.warning("(rc:%d, args:%s, stderr:1): %s", rc, repr(args), stderr.rstrip())

        return (rc, None)

    data = json.loads(stdout)

    last_log = data.get("last_log")

    if last_log is not None:
        last_log = last_log.split("/")[-1]

        data["last_log"] = last_log

    return (rc, data)

def up(name, director_file, env=None, cwd=None, overwrite=False):
    args = ["appjail-director", "up", "-j", "-f", director_file, "-p", name]

    if overwrite:
        args.append("--overwrite")

    (rc, stdout, stderr) = overlord.process.run_proc(args, env=env, cwd=cwd)

    stdout = json.loads(stdout)

    output = {
        "rc" : rc,
        "stdout" : stdout,
        "stderr" : stderr
    }

    return output

def down(name, destroy=False, ignore_failed=False, ignore_services=False, env=None, cwd=None):
    args = ["appjail-director", "down", "-j"]

    if destroy:
        args.append("-d")

    if ignore_failed:
        args.append("--ignore-failed")

    if ignore_services:
        args.append("--ignore-services")

    args.extend(["-p", name])

    (rc, stdout, stderr) = overlord.process.run_proc(args, env=env, cwd=cwd)

    stdout = json.loads(stdout)

    output = {
        "rc" : rc,
        "stdout" : stdout,
        "stderr" : stderr
    }

    return output

def cancel(name, env=None, cwd=None):
    args = ["appjail-director", "cancel", "-p", name]

    (rc, _, _) = overlord.process.run_proc(args)

    return rc

def check(project):
    args = ["appjail-director", "check", "-p", project]

    (rc, _, _) = overlord.process.run_proc(args)

    return rc == 0
