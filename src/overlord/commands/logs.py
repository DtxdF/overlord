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
import ssl
import sys

import click
import httpx

import overlord.chains
import overlord.client
import overlord.commands
import overlord.process
import overlord.util

from overlord.sysexits import EX_NOINPUT, EX_SOFTWARE

logger = logging.getLogger(__name__)

@overlord.commands.cli.command(add_help_option=False)
@click.option("-f", "--file", required=True)
@click.option("-d", "--date", required=True)
@click.option("-s", "--service", required=True)
@click.option("-l", "--log", required=True)
@click.argument("entrypoint")
def get_project_log(*args, **kwargs):
    asyncio.run(_get_project_log(*args, **kwargs))

async def _get_project_log(file, date, service, log, entrypoint):
    try:
        overlord.process.init()

        overlord.spec.load(file)

        (entrypoint, chain) = overlord.chains.get_chain(entrypoint)

        if entrypoint not in overlord.spec.list_datacenters():
            logger.error("(datacenter:%s) data center cannot be found.", entrypoint)
            sys.exit(EX_NOINPUT)

        if chain:
            chain = overlord.chains.join_chain(chain)

        else:
            chain = None

        entrypoint_url = overlord.spec.get_datacenter_entrypoint(entrypoint)
        access_token = overlord.spec.get_datacenter_access_token(entrypoint)

        limits_settings = {
            "max_keepalive_connections" : overlord.spec.get_datacenter_max_keepalive_connections(entrypoint),
            "max_connections" : overlord.spec.get_datacenter_max_connections(entrypoint),
            "keepalive_expiry" : overlord.spec.get_datacenter_keepalive_expiry(entrypoint)
        }
        timeout_settings = {
            "timeout" : overlord.spec.get_datacenter_timeout(entrypoint),
            "read" : overlord.spec.get_datacenter_read_timeout(entrypoint),
            "write" : overlord.spec.get_datacenter_write_timeout(entrypoint),
            "connect" : overlord.spec.get_datacenter_connect_timeout(entrypoint),
            "pool" : overlord.spec.get_datacenter_pool_timeout(entrypoint)
        }

        kwargs = {}

        cacert = overlord.spec.get_datacenter_cacert(entrypoint)

        if cacert is not None:
            ctx = ssl.create_default_context(cafile=cacert)

            kwargs["verify"] = ctx

        client = overlord.client.OverlordClient(
            entrypoint_url,
            access_token,
            limits=httpx.Limits(**limits_settings),
            timeout=httpx.Timeout(**timeout_settings),
            **kwargs
        )

        log_content = await client.get_project_log(date, service, log, chain=chain)

        print(log_content)

    except Exception as err:
        error = overlord.util.get_error(err)
        error_type = error.get("type")
        error_message = error.get("message")

        logger.exception("(exception%s) %s:", error_type, error_message)

        sys.exit(EX_SOFTWARE)

@overlord.commands.cli.command(add_help_option=False)
@click.option("-f", "--file", required=True)
@click.option("-t", "--type", required=True)
@click.option("-e", "--entity", required=True)
@click.option("-s", "--subtype", required=True)
@click.option("-l", "--log", required=True)
@click.argument("entrypoint", type=str)
def get_jail_log(*args, **kwargs):
    asyncio.run(_get_jail_log(*args, **kwargs))

async def _get_jail_log(file, type, entity, subtype, log, entrypoint):
    try:
        overlord.process.init()

        overlord.spec.load(file)

        (entrypoint, chain) = overlord.chains.get_chain(entrypoint)

        if entrypoint not in overlord.spec.list_datacenters():
            logger.error("(datacenter:%s) data center cannot be found.", entrypoint)
            sys.exit(EX_NOINPUT)

        if chain:
            chain = overlord.chains.join_chain(chain)

        else:
            chain = None

        entrypoint_url = overlord.spec.get_datacenter_entrypoint(entrypoint)
        access_token = overlord.spec.get_datacenter_access_token(entrypoint)

        limits_settings = {
            "max_keepalive_connections" : overlord.spec.get_datacenter_max_keepalive_connections(entrypoint),
            "max_connections" : overlord.spec.get_datacenter_max_connections(entrypoint),
            "keepalive_expiry" : overlord.spec.get_datacenter_keepalive_expiry(entrypoint)
        }
        timeout_settings = {
            "timeout" : overlord.spec.get_datacenter_timeout(entrypoint),
            "read" : overlord.spec.get_datacenter_read_timeout(entrypoint),
            "write" : overlord.spec.get_datacenter_write_timeout(entrypoint),
            "connect" : overlord.spec.get_datacenter_connect_timeout(entrypoint),
            "pool" : overlord.spec.get_datacenter_pool_timeout(entrypoint)
        }

        client = overlord.client.OverlordClient(
            entrypoint_url,
            access_token,
            limits=httpx.Limits(**limits_settings),
            timeout=httpx.Timeout(**timeout_settings)
        )

        log_content = await client.get_jail_log(type, entity, subtype, log, chain=chain)

        print(log_content)

    except Exception as err:
        error = overlord.util.get_error(err)
        error_type = error.get("type")
        error_message = error.get("message")

        logger.exception("(exception:%s) %s:", error_type, error_message)

        sys.exit(EX_SOFTWARE)
