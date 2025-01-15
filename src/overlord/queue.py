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

import aiostalk

import overlord.config

logger = logging.getLogger(__name__)

async def connect():
    addr = overlord.config.get_beanstalkd_addr()

    logger.debug("Connecting to '%s'", str(addr))

    client = aiostalk.Client(addr)

    await client.connect()

    return client

async def put(message, tube):
    client = await connect()

    json_message = json.dumps(message)

    logger.debug("Changing tube to '%s'", tube)

    await client.use(tube)

    logger.debug("Sending %d bytes", len(json_message))

    job_id = await client.put(json_message)

    await client.close()

    logger.debug("Job ID is '%d'", job_id)

    return job_id

async def reserve(tube):
    client = await connect()

    logger.debug("Watching tube '%s'", tube)

    await client.watch(tube)

    job = await client.reserve()

    await client.delete(job)
    await client.close()
    
    job_id = job.id
    job_body = json.loads(job.body)

    logger.debug("Job ID is '%d'", job_id)

    return (job_id, job_body)

async def reserve_project():
    return await reserve("overlord_project")

async def put_create_project(message):
    return await put({ "type" : "create", "message" : message }, "overlord_project")

async def put_destroy_project(message):
    return await put({ "type" : "destroy", "message" : message }, "overlord_project")
