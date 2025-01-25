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
import re
import sys
import time

import asciitree
import click
import httpx
import humanfriendly

import overlord.client
import overlord.commands
import overlord.process
import overlord.util

from overlord.sysexits import EX_NOINPUT, EX_SOFTWARE

logger = logging.getLogger(__name__)

@overlord.commands.cli.command(add_help_option=False)
@click.option("-f", "--file", required=True)
@click.option("-t", "--type", required=True, type=click.Choice(("jails", "projects", "chains", "chains:tree", "projects:logs", "jails:logs")))
@click.option("--jail-item", multiple=True, default=[], type=click.Choice(["stats", "info", "cpuset", "devfs", "expose", "healthcheck", "limits", "fstab", "labels", "nat", "volumes"]))
@click.option("--all-labels", is_flag=True, default=False)
@click.option("--filter", default=[], multiple=True)
def get_info(*args, **kwargs):
    asyncio.run(_get_info(*args, **kwargs))

async def _get_info(file, type, jail_item, all_labels, filter):
    try:
        tree_chain = {}

        overlord.process.init()

        overlord.spec.load(file)

        exclude_labels = overlord.spec.get_deployIn_exclude()

        labels = overlord.spec.get_deployIn_labels()

        if len(labels) == 0:
            labels = overlord.default.LABELS

        entrypoints = overlord.spec.get_deployIn_entrypoints()

        for entrypoint in entrypoints:
            (main_entrypoint, chain) = overlord.chains.get_chain(entrypoint)

            if main_entrypoint not in overlord.spec.list_datacenters():
                logger.error("Datacenter '%s' cannot be found.", main_entrypoint)
                sys.exit(EX_NOINPUT)

            entrypoint = overlord.spec.get_datacenter_entrypoint(main_entrypoint)
            access_token = overlord.spec.get_datacenter_access_token(main_entrypoint)

            limits_settings = {
                "max_keepalive_connections" : overlord.spec.get_datacenter_max_keepalive_connections(main_entrypoint),
                "max_connections" : overlord.spec.get_datacenter_max_connections(main_entrypoint),
                "keepalive_expiry" : overlord.spec.get_datacenter_keepalive_expiry(main_entrypoint)
            }
            timeout_settings = {
                "timeout" : overlord.spec.get_datacenter_timeout(main_entrypoint),
                "read" : overlord.spec.get_datacenter_read_timeout(main_entrypoint),
                "write" : overlord.spec.get_datacenter_write_timeout(main_entrypoint),
                "connect" : overlord.spec.get_datacenter_connect_timeout(main_entrypoint),
                "pool" : overlord.spec.get_datacenter_pool_timeout(main_entrypoint)
            }

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
                entrypoint_labels = []

                if not all_labels:
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

                            logger.debug("Entrypoint '%s' (chain:%s) will be excluded because it matches the label '%s'", main_entrypoint, chain, label)

                            break

                    if exclude:
                        logger.debug("Ignoring entrypoint '%s' (chain:%s)", main_entrypoint, chain)

                        continue

                    match = False

                    for label in entrypoint_labels:
                        if label in labels:
                            match = True

                            logger.debug("Entrypoint '%s' (chain:%s) matches with label '%s'", main_entrypoint, chain, label)

                            break

                    if not match:
                        logger.debug("Ignoring entrypoint '%s' (chain:%s)", main_entrypoint, chain)

                        continue

                info = {
                    "datacenter" : entrypoint,
                    "entrypoint" : main_entrypoint,
                    "chain" : chain,
                    "labels" : entrypoint_labels
                }

                if type == "jails":
                    await print_info_jails(client, chain, info, jail_item, filter)

                elif type == "projects":
                    await print_info_projects(client, chain, info, filter)

                elif type == "chains":
                    if not match_pattern(chain, filter):
                        continue

                    print_header(info)

                elif type == "chains:tree":
                    if chain is None:
                        continue

                    if entrypoint not in tree_chain:
                        tree_chain[entrypoint] = {}

                    _root = tree_chain[entrypoint]

                    for _chain in overlord.chains.split_chain(chain):
                        if _chain not in _root:
                            _root[_chain] = {}

                        _root = _root[_chain]

                elif type == "projects:logs":
                    await print_info_projects_logs(client, chain, info, filter)

                elif type == "jails:logs":
                    await print_info_jails_logs(client, chain, info, filter)

        if tree_chain:
            tree = asciitree.LeftAligned()

            print(tree(tree_chain))

    except Exception as err:
        error = overlord.util.get_error(err)
        error_type = error.get("type")
        error_message = error.get("message")

        logger.exception("%s: %s:", error_type, error_message)

        sys.exit(EX_SOFTWARE)

def match_pattern(value, patterns):
    if not patterns:
        return True

    if value is None:
        return False

    for pattern in patterns:
        if re.search(pattern, value):
            return True

    return False

async def print_info_jails(client, chain, api_info, items, patterns):
    info = {}
    info.update(api_info)
    info["jails"] = {}

    jails = await _safe_client(client, "get_jails", chain=chain)

    if jails is None:
        return

    for jail in jails:
        if not match_pattern(jail, patterns):
            continue

        info["jails"][jail] = {}

        functions = []

        if not items:
            functions.extend(["get_stats", "get_info", "get_cpuset", "get_devfs", "get_expose", "get_healthcheck", "get_limits", "get_fstab", "get_labels", "get_nat", "get_volumes"])

        else:
            for item in items:
                functions.append(f"get_{item}")

        for func in functions:
            result = await _safe_client(client, func, jail, chain=chain)

            if result is not None:
                info["jails"][jail][func] = result

    jails = info.get("jails")

    if len(jails) == 0:
        logger.debug("Nothing to show in '%s' (chain:%s)",
                     api_info.get("datacenter"), api_info.get("chain"))
        return

    print_header(info)

    print("  jails:")

    for name, info in jails.items():
        print_name = True

        for func in ("get_stats", "get_info", "get_cpuset", "get_devfs", "get_expose", "get_healthcheck", "get_limits", "get_fstab", "get_labels", "get_nat", "get_volumes"):
            result = info.get(func)

            if result is None:
                continue

            if print_name:
                print(f"    {name}:")

                print_name = False

            info_name = func.replace("get_", "")

            if isinstance(result, str):
                print(f"        {info_name}: {result}")

            elif isinstance(result, list):
                if len(result) == 0:
                    continue

                print(f"      {info_name}:")

                for value in result:
                    print(f"        - {value}")

            elif isinstance(result, dict):
                if len(result) == 0:
                    continue

                print(f"      {info_name}:")

                for key, value in result.items():
                    if info_name == "stats":
                        value = _get_rctl_humanvalue(key, value)

                    print(f"        {key}: {value}")

def _get_rctl_humanvalue(key, value):
    if key == "datasize" \
            or key == "stacksize" \
            or key == "coredumpsize" \
            or key == "memoryuse" \
            or key == "memorylocked" \
            or key == "vmemoryuse" \
            or key == "swapuse" \
            or key == "shmsize" \
            or key == "readbps" \
            or key == "writebps":
        value = "%d (%s)" % (value, humanfriendly.format_size(value, binary=True))

    return value

async def print_info_projects(client, chain, api_info, patterns):
    info = {}
    info.update(api_info)
    info["projects"] = {}

    projects = await _safe_client(client, "get_projects", chain=chain)

    if projects is None:
        return

    for project in projects:
        if not match_pattern(project, patterns):
            continue

        result = await _safe_client(client, "get_info", project, type=overlord.client.OverlordEntityTypes.PROJECT, chain=chain)

        if result is not None:
            info["projects"][project] = result

        result = await _safe_client(client, "get_status_up", project, chain=chain)

        if result is not None:
            info["projects"][project]["up"] = result
        
        result = await _safe_client(client, "get_status_down", project, chain=chain)

        if result is not None:
            info["projects"][project]["down"] = result

    project_info = info["projects"]

    if len(project_info) == 0:
        logger.debug("Nothing to show in '%s' (chain:%s)",
                     api_info.get("datacenter"), api_info.get("chain"))
        return

    print_header(info)

    print("  projects:")

    for name, info in project_info.items():
        state = info.get("state")
        last_log = info.get("last_log")
        locked = info.get("locked")
        services = info.get("services", [])
        up = info.get("up", {})
        down = info.get("down", {})

        print(f"    {name}:")
        print(f"      state: {state}")
        print(f"      last_log: {last_log}")
        print(f"      locked: {locked}")
        print(f"      services:")

        for service in services:
            print(f"        - {service}")

        status = {
            "up" : up,
            "down" : down
        }

        for status_name, status_value in status.items():
            print_status_name = True

            for key, value in status_value.items():
                if print_status_name:
                    print(f"      {status_name}:")

                    print_status_name = False

                if isinstance(value, list):
                    print(f"        {key}:")

                    for _value in value:
                        print(f"        - {_value}")

                else:
                    if key == "last_update":
                        print("        last_update: %s" % time.ctime(value))

                    elif key == "output":
                        output = value

                        print_output = True

                        for key, value in output.items():
                            if print_output:
                                print("        output:")

                                print_output = False

                            if key == "stderr":
                                if len(value) == 0:
                                    continue

                                print(f"         {key}:")

                                for line in value.splitlines():
                                    print(f"           {line}")

                            else:
                                print(f"         {key}: {value}")

                    elif key == "labels":
                        error = value.get("error")
                        message = value.get("message")

                        print("        labels:")
                        print(f"         error: {error}")
                        print(f"         message: {message}")

                        load_balancer = value.get("load-balancer", {})

                        print_service = True

                        for service, info in load_balancer.items():
                            if print_service:
                                print("         load-balancer:")
                                print("           services:")

                                print_service = False

                            error = info.get("error")
                            message = info.get("message")

                            print(f"             {service}:")
                            print(f"               error: {error}")
                            print(f"               message: {message}")

                    else:
                        print(f"        {key}: {value}")

async def print_info_projects_logs(client, chain, api_info, patterns):
    logs = await _safe_client(client, "get_projects_logs", chain=chain)

    if logs is None:
        return

    files = []

    for date, services in logs.items():
        for service, logs in services.items():
            for log in logs:
                log_file = f"{date}/{service}/{log}"

                if not match_pattern(log_file, patterns):
                    continue

                files.append(log_file)

    if len(files) == 0:
        logger.debug("Nothing to show in '%s' (chain:%s)",
                     api_info.get("datacenter"), api_info.get("chain"))
        return

    print_header(api_info)

    print("  logs:")

    for log_file in files:
        print(f"    - {log_file}")

async def print_info_jails_logs(client, chain, api_info, patterns):
    logs = await _safe_client(client, "get_jails_logs", chain=chain)

    if logs is None:
        return

    files = []

    for type, entities in logs.items():
        for entity, subtypes in entities.items():
            for subtype, logs in subtypes.items():
                for logfile in logs:
                    log_file = f"{type}/{entity}/{subtype}/{logfile}"

                    if not match_pattern(log_file, patterns):
                        continue

                    files.append(log_file)

    if len(files) == 0:
        logger.debug("Nothing to show in '%s' (chain:%s)",
                     api_info.get("datacenter"), api_info.get("chain"))
        return

    print_header(api_info)

    print("  logs:")

    for log_file in files:
        print(f"    - {log_file}")

def print_header(info):
    datacenter = info.get("datacenter")
    entrypoint = info.get("entrypoint")
    chain = info.get("chain")
    labels = info.get("labels")

    print("datacenter:", datacenter)
    print("  entrypoint:", entrypoint)
    print("  chain:", chain)

    print_labels = True

    for label in labels:
        if print_labels:
            print("  labels:")

            print_labels = False

        print(f"    - {label}")

async def _safe_client(client, func, *args, **kwargs):
    try:
        return await getattr(client, func)(*args, **kwargs)

    except Exception as err:
        error = overlord.util.get_error(err)
        error_type = error.get("type")
        error_message = error.get("message")

        logger.warning("Error executing the function '%s': %s: %s", func, error_type, error_message)
