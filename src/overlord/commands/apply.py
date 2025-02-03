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
import sys

import click
import httpx

import overlord.chains
import overlord.client
import overlord.commands
import overlord.default
import overlord.process
import overlord.spec
import overlord.util

from overlord.sysexits import EX_OK, EX_NOINPUT, EX_SOFTWARE

logger = logging.getLogger(__name__)

@overlord.commands.cli.command(add_help_option=False)
@click.option("-f", "--file", required=True)
def apply(*args, **kwargs):
    asyncio.run(_apply(*args, **kwargs))

async def _apply(file):
    try:
        deployments = 0

        overlord.spec.load(file)

        maximumDeployments = overlord.spec.get_maximumDeployments()

        exclude_labels = overlord.spec.get_deployIn_exclude()

        labels = overlord.spec.get_deployIn_labels()

        if len(labels) == 0:
            labels = overlord.default.LABELS

        entrypoints = overlord.spec.get_deployIn_entrypoints()
        datacenters = {}

        for entrypoint in entrypoints:
            (main_entrypoint, chain) = overlord.chains.get_chain(entrypoint)

            datacenter = overlord.spec.get_datacenter(main_entrypoint)

            if datacenter is None:
                logger.error("Datacenter '%s' cannot be found.", main_entrypoint)
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

            kind = overlord.spec.get_kind()

            if chain:
                chain = overlord.chains.join_chain(chain)
            else:
                chain = None

            client = overlord.client.OverlordClient(
                entrypoint,
                access_token,
                limits=httpx.Limits(**limits_settings),
                timeout=httpx.Timeout(**timeout_settings)
            )

            chains = [chain]

            async for _chain in client.get_all_chains(chain=chain):
                chains.append(_chain)

            for chain in chains:
                try:
                    entrypoint_labels = await client.get_api_labels(chain=chain)

                except Exception as err:
                    error = overlord.util.get_error(err)
                    error_type = error.get("type")
                    error_message = error.get("message")

                    logger.warning("Error obtaining the labels of entrypoint URL '%s' (chain:%s): %s: %s",
                                   client.base_url, chain, error_type, error_message)
                    continue

                exclude = False

                for label in entrypoint_labels:
                    if label in exclude_labels:
                        exclude = True

                        logger.debug("Entrypoint '%s' (chain:%s) will be excluded because it matches the label '%s'", datacenter, chain, label)

                        break

                if exclude:
                    logger.debug("Ignoring entrypoint '%s' (chain:%s)", datacenter, chain)

                    continue

                match = False

                for label in entrypoint_labels:
                    if label in labels:
                        match = True

                        logger.debug("Entrypoint '%s' (chain:%s) matches the label '%s'", datacenter, chain, label)

                        break

                if not match:
                    logger.debug("Ignoring entrypoint '%s' (chain:%s)", datacenter, chain)

                    continue

                if kind == overlord.spec.OverlordKindTypes.PROJECT.value:
                    project_name = overlord.spec.director_project.get_projectName()
                    environment = overlord.spec.director_project.get_environment(
                        datacenter=datacenter, chain=chain, labels=entrypoint_labels
                    )

                    project_from_metadata = overlord.spec.director_project.get_projectFromMetadata()

                    if project_from_metadata is None:
                        project_file = overlord.spec.director_project.get_projectFile()

                    else:
                        try:
                            logger.debug("Obtaining the project file '%s' at entrypoint URL '%s' (chain:%s)",
                                         project_from_metadata, client.base_url, chain)

                            project_file = await client.metadata_get(project_from_metadata, chain=chain)

                        except Exception as err:
                            error = overlord.util.get_error(err)
                            error_type = error.get("type")
                            error_message = error.get("message")

                            logger.warning("Error obtaining the project file '%s' at entrypoint URL '%s' (chain:%s): %s: %s",
                                           project_from_metadata, client.base_url, chain, error_type, error_message)

                            continue

                    try:
                        response = await client.up(project_name, project_file, environment, chain=chain)

                        deployments += 1

                    except Exception as err:
                        error = overlord.util.get_error(err)
                        error_type = error.get("type")
                        error_message = error.get("message")

                        logger.warning("Error creating the project '%s' at entrypoint URL '%s' (chain:%s): %s: %s",
                                       project_name, client.base_url, chain, error_type, error_message)

                        continue

                    job_id = response.get("job_id")

                    logger.debug("Job ID is '%d'", job_id)

                elif kind == overlord.spec.OverlordKindTypes.METADATA.value:
                    metadata = overlord.spec.metadata.get_metadata()

                    for key, value in metadata.items():
                        try:
                            logger.info("Writing metadata '%s' ...", key)

                            await client.metadata_set(key, value, chain=chain)

                            deployments += 1

                        except Exception as err:
                            error = overlord.util.get_error(err)
                            error_type = error.get("type")
                            error_message = error.get("message")

                            logger.exception("Error creating the metadata '%s' at entrypoint URL '%s' (chain:%s): %s: %s",
                                           key, client.base_url, chain, error_type, error_message)

                            continue

                if maximumDeployments > 0 \
                        and deployments >= maximumDeployments:
                    logger.warning("Maximum deployments has been reached! (%d/%d)", deployments, maximumDeployments)
                    sys.exit(EX_OK)

        if deployments == 0:
            logger.warning("No deployment has had any effect.")

    except Exception as err:
        error = overlord.util.get_error(err)
        error_type = error.get("type")
        error_message = error.get("message")

        logger.exception("%s: %s", error_type, error_message)

        sys.exit(EX_SOFTWARE)
