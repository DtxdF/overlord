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
import ssl
import sys
import tempfile

import click
import httpx
import yaml

import overlord.chains
import overlord.client
import overlord.commands
import overlord.util

from mako.template import Template
from mako.lookup import TemplateLookup

from overlord.sysexits import EX_NOINPUT, EX_SOFTWARE, EX_CONFIG

logger = logging.getLogger(__name__)

FROM_APPCONFIG = False

@overlord.commands.cli.command(add_help_option=False)
@click.option("-f", "--file", required=True)
@click.option("-F", "--force", is_flag=True, default=False)
@click.option("--filter-chain", default=[], multiple=True)
@click.option("--filter-root-chain", is_flag=True, default=False)
@click.option("--mako-directories", default=["."], multiple=True)
def destroy(*args, **kwargs):
    asyncio.run(_destroy(*args, **kwargs))

async def _destroy(file, force, filter_chain, filter_root_chain, mako_directories):
    global FROM_APPCONFIG

    try:
        overlord.spec.load(file)

        kind = overlord.spec.get_kind()

        if kind == overlord.spec.OverlordKindTypes.READONLY.value:
            logger.error("(kind:readOnly) can't destroy a read-only deployment!")
            sys.exit(EX_CONFIG)

        if FROM_APPCONFIG \
                and kind == overlord.spec.OverlordKindTypes.APPCONFIG.value:
            logger.error("(kind:appConfig) loop detected in an appConfig deployment!")
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
                if len(filter_chain) > 0:
                    if chain is None:
                        if not filter_root_chain:
                            logger.debug("(datacenter:%s, filter-root-chain:0) excluding root chain ...", datacenter)
                            continue

                    elif chain not in filter_chain:
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
                                _environment = yaml.load(_environment, Loader=yaml.SafeLoader)

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

                    try:
                        is_autoscalable = await client.metadata_check(f"overlord.autoscale.{project_name}", chain=chain)

                    except Exception as err:
                        error = overlord.util.get_error(err)
                        error_type = error.get("type")
                        error_message = error.get("message")

                        logger.warning("(datacenter:%s, chain:%s, exception:%s) error when checking if the project is auto-scalable: %s",
                                       datacenter, chain, error_type, error_message)

                        continue

                    if is_autoscalable:
                        metadata_cleanup = f"overlord.autoscale-cleanup.{project_name}"

                        if not overlord.metadata.check_keyname(metadata_cleanup):
                            logger.warning("(datacenter:%s, chain:%s, metadata:%s) invalid metadata name.",
                                         datacenter, chain, metadata_cleanup)
                            continue

                        try:
                            logger.info("(datacenter:%s, chain:%s, metadata:%s) Writing metadata ...",
                                        datacenter, chain, metadata_cleanup)

                            metadata_cleanup_value = {
                                "force" : force
                            }
                            metadata_cleanup_value = json.dumps(metadata_cleanup_value)

                            await client.metadata_set(
                                metadata_cleanup,
                                metadata_cleanup_value,
                                chain=chain
                            )

                        except Exception as err:
                            error = overlord.util.get_error(err)
                            error_type = error.get("type")
                            error_message = error.get("message")

                            logger.warning("(datacenter:%s, chain:%s, metadata:%s, exception:%s) error writing the metadata: %s",
                                           datacenter, chain, metadata_cleanup, error_type, error_message)

                            continue

                    else:
                        try:
                            response = await client.down(project_name, environment, force, chain=chain)

                        except Exception as err:
                            error = overlord.util.get_error(err)
                            error_type = error.get("type")
                            error_message = error.get("message")

                            logger.warning("(datacenter:%s, chain:%s, project:%s, exception:%s) error destroying the project: %s",
                                           datacenter, chain, project_name, error_type, error_message)

                            continue

                        job_id = response.get("job_id")

                        if job_id is not None:
                            logger.debug("(datacenter:%s, chain:%s, project:%s, job:%d) request for destruction has been made!",
                                         datacenter, chain, project_name, job_id)

                elif kind == overlord.spec.OverlordKindTypes.APPCONFIG.value:
                    appName = overlord.spec.app_config.get_appName()
                    appFrom = overlord.spec.app_config.get_appFrom()
                    appConfig = overlord.spec.app_config.get_appConfig()
                    appConfig["appName"] = appName

                    try:
                        appTemplate = await client.metadata_get(appFrom, chain=chain)

                    except Exception as err:
                        error = overlord.util.get_error(err)
                        error_type = error.get("type")
                        error_message = error.get("message")

                        logger.warning("(datacenter:%s, chain:%s, metadata:%s, exception:%s) error obtaining the template from the metadata: %s",
                                       datacenter, chain, appFrom, error_type, error_message)

                        continue

                    try:
                        appLookup = TemplateLookup(directories=mako_directories)
                        appRendered = Template(appTemplate, lookup=appLookup)

                        with io.StringIO(initial_value=appRendered.render(**appConfig)) as fd:
                            appSpec = yaml.load(fd, Loader=yaml.SafeLoader)

                        appSpec["datacenters"] = overlord.spec.get_datacenters()
                        appSpec["deployIn"] = overlord.spec.get_deployIn()
                        appSpec["maximumDeployments"] = overlord.spec.get_maximumDeployments()

                        appYAML = yaml.dump(appSpec)

                    except Exception as err:
                        error = overlord.util.get_error(err)
                        error_type = error.get("type")
                        error_message = error.get("message")

                        logger.warning("(datacenter:%s, chain:%s, metadata:%s, exception:%s) error parsing the template: %s",
                                       datacenter, chain, appFrom, error_type, error_message)
                        continue

                    appKind = appSpec.get("kind")

                    if appKind is None:
                        raise overlord.exceptions.InvalidSpec("(datacenter:%s, chain:%s, appFrom:%s) 'kind' is required but hasn't been specified." % (datacenter, chain, appFrom))

                    if appKind != overlord.spec.OverlordKindTypes.VMJAIL.value \
                            and appKind != overlord.spec.OverlordKindTypes.PROJECT.value:
                        raise overlord.exceptions.InvalidKind(f"(datacenter:%s, chain:%s, appFrom:%s, kind:%s): appConfig deployment only accepts the following deployments: directorProject and vmJail" % (datacenter, chain, appFrom, appKind))

                    with tempfile.NamedTemporaryFile(prefix="overlord", mode="wb", buffering=0) as fd:
                        fd.write(appYAML.encode())

                        FROM_APPCONFIG = True

                        await _destroy(
                            fd.name, force, filter_chain, filter_root_chain,
                            mako_directories
                        )

                    return

                elif kind == overlord.spec.OverlordKindTypes.METADATA.value:
                    metadata = overlord.spec.metadata.get_metadata()

                    for metadata_name in metadata:
                        if not overlord.metadata.check_keyname(metadata_name):
                            logger.warning("(datacenter:%s, chain:%s, metadata:%s) invalid metadata name.",
                                         datacenter, chain, metadata_name)
                            continue

                        try:
                            await client.metadata_delete(metadata_name, chain=chain)

                        except Exception as err:
                            error = overlord.util.get_error(err)
                            error_type = error.get("type")
                            error_message = error.get("message")

                            logger.warning("(datacenter:%s, chain:%s, metadata:%s, exception:%s) %s",
                                           datacenter, chain, metadata_name, error_type, error_message)

                            continue

                elif kind == overlord.spec.OverlordKindTypes.VMJAIL.value:
                    vm_name = overlord.spec.vm_jail.get_vmName()

                    try:
                        response = await client.down(vm_name, force=force, chain=chain)

                    except Exception as err:
                        error = overlord.util.get_error(err)
                        error_type = error.get("type")
                        error_message = error.get("message")

                        logger.warning("(datacenter:%s, chain:%s, VM:%s, exception:%s) error destroying the VM!",
                                       datacenter, chain, vm_name, error_type, error_message)

                        continue

                    job_id = response.get("job_id")

                    if job_id is not None:
                        logger.debug("(datacenter:%s, chain:%s, VM:%s, job:%d) request for destruction has been made!",
                                     datacenter, chain, vm_name, job_id)

    except Exception as err:
        error = overlord.util.get_error(err)
        error_type = error.get("type")
        error_message = error.get("message")

        logger.exception("(exception:%s) %s", error_type, error_message)

        sys.exit(EX_SOFTWARE)
