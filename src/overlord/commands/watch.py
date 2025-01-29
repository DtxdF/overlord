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
import json
import logging
import os
import re
import sys
import tempfile
import time

import click
import httpx

import overlord.cache
import overlord.commands
import overlord.config
import overlord.dataplaneapi
import overlord.default
import overlord.director
import overlord.skydns
import overlord.queue
import overlord.util

logger = logging.getLogger(__name__)

@overlord.commands.cli.command(add_help_option=False)
def watch_projects():
    asyncio.run(_watch_projects())

async def _watch_projects():
    try:
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
                    "last_update" : time.time(),
                    "job_id" : job_id
                })

                director_file = message.get("director_file") + "\n"

                with tempfile.NamedTemporaryFile(prefix="overlord", mode="wb", buffering=0) as fd:
                    fd.write(director_file.encode())

                    result = overlord.director.up(project, fd.name, env=environment)

                    special_labels_response = await run_special_labels(project, type)

                    error = special_labels_response.get("error")

                    if not error:
                        for integration in ("load-balancer", "skydns"):
                            integration_info = special_labels_response.get(integration, {})

                            error = integration_info.get("error", False)

                            if error:
                                break

                    if error:
                        operation_status = "INCOMPLETED"

                    else:
                        operation_status = "COMPLETED"

                    overlord.cache.save_project_status_up(project, {
                        "operation" : operation_status,
                        "output" : result,
                        "last_update" : time.time(),
                        "job_id" : job_id,
                        "labels" : special_labels_response
                    })

            elif type == "destroy":
                logger.debug(f"Destroying project '{project}'")

                special_labels_response = await run_special_labels(project, type)

                overlord.cache.save_project_status_down(project, {
                    "operation" : "RUNNING",
                    "last_update" : time.time(),
                    "job_id" : job_id,
                    "labels" : special_labels_response
                })

                error = special_labels_response.get("error")

                if not error:
                    for integration in ("load-balancer", "skydns"):
                        integration_info = special_labels_response.get(integration, {})

                        error = integration_info.get("error", False)

                        if error:
                            break

                if error:
                    operation_status = "INCOMPLETED"
                    result = {}

                else:
                    operation_status = "COMPLETED"
                    result = overlord.director.down(project, destroy=True, ignore_failed=True, env=environment)

                overlord.cache.save_project_status_down(project, {
                    "operation" : operation_status,
                    "output" : result,
                    "last_update" : time.time(),
                    "job_id" : job_id,
                    "labels" : special_labels_response
                })

    except Exception as err:
        error = overlord.util.get_error(err)
        error_type = error.get("type")
        error_message = error.get("message")

        logger.exception("%s: %s:", error_type, error_message)

        sys.exit(EX_SOFTWARE)

async def run_special_labels(project, type):
    response = {
        "error" : False,
        "message" : None
    }

    if not overlord.director.check(project):
        return response

    (rc, info) = overlord.director.describe(project)

    if rc != 0:
        response["error"] = True
        response["message"] = "Error retrieving information about the project '%s'" % project

        return response

    state = info["state"]

    if state != "DONE":
        response["error"] = True
        response["message"] = "Project '%s' has an unexpected state '%s'" % (project, state)

        return response

    services = info["services"]

    for service in services:
        name = service["name"]
        status = service["status"]
        jail = service["jail"]

        if status != 0:
            continue

        (rc, labels) = overlord.jail.get_labels(jail)

        if rc != 0:
            logger.warning("Error retrieving the labels of service '%s.%s' - exit status code is %d", project, name, rc)

        else:
            data = {}

            for label in labels:
                if not label.startswith("overlord."):
                    continue

                (rc, label) = overlord.jail.list_label(jail, label)

                if rc != 0:
                    logger.warning("Error retrieving the label of service '%s.%s' - exit status code is %d", project, name, rc)

                else:
                    label_name = label["name"]
                    label_value = label["value"]

                    data[label_name] = label_value

            for integration in ("load-balancer", "skydns"):
                if integration not in response:
                    response[integration] = {}

                try:
                    if integration == "load-balancer":
                        task = run_special_label_load_balancer(project, type, service, data)

                    elif integration == "skydns":
                        task = run_special_label_skydns(project, type, service, data)

                    (error, message) = await task

                    response[integration][name] = {
                        "error" : error,
                        "message" : message
                    }

                except Exception as err:
                    error = overlord.util.get_error(err)
                    error_type = error.get("type")
                    error_message = error.get("message")

                    logger.exception("Exception in %s: %s: %s", integration, error_type, error_message)

                    response[integration][name] = {
                        "error" : True,
                        "message" : "Exception %s: %s" % (error_type, error_message)
                    }

    return response

async def run_special_label_skydns(project, type, service, labels):
    service_name = service["name"]

    use_skydns = labels.get("overlord.skydns")

    if use_skydns is None:
        error = False
        message = None

        return (error, message)

    group = labels.get("overlord.skydns.group")

    if group is None:
        error = True
        message = f"(project:{project}, service:{service_name}, label:overlord.skydns.group) group has not been specified, but is required."

        return (error, message)

    interface = labels.get("overlord.skydns.interface")

    if interface is None:
        error = True
        message = f"(project:{project}, service:{service_name}, label:overlord.skydns.interface) interface has not been specified, but is required."

        return (error, message)

    network = labels.get("overlord.skydns.interface.address")

    try:
        address = overlord.util.iface2ip(interface, network)

    except Exception as err:
        error = overlord.util.get_error(err)
        error_type = error.get("type")
        error_message = error.get("message")

        error = True
        message = f"(project:{project}, service:{service_name}, label:overlord.skydns.interface.address exception:{error_type}) {error_message}"

        return (error, message) 

    if type == "destroy":
        error = False
        
        records = overlord.skydns.delete_records(group)
        ptr = overlord.skydns.delete_ptr(address)

        message = f"(project:{project}, service:{service_name}, records:[all:{records},ptr:{ptr}]) DNS records have been removed."

        return (error, message)

    ttl = labels.get("overlord.skydns.ttl", overlord.default.DNS["ttl"])

    try:
        ttl = int(ttl)

    except ValueError:
        error = True
        message = f"(project:{project}, service:{service_name}, label:overlord.skydns.ttl) invalid TTL."

        return (error, message)

    response = {
        "ptr" : None,
        "txt" : [],
        "address" : None,
        "srv" : None
    }

    result = overlord.skydns.update_address(address, group, ttl)

    response["address"] = result

    use_skydns_ptr = labels.get("overlord.skydns.ptr")

    if use_skydns_ptr is not None:
        result = overlord.skydns.update_ptr(address, group)

        response["ptr"] = result

    use_skydns_srv = labels.get("overlord.skydns.srv")

    if use_skydns_srv is not None:
        port = labels.get("overlord.skydns.srv.port")

        if port is None:
            error = True
            message = f"(project:{project}, service:{service_name}, label:overlord.skydns.srv.port) port has not been specified, but is required."

            return (error, message)

        try:
            port = int(port)

        except ValueError:
            error = True
            message = f"(project:{project}, service:{service_name}, port:{port}, label:overlord.skydns.srv.port) invalid port."

            return (error, message)

        proto = labels.get("overlord.skydns.srv.proto")

        if proto is None:
            error = True
            message = f"(project:{project}, service:{service_name}, label:overlord.skydns.srv.proto) protocol has not been specified, but is required."

            return (error, message)

        srv_service = labels.get("overlord.skydns.srv.service")

        if srv_service is None:
            error = True
            message = f"(project:{project}, service:{service_name}, label:overlord.skydns.srv.service) service has not been specified, but is required."

            return (error, message)

        priority = labels.get("overlord.skydns.srv.priority", overlord.default.DNS["srv"]["priority"])

        try:
            priority = int(priority)

        except ValueError:
            error = True
            message = f"(project:{project}, service:{service_name}, priority:{priority}, label:overlord.skydns.srv.priority) invalid priority."

            return (error, message)

        weight = labels.get("overlord.skydns.srv.weight", overlord.default.DNS["srv"]["weight"])

        try:
            weight = int(weight)

        except ValueError:
            error = True
            message = f"(project:{project}, service:{service_name}, weight:{weight}, label:overlord.skydns.srv.weight) invalid weight."

            return (error, message)

        ttl = labels.get("overlord.skydns.srv.ttl", overlord.default.DNS["ttl"])

        try:
            ttl = int(ttl)

        except ValueError:
            error = True
            message = f"(project:{project}, service:{service_name}, ttl:{ttl}, label:overlord.skydns.srv.ttl) invalid TTL."

            return (error, message)
        
        result = overlord.skydns.update_srv(group, srv_service, proto, port, priority, weight, ttl)

        response["srv"] = result

    use_skydns_txt = labels.get("overlord.skydns.txt")

    if use_skydns_txt is not None:
        for key, value in labels.items():
            match = re.match(r"^overlord\.skydns\.txt(\d+)$", key)

            if match:
                index = int(match.group(1))
                text = value

                ttl = labels.get(f"overlord.skydns.txt{index}.ttl", overlord.default.DNS["ttl"])

                try:
                    ttl = int(ttl)

                except ValueError:
                    error = True
                    message = f"(project:{project}, service:{service_name}, ttl:{ttl}, label:overlord.skydns.txt{index}.ttl) invalid TTL."

                    return (error, message)

                result = overlord.skydns.update_text(group, index, text, ttl)

                response["txt"].append({ f"txt{index}" : result })

    record_address = response.get("address")
    record_ptr = response.get("ptr")
    record_txt = response.get("txt")
    record_srv = response.get("srv")

    error = False
    message = f"(project:{project}, service:{service_name}, records:[address:{record_address},ptr:{record_ptr},txt:{record_txt},srv:{record_srv}] records has been updated."

    return (error, message)

async def run_special_label_load_balancer(project, type, service, labels):
    service_name = service["name"]

    use_load_balancer = labels.get("overlord.load-balancer")

    if use_load_balancer is None:
        error = False
        message = None

        return (error, message)

    limits_settings = {
        "max_keepalive_connections" : overlord.config.get_dataplaneapi_max_keepalive_connections(),
        "max_connections" : overlord.config.get_dataplaneapi_max_connections(),
        "keepalive_expiry" : overlord.config.get_dataplaneapi_keepalive_expiry()
    }
    timeout_settings = {
        "timeout" : overlord.config.get_dataplaneapi_timeout(),
        "read" : overlord.config.get_dataplaneapi_read_timeout(),
        "write" : overlord.config.get_dataplaneapi_write_timeout(),
        "connect" : overlord.config.get_dataplaneapi_connect_timeout(),
        "pool" : overlord.config.get_dataplaneapi_pool_timeout()
    }

    serverid = overlord.config.get_dataplaneapi_serverid()
    entrypoint = overlord.config.get_dataplaneapi_entrypoint()
    username = overlord.config.get_dataplaneapi_auth_username()
    password = overlord.config.get_dataplaneapi_auth_password()

    if entrypoint is None \
            or username is None \
            or password is None:
        error = True
        message = f"(project:{project}, service:{service_name}) Data Plane API client is not configured."

        return (error, message)

    client = overlord.dataplaneapi.DataPlaneAPIClientv3(
        entrypoint,
        username,
        password,
        limits=httpx.Limits(**limits_settings),
        timeout=httpx.Timeout(**timeout_settings)
    )

    configuration_version = await client.get_configuration_version()

    backend = labels.get("overlord.load-balancer.backend")

    if backend is None:
        error = True
        message = f"(project:{project}, service:{service_name}, label:overlord.load-balancer.backend) backend has not been specified, but is required."

        return (error, message)

    backend_info = await client.get_backend(backend, _raise_for_status=False)
    
    code = backend_info.status_code

    if code == 404:
        error = True
        message = f"(project:{project}, service:{service_name}, backend:{backend}, label:overlord.load-balancer.backend) backend is not found."

        return (error, message)
    
    elif code != 200:
        error = True
        message = f"(project:{project}, service:{service_name}, backend:{backend}, code:{code}, label:overlord.load-balancer.backend) unexpected HTTP status code from Data Plane API."

        return (error, message)

    interface = labels.get("overlord.load-balancer.interface")

    if interface is None:
        error = True
        message = f"(project:{project}, service:{service_name}, label:overlord.load-balancer.interface) interface has not been specified, but is required."

        return (error, message)

    port = labels.get("overlord.load-balancer.interface.port")

    if port is None:
        error = True
        message = f"(project:{project}, service:{service_name}, label:overlord.load-balancer.interface.port) port has not been specified, but is required."

        return (error, message)

    try:
        port = int(port)

    except ValueError as err:
        error = True
        message = f"(project:{project}, service:{service_name}, port:{port}, label:overlord.load-balancer.interface.port) invalid port."

        return (error, message)

    network = labels.get("overlord.load-balancer.interface.address")

    try:
        address = overlord.util.iface2ip(interface, network)

    except Exception as err:
        error = overlord.util.get_error(err)
        error_type = error.get("type")
        error_message = error.get("message")

        error = True
        message = f"(project:{project}, service:{service_name}, interface:{interface}, address:{network}, exception:{error_type}, label:overlord.load-balancer.interface.address) {error_message}"

        return (error, message) 

    if address is None:
        error = True
        message = f"(project:{project}, service:{service_name}, interface:{interface}, address:{network}, label:overlord.load-balancer.interface.address) no IP address has been found."

        return (error, message)

    server_info = await client.get_server(serverid, backend, _raise_for_status=False)

    code = server_info.status_code

    if type == "create":
        body = {}

        for label_name, label_value in labels.items():
            _parsed = label_name.split("overlord.load-balancer.set.", 1)

            if len(_parsed) != 2:
                continue

            name = _parsed[1]

            try:
                body[name] = json.loads(label_value)

            except Exception as err:
                error = overlord.util.get_error(err)
                error_type = error.get("type")
                error_message = error.get("message")

                error = True
                message = f"(project:{project}, service:{service_name}, exception:{error_type}, label:{label_name}) {error_message}"

                return (error, message)

        body["name"] = serverid
        body["address"] = address
        body["port"] = port

        logger.debug("Body request: %s", body)

        if code == 200:
            replace_server_info = await client.replace_server(
                serverid,
                backend,
                version=configuration_version,
                body=body,
                _raise_for_status=False
            )

            code = replace_server_info.status_code

            if code == 200 \
                    or code == 202:
                error = False
                message = f"(project:{project}, service:{service_name}, backend:{backend}, serverid:{serverid}, code:{code}) server has been successfully updated."

                return (error, message)

            else:
                error = True
                response = replace_server_info.content
                message = f"(project:{project}, service:{service_name}, backend:{backend}, serverid:{serverid}, code:{code}) error updating the server - {response}"

                return (error, message)

        elif code == 404:
            add_server_info = await client.add_server(
                backend,
                version=configuration_version,
                body=body,
                _raise_for_status=False
            )

            code = add_server_info.status_code

            if code == 201 \
                    or code == 202:
                error = False
                message = f"(project:{project}, service:{service_name}, backend:{backend}, serverid:{serverid}, code:{code}) server has been successfully added."

                return (error, message)

            else:
                error = True
                response = add_server_info.content
                message = f"(project:{project}, service:{service_name}, backend:{backend}, serverid:{serverid}, code:{code}) error adding the server - {response}"

                return (error, message)

        else:
            error = True
            response = server_info.content
            message = f"(project:{project}, service:{service_name}, backend:{backend}, serverid:{serverid}, code:{code}) error retrieving information about the server - {response}"

            return (error, message)

    elif type == "destroy":
        if code != 200:
            error = False
            message = None

            return (error, message)

        delete_server_info = await client.delete_server(
            serverid,
            backend,
            version=configuration_version,
            _raise_for_status=False
        )

        code = delete_server_info.status_code

        if code == 202 \
                or code == 204:
            error = False
            message = f"(project:{project}, service:{service_name}, backend:{backend}, serverid:{serverid}, code:{code}) server has been removed."

            return (error, message)

        else:
            error = True
            response = delete_server_info.content
            message = f"(project:{project}, service:{service_name}, backend:{backend}, serverid:{serverid}, code:{code}) error removing the server - {response}"

            return (error, message)
