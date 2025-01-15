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
import logging
import os
import tempfile
import time

import click

import overlord.cache
import overlord.commands
import overlord.director
import overlord.queue

logger = logging.getLogger(__name__)

@overlord.commands.cli.command(add_help_option=False)
def watch_projects():
    asyncio.run(_watch_projects())

async def _watch_projects():
    overlord.process.init()

    while True:
        logger.debug("Waiting for new jobs ...")

        (job_id, job_body) = await overlord.queue.reserve_project()

        message = job_body.get("message")
        project = message.get("name")
        environment = dict(os.environ)
        environment.update(message.get("environment"))

        type = job_body.get("type")

        if type == "create":
            logger.debug(f"Creating project '{project}'")

            overlord.cache.save_project_status_up(project, {
                "operation" : "RUNNING",
                "last_project" : project,
                "last_update" : time.time(),
                "job_id" : job_id
            })

            director_file = message.get("director_file") + "\n"

            with tempfile.NamedTemporaryFile(prefix="overlord", mode="wb", buffering=0) as fd:
                fd.write(director_file.encode())

                (rc, result) = overlord.director.up(project, fd.name, env=environment)

                overlord.cache.save_project_status_up(project, {
                    "operation" : "COMPLETED",
                    "output" : result,
                    "last_project" : project,
                    "last_update" : time.time(),
                    "job_id" : job_id
                })

        elif type == "destroy":
            logger.debug(f"Destroying project '{project}'")

            overlord.cache.save_project_status_down(project, {
                "operation" : "RUNNING",
                "last_project" : project,
                "last_update" : time.time(),
                "job_id" : job_id
            })

            (rc, result) = overlord.director.down(project, destroy=True, ignore_failed=True, env=environment)

            overlord.cache.save_project_status_down(project, {
                "operation" : "COMPLETED",
                "output" : result,
                "last_project" : project,
                "last_update" : time.time(),
                "job_id" : job_id
            })
