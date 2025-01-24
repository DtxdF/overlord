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
import sys
import tempfile
import time

import click
import httpx

import overlord.cache
import overlord.commands
import overlord.config
import overlord.dataplaneapi
import overlord.director
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

                    (rc, result) = overlord.director.up(project, fd.name, env=environment)

                    special_labels_response = await run_special_labels(project, type)

                    overlord.cache.save_project_status_up(project, {
                        "operation" : "COMPLETED",
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

                (rc, result) = overlord.director.down(project, destroy=True, ignore_failed=True, env=environment)

                overlord.cache.save_project_status_down(project, {
                    "operation" : "COMPLETED",
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

            if "load-balancer" not in response:
                response["load-balancer"] = {}

            try:
                (error, message) = await run_special_label_load_balancer(project, type, service, data)

                response["load-balancer"][name] = {
                    "error" : error,
                    "message" : message
                }

            except Exception as err:
                error = overlord.util.get_error(err)
                error_type = error.get("type")
                error_message = error.get("message")

                logger.exception("Exception in load-balancer: %s: %s", error_type, error_message)

                response["load-balancer"][name] = {
                    "error" : True,
                    "message" : "Exception %s: %s" % (error_type, error_message)
                }

    return response

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
        message = "Service '%s.%s' wants to use the load-balancer but you haven't configured the Data Plane API." % (
            project, service_name
        )

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
        message = "Service '%s.%s' wants to use the load-balancer but it hasn't specified a backend." % (
            project, service_name
        )

        return (error, message)

    backend_info = await client.get_backend(backend, _raise_for_status=False)
    
    code = backend_info.status_code

    if code == 404:
        error = True
        message = "Service '%s.%s' wants to use the load-balancer but has specified the backend '%s' which does not exist." % (
            project, service_name, backend
        )

        return (error, message)
    
    elif code != 200:
        error = True
        message = "Service '%s.%s' wants to use the load-balancer but Data Plane API returns a different code (%d) than expected." % (
            project, service_name, code
        )

        return (error, message)

    interface = labels.get("overlord.load-balancer.interface")

    if interface is None:
        error = True
        message = "Service '%s.%s' wants to use the load-balancer but it hasn't specified an interface." % (
            project, service_name
        )

        return (error, message)

    port = labels.get("overlord.load-balancer.interface.port")

    if port is None:
        error = True
        message = "Service '%s.%s' wants to use the load-balancer but is hasn't specified the port." % (
            project, service_name
        )

        return (error, message)

    try:
        port = int(port)

    except ValueError as err:
        error = True
        message = "Service '%s.%s' wants to use the load-balancer but it has specified an invalid port '%s'." % (
            project, service_name, port
        )

        return (error, message)

    network = labels.get("overlord.load-balancer.interface.address")

    try:
        address = overlord.util.iface2ip(interface, network)

    except Exception as err:
        error = overlord.util.get_error(err)
        error_type = error.get("type")
        error_message = error.get("message")

        error = True
        message = "Error when trying to get information about the '%s' interface (address:%s): %s: %s" % (
            interface, network, error_type, error_message
        )

        return (error, message) 

    if address is None:
        error = True
        message = "Service '%s.%s' wants to use the load-balancer but no matching IP address has been found for the '%s' interface (address:%s)" % (
            project, service_name, interface, address
        )

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
                error = True
                message = "Service '%s.%s' wants to use the load-balancer but it has specified an invalid value from label '%s': %s" % (project, service_name, label_name, label_value)

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
                message = "Server '%s' from backend '%s' used by '%s.%s' has been successfully updated." % (
                    serverid, backend, project, service_name
                )

                return (error, message)

            else:
                error = True
                message = "Error updating server '%s' from backend '%s' used by '%s.%s'." % (
                    serverid, backend, project, service_name
                )

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
                message = "Server '%s' from backend '%s' used by '%s.%s' has been successfully added." % (
                    serverid, backend, project, service_name
                )

                return (error, message)

            else:
                error = True
                message = "Error adding server '%s' from backend '%s' used by '%s.%s' - status code is '%d'" % (
                    serverid, backend, project, service_name, code
                )

                return (error, message)

        else:
            error = True
            message = "Error retrieving information about server '%s' from backend '%s' used by '%s.%s' - status code is '%d'" % (
                serverid, backend, project, service_name, code
            )

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
            message = "Server '%s' used by service '%s.%s' has been removed from backend '%s'." % (
                serverid, project, service_name, backend
            )

            return (error, message)

        else:
            error = True
            message = "An error occurred while removing server '%s' from backend '%s' used by service '%s.%s'." % (
                serverid, backend, service_name, backend
            )

            return (error, message)
