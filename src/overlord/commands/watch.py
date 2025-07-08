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

import asyncio
import json
import logging
import os
import sys

import click

import overlord.commands
import overlord.config
import overlord.process
import overlord.queue
import overlord.util

from concurrent.futures import ProcessPoolExecutor

from overlord.sysexits import EX_SOFTWARE

logger = logging.getLogger(__name__)

EXECUTOR = None
CHILD = None

@overlord.commands.cli.command(add_help_option=False)
def watch_commands():
    global EXECUTOR

    max_commands = overlord.config.get_max_watch_commands()

    overlord.trap.add(clean)

    EXECUTOR = ProcessPoolExecutor(max_workers=max_commands)

    for _ in range(max_commands):
        EXECUTOR.submit(_watch_commands)

def _watch_commands(*args, **kwargs):
    asyncio.run(_async_watch_commands())

async def _async_watch_commands():
    global CHILD

    try:
        CHILD = os.getpid()

        overlord.process.init()

        while True:
            logger.debug("Waiting for new jobs ...")

            (job_id, job_body) = await overlord.queue.reserve_cmd()

            args = job_body.get("args")
            command = args[0]
            args = args[1:]

            logger.debug("(job:%d, command:%s, args-length:%d) Executing command with args: %s",
                         job_id, command, len(args), args)

            (rc, stdout, stderr) = overlord.process.run_proc([command] + args)

            logger.debug("(job:%d, command:%s, rc:%d) stdout:%s, stderr:%s",
                         job_id, command, rc, stdout, stderr)

    except Exception as err:
        error = overlord.util.get_error(err)
        error_type = error.get("type")
        error_message = error.get("message")

        logger.exception("(exception:%s) %s:", error_type, error_message)

        sys.exit(EX_SOFTWARE)

@overlord.commands.cli.command(add_help_option=False)
def watch_projects():
    asyncio.run(_async_watch_projects())

@overlord.commands.cli.command(add_help_option=False)
def watch_vm():
    asyncio.run(_async_watch_vm())

async def _async_watch_projects():
    try:
        overlord.process.init()

        while True:
            logger.debug("Waiting for new jobs ...")

            (job_id, job_body) = await overlord.queue.reserve_project()

            job_body.update({
                "job_id" : job_id
            })

            command = os.path.join(
                sys.prefix, "libexec/overlord/create.py"
            )

            json_data = json.dumps(job_body)

            args = [
                sys.executable, command,
                "projects", "-d", json_data
            ]

            await overlord.queue.put_cmd({
                "args" : args
            })

    except Exception as err:
        error = overlord.util.get_error(err)
        error_type = error.get("type")
        error_message = error.get("message")

        logger.exception("(exception:%s) %s:", error_type, error_message)

        sys.exit(EX_SOFTWARE)

async def _async_watch_vm():
    try:
        overlord.process.init()

        while True:
            logger.debug("Waiting for new jobs ...")

            (job_id, job_body) = await overlord.queue.reserve_vm()

            job_body.update({
                "job_id" : job_id
            })

            command = os.path.join(
                sys.prefix, "libexec/overlord/create.py"
            )

            json_data = json.dumps(job_body)

            args = [
                sys.executable, command,
                "vm", "-d", json_data
            ]

            await overlord.queue.put_cmd({
                "args" : args
            })

    except Exception as err:
        error = overlord.util.get_error(err)
        error_type = error.get("type")
        error_message = error.get("message")

        logger.exception("(exception:%s) %s:", error_type, error_message)

        sys.exit(EX_SOFTWARE)

def clean(*args, **kwargs):
    if CHILD is not None:
        logger.info("Terminated.")
        return

    logger.info("Cleaning up ...")

    overlord.process.kill_child_processes(os.getpid())

    if EXECUTOR is not None:
        EXECUTOR.shutdown(wait=False)
