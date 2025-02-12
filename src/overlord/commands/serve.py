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
import time

import aiofiles
import click
import httpx
import tornado

import overlord.cache
import overlord.chains
import overlord.client
import overlord.commands
import overlord.config
import overlord.metadata
import overlord.queue
import overlord.tornado
import overlord.util

logger = logging.getLogger(__name__)

CHAINS = {}
METADATA = {}

class InternalHandler(overlord.tornado.JSONAuthHandler):
    def check_jail(self, jail):
        if overlord.cache.check_jail(jail):
            return True

        else:
            self.write_template({
                "message" : "Jail cannot be found."
            }, status_code=404)

            return False

    def check_project(self, project):
        if overlord.cache.check_project(project):
            return True

        else:
            self.write_template({
                "message" : "Project cannot be found."
            }, status_code=404)

            return False

    def check_metadata(self, key):
        if overlord.metadata.check(key):
            return True

        else:
            self.write_template({
                "message" : "Metadata cannot be found."
            }, status_code=404)

            return False

class ChainInternalHandler(InternalHandler):
    def get_chain(self, chain):
        return CHAINS.get(chain)

    async def remote_call(self, chain, func, *args, **kwargs):
        (next_entrypoint, next_chain) = overlord.chains.get_chain(chain)

        chain_cli = self.get_chain(next_entrypoint)

        if chain_cli is None:
            raise tornado.web.HTTPError(404, reason=f"Next entrypoint '{next_entrypoint}' cannot be found.")

        if len(next_chain) == 0:
            logger.debug("(function:%s, entrypoint:%s) connecting ...",
                         func, next_entrypoint)

            result = getattr(chain_cli, func)(*args, **kwargs)

        else:
            new_chain = overlord.chains.join_chain(next_chain)

            logger.debug("(function:%s, entrypoint:%s, chain:%s) connecting ...",
                         func, next_entrypoint, new_chain)

            result = getattr(chain_cli, func)(*args, chain=new_chain, **kwargs)

        try:
            return await result

        except Exception as err:
            error = overlord.util.get_error(err)
            error_type = error.get("type")
            error_message = error.get("message")

            new_chain = overlord.chains.join_chain(next_chain)

            logger.exception("(function:%s, entrypoint:%s, chain:%s, exception:%s) error executing the remote call: %s",
                             func, next_entrypoint, new_chain, error_type, error_message)

            self.write_template({
                "function" : func,
                "entrypoint" : next_entrypoint,
                "chain" : new_chain,
                "error" : error_type,
                "message" : error_message
            }, status_code=503)
            self.finish()

class JailsHandler(InternalHandler):
    async def get(self):
        self.write_template({
            "jails" : overlord.cache.get_jails()
        })

class JailsLogsHandler(InternalHandler):
    async def get(self):
        logsdir = overlord.config.get_appjail_logs()

        if not os.path.isdir(logsdir):
            self.write_template({ "logs" : {} })
            return

        logs = {}

        for type in os.listdir(logsdir):
            if type not in logs:
                logs[type] = {}

            typedir = os.path.join(logsdir, type)

            if not os.path.isdir(typedir):
                continue

            for entity in os.listdir(typedir):
                if entity not in logs[type]:
                    logs[type][entity] = {}

                entitydir = os.path.join(typedir, entity)

                if not os.path.isdir(entitydir):
                    continue

                for subtype in os.listdir(entitydir):
                    if entity not in logs[type][entity]:
                        logs[type][entity][subtype] = []

                    subtypedir = os.path.join(entitydir, subtype)
                
                    if not os.path.isdir(subtypedir):
                        continue

                    for logfile in os.listdir(subtypedir):
                        logs[type][entity][subtype].append(logfile)

        self.write_template({
            "logs" : logs
        })

class JailLogHandler(InternalHandler):
    async def get(self, type, entity, subtype, log):
        log = os.path.join(type, entity, subtype, log)

        logsdir = overlord.config.get_appjail_logs()

        pathname = os.path.join(logsdir, log)

        if not os.path.isfile(pathname):
            self.write_template({
                "message" : "Log cannot be found."
            }, status_code=404)
            return

        async with aiofiles.open(pathname, "r") as fd:
            content = await fd.read()

        content = overlord.util.sansi(content)

        self.write_template({
            "log_content" : content
        })

class JailStatsHandler(InternalHandler):
    async def get(self, jail):
        if not self.check_jail(jail):
            return

        self.write_template({
            "stats" : overlord.cache.get_jail_stats(jail)
        })

class JailInfoHandler(InternalHandler):
    async def get(self, jail):
        if not self.check_jail(jail):
            return
        
        self.write_template({
            "info" : overlord.cache.get_jail_info(jail)
        })

    async def head(self, jail):
        if overlord.cache.check_jail(jail):
            self.set_status(200)

        else:
            self.set_status(404)

class JailCPUSetHandler(InternalHandler):
    async def get(self, jail):
        if not self.check_jail(jail):
            return

        self.write_template({
            "cpuset" : overlord.cache.get_jail_cpuset(jail)
        })

class JailDEVFSHandler(InternalHandler):
    async def get(self, jail):
        if not self.check_jail(jail):
            return

        self.write_template({
            "devfs" : overlord.cache.get_jail_devfs(jail)
        })

class JailExposeHandler(InternalHandler):
    async def get(self, jail):
        if not self.check_jail(jail):
            return

        self.write_template({
            "expose" : overlord.cache.get_jail_expose(jail)
        })

class JailHealthcheckHandler(InternalHandler):
    async def get(self, jail):
        if not self.check_jail(jail):
            return

        self.write_template({
            "healthcheck" : overlord.cache.get_jail_healthcheck(jail)
        })

class JailLimitsHandler(InternalHandler):
    async def get(self, jail):
        if not self.check_jail(jail):
            return

        self.write_template({
            "limits" : overlord.cache.get_jail_limits(jail)
        })

class JailFstabHandler(InternalHandler):
    async def get(self, jail):
        if not self.check_jail(jail):
            return

        self.write_template({
            "fstab" : overlord.cache.get_jail_fstab(jail)
        })

class JailLabelsHandler(InternalHandler):
    async def get(self, jail):
        if not self.check_jail(jail):
            return

        self.write_template({
            "labels" : overlord.cache.get_jail_label(jail)
        })

class JailNATHandler(InternalHandler):
    async def get(self, jail):
        if not self.check_jail(jail):
            return

        self.write_template({
            "nat" : overlord.cache.get_jail_nat(jail)
        })

class JailVolumesHandler(InternalHandler):
    async def get(self, jail):
        if not self.check_jail(jail):
            return

        self.write_template({
            "volumes" : overlord.cache.get_jail_volume(jail)
        })

class ProjectsHandler(InternalHandler):
    async def get(self):
        self.write_template({
            "projects" : overlord.cache.get_projects()
        })

class ProjectInfoHandler(InternalHandler):
    async def get(self, project):
        if not self.check_project(project):
            return

        self.write_template({
            "info" : overlord.cache.get_project_info(project)
        })

    async def head(self, project):
        if overlord.cache.check_project(project):
            self.set_status(200)

        else:
            self.set_status(404)

class ProjectUpHandler(InternalHandler):
    async def get(self, project):
        if not self.check_project(project):
            return

        result = overlord.cache.get_project_status_up(project)

        if "last_update" in result:
            result["last_update"] = time.time() - result["last_update"]

        self.write_template({
            "status" : result
        })

    async def post(self, project):
        director_file = self.get_json_argument("director_file", value_type=str, strip=False)
        environment = self.get_json_argument("environment", {}, value_type=dict)

        for env_name, env_value in environment.items():
            if not isinstance(env_name, str) \
                    or not isinstance(env_value, str):
                self.write_template({
                    "message" : f"Invalid environment name ({env_name}) or value ({env_value})."
                }, status_code=404)
                return

        job_id = await overlord.queue.put_create_project({
            "director_file" : director_file,
            "name" : project,
            "environment" : environment
        })

        self.write_template({
            "job_id" : job_id
        })

class ProjectDownHandler(InternalHandler):
    async def get(self, project):
        if not self.check_project(project):
            return

        result = overlord.cache.get_project_status_down(project)

        if "last_update" in result:
            result["last_update"] = time.time() - result["last_update"]

        self.write_template({
            "status" : result
        })

    async def post(self, project):
        environment = self.get_json_argument("environment", {}, value_type=dict)

        for env_name, env_value in environment.items():
            if not isinstance(env_name, str) \
                    or not isinstance(env_value, str):
                self.write_template({
                    "message" : f"Invalid environment name ({env_name}) or value ({env_value})."
                }, status_code=404)
                return

        job_id = await overlord.queue.put_destroy_project({
            "name" : project,
            "environment" : environment
        })

        self.write_template({
            "job_id" : job_id
        })

class ProjectAutoScaleHandler(InternalHandler):
    async def get(self, project):
        result = overlord.cache.get_project_status_autoscale(project)

        if "last_update" in result:
            result["last_update"] = time.time() - result["last_update"]

        self.write_template({
            "status" : result
        })

class ProjectsLogsHandler(InternalHandler):
    async def get(self):
        logsdir = overlord.config.get_director_logs()

        if not os.path.isdir(logsdir):
            self.write_template({ "logs" : {} })
            return

        logs = {}

        for date_logdir in os.listdir(logsdir):
            logs[date_logdir] = {}

            for service_logdir in os.listdir(os.path.join(logsdir, date_logdir)):
                log_path = os.path.join(logsdir, date_logdir, service_logdir)

                if os.path.isfile(log_path):
                    continue # ignore 'exception.log'

                logs[date_logdir][service_logdir] = []

                for log in os.listdir(log_path):
                    logs[date_logdir][service_logdir].append(log)

        self.write_template({
            "logs" : logs
        })

class ProjectsLogHandler(InternalHandler):
    async def get(self, date, service, log):
        log = os.path.join(date, service, log)

        logsdir = overlord.config.get_director_logs()

        pathname = os.path.join(logsdir, log)

        if not os.path.isfile(pathname):
            self.write_template({
                "message" : "Log cannot be found."
            }, status_code=404)
            return

        async with aiofiles.open(pathname, "r") as fd:
            content = await fd.read()

        content = overlord.util.sansi(content)

        self.write_template({
            "log_content" : content
        })

class MetadataHandler(InternalHandler):
    async def get(self, key):
        if not self.check_metadata(key):
            return

        content = await overlord.metadata.get(key)

        self.write_template({
            "metadata" : content
        })

    async def post(self, key):
        if overlord.metadata.check(key):
            self.write_template({
                "message" : f"The specified metadata '{key}' already exists."
            }, status_code=409)
            return

        value = self.get_json_argument("value", value_type=str, strip=False)

        if key not in METADATA:
            METADATA[key] = asyncio.Lock()

        lock = METADATA[key]

        try:
            async with lock:
                await overlord.metadata.set(key, value)

        except overlord.exceptions.MetadataTooLong as err:
            self.write_template({
                "message" : str(err)
            }, status_code=400)

        else:
            self.write_template({
                "message" : f"Metadata '{key}' has been successfully created."
            }, status_code=201)

    async def put(self, key):
        if not self.check_metadata(key):
            return

        value = self.get_json_argument("value", value_type=str, strip=False)

        if key not in METADATA:
            METADATA[key] = asyncio.Lock()

        lock = METADATA[key]

        try:
            async with lock:
                await overlord.metadata.set(key, value)

        except overlord.exceptions.MetadataTooLong as err:
            self.write_template({
                "message" : str(err)
            }, status_code=400)

        else:
            self.write_template({
                "message" : f"Metadata '{key}' has been successfully updated."
            }, status_code=200)

    async def delete(self, key):
        if not self.check_metadata(key):
            return

        self.set_status(204)

        overlord.metadata.delete(key)

    async def head(self, key):
        if overlord.metadata.check(key):
            self.set_status(200)

        else:
            self.set_status(404)

class LabelsHandler(InternalHandler):
    async def get(self):
        self.write_template({
            "labels" : overlord.config.get_labels()
        })

class ChainsHandler(ChainInternalHandler):
    async def get(self):
        self.write_template({
            "chains" : overlord.config.list_chains()
        })

class ChainMetadataHandler(ChainInternalHandler):
    async def get(self, chain, key):
        result = await self.remote_call(chain, "metadata_get", key)

        self.write_template({
            "metadata" : result
        })

    async def post(self, chain, key):
        value = self.get_json_argument("value", value_type=str, strip=False)

        result = await self.remote_call(chain, "metadata_set", key, value)

        self.write_template({
            "message" : result
        })

    async def put(self, chain, key):
        value = self.get_json_argument("value", value_type=str, strip=False)

        result = await self.remote_call(chain, "metadata_set", key, value)

        self.write_template({
            "message" : result
        })

    async def delete(self, chain, key):
        result = await self.remote_call(chain, "metadata_delete", key)

        if result:
            self.set_status(204)

    async def head(self, chain, key):
        result = await self.remote_call(chain, "metadata_check", key)

        if result:
            self.set_status(200)

        else:
            self.set_status(404)

class ChainChainsHandler(ChainInternalHandler):
    async def get(self, chain):
        result = await self.remote_call(chain, "get_chains")

        self.write_template({
            "chains" : result
        })

class ChainLabelsHandler(ChainInternalHandler):
    async def get(self, chain):
        result = await self.remote_call(chain, "get_api_labels")

        self.write_template({
            "labels" : result
        })

class ChainJailsHandler(ChainInternalHandler):
    async def get(self, chain):
        result = await self.remote_call(chain, "get_jails")

        self.write_template({
            "jails" : result
        })

class ChainJailsLogsHandler(ChainInternalHandler):
    async def get(self, chain):
        result = await self.remote_call(chain, "get_jails_logs")

        self.write_template({
            "logs" : result
        })

class ChainJailLogHandler(ChainInternalHandler):
    async def get(self, chain, type, entity, subtype, log):
        result = await self.remote_call(chain, "get_jail_log", type, entity, subtype, log)

        self.write_template({
            "log_content" : result
        })

class ChainJailStatsHandler(ChainInternalHandler):
    async def get(self, chain, jail):
        result = await self.remote_call(chain, "get_stats", jail)

        self.write_template({
            "stats" : result
        })

class ChainJailInfoHandler(ChainInternalHandler):
    async def get(self, chain, jail):
        result = await self.remote_call(chain, "get_info", jail)

        self.write_template({
            "info" : result
        })

    async def head(self, chain, jail):
        result = await self.remote_call(chain, "check", jail)

        if result:
            self.set_status(200)

        else:
            self.set_status(404)

class ChainJailCPUSetHandler(ChainInternalHandler):
    async def get(self, chain, jail):
        result = await self.remote_call(chain, "get_cpuset", jail)

        self.write_template({
            "cpuset" : result
        })

class ChainJailDEVFSHandler(ChainInternalHandler):
    async def get(self, chain, jail):
        result = await self.remote_call(chain, "get_devfs", jail)

        self.write_template({
            "devfs" : result
        })

class ChainJailExposeHandler(ChainInternalHandler):
    async def get(self, chain, jail):
        result = await self.remote_call(chain, "get_expose", jail)

        self.write_template({
            "expose" : result
        })

class ChainJailHealthcheckHandler(ChainInternalHandler):
    async def get(self, chain, jail):
        result = await self.remote_call(chain, "get_healthcheck", jail)

        self.write_template({
            "healthcheck" : result
        })

class ChainJailLimitsHandler(ChainInternalHandler):
    async def get(self, chain, jail):
        result = await self.remote_call(chain, "get_limits", jail)

        self.write_template({
            "limits" : result
        })

class ChainJailFstabHandler(ChainInternalHandler):
    async def get(self, chain, jail):
        result = await self.remote_call(chain, "get_fstab", jail)

        self.write_template({
            "fstab" : result
        })

class ChainJailLabelsHandler(ChainInternalHandler):
    async def get(self, chain, jail):
        result = await self.remote_call(chain, "get_labels", jail)

        self.write_template({
            "labels" : result
        })

class ChainJailNATHandler(ChainInternalHandler):
    async def get(self, chain, jail):
        result = await self.remote_call(chain, "get_nat", jail)

        self.write_template({
            "nat" : result
        })

class ChainJailVolumesHandler(ChainInternalHandler):
    async def get(self, chain, jail):
        result = await self.remote_call(chain, "get_volumes", jail)

        self.write_template({
            "volumes" : result
        })

class ChainProjectsHandler(ChainInternalHandler):
    async def get(self, chain):
        result = await self.remote_call(chain, "get_projects")

        self.write_template({
            "projects" : result
        })

class ChainProjectInfoHandler(ChainInternalHandler):
    async def get(self, chain, project):
        result = await self.remote_call(chain, "get_info", project, type=overlord.client.OverlordEntityTypes.PROJECT)

        self.write_template({
            "info" : result
        })

    async def head(self, chain, project):
        result = await self.remote_call(chain, "check", project, type=overlord.client.OverlordEntityTypes.PROJECT)

        if result:
            self.set_status(200)

        else:
            self.set_status(404)

class ChainProjectUpHandler(ChainInternalHandler):
    async def get(self, chain, project):
        result = await self.remote_call(chain, "get_status_up", project)

        self.write_template({
            "status" : result
        })

    async def post(self, chain, project):
        director_file = self.get_json_argument("director_file", value_type=str, strip=False)
        environment = self.get_json_argument("environment", {}, value_type=dict)

        result = await self.remote_call(chain, "up", project, director_file, environment)

        self.write_template(result)

class ChainProjectDownHandler(ChainInternalHandler):
    async def get(self, chain, project):
        result = await self.remote_call(chain, "get_status_down", project)

        self.write_template({
            "status" : result
        })

    async def post(self, chain, project):
        environment = self.get_json_argument("environment", {}, value_type=dict)

        result = await self.remote_call(chain, "down", project, environment)

        self.write_template(result)

class ChainProjectAutoScaleHandler(ChainInternalHandler):
    async def get(self, chain, project):
        result = await self.remote_call(chain, "get_status_autoscale", project)

        self.write_template({
            "status" : result
        })

class ChainProjectsLogsHandler(ChainInternalHandler):
    async def get(self, chain):
        result = await self.remote_call(chain, "get_projects_logs")

        self.write_template({
            "logs" : result
        })

class ChainProjectsLogHandler(ChainInternalHandler):
    async def get(self, chain, date, service, log):
        result = await self.remote_call(chain, "get_project_log", date, service, log)

        self.write_template({
            "log_content" : result
        })

def make_app():
    settings = {
        "debug" : overlord.config.get_debug(),
        "default_handler_class" : overlord.tornado.NotFoundHandler,
        "default_handler_args"  : {
            "status_code" : 404,
            "message"     : "Resource not found."
        },
        "compress_response" : overlord.config.get_compress_response(),
    }

    return tornado.web.Application([
        (r"/", overlord.tornado.RequiredResourceHandler),
        (r"/v1/?", overlord.tornado.RequiredResourceHandler),
        (r"/v1/jails/?", JailsHandler),
        (r"/v1/jails/logs/?", JailsLogsHandler),
        (r"/v1/jail/log/([^/]+)/([^/]+)/([^/]+)/([^/]+)", JailLogHandler),
        (r"/v1/jail/stats/([a-zA-Z0-9_][a-zA-Z0-9_-]*)", JailStatsHandler),
        (r"/v1/jail/info/([a-zA-Z0-9_][a-zA-Z0-9_-]*)", JailInfoHandler),
        (r"/v1/jail/cpuset/([a-zA-Z0-9_][a-zA-Z0-9_-]*)", JailCPUSetHandler),
        (r"/v1/jail/devfs/([a-zA-Z0-9_][a-zA-Z0-9_-]*)", JailDEVFSHandler),
        (r"/v1/jail/expose/([a-zA-Z0-9_][a-zA-Z0-9_-]*)", JailExposeHandler),
        (r"/v1/jail/healthcheck/([a-zA-Z0-9_][a-zA-Z0-9_-]*)", JailHealthcheckHandler),
        (r"/v1/jail/limits/([a-zA-Z0-9_][a-zA-Z0-9_-]*)", JailLimitsHandler),
        (r"/v1/jail/fstab/([a-zA-Z0-9_][a-zA-Z0-9_-]*)", JailFstabHandler),
        (r"/v1/jail/labels/([a-zA-Z0-9_][a-zA-Z0-9_-]*)", JailLabelsHandler),
        (r"/v1/jail/nat/([a-zA-Z0-9_][a-zA-Z0-9_-]*)", JailNATHandler),
        (r"/v1/jail/volumes/([a-zA-Z0-9_][a-zA-Z0-9_-]*)", JailVolumesHandler),
        (r"/v1/projects/?", ProjectsHandler),
        (r"/v1/projects/logs/?", ProjectsLogsHandler),
        (r"/v1/projects/log/([0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]_[0-9][0-9]h[0-9][0-9]m[0-9][0-9]s)/([a-zA-Z0-9._-]+)/([a-z-]+\.log)", ProjectsLogHandler),
        (r"/v1/project/info/([a-zA-Z0-9._-]+)", ProjectInfoHandler),
        (r"/v1/project/up/([a-zA-Z0-9._-]+)", ProjectUpHandler),
        (r"/v1/project/down/([a-zA-Z0-9._-]+)", ProjectDownHandler),
        (r"/v1/project/autoscale/([a-zA-Z0-9._-]+)", ProjectAutoScaleHandler),
        (r"/v1/metadata/" + overlord.metadata.REGEX_KEY, MetadataHandler),
        (r"/v1/labels/?", LabelsHandler),
        (r"/v1/chains/?", ChainsHandler),
        (r"/v1/chain/([a-zA-Z0-9_][a-zA-Z0-9._-]*)/metadata/" + overlord.metadata.REGEX_KEY, ChainMetadataHandler),
        (r"/v1/chain/([a-zA-Z0-9_][a-zA-Z0-9._-]*)/labels/?", ChainLabelsHandler),
        (r"/v1/chain/([a-zA-Z0-9_][a-zA-Z0-9._-]*)/chains/?", ChainChainsHandler),
        (r"/v1/chain/([a-zA-Z0-9_][a-zA-Z0-9._-]*)/jails/?", ChainJailsHandler),
        (r"/v1/chain/([a-zA-Z0-9_][a-zA-Z0-9._-]*)/jails/logs/?", ChainJailsLogsHandler),
        (r"/v1/chain/([a-zA-Z0-9_][a-zA-Z0-9._-]*)/jail/log/([^/]+)/([^/]+)/([^/]+)/([^/]+)", ChainJailLogHandler),
        (r"/v1/chain/([a-zA-Z0-9_][a-zA-Z0-9._-]*)/jail/stats/([a-zA-Z0-9_][a-zA-Z0-9_-]*)", ChainJailStatsHandler),
        (r"/v1/chain/([a-zA-Z0-9_][a-zA-Z0-9._-]*)/jail/info/([a-zA-Z0-9_][a-zA-Z0-9_-]*)", ChainJailInfoHandler),
        (r"/v1/chain/([a-zA-Z0-9_][a-zA-Z0-9._-]*)/jail/cpuset/([a-zA-Z0-9_][a-zA-Z0-9_-]*)", ChainJailCPUSetHandler),
        (r"/v1/chain/([a-zA-Z0-9_][a-zA-Z0-9._-]*)/jail/devfs/([a-zA-Z0-9_][a-zA-Z0-9_-]*)", ChainJailDEVFSHandler),
        (r"/v1/chain/([a-zA-Z0-9_][a-zA-Z0-9._-]*)/jail/expose/([a-zA-Z0-9_][a-zA-Z0-9_-]*)", ChainJailExposeHandler),
        (r"/v1/chain/([a-zA-Z0-9_][a-zA-Z0-9._-]*)/jail/healthcheck/([a-zA-Z0-9_][a-zA-Z0-9_-]*)", ChainJailHealthcheckHandler),
        (r"/v1/chain/([a-zA-Z0-9_][a-zA-Z0-9._-]*)/jail/limits/([a-zA-Z0-9_][a-zA-Z0-9_-]*)", ChainJailLimitsHandler),
        (r"/v1/chain/([a-zA-Z0-9_][a-zA-Z0-9._-]*)/jail/fstab/([a-zA-Z0-9_][a-zA-Z0-9_-]*)", ChainJailFstabHandler),
        (r"/v1/chain/([a-zA-Z0-9_][a-zA-Z0-9._-]*)/jail/labels/([a-zA-Z0-9_][a-zA-Z0-9_-]*)", ChainJailLabelsHandler),
        (r"/v1/chain/([a-zA-Z0-9_][a-zA-Z0-9._-]*)/jail/nat/([a-zA-Z0-9_][a-zA-Z0-9_-]*)", ChainJailNATHandler),
        (r"/v1/chain/([a-zA-Z0-9_][a-zA-Z0-9._-]*)/jail/volumes/([a-zA-Z0-9_][a-zA-Z0-9_-]*)", ChainJailVolumesHandler),
        (r"/v1/chain/([a-zA-Z0-9_][a-zA-Z0-9._-]*)/projects/?", ChainProjectsHandler),
        (r"/v1/chain/([a-zA-Z0-9_][a-zA-Z0-9._-]*)/projects/logs/?", ChainProjectsLogsHandler),
        (r"/v1/chain/([a-zA-Z0-9_][a-zA-Z0-9._-]*)/projects/log/([0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]_[0-9][0-9]h[0-9][0-9]m[0-9][0-9]s)/([a-zA-Z0-9._-]+)/([a-z-]+\.log)", ChainProjectsLogHandler),
        (r"/v1/chain/([a-zA-Z0-9_][a-zA-Z0-9._-]*)/project/info/([a-zA-Z0-9._-]+)", ChainProjectInfoHandler),
        (r"/v1/chain/([a-zA-Z0-9_][a-zA-Z0-9._-]*)/project/up/([a-zA-Z0-9._-]+)", ChainProjectUpHandler),
        (r"/v1/chain/([a-zA-Z0-9_][a-zA-Z0-9._-]*)/project/down/([a-zA-Z0-9._-]+)", ChainProjectDownHandler),
        (r"/v1/chain/([a-zA-Z0-9_][a-zA-Z0-9._-]*)/project/autoscale/([a-zA-Z0-9._-]+)", ChainProjectDownHandler)
    ], **settings)

async def listen():
    app = make_app()

    app.listen(overlord.config.get_port())

    await asyncio.Event().wait()

@overlord.commands.cli.command(add_help_option=False)
def serve():
    overlord.trap.add(overlord.trap.exit_with_error)

    for chain in overlord.config.list_chains():
        limits_settings = {
            "max_keepalive_connections" : overlord.config.get_chain_max_keepalive_connections(chain),
            "max_connections" : overlord.config.get_chain_max_connections(chain),
            "keepalive_expiry" : overlord.config.get_chain_keepalive_expiry(chain)
        }
        timeout_settings = {
            "timeout" : overlord.config.get_chain_timeout(chain),
            "read" : overlord.config.get_chain_read_timeout(chain),
            "write" : overlord.config.get_chain_write_timeout(chain),
            "connect" : overlord.config.get_chain_connect_timeout(chain),
            "pool" : overlord.config.get_chain_pool_timeout(chain)
        }

        entrypoint = overlord.config.get_chain_entrypoint(chain)
        access_token = overlord.config.get_chain_access_token(chain)

        CHAINS[chain] = overlord.client.OverlordClient(
            entrypoint,
            access_token,
            limits=httpx.Limits(**limits_settings),
            timeout=httpx.Timeout(**timeout_settings)
        )

    asyncio.run(listen())
