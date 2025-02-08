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
import hashlib
import json
import logging
import sys
import time

import click
import httpx

import overlord.cache
import overlord.commands
import overlord.jwt
import overlord.config
import overlord.default
import overlord.director
import overlord.exceptions
import overlord.jail
import overlord.metadata
import overlord.process
import overlord.util

from overlord.sysexits import EX_SOFTWARE, EX_UNAVAILABLE

logger = logging.getLogger(__name__)

AUTOSCALE_CHANGES = {}

@overlord.commands.cli.command(add_help_option=False)
def poll_autoscale(*args, **kwargs):
    asyncio.run(_poll_autoscale(*args, **kwargs))

async def _poll_autoscale():
    overlord.process.init()

    try:
        main_port = overlord.config.get_port()
        main_entrypoint = f"http://127.0.0.1:{main_port}"

        limits_settings = {
            "max_keepalive_connections" : overlord.default.CHAIN_MAX_KEEPALIVE_CONNECTIONS,
            "max_connections" : overlord.default.CHAIN_MAX_CONNECTIONS,
            "keepalive_expiry" : overlord.default.CHAIN_KEEPALIVE_EXPIRY
        }
        timeout_settings = {
            "timeout" : overlord.default.CHAIN_TIMEOUT,
            "read" : overlord.default.CHAIN_READ_TIMEOUT,
            "write" : overlord.default.CHAIN_WRITE_TIMEOUT,
            "connect" : overlord.default.CHAIN_CONNECT_TIMEOUT,
            "pool" : overlord.default.CHAIN_POOL_TIMEOUT
        }

        access_token = overlord.jwt.encode({})

        client = overlord.client.OverlordClient(
            main_entrypoint,
            access_token,
            limits=httpx.Limits(**limits_settings),
            timeout=httpx.Timeout(**timeout_settings)
        )

        while True:
            files = overlord.metadata.glob("overlord.autoscale.*")

            for metadata_file in files:
                metadata = metadata_file.name

                logger.debug("(metadata:%s) processing ...", metadata)

                (_, project_name) = metadata.split("overlord.autoscale.", 1)

                overlord.cache.save_project_status_autoscale(project_name, {
                    "last_update" : time.time(),
                    "operation" : "RUNNING"
                })

                try:
                    value = await overlord.metadata.get(metadata)

                    options = json.loads(value)

                except Exception as err:
                    error = overlord.util.get_error(err)
                    error_type = error.get("type")
                    error_message = error.get("message")

                    overlord.cache.save_project_status_autoscale(project_name, {
                        "last_update" : time.time(),
                        "operation" : "FAILED",
                        "exception" : {
                            "type" : error_type,
                            "message" : error_message
                        }
                    })

                    logger.exception("(project:%s, exception:%s) %s", project_name, error_type, error_message)

                    continue

                checksum = hashlib.sha1(value.encode()).digest()

                if project_name in AUTOSCALE_CHANGES:
                    force = checksum != AUTOSCALE_CHANGES[project_name]

                else:
                    force = False

                AUTOSCALE_CHANGES[project_name] = checksum

                try:
                    result = await scale_project(client, project_name, options, force)

                except Exception as err:
                    error = overlord.util.get_error(err)
                    error_type = error.get("type")
                    error_message = error.get("message")

                    overlord.cache.save_project_status_autoscale(project_name, {
                        "last_update" : time.time(),
                        "operation" : "FAILED",
                        "exception" : {
                            "type" : error_type,
                            "message" : error_message
                        }
                    })

                    logger.exception("(project:%s, exception:%s) %s", project_name, error_type, error_message)

                    continue

                overlord.cache.save_project_status_autoscale(project_name, {
                    "last_update" : time.time(),
                    "operation" : "COMPLETED",
                    "output" : result
                })

            await asyncio.sleep(overlord.config.get_polling_autoscale() + overlord.util.get_skew())

    except Exception as err:
        error = overlord.util.get_error(err)
        error_type = error.get("type")
        error_message = error.get("message")

        logger.exception("(exception:%s) %s", error_type, error_message)

        sys.exit(EX_SOFTWARE)

async def scale_project(client, project_name, options, force):
    options = get_options(options)

    response = {
        "message" : None,
        "nodes" : {}
    }

    destroy = True

    fails = 0

    project_file = options.get("projectFile")
    environment = options.get("environment")
    scale_options = options.get("autoScale")
    replicas = scale_options.get("replicas")
    min = replicas.get("min")
    max = replicas.get("max")
    type = scale_options.get("type")
    value = scale_options.get("value")
    rules = scale_options.get("rules")
    labels = scale_options.get("labels")

    good = {
        "count" : 0,
        "nodes" : []
    }
    bad = {
        "count" : 0,
        "nodes" : []
    }

    def count_fails(*args, **kwargs):
        nonlocal fails

        fails += 1

    logger.debug("(project:%s, labels:%s) processing ...", project_name, labels)

    chains = [None]

    async for _chain in client.get_all_chains(on_fail=count_fails):
        chains.append(_chain)

    for chain in chains:
        try:
            if not await match_label(client, chain, labels):
                logger.debug("(chain:%s, project:%s, labels:%s) ignoring ...",
                             chain, project_name, labels)
                continue

        except Exception as err:
            count_fails()

            error = overlord.util.get_error(err)
            error_type = error.get("type")
            error_message = error.get("message")

            logger.exception("(chain:%s, project:%s, exception:%s) %s",
                             chain, project_name, error_type, error_message)
            continue

        try:
            health = await check_project(client, project_name, chain)

        except Exception as err:
            count_fails()

            error = overlord.util.get_error(err)
            error_type = error.get("type")
            error_message = error.get("message")

            logger.exception("(chain:%s, project:%s, exception:%s) %s", chain, project_name, error_type, error_message)

            continue

        if health:
            good["count"] += 1
            good["nodes"].append(chain)

            logger.debug("(chain:%s, project:%s, good:%d) will be placed on the good list", chain, project_name, good["count"])

        else:
            bad["count"] += 1
            bad["nodes"].append(chain)

            logger.debug("(chain:%s, project:%s, bad:%d) will be placed on the bad list", chain, project_name, bad["count"])

    cleanup = overlord.metadata.check(f"overlord.autoscale-cleanup.{project_name}")

    if force \
            and good["count"] > 0:
        if cleanup:
            # If a user has previously created a metadata to destroy the project and then the
            # same or another user changes the metadata, this cancels the previous request.
            overlord.metadata.delete(f"overlord.autoscale-cleanup.{project_name}")

        logger.debug("(project:%s) redeploying the project ...", project_name)

        for chain in good["nodes"]:
            logger.debug("(chain:%s, project:%s, nodes:%d) deploying ...", chain, project_name, good["count"])

            try:
                response["nodes"][chain] = await client.up(project_name, project_file, environment, chain=chain)

            except Exception as err:
                error = overlord.util.get_error(err)
                error_type = error.get("type")
                error_message = error.get("message")

                response["nodes"][chain] = {
                    "exception" : {
                        "type" : error_type,
                        "message" : error_message
                    }
                }

                logger.exception("(chain:%s, project:%s, exception:%s) %s", chain, project_name, error_type, error_message)

                continue

        return response

    if cleanup:
        nodes = {
            "count" : good["count"] + bad["count"],
            "nodes" : good["nodes"] + bad["nodes"]
        }

        if nodes["count"] > 0:
            logger.debug("(project:%s) destroying the project...", project_name)

            remove_metadata = True

            for chain in nodes["nodes"]:
                try:
                    if await client.check(project_name, type=overlord.client.OverlordEntityTypes.PROJECT, chain=chain):
                        logger.debug("(chain:%s, project:%s, nodes:%d) destroying ...", chain, project_name, nodes["count"])

                        response["nodes"][chain] = await client.down(project_name, environment, chain=chain)

                        remove_metadata = False

                except Exception as err:
                    error = overlord.util.get_error(err)
                    error_type = error.get("type")
                    error_message = error.get("message")

                    response["nodes"][chain] = {
                        "exception" : {
                            "type" : error_type,
                            "message" : error_message
                        }
                    }

                    logger.exception("(chain:%s, project:%s, exception:%s) %s", chain, project_name, error_type, error_message)

                    continue

            if not remove_metadata:
                return response

        if fails > 0:
            response["message"] = f"(project:{project_name}, fails:{fails}) metadata cannot be destroyed because there is a likelihood that a project has been deployed in a failed chain."

            logger.debug("(project:%s, fails:%d) metadata cannot be destroyed because there is a likelihood that a project has been deployed in a failed chain.",
                         project_name, fails)

        else:
            if overlord.metadata.check(f"overlord.autoscale.{project_name}"):
                logger.debug("(project:%s, metadata:overlord.autoscale.%s) destroying metadata ...",
                             project_name, project_name)

                overlord.metadata.delete(f"overlord.autoscale.{project_name}")

            if overlord.metadata.check(f"overlord.autoscale-cleanup.{project_name}"):
                logger.debug("(project:%s, metadata:overlord.autoscale-cleanup.%s) destroying metadata ...",
                             project_name, project_name)

                overlord.metadata.delete(f"overlord.autoscale-cleanup.{project_name}")

            response["message"] = "There are no more nodes to destroy the project."

        return response

    if max is None:
        max = good["count"] + bad["count"]

        logger.debug("(project:%s) 'max' is not specified, %d will be the default.", project_name, max)

    if good["count"] < min:
        logger.debug("(project:%s, nodes:%d, min:%d) more deployments are needed!", project_name, good["count"], min)

        for chain in bad["nodes"]:
            logger.debug("(chain:%s, project:%s, nodes:%d, min:%d) deploying ...", chain, project_name, good["count"], min)

            try:
                response["nodes"][chain] = await client.up(project_name, project_file, environment, chain=chain)

            except Exception as err:
                error = overlord.util.get_error(err)
                error_type = error.get("type")
                error_message = error.get("message")

                response["nodes"][chain] = {
                    "exception" : {
                        "type" : error_type,
                        "message" : error_message
                    }
                }

                logger.exception("(chain:%s, project:%s, exception:%s) %s", chain, project_name, error_type, error_message)

                continue

            good["count"] += 1

            if good["count"] >= min:
                logger.debug("(project:%s, nodes:%d, min:%d) done.", project_name, good["count"], min)

                break

        if good["count"] < min:
            logger.debug("(project:%s, nodes:%d, min:%d) insufficient nodes to replicate the project", project_name, good["count"], min)

            response["message"] = "Insufficient nodes to replicate the project (%d/%d)" % (good["count"], min)

        return response

    if rules is not None:
        index = 0

        logger.debug("(project:%s, rules:%d) processing rules ...", project_name, len(rules))

        for chain in good["nodes"]:
            try:
                test = await test_rctl(client, project_name, chain, type, value, rules)

            except Exception as err:
                error = overlord.util.get_error(err)
                error_type = error.get("type")
                error_message = error.get("message")

                response["nodes"][chain] = {
                    "exception" : {
                        "type" : error_type,
                        "message" : error_message
                    }
                }

                logger.exception("(chain:%s, project:%s, exception:%s) %s", chain, project_name, error_type, error_message)

                continue

            if test:
                logger.debug("(chain:%s, project:%s) ok", chain, project_name)
                continue

            else:
                logger.debug("(chain:%s, project:%s) fail", chain, project_name)

                # We need all nodes to pass the tests before we can start destroying projects.
                destroy = False

            if good["count"] >= max:
                logger.debug("(chain:%s, project:%s, nodes:%d, max:%d) maximum number of nodes has been reached", chain, project_name, good["count"], max)

                # We can't deploy more projects, but we need to perform the above tests.
                continue

            if bad["count"] == 0:
                logger.debug("(chain:%s, project:%s) I need more nodes, but there are no more!", chain, project_name)

                # We can't get out of the loop because we need to run the previous tests.
                # The exception is when a test fails, so it is safe to destroy projects.
                if destroy:
                    continue

                else:
                    break

            if index >= bad["count"]:
                logger.error("(chain:%s, project:%s) I need more nodes, but all the ones I could use have failed!", chain, project_name)

                # Idem.
                if destroy:
                    continue

                else:
                    break

            node = bad["nodes"][index]

            index += 1

            logger.debug("(chain:%s, project:%s, nodes:%d, max:%d) deploying ...", chain, project_name, bad["count"], max)

            try:
                response["nodes"][node] = await client.up(project_name, project_file, environment, chain=node)

            except Exception as err:
                error = overlord.util.get_error(err)
                error_type = error.get("type")
                error_message = error.get("message")

                response["nodes"][node] = {
                    "exception" : {
                        "type" : error_type,
                        "message" : error_message
                    }
                }

                logger.exception("(chain:%s, project:%s, exception:%s) %s", chain, project_name, error_type, error_message)

                continue

            else:
                return response

    if destroy \
            and good["count"] > min:
        logger.debug("(project:%s, nodes:%d, min:%d) I think it's time to destroy some projects 3:D", project_name, good["count"], min)

        for chain in good["nodes"]:
            logger.debug("(chain:%s, project:%s, nodes:%d, min:%d) destroying ...", chain, project_name, good["count"], min)

            try:
                response["nodes"][chain] = await client.down(project_name, environment, chain=chain)

            except Exception as err:
                error = overlord.util.get_error(err)
                error_type = error.get("type")
                error_message = error.get("message")

                response["nodes"][chain] = {
                    "exception" : {
                        "type" : error_type,
                        "message" : error_message
                    }
                }

                logger.exception("(chain:%s, project:%s, exception:%s) %s", chain, project_name, error_type, error_message)

                continue

            else:
                return response

    return response

async def test_rctl(client, project_name, chain, type, value, rules):
    if not await client.check(project_name, type=overlord.client.OverlordEntityTypes.PROJECT, chain=chain):
        return False

    info = await client.get_info(project_name, type=overlord.client.OverlordEntityTypes.PROJECT, chain=chain)

    state = info.get("state")

    if state == "UNFINISHED":
        # I assume that the project is currently be created.
        return True

    elif state != "DONE":
        return False

    services = info.get("services", {})
    total = {}

    for service_info in services:
        service_status = service_info["status"]

        if service_status != 0:
            return False

        service_jail = service_info["jail"]

        if not await client.check(service_jail, chain=chain):
            return False

        stats = await client.get_stats(service_jail, chain=chain)

        if len(stats) == 0:
            return False

        for rule_name, rule_value in rules.items():
            current_value = stats.get(rule_name)

            if type == "any-jail":
                result = current_value >= rule_value

                logger.debug("(project:%s, chain:%s, type:%s, value:%s, rule:%s) %d >= %d = %s",
                             project_name, chain, type, value, rule_name, current_value, rule_value, result)

                if result:
                    return False

            elif type == "any-project" \
                    or type == "percent-project" \
                    or type == "average":
                if rule_name not in total:
                    total[rule_name] = 0

                total[rule_name] += current_value

            elif type == "percent-jail":
                percent = (rule_value * value) / 100

                result = current_value >= percent

                logger.debug("(project:%s, chain:%s, type:%s, value:%s, rule:%s) %d >= %d = %s",
                             project_name, chain, type, value, rule_name, current_value, percent, result)

                if result:
                    return False

    for rule_name, total_value in total.items():
        rule_value = rules[rule_name]

        if type == "any-project":
            result = total_value >= rule_value

            logger.debug("(project:%s, chain:%s, type:%s, value:%s, rule:%s) %d >= %d = %s",
                         project_name, chain, type, value, rule_name, total_value, rule_value, result)

            if result:
                return False
        
        elif type == "percent-project":
            percent = (rule_value * value) / 100

            result = total_value >= percent

            logger.debug("(project:%s, chain:%s, type:%s, value:%s, rule:%s) %d >= %d = %s",
                         project_name, chain, type, value, rule_name, total_value, percent, result)

            if result:
                return False

        elif type == "average":
            average = total_value / len(services)

            result = average >= rule_value

            logger.debug("(project:%s, chain:%s, type:%s, value:%s, rule:%s) %d >= %d = %s",
                         project_name, chain, type, value, rule_name, average, rule_value, result)

            if result:
                return False

    return True

async def check_project(client, project_name, chain):
    if not await client.check(project_name, type=overlord.client.OverlordEntityTypes.PROJECT, chain=chain):
        return False

    info = await client.get_info(project_name, type=overlord.client.OverlordEntityTypes.PROJECT, chain=chain)

    state = info.get("state")

    if state == "UNFINISHED":
        # I assume that the project is currently be created.
        return True

    elif state != "DONE":
        return False

    services = info.get("services", {})

    for service_info in services:
        service_status = service_info["status"]

        if service_status != 0:
            return False

        service_jail = service_info["jail"]

        if not await client.check(service_jail, chain=chain):
            return False

        jail_info = await client.get_info(service_jail, chain=chain)

        is_dirty = jail_info.get("dirty", "0") == "1"

        if is_dirty:
            return False

        healthcheckers = await client.get_healthcheck(service_jail, chain=chain)

        for healthcheck in healthcheckers:
            healthcheck_status = healthcheck.get("status")

            if healthcheck_status is None:
                continue

            if healthcheck_status == "unhealthy":
                return False

    return True

def get_options(options):
    project_file = options.get("projectFile")

    if project_file is None:
        raise overlord.exceptions.InvalidSpec("'projectFile' is required but hasn't been specified.")

    overlord.spec.director_project.validate_environment(options)

    environment = options.get("environment")

    if environment is None:
        environment = {}

    overlord.spec.director_project.validate_autoScale(options)

    scale_options = options.get("autoScale")

    if scale_options is None:
        raise overlord.exceptions.InvalidSpec("'autoScale' is required but hasn't been specified.")

    scale_options = options.get("autoScale")

    if not scale_options:
        scale_options = overlord.default.SCALE

    replicas = scale_options.get("replicas")

    if replicas is None:
        replicas = overlord.default.SCALE["replicas"]

    min = replicas.get("min")

    if min is None:
        min = overlord.default.SCALE["replicas"]["min"]

    max = replicas.get("max")

    if max is not None:
        if max < min:
            raise overlord.exceptions.InvalidSpec(f"The maximum number of replicates is less than the minimum: {max} < {min}")

    type = scale_options.get("type")

    if type is None:
        type = overlord.default.SCALE["type"]

    labels = scale_options.get("labels")

    if labels is None:
        labels = overlord.default.LABELS

    options = {
        "projectFile" : project_file,
        "environment" : environment,
        "autoScale" : {
            "replicas" : {
                "min" : min,
                "max" : max
            },
            "type" : type,
            "value" : scale_options.get("value"),
            "rules" : scale_options.get("rules"),
            "labels" : labels
        }
    }

    return options

async def match_label(client, chain, labels):
    entrypoint_labels = await client.get_api_labels(chain=chain)

    for label in entrypoint_labels:
        if label in labels:
            return True

    return False

@overlord.commands.cli.command(add_help_option=False)
def poll_jails():
    check_appjail()

    try:
        while True:
            (rc, jails) = overlord.jail.get_list()

            if rc != 0:
                logger.error("(status:%d) error retrieving the list of jails.", rc)
                sys.exit(rc)

            overlord.cache.gc_jails(jails)

            time.sleep(overlord.config.get_polling_jails() + overlord.util.get_skew())

    except Exception as err:
        error = overlord.util.get_error(err)
        error_type = error.get("type")
        error_message = error.get("message")

        logger.exception("(exception:%s) %s", error_type, error_message)

        sys.exit(EX_SOFTWARE)

@overlord.commands.cli.command(add_help_option=False)
def poll_jail_info():
    check_appjail()

    try:
        overlord.process.init()

        while True:
            jails = overlord.cache.get_jails()

            for jail in jails:
                (rc, info) = overlord.jail.info(jail)

                if rc != 0:
                    logger.warning("(status:%d, jail:%s) error when retrieving information about the jail", rc, jail)
                    continue

                overlord.cache.save_jail_info(jail, info)

            time.sleep(overlord.config.get_polling_jail_info() + overlord.util.get_skew())

    except Exception as err:
        error = overlord.util.get_error(err)
        error_type = error.get("type")
        error_message = error.get("message")

        logger.exception("(exception:%s) %s", error_type, error_message)

        sys.exit(EX_SOFTWARE)

@overlord.commands.cli.command(add_help_option=False)
@click.option("--item", default=[], multiple=True, type=click.Choice(("cpuset", "devfs", "expose", "healthcheck", "limits", "fstab", "label", "nat", "volume")))
def poll_jail_extras(item):
    check_appjail()

    try:
        overlord.process.init()

        flags = {
            "cpuset" : False,
            "devfs" : False,
            "expose" : False,
            "healthcheck" : False,
            "limits" : False,
            "fstab" : False,
            "label" : False,
            "nat" : False,
            "volume" : False
        }

        items = item

        if len(items) == 0:
            for item in flags:
                flags[item] = True

        for item in items:
            flags[item] = True

        while True:
            jails = overlord.cache.get_jails()

            for jail in jails:
                if flags.get("cpuset") and overlord.jail.status(jail):
                    (rc, cpuset) = overlord.jail.get_cpuset(jail)

                    if rc != 0:
                        logger.warning("(status:%d, jail:%s) error when retrieving CPU sets", rc, jail)

                    else:
                        overlord.cache.save_jail_cpuset(jail, cpuset)

                if flags.get("devfs"):
                    (rc, nros) = overlord.jail.get_devfs_nros(jail)

                    if rc != 0:
                        logger.warning("(status:%d, jail:%s) error when retrieving DEVFS rules", rc, jail)

                    else:
                        data = []

                        for nro in nros:
                            (rc, devfs) = overlord.jail.list_devfs(jail, nro)

                            if rc != 0:
                                logger.warning("(status:%d, jail:%s, nro:%d) error when retrieving the DEVFS rule", rc, jail, nro)

                            else:
                                data.append(devfs)

                        overlord.cache.save_jail_devfs(jail, data)

                if flags.get("expose"):
                    (rc, nros) = overlord.jail.get_expose_nros(jail)

                    if rc != 0:
                        logger.warning("(status:%d, jail:%s) error when retrieving port-forwarding rules", rc, jail)

                    else:
                        data = []

                        for nro in nros:
                            (rc, expose) = overlord.jail.list_expose(jail, nro)

                            if rc != 0:
                                logger.warning("(status:%d, jail:%s, nro:%d) error when retrieving the port-forwarding rule", rc, jail, nro)

                            else:
                                data.append(expose)

                        overlord.cache.save_jail_expose(jail, data)

                if flags.get("healthcheck"):
                    (rc, nros) = overlord.jail.get_healthcheck_nros(jail)

                    if rc != 0:
                        logger.warning("(status:%d, jail:%s) error when retrieving healthcheckers", rc, jail)

                    else:
                        data = []

                        for nro in nros:
                            (rc, healthcheck) = overlord.jail.list_healthcheck(jail, nro)

                            if rc != 0:
                                logger.warning("(status:%d, jail:%s, nro:%d) error when retrieving the healthchecker", rc, jail, nro)

                            else:
                                data.append(healthcheck)

                        overlord.cache.save_jail_healthcheck(jail, data)

                if flags.get("limits"):
                    (rc, nros) = overlord.jail.get_limits_nros(jail)

                    if rc != 0:
                        logger.warning("(status:%d, jail:%s) error when retrieving limits rules", rc, jail)

                    else:
                        data = []

                        for nro in nros:
                            (rc, limits) = overlord.jail.list_limits(jail, nro)

                            if rc != 0:
                                logger.warning("(status:%d, jail:%s, nro:%d) error when retrieving the limits rule", rc, jail, nro)

                            else:
                                data.append(limits)

                        overlord.cache.save_jail_limits(jail, data)

                if flags.get("fstab"):
                    (rc, nros) = overlord.jail.get_fstab_nros(jail)

                    if rc != 0:
                        logger.warning("(status:%d, jail:%s) error when retrieving fstab entries", rc, jail)

                    else:
                        data = []

                        for nro in nros:
                            (rc, fstab) = overlord.jail.list_fstab(jail, nro)

                            if rc != 0:
                                logger.warning("(status:%d, jail:%s, nro:%d) error when retrieving the fstab entry", rc, jail, nro)

                            else:
                                data.append(fstab)

                        overlord.cache.save_jail_fstab(jail, data)

                if flags.get("label"):
                    (rc, labels) = overlord.jail.get_labels(jail)

                    if rc != 0:
                        logger.warning("(status:%d, jail:%s) error when retrieving the labels", rc, jail)

                    else:
                        data = []

                        for label in labels:
                            (rc, label) = overlord.jail.list_label(jail, label)

                            if rc != 0:
                                logger.warning("(status:%d, jail:%s, label:%s) error when retrieving the label", rc, jail, label)

                            else:
                                data.append(label)

                        overlord.cache.save_jail_label(jail, data)

                if flags.get("nat"):
                    (rc, networks) = overlord.jail.get_nat_networks(jail)

                    if rc != 0:
                        logger.warning("(status:%d, jail:%s) error when retrieving the NAT networks", rc, jail)

                    else:
                        data = []

                        for network in networks:
                            (rc, entries) = overlord.jail.list_nat(jail, network)

                            if rc != 0:
                                logger.warning("(status:%d, jail:%s, network:%s) error when retrieving the NAT entry", rc, jail, network)

                            else:
                                data.append(entries)

                        overlord.cache.save_jail_nat(jail, data)

                if flags.get("volume"):
                    (rc, volumes) = overlord.jail.get_volumes(jail)

                    if rc != 0:
                        logger.warning("(status:%d, jail:%s) error when retrieving volumes", rc, jail)

                    else:
                        data = []

                        for volume in volumes:
                            (rc, entries) = overlord.jail.list_volume(jail, volume)

                            if rc != 0:
                                logger.warning("(status:%d, jail:%s, volume:%s) error when retrieving the volume", rc, jail, volume)

                            else:
                                data.append(entries)

                        overlord.cache.save_jail_volume(jail, data)

            time.sleep(overlord.config.get_polling_jail_extras() + overlord.util.get_skew())

    except Exception as err:
        error = overlord.util.get_error(err)
        error_type = error.get("type")
        error_message = error.get("message")

        logger.exception("(exception:%s) %s", error_type, error_message)

        sys.exit(EX_SOFTWARE)

@overlord.commands.cli.command(add_help_option=False)
def poll_jail_stats():
    check_appjail()
    check_rctl()

    try:
        overlord.process.init()

        while True:
            jails = overlord.cache.get_jails()

            for jail in jails:
                if not overlord.jail.status(jail):
                    continue

                (rc, stats) = overlord.jail.stats(jail)

                if rc != 0:
                    logger.warning("(status:%d, jail:%s) error when retrieving the metrics", rc, jail)
                    continue

                overlord.cache.save_jail_stats(jail, stats)

            time.sleep(overlord.config.get_polling_jail_stats() + overlord.util.get_skew())

    except Exception as err:
        error = overlord.util.get_error(err)
        error_type = error.get("type")
        error_message = error.get("message")

        logger.exception("(exception:%s) %s", error_type, error_message)

        sys.exit(EX_SOFTWARE)

@overlord.commands.cli.command(add_help_option=False)
def poll_projects():
    check_director()

    try:
        while True:
            (rc, projects) = overlord.director.get_list()

            if rc != 0:
                logger.error("(status:%d) error retrieving the list of projects.", rc)
                sys.exit(rc)

            overlord.cache.gc_projects(projects)

            time.sleep(overlord.config.get_polling_projects() + overlord.util.get_skew())

    except Exception as err:
        error = overlord.util.get_error(err)
        error_type = error.get("type")
        error_message = error.get("message")

        logger.exception("(exception:%s) %s", error_type, error_message)

        sys.exit(EX_SOFTWARE)

@overlord.commands.cli.command(add_help_option=False)
def poll_project_info():
    check_director()

    try:
        overlord.process.init()

        while True:
            projects = overlord.cache.get_projects()

            for project in projects:
                (rc, info) = overlord.director.describe(project)

                if rc != 0:
                    logger.warning("(status:%d, project:%s) error when retrieving information about the project", rc, project)
                    continue

                overlord.cache.save_project_info(project, info)

            time.sleep(overlord.config.get_polling_project_info() + overlord.util.get_skew())

    except Exception as err:
        error = overlord.util.get_error(err)
        error_type = error.get("type")
        error_message = error.get("message")

        logger.exception("(exception:%s) %s", error_type, error_message)

        sys.exit(EX_SOFTWARE)

def check_appjail():
    if not overlord.jail.check_dependency():
        logger.error("AppJail is not installed. Cannot continue ...")
        sys.exit(EX_UNAVAILABLE)

def check_rctl():
    proc = overlord.process.run(["sysctl", "-n", "kern.racct.enable"])

    rc = 0
    value = None

    for output in proc:
        if "rc" in output:
            rc = output["rc"]

        elif "line" in output:
            value = output["line"]
            value = int(value)

    if value == 0:
        logger.error("rctl(4) framework is not enabled. Cannot continue ...")
        sys.exit(EX_UNAVAILABLE)

def check_director():
    if not overlord.director.check_dependency():
        logger.error("Director is not installed. Cannot continue ...")
        sys.exit(EX_UNAVAILABLE)
