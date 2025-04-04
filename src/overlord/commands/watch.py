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
import ssl
import sys
import tempfile
import time

import click
import httpx
import yaml

import overlord.cache
import overlord.commands
import overlord.config
import overlord.dataplaneapi
import overlord.default
import overlord.director
import overlord.exceptions
import overlord.jail
import overlord.vm
import overlord.process
import overlord.trap
import overlord.skydns
import overlord.queue
import overlord.util
import overlord.metadata

from concurrent.futures import ProcessPoolExecutor

from overlord.sysexits import EX_SOFTWARE

logger = logging.getLogger(__name__)

EXECUTOR = None
CHILD = None

@overlord.commands.cli.command(add_help_option=False)
def watch_projects():
    global EXECUTOR

    max_watch_projects = overlord.config.get_max_watch_projects()

    overlord.trap.add(clean)

    EXECUTOR = ProcessPoolExecutor(max_workers=max_watch_projects)

    for _ in range(max_watch_projects):
        EXECUTOR.submit(_watch_projects)

@overlord.commands.cli.command(add_help_option=False)
def watch_vm():
    global EXECUTOR

    max_watch_vm = overlord.config.get_max_watch_vm()

    overlord.trap.add(clean)

    EXECUTOR = ProcessPoolExecutor(max_workers=max_watch_vm)

    for _ in range(max_watch_vm):
        EXECUTOR.submit(_watch_vm)

def clean(*args, **kwargs):
    if CHILD is not None:
        logger.info("My work is finished :D")
        return

    logger.info("Cleaning up ...")

    overlord.process.kill_child_processes(os.getpid())

    if EXECUTOR is not None:
        EXECUTOR.shutdown(wait=False)

def _watch_vm(*args, **kwargs):
    asyncio.run(_async_watch_vm())

async def _async_watch_vm():
    global CHILD

    try:
        CHILD = os.getpid()

        overlord.process.init()

        while True:
            logger.debug("Waiting for new jobs ...")

            (job_id, job_body) = await overlord.queue.reserve_vm()

            message = job_body.get("message")
            vm = message.get("name")

            if ignore_project(vm):
                continue

            try:
                makejailFromMetadata = message.get("makejailFromMetadata")

                if makejailFromMetadata is None:
                    makejail = message.get("makejail")

                else:
                    makejail = overlord.metadata.get_filename(makejailFromMetadata)

                profile = {
                    "name" : vm,
                    "makejail" : makejail,
                    "template" : message.get("template"),
                    "diskLayout" : message.get("diskLayout"),
                    "script" : message.get("script"),
                    "metadata" : message.get("metadata"),
                    "environment" : {
                        "process" : dict(os.environ),
                        "build" : message.get("build-environment"),
                        "start" : message.get("start-environment")
                    },
                    "arguments" : {
                        "build" : message.get("build-arguments"),
                        "start" : message.get("start-environment")
                    },
                    "options" : message.get("options"),
                    "restart" : message.get("restart")
                }

                await create_vm(job_id, **profile)

            except Exception as err:
                error = overlord.util.get_error(err)
                error_type = error.get("type")
                error_message = error.get("message")

                logger.exception("(exception:%s) %s:", error_type, error_message)
                
                overlord.cache.save_vm_status(profile["name"], {
                    "operation" : "FAILED",
                    "exception" : {
                        "type" : error_type,
                        "message" : error_message
                    },
                    "last_update" : time.time(),
                    "job_id" : job_id
                })

    except Exception as err:
        error = overlord.util.get_error(err)
        error_type = error.get("type")
        error_message = error.get("message")

        logger.exception("(exception:%s) %s:", error_type, error_message)

        sys.exit(EX_SOFTWARE)

async def create_vm(job_id, *, name, makejail, template, diskLayout, script, metadata, environment, arguments, options, restart):
    vm = name

    logger.debug("(VM:%s) creating VM ...", vm)

    restarted = False

    jail_path = None

    if overlord.jail.status(vm) < 2:
        jail_path = overlord.jail.get_jail_path(vm)

        if jail_path is None:
            logger.error("(jail:%s) can't get jail path!", vm)
            return

        if overlord.vm.is_done(jail_path):
            if not restart:
                return

            if overlord.director.check(vm):
                logger.debug("(vm:%s) stopping ...", vm)

                poweroff_if_vm(vm)

                overlord.director.down(vm, env=environment["process"])

                restarted = True

    overlord.cache.save_project_status_up(vm, {
        "operation" : "RUNNING",
        "last_update" : time.time(),
        "job_id" : job_id
    })

    director_file = {
        "services" : {
            "vm" : {
                "name" : vm,
                "makejail" : makejail,
                "options" : [
                    { "label" : "overlord.vm:1" }
                ]
            }
        }
    }

    if options:
        director_file["options"] = options

    if environment["start"]:
        director_file["services"]["vm"]["start-environment"] = environment["start"]

    if environment["build"]:
        director_file["services"]["vm"]["environment"] = environment["build"]

    if arguments["start"]:
        director_file["services"]["vm"]["start"] = arguments["start"]

    if arguments["build"]:
        director_file["services"]["vm"]["arguments"] = arguments["build"]

    director_file = yaml.dump(director_file)

    with tempfile.NamedTemporaryFile(prefix="overlord", mode="wb", buffering=0) as fd:
        fd.write(director_file.encode())

        result = overlord.director.up(vm, fd.name, env=environment["process"])

        errlevel = result["stdout"]["errlevel"]

        if errlevel == 0:
            failed = result["stdout"]["failed"]

            error = len(failed) > 0

        else:
            error = True

        if error:
            operation_status = "INCOMPLETED"

        else:
            operation_status = "COMPLETED"

        overlord.cache.save_project_status_up(vm, {
            "operation" : operation_status,
            "output" : result,
            "last_update" : time.time(),
            "job_id" : job_id,
            "restarted" : restarted
        })

        if error:
            return

        # We must limit our execution to just restarting the project and nothing else.
        if restarted:
            return

        overlord.cache.save_vm_status(vm, {
            "operation" : "RUNNING",
            "last_update" : time.time(),
            "job_id" : job_id
        })

        from_ = diskLayout["from"]

        driver = diskLayout["driver"]
        size = diskLayout["size"]

        template["disk0_type"] = driver
        template["disk0_name"] = "disk0.img"
        template["disk0_dev"] = "file"
        template["disk0_size"] = size

        if jail_path is None:
            jail_path = overlord.jail.get_jail_path(vm)

            if jail_path is None:
                logger.error("(jail:%s) can't get jail path!", vm)
                return

        overlord.vm.write_template(jail_path, "overlord", template)

        from_type = from_["type"]

        ignore_done = False
        ignore_create = False

        if from_type == "iso":
            installed = from_.get("installed")

            if installed is None:
                installed = False

            if installed:
                ignore_create = True

        if not ignore_create:
            (rc, result) = overlord.vm.create(vm, vm, template="overlord")

            if rc != 0:
                overlord.cache.save_vm_status(vm, {
                    "operation" : "FAILED",
                    "output" : result,
                    "last_update" : time.time(),
                    "job_id" : job_id
                })

                return

        (rc, result) = (0, "")

        if from_type == "components" \
                or from_type == "appjailImage":
            for metadata_name in metadata:
                await overlord.vm.write_metadata(jail_path, metadata_name)
            disk = diskLayout.get("disk")

            if disk is None:
                raise overlord.exceptions.InvalidSpec("'diskLayout.disk' is required but hasn't been specified.")

            fstab = diskLayout.get("fstab")

            if fstab is None:
                raise overlord.exceptions.InvalidSpec("'diskLayout.fstab' is required but hasn't been specified.")

            scheme = disk["scheme"]
            partitions = disk["partitions"]
            bootcode = disk.get("bootcode")

            await overlord.vm.write_partitions(jail_path, scheme, partitions, bootcode)
            await overlord.vm.write_fstab(jail_path, fstab)

            if script is not None:
                await overlord.vm.write_script(jail_path, script)

            if from_type == "components":
                components = from_["components"]
                osVersion = from_["osVersion"]
                osArch = from_["osArch"]
                downloadURL = from_.get("downloadURL")

                if downloadURL is None:
                    downloadURL = overlord.default.VM["from"]["downloadURL"]

                downloadURL = downloadURL.format(
                    ARCH=osArch, VERSION=osVersion
                )

                components_path = os.path.join(
                    overlord.config.get_components(), osArch, osVersion
                )

                (rc, result) = overlord.vm.install_from_components(vm, downloadURL, components_path, components)

            elif from_type == "appjailImage":
                entrypoint = from_["entrypoint"]
                imageName = from_["imageName"]
                imageArch = from_["imageArch"]
                imageTag = from_["imageTag"]

                (rc, result) = overlord.vm.install_from_appjail_image(vm, entrypoint, imageName, imageArch, imageTag)

        elif from_type == "iso":
            if installed:
                (rc, result) = overlord.vm.start(vm)

            else:
                isoFile = from_["isoFile"]

                (rc, result) = overlord.vm.install_from_iso(vm, isoFile)

                ignore_done = True

        result = overlord.util.sansi(result)

        if rc == 0:
            operation_status = "COMPLETED"

            if not ignore_done:
                overlord.vm.write_done(jail_path)

        else:
            operation_status = "FAILED"

        overlord.cache.save_vm_status(vm, {
            "operation" : operation_status,
            "output" : result,
            "last_update" : time.time(),
            "job_id" : job_id
        })

def _watch_projects(*args, **kwargs):
    asyncio.run(_async_watch_projects())

async def _async_watch_projects():
    global CHILD

    try:
        CHILD = os.getpid()

        overlord.process.init()

        while True:
            logger.debug("Waiting for new jobs ...")

            (job_id, job_body) = await overlord.queue.reserve_project()

            message = job_body.get("message")
            project = message.get("name")
            environment = dict(os.environ)
            environment.update(message.get("environment"))

            environment["OVERLORD_METADATA"] = overlord.config.get_metadata_location()

            type = job_body.get("type")

            if ignore_project(project):
                continue

            if type == "create":
                restart = message.get("restart", False)

                restarted = False

                if restart and \
                        overlord.director.check(project):
                    logger.debug("(project:%s) stopping ...", project)

                    poweroff_if_vm(project)

                    overlord.director.down(project, env=environment)

                    restarted = True

                logger.debug("(project:%s) processing ...", project)

                overlord.cache.save_project_status_up(project, {
                    "operation" : "RUNNING",
                    "last_update" : time.time(),
                    "job_id" : job_id
                })

                director_file = message.get("director_file")

                with tempfile.NamedTemporaryFile(prefix="overlord", mode="wb", buffering=0) as fd:
                    fd.write(director_file.encode())

                    result = overlord.director.up(project, fd.name, env=environment)

                    special_labels_response = await run_special_labels(project, type)

                    error = special_labels_response.get("error")

                    if not error:
                        for integration in ("load-balancer", "skydns"):
                            services = special_labels_response.get(integration, {})

                            for _, info in services.items():
                                error = info.get("error", False)

                                if error:
                                    break

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
                        "restarted" : restarted,
                        "labels" : special_labels_response
                    })

            elif type == "destroy":
                force = message.get("force", False)

                logger.debug("(project:%s, force:%s) destroying project ...", project, force)

                special_labels_response = await run_special_labels(project, type, force)

                overlord.cache.save_project_status_down(project, {
                    "operation" : "RUNNING",
                    "last_update" : time.time(),
                    "job_id" : job_id,
                    "labels" : special_labels_response
                })

                error = special_labels_response.get("error")

                if not error:
                    for integration in ("load-balancer", "skydns"):
                        services = special_labels_response.get(integration, {})

                        for _, info in services.items():
                            error = info.get("error", False)

                            if error:
                                break

                        if error:
                            break

                if error:
                    operation_status = "INCOMPLETED"
                    result = {}

                else:
                    operation_status = "COMPLETED"

                    poweroff_if_vm(project)

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

        logger.exception("(exception:%s) %s:", error_type, error_message)

        sys.exit(EX_SOFTWARE)

def poweroff_if_vm(project):
    if not overlord.director.check(project):
        return

    (rc, info) = overlord.director.describe(project)

    if rc != 0:
        return

    services = info["services"]

    if len(services) != 1:
        return

    jail = services[0]["jail"]

    args = ["appjail", "label", "get", "-I", "-l", "overlord.vm", "--", jail, "value"]

    (rc, _, _) = overlord.process.run_proc(args)

    if rc != 0:
        return

    logger.debug("(jail:%s, vm:1) doing a forced shutdown!", jail)

    overlord.vm.poweroff(jail, jail)

def ignore_project(project):
    if not overlord.director.check(project):
        return False

    (rc, info) = overlord.director.describe(project)

    if rc != 0:
        return False

    state = info["state"]

    if state == "UNFINISHED" \
            or state == "DESTROYING":
        return True

    else:
        return False

async def run_special_labels(project, type, force=False):
    response = {
        "error" : False,
        "message" : None
    }

    if force:
        return response

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

        labels = overlord.jail.get_labels(jail)

        if labels is None:
            continue

        else:
            data = {}
            error = False

            for label in labels:
                if not label.startswith("overlord."):
                    continue

                label = overlord.jail.list_label(jail, label)

                if label is None:
                    logger.warning("(service:%s, label:%s) error when retrieving the label", name, label)

                    error = True
                    
                    break

                else:
                    label_name = label["name"]
                    label_value = label["value"]

                    data[label_name] = label_value

            if error:
                continue

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

                    logger.exception("(integration:%s, exception:%s) %s", integration, error_type, error_message)

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

    ttl = labels.get("overlord.skydns.ttl", overlord.default.DNS["ttl"])

    try:
        ttl = int(ttl)

    except ValueError:
        error = True
        message = f"(project:{project}, service:{service_name}, label:overlord.skydns.ttl) invalid TTL."

        return (error, message)

    response = {
        "ptr" : None,
        "address" : None,
        "srv" : None
    }

    if type == "create":
        result = overlord.skydns.update_address(address, group, ttl)

    elif type == "destroy":
        result = overlord.skydns.delete_address(group)

    response["address"] = result

    use_skydns_ptr = labels.get("overlord.skydns.ptr")

    if use_skydns_ptr is not None:
        if type == "create":
            result = overlord.skydns.update_ptr(address, group)

        elif type == "destroy":
            result = overlord.skydns.delete_ptr(address)

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
        
        if type == "create":
            result = overlord.skydns.update_srv(group, srv_service, proto, port, priority, weight, ttl)

        elif type == "destroy":
            result = overlord.skydns.delete_srv(group, srv_service, proto)

        response["srv"] = result

    record_address = response.get("address")
    record_ptr = response.get("ptr")
    record_srv = response.get("srv")

    if type == "create":
        _message = "records has been updated."

    elif type == "destroy":
        _message = "records has been removed."

    error = False
    message = f"(project:{project}, service:{service_name}, records:[address:{record_address},ptr:{record_ptr},srv:{record_srv}] {_message}"

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

    serverid = overlord.util.get_serverid()
    entrypoint = overlord.config.get_dataplaneapi_entrypoint()
    username = overlord.config.get_dataplaneapi_auth_username()
    password = overlord.config.get_dataplaneapi_auth_password()

    if entrypoint is None \
            or username is None \
            or password is None:
        error = True
        message = f"(project:{project}, service:{service_name}) Data Plane API client is not configured."

        return (error, message)

    kwargs = {}

    cacert = overlord.config.get_dataplaneapi_cacert()

    if cacert is not None:
        ctx = ssl.create_default_context(cafile=cacert)

        kwargs["verify"] = ctx

    client = overlord.dataplaneapi.DataPlaneAPIClientv3(
        entrypoint,
        username,
        password,
        limits=httpx.Limits(**limits_settings),
        timeout=httpx.Timeout(**timeout_settings),
        **kwargs
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

    transaction_id_info = await client.get_transaction_id(configuration_version)

    if transaction_id_info.status_code != 201:
        error = True
        message = f"(project:{project}, service:{service_name}) can't get transaction ID"

        return (error, message)

    transaction_id = transaction_id_info.json()["id"]

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
                message = f"(project:{project}, service:{service_name}, exception:{error_type}, label:{label_name}, transaction_id:{transaction_id}) {error_message}"

                return (error, message)

        body["name"] = serverid
        body["address"] = address
        body["port"] = port

        logger.debug("(project:%s, service:%s) body request: %s",
                     project, service_name, json.dumps(body, indent=4))

        if code == 200:
            replace_server_info = await client.replace_server(
                serverid,
                backend,
                transaction_id=transaction_id,
                body=body,
                _raise_for_status=False
            )

            code = replace_server_info.status_code

            if code != 200 \
                    and code != 202:
                error = True
                response = replace_server_info.content
                message = f"(project:{project}, service:{service_name}, backend:{backend}, serverid:{serverid}, code:{code}, transaction_id:{transaction_id}, commit:0) error updating the server - {response}"

                return (error, message)

            commit_info = await client.commit_transaction(transaction_id, _raise_for_status=False)

            code = commit_info.status_code

            if code != 200 \
                    and code != 202:
                error = True
                response = commit_info.content
                message = f"(project:{project}, service:{service_name}, backend:{backend}, serverid:{serverid}, code:{code}, transaction_id:{transaction_id}, commit:1) error updating the server - {response}"

                return (error, message)

            error = False
            message = f"(project:{project}, service:{service_name}, backend:{backend}, serverid:{serverid}, code:{code}, transaction_id:{transaction_id}, commit:1) server has been successfully updated."

            return (error, message)

        elif code == 404:
            add_server_info = await client.add_server(
                backend,
                transaction_id=transaction_id,
                body=body,
                _raise_for_status=False
            )

            code = add_server_info.status_code

            if code != 201 \
                    and code != 202:
                error = True
                response = add_server_info.content
                message = f"(project:{project}, service:{service_name}, backend:{backend}, serverid:{serverid}, code:{code}, transaction_id:{transaction_id}, commit:0) error adding the server - {response}"

                return (error, message)

            commit_info = await client.commit_transaction(transaction_id, _raise_for_status=False)

            code = commit_info.status_code

            if code != 200 \
                    and code != 202:
                error = True
                response = commit_info.content
                message = f"(project:{project}, service:{service_name}, backend:{backend}, serverid:{serverid}, code:{code}, transaction_id:{transaction_id}, commit:1) error adding the server - {response}"

                return (error, message)

            error = False
            message = f"(project:{project}, service:{service_name}, backend:{backend}, serverid:{serverid}, code:{code}, transaction_id:{transaction_id}, commit:1) server has been successfully added."

            return (error, message)

        else:
            error = True
            response = server_info.content
            message = f"(project:{project}, service:{service_name}, backend:{backend}, serverid:{serverid}, code:{code}, transaction_id:{transaction_id}) error retrieving information about the server - {response}"

            return (error, message)

    elif type == "destroy":
        if code != 200:
            error = False
            message = None

            return (error, message)

        delete_server_info = await client.delete_server(
            serverid,
            backend,
            transaction_id=transaction_id,
            _raise_for_status=False
        )

        code = delete_server_info.status_code

        if code != 202 \
                and code != 204:
            error = True
            response = delete_server_info.content
            message = f"(project:{project}, service:{service_name}, backend:{backend}, serverid:{serverid}, code:{code}, transaction_id:{transaction_id}, commit:0) error removing the server - {response}"

            return (error, message)

        commit_info = await client.commit_transaction(transaction_id, _raise_for_status=False)

        code = commit_info.status_code

        if code != 200 \
                and code != 202:
            error = True
            response = commit_info.content
            message = f"(project:{project}, service:{service_name}, backend:{backend}, serverid:{serverid}, code:{code}, transaction_id:{transaction_id}, commit:1) error removing the server - {response}"

            return (error, message)
        
        error = False
        message = f"(project:{project}, service:{service_name}, backend:{backend}, serverid:{serverid}, code:{code}, transaction_id:{transaction_id}, commit:1) server has been removed."

        return (error, message)
