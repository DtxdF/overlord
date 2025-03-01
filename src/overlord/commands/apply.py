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
import io
import json
import logging
import sys

import click
import httpx
import yaml

import overlord.chains
import overlord.client
import overlord.commands
import overlord.default
import overlord.metadata
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

                metadata = {}

                if kind == overlord.spec.OverlordKindTypes.PROJECT.value:
                    project_name = overlord.spec.director_project.get_projectName()
                    environment = overlord.spec.director_project.get_environment(
                        datacenter=datacenter, chain=chain, labels=entrypoint_labels
                    )

                    environ_from_metadata = overlord.spec.director_project.get_environFromMetadata()

                    if environ_from_metadata is not None:
                        try:
                            _environment = await client.metadata_get(environ_from_metadata, chain=chain)

                        except Exception as err:
                            error = overlord.util.get_error(err)
                            error_type = error.get("type")
                            error_message = error.get("message")

                            logger.warning("(datacenter:%s, chain:%s, metadata:%s, exception:%s) error obtaining the environment from the metadata: %s",
                                           datacenter, chain, environ_from_metadata, error_type, error_message)
                            continue

                        with io.StringIO(initial_value=_environment) as fd:
                            try:
                                _environment = yaml.load(fd, Loader=yaml.SafeLoader)

                            except Exception as err:
                                error = overlord.util.get_error(err)
                                error_type = error.get("type")
                                error_message = error.get("message")

                                logger.warning("(datacenter:%s, chain:%s, metadata:%s, exception:%s) error parsing the environment: %s",
                                               datacenter, chain, environ_from_metadata, error_type, error_message)
                                continue

                        if not isinstance(_environment, dict):
                            logger.warning("(datacenter:%s, chain:%s, metadata:%s) environment is not a dictionary!",
                                           datacenter, chain, environ_from_metadata)
                            continue

                        environment.update(_environment)

                    logger.debug("(datacenter:%s, chain:%s): environment: %s",
                                 datacenter, chain, json.dumps(environment, indent=4))

                    project_from_metadata = overlord.spec.director_project.get_projectFromMetadata()

                    if project_from_metadata is None:
                        project_file = overlord.spec.director_project.get_projectFile()

                    else:
                        try:
                            project_file = await client.metadata_get(project_from_metadata, chain=chain)

                        except Exception as err:
                            error = overlord.util.get_error(err)
                            error_type = error.get("type")
                            error_message = error.get("message")

                            logger.warning("(datacenter:%s, chain:%s, metadata:%s, exception:%s) error obtaining the project file from the metadata: %s",
                                           datacenter, chain, project_from_metadata, error_type, error_message)

                            continue

                    scale_options = overlord.spec.director_project.get_autoScale()

                    if len(scale_options) == 0:
                        try:
                            response = await client.up(project_name, project_file, environment, chain=chain)

                            deployments += 1

                        except Exception as err:
                            error = overlord.util.get_error(err)
                            error_type = error.get("type")
                            error_message = error.get("message")

                            logger.warning("(datacenter:%s, chain:%s, project:%s, exception:%s) error creating the project: %s",
                                           datacenter, chain, project_name, error_type, error_message)

                            continue

                        job_id = response.get("job_id")

                        if job_id is not None:
                            logger.debug("(datacenter:%s, chain:%s, project:%s, job:%d) request for creating has been made!",
                                         datacenter, chain, project_name, job_id)

                    else:
                        metadata = {
                            f"overlord.autoscale.{project_name}" : json.dumps({
                                "projectFile" : project_file,
                                "environment" : environment,
                                "autoScale" : scale_options
                            }, indent=4)
                        }

                elif kind == overlord.spec.OverlordKindTypes.VMJAIL.value:
                    vm_name = overlord.spec.vm_jail.get_vmName()

                    profile = {
                        "template" : overlord.spec.vm_jail.get_template(),
                        "diskLayout" : overlord.spec.vm_jail.get_diskLayout()
                    }

                    makejail = overlord.spec.vm_jail.get_makejail()

                    if makejail is None:
                        profile["makejailFromMetadata"] = overlord.spec.vm_jail.get_makejailFromMetadata()

                    else:
                        profile["makejail"] = makejail

                    vm_script = overlord.spec.vm_jail.get_script()

                    if vm_script is not None:
                        profile["script"] = vm_script

                    vm_metadata = overlord.spec.vm_jail.get_metadata()

                    if vm_metadata:
                        profile["metadata"] = vm_metadata

                    try:
                        response = await client.create_vm(vm_name, profile, chain=chain)

                        deployments += 1

                    except Exception as err:
                        error = overlord.util.get_error(err)
                        error_type = error.get("type")
                        error_message = error.get("message")

                        logger.warning("(datacenter:%s, chain:%s, VM:%s, exception:%s) error creating the VM: %s",
                                       datacenter, chain, vm_name, error_type, error_message)

                        continue

                    job_id = response.get("job_id")

                    if job_id is not None:
                        logger.debug("(datacenter:%s, chain:%s, VM:%s, job:%d) request for creating has been made!",
                                     datacenter, chain, vm_name, job_id)

                if len(metadata) > 0 or \
                        kind == overlord.spec.OverlordKindTypes.METADATA.value:
                    if len(metadata) == 0:
                        metadata = overlord.spec.metadata.get_metadata()

                    for key, value in metadata.items():
                        if not overlord.metadata.check_keyname(key):
                            logger.warning("(datacenter:%s, chain:%s, metadata:%s) invalid metadata name.",
                                         datacenter, chain, key)
                            continue

                        try:
                            logger.info("(datacenter:%s, chain:%s, metadata:%s) Writing metadata ...",
                                        datacenter, chain, key)

                            await client.metadata_set(key, value, chain=chain)

                            deployments += 1

                        except Exception as err:
                            error = overlord.util.get_error(err)
                            error_type = error.get("type")
                            error_message = error.get("message")

                            logger.warning("(datacenter:%s, chain:%s, metadata:%s, exception:%s) error writing the metadata: %s",
                                           datacenter, chain, key, error_type, error_message)

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

        logger.exception("(exception:%s) %s", error_type, error_message)

        sys.exit(EX_SOFTWARE)
