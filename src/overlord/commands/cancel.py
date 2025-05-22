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
import overlord.spec
import overlord.util

from overlord.sysexits import EX_OK, EX_NOINPUT, EX_SOFTWARE, EX_CONFIG

logger = logging.getLogger(__name__)

@overlord.commands.cli.command(add_help_option=False)
@click.option("-f", "--file", required=True)
@click.option("--filter-chain", default=[], multiple=True)
def cancel(*args, **kwargs):
    asyncio.run(_cancel(*args, **kwargs))

async def _cancel(file, filter_chain):
    try:
        overlord.spec.load(file)

        kind = overlord.spec.get_kind()

        if kind != overlord.spec.OverlordKindTypes.PROJECT.value \
                and kind != overlord.spec.OverlordKindTypes.VMJAIL.value:
            logger.error(f"(kind:{kind}) can't cancel this type of deployment!")
            sys.exit(EX_CONFIG)


        scale_options = overlord.spec.director_project.get_autoScale()

        if len(scale_options) > 0:
            logger.error(f"(kind:{kind}) can't cancel a deployment with scale options set.")
            sys.exit(EX_CONFIG)

        exclude_labels = overlord.spec.get_deployIn_exclude()

        labels = overlord.spec.get_deployIn_labels()

        entrypoints = overlord.spec.get_deployIn_entrypoints()
        datacenters = {}

        for entrypoint in entrypoints:
            (main_entrypoint, chain) = overlord.chains.get_chain(entrypoint)

            datacenter = overlord.spec.get_datacenter(main_entrypoint)

            if datacenter is None:
                logger.error("(datacenter:%s) data center cannot be found.", main_entrypoint)
                sys.exit(EX_NOINPUT)

            chain = overlord.chains.join_chain([main_entrypoint] + chain)

            datacenters[chain] = {
                "entrypoint" : overlord.spec.get_datacenter_entrypoint(main_entrypoint),
                "access_token" : overlord.spec.get_datacenter_access_token(main_entrypoint),
                "timeout" : overlord.spec.get_datacenter_timeout(main_entrypoint),
                "read_timeout" : overlord.spec.get_datacenter_read_timeout(main_entrypoint),
                "write_timeout" : overlord.spec.get_datacenter_write_timeout(main_entrypoint),
                "connect_timeout" : overlord.spec.get_datacenter_connect_timeout(main_entrypoint),
                "pool_timeout" : overlord.spec.get_datacenter_pool_timeout(main_entrypoint),
                "max_keepalive_connections" : overlord.spec.get_datacenter_max_keepalive_connections(main_entrypoint),
                "max_connections" : overlord.spec.get_datacenter_max_connections(main_entrypoint),
                "keepalive_expiry" : overlord.spec.get_datacenter_keepalive_expiry(main_entrypoint),
                "cacert" : overlord.spec.get_datacenter_cacert(main_entrypoint),
                "datacenter" : main_entrypoint
            }

        for chain, settings in datacenters.items():
            (datacenter, chain) = overlord.chains.get_chain(chain)
            entrypoint = settings.get("entrypoint")
            access_token = settings.get("access_token")

            limits_settings = {
                "max_keepalive_connections" : settings.get("max_keepalive_connections"),
                "max_connections" : settings.get("max_connections"),
                "keepalive_expiry" : settings.get("keepalive_expiry")
            }
            timeout_settings = {
                "timeout" : settings.get("timeout"),
                "read" : settings.get("read_timeout"),
                "write" : settings.get("write_timeout"),
                "connect" : settings.get("connect_timeout"),
                "pool" : settings.get("pool_timeout")
            }

            if chain:
                chain = overlord.chains.join_chain(chain)

            else:
                chain = None

            kwargs = {}

            cacert = settings.get("cacert")

            if cacert is not None:
                ctx = ssl.create_default_context(cafile=cacert)

                kwargs["verify"] = ctx

            client = overlord.client.OverlordClient(
                entrypoint,
                access_token,
                limits=httpx.Limits(**limits_settings),
                timeout=httpx.Timeout(**timeout_settings),
                **kwargs
            )

            chains = [chain]

            async for _chain in client.get_all_chains(chain=chain):
                chains.append(_chain)

            for chain in chains:
                if len(filter_chain) > 0 \
                        and chain not in filter_chain:
                    logger.debug("(datacenter:%s, chain:%s, filter:%s) it doesn't match the specified chain, ignoring ...",
                                 datacenter, chain, filter_chain)
                    continue

                try:
                    entrypoint_labels = await client.get_api_labels(chain=chain)

                except Exception as err:
                    error = overlord.util.get_error(err)
                    error_type = error.get("type")
                    error_message = error.get("message")

                    logger.warning("(datacenter:%s, chain:%s, exception:%s) error obtaining API labels: %s",
                                   datacenter, chain, error_type, error_message)
                    continue

                exclude = False

                for label in entrypoint_labels:
                    if label in exclude_labels:
                        exclude = True

                        logger.debug("(datacenter:%s, chain:%s, label:%s) excluding ...",
                                     datacenter, chain, label)

                        break

                if exclude:
                    continue

                match = False

                for label in entrypoint_labels:
                    if label in labels:
                        match = True

                        logger.debug("(datacenter:%s, chain:%s, label:%s) match!",
                                     datacenter, chain, label)

                        break

                if not match:
                    continue

                if kind == overlord.spec.OverlordKindTypes.PROJECT.value:
                    name = overlord.spec.director_project.get_projectName()

                elif kind == overlord.spec.OverlordKindTypes.VMJAIL.value:
                    name = overlord.spec.vm_jail.get_vmName()

                try:
                    response = await client.cancel(name, chain=chain)

                except Exception as err:
                    error = overlord.util.get_error(err)
                    error_type = error.get("type")
                    error_message = error.get("message")

                    logger.warning("(datacenter:%s, chain:%s, project:%s, exception:%s) error cancelling this project!",
                                   datacenter, chain, name, error_type, error_message)

                    continue

                job_id = response.get("job_id")

                if job_id is not None:
                    logger.debug("(datacenter:%s, chain:%s, project:%s, job:%d) request for cancelling has been made!",
                                 datacenter, chain, name, job_id)

    except Exception as err:
        error = overlord.util.get_error(err)
        error_type = error.get("type")
        error_message = error.get("message")

        logger.exception("(exception:%s) %s", error_type, error_message)

        sys.exit(EX_SOFTWARE)
