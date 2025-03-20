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

import os
import signal
import subprocess
import sys
import time

import psutil

import overlord.config
import overlord.trap

from overlord.sysexits import EX_SOFTWARE

PROCS = set()
INIT = False
EXIT = True

def run(cmd, env=None, timeout=None, cwd=None):
    init()

    settings = {
        "stdout" : subprocess.PIPE,
        "stderr" : subprocess.PIPE,
        "stdin" : subprocess.DEVNULL,
        "text" : True,
        "env" : env,
        "cwd" : cwd
    }

    if isinstance(cmd, str):
        settings["shell"] = True
    else:
        settings["shell"] = False

    with subprocess.Popen(cmd, **settings) as proc:
        PROCS.add(proc.pid)

        for line in proc.stdout:
            yield { "line" : line }

        for stderr in proc.stderr:
            yield { "stderr" : stderr }

        while True:
            try:
                if timeout is None:
                    timeout = overlord.config.get_execution_time()

                proc.wait(timeout)

            except subprocess.TimeoutExpired:
                proc.terminate()
                break

            except KeyboardInterrupt:
                proc.terminate()
                break

            if proc.poll() is not None:
                break

        yield { "rc" : proc.returncode }

    PROCS.remove(proc.pid)

def run_proc(*args, **kwargs):
    proc = run(*args, **kwargs)

    rc = 0
    stdout = []
    stderr = []

    for output in proc:
        if "line" in output:
            stdout.append(output["line"])

        elif "stderr" in output:
            stderr.append(output["stderr"])

        elif "rc" in output:
            rc = output["rc"]

    return (rc, " ".join(stdout), " ".join(stderr))

def notexit():
    global EXIT

    EXIT = False

def clean(*args, **kwargs):
    for pid in PROCS:
        if psutil.pid_exists(pid):
            os.kill(pid, signal.SIGTERM)

    if EXIT:
        sys.exit(EX_SOFTWARE)

def init():
    global INIT

    if not INIT:
        overlord.trap.add(clean)

        INIT = True

def kill_child_processes(ppid, sig=signal.SIGTERM):
    try:
        parent = psutil.Process(ppid)

    except psutil.NoSuchProcess:
        return

    children = parent.children(recursive=True)

    for process in children:
        process.send_signal(sig)
