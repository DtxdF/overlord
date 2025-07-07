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
import overlord.exceptions
import overlord.util

logger = logging.getLogger(__name__)

async def connect():
    addr = overlord.config.get_beanstalkd_addr()

    logger.debug("Connecting to '%s'", str(addr))

    client = aiostalk.Client(addr)

    await client.connect()

    return client

async def put(message, tube):
    client = await connect()

    secret = overlord.util.get_beanstalkd_secret()

    json_message = json.dumps(message)

    digest = overlord.util.hmac_hexdigest(secret, json_message.encode())

    message = {
        "message" : message,
        "digest" : digest
    }

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

    if "digest" not in job_body \
            or "message" not in job_body:
        raise overlord.exceptions.InvalidQueue(f"Malformed job body from job '{job_id}'")

    expected = job_body["digest"]
    message = job_body["message"]

    json_message = json.dumps(message)

    secret = overlord.util.get_beanstalkd_secret()

    digest = overlord.util.hmac_hexdigest(secret, json_message.encode())

    if not overlord.util.hmac_validation(secret, json_message.encode(), expected):
        raise overlord.exceptions.InvalidQueue(f"Job body validation failed from job '{job_id}': {expected} != {digest}")

    return (job_id, message)

async def reserve_project():
    return await reserve("overlord_project")

async def reserve_vm():
    return await reserve("overlord_vm")

async def put_create_project(message):
    return await put({ "type" : "create", "message" : message }, "overlord_project")

async def put_destroy_project(message):
    return await put({ "type" : "destroy", "message" : message }, "overlord_project")

async def put_cancel_project(message):
    return await put({ "type" : "cancel", "message" : message }, "overlord_project")

async def put_create_vm(message):
    return await put({ "type" : "create", "message" : message }, "overlord_vm")

async def put_destroy_vm(message):
    return await put({ "type" : "destroy", "message" : message }, "overlord_vm")
