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

import enum
import logging
import re

import httpx

import overlord.chains
import overlord.director
import overlord.jail
import overlord.util
import overlord.exceptions

logger = logging.getLogger(__name__)

class OverlordEntityTypes(enum.Enum):
    JAIL = 1
    PROJECT = 2

class OverlordAuth(httpx.Auth):
    def __init__(self, token):
        self.token = token

    def auth_flow(self, request):
        request.headers["Authentication"] = f"Bearer {self.token}"

        yield request

class OverlordClient(httpx.AsyncClient):
    def __init__(self, base_url, access_token, *args, **kwargs):
        """
        Create a new instance of an Overlord client. This class inherits all the methods
        and properties of ``httpx.AsyncClient`` so you can take advantage of this.

        Any other arguments or parameters are passed to the parent method ``__init__``.

        Args:
            base_url (str): A URL to use as the base when building request URLs.
            access_token (str): Access token for the server to allow access to the client.
        """

        auth = OverlordAuth(access_token)

        super().__init__(
            *args,
            base_url=base_url,
            auth=auth,
            **kwargs)

    async def up(self, name, director_file, environment={}, chain=None):
        """
        Create a new project.

        Args:
            name (str): Project name.
            director_file (str):
                Project file. Represents the contents of the file, not the
                file name or path.
            environment (dict(str, str), optional):
                A dictionary with additional environments to include when creating the project.
            chain (str, optional):
                The chain that the server(s) should use to redirect the request.

        Returns:
            dict:
                dict: Dictionary containing the key ``job_id`` representing the job identifier
                in beanstalkd, which is mostly useful for debugging.

        Raises:
            - overlord.exceptions.InvalidProjectName
            - overlord.exceptions.InvalidArguments
            - overlord.exceptions.APIError
        """

        if not overlord.director.check_project_name(name):
            raise overlord.exceptions.InvalidProjectName(f"{name}: Invalid project name.")

        parsed = await self.__post_parsed(f"project/up/{name}", chain=chain, json={
            "director_file" : director_file,
            "environment" : environment
        })

        return parsed

    async def down(self, name, environment={}, chain=None):
        """
        Destroy a project.

        Args:
            name (str): Project name.
            environment (dict(str, str), optional):
                A dictionary with additional environments to include when destroying the project.
            chain (str, optional):
                The chain that the server(s) should use to redirect the request.

        Returns:
            dict:
                dict: Dictionary containing the key ``job_id`` representing the job identifier
                in beanstalkd, which is mostly useful for debugging.

        Raises:
            - overlord.exceptions.InvalidProjectName
            - overlord.exceptions.InvalidArguments
            - overlord.exceptions.APIError
        """

        if not overlord.director.check_project_name(name):
            raise overlord.exceptions.InvalidProjectName(f"{name}: Invalid project name.")

        parsed = await self.__post_parsed(f"project/down/{name}", chain=chain, json={
            "environment" : environment
        })

        return parsed

    async def get_status_up(self, name, chain=None):
        """
        Gets the status of the operation created by the ``up`` method.

        Args:
            name (str): Project name.
            chain (str, optional):
                The chain that the server(s) should use to redirect the request.

        Returns:
            dict: Dictionary representing a the information included in the operation created by
            ``up``.

        Raises:
            - overlord.exceptions.InvalidProjectName
            - overlord.exceptions.InvalidEntityType
            - overlord.exceptions.InvalidArguments
            - overlord.exceptions.APIError
        """

        if not overlord.director.check_project_name(name):
            raise overlord.exceptions.InvalidProjectName(f"{name}: Invalid project name.")

        parsed = await self.__get_entity(name, "up", OverlordEntityTypes.PROJECT, chain)

        return parsed.get("status", {})

    async def get_status_down(self, name, chain=None):
        """
        Gets the status of the operation created by the ``down`` method.

        Args:
            name (str): Project name.
            chain (str, optional):
                The chain that the server(s) should use to redirect the request.

        Returns:
            dict: Dictionary representing a the information included in the operation created
            by ``down``.

        Raises:
            - overlord.exceptions.InvalidProjectName
            - overlord.exceptions.InvalidEntityType
            - overlord.exceptions.InvalidArguments
            - overlord.exceptions.APIError
        """

        if not overlord.director.check_project_name(name):
            raise overlord.exceptions.InvalidProjectName(f"{name}: Invalid project name.")

        parsed = await self.__get_entity(name, "down", OverlordEntityTypes.PROJECT, chain)

        return parsed.get("status", {})

    async def get_projects_logs(self, chain=None):
        """
        Gets the logs created by Director.

        Args:
            chain (str, optional):
                The chain that the server(s) should use to redirect the request.

        Returns:
            dict: Dictionary stored as ``{date}/{service}/{log_name}`` where ``{date}`` is a
            dictionary and ``{service}`` is a list of strings containing the ``{log_name}``.

        Raises:
            - overlord.exceptions.InvalidArguments
            - overlord.exceptions.APIError
        """

        parsed = await self.__get_parsed("projects/logs", chain=chain)
        logs = parsed.get("logs", {})

        return logs

    async def get_jails_logs(self, chain=None):
        """
        Gets the logs created by AppJail.

        Args:
            chain (str, optional):
                The chain that the server(s) should use to redirect the request.

        Returns:
            dict: Dictionary stored as ``{type}/{entity}/{subtype}/{log_name}`` where ``{type}``
            is a dictionary containing each ``{entity}``, another dictionary containing each
            ``{subtype}`, a list of strings containing ``{log_name}``.

        Raises:
            - overlord.exceptions.InvalidArguments
            - overlord.exceptions.APIError
        """

        parsed = await self.__get_parsed("jails/logs", chain=chain)
        logs = parsed.get("logs", {})

        return logs

    async def get_project_log(self, date, service, log, chain=None):
        """
        Gets the content of a log created by Director.

        Args:
            date (str): Date on which the log was created.
            service (str): Service owner of this log.
            log (str): Log file name.
            chain (str, optional):
                The chain that the server(s) should use to redirect the request.

        Returns:
            str: The contents of the specified log.

        Raises:
            - overlord.exceptions.InvalidArguments
            - overlord.exceptions.APIError
        """

        if re.match(r"[/]", date) \
                or re.match(r"[/]", service) \
                or re.match(r"[/]", log):
            raise overlord.exceptions.InvalidArguments("One or more arguments contains a character not allowed.")

        parsed = await self.__get_parsed(f"projects/log/{date}/{service}/{log}", chain=chain)
        log_content = parsed.get("log_content")

        return log_content

    async def get_jail_log(self, type, entity, subtype, log, chain=None):
        """
        Gets the content of a log created by AppJail.
        
        Args:
            type (str): Group of entities.
            entity (str): Individual in a group.
            subtype (str): Group of logs.
            log (str): Log file name.
            chain (str, optional):
                The chain that the server(s) should use to redirect the request.

        Returns:
            str: The contents of the specified log.

        Raises:
            - overlord.exceptions.InvalidArguments
            - overlord.exceptions.APIError
        """

        if re.match(r"[/]", type) \
                or re.match(r"[/]", entity) \
                or re.match(r"[/]", subtype) \
                or re.match(r"[/]", log):
            raise overlord.exceptions.InvalidArguments("One or more arguments contains a character not allowed.")

        parsed = await self.__get_parsed(f"jail/log/{type}/{entity}/{subtype}/{log}", chain=chain)
        log_content = parsed.get("log_content")

        return log_content

    async def get_jails(self, chain=None):
        """
        Gets a list of jails.

        Args:
            chain (str, optional):
                The chain that the server(s) should use to redirect the request.

        Returns:
            list(str): List of jails.

        Raises:
            - overlord.exceptions.InvalidArguments
            - overlord.exceptions.APIError
        """

        parsed = await self.__get_parsed("jails", chain=chain)
        jails = parsed.get("jails", [])

        return jails

    async def get_projects(self, chain=None):
        """
        Gets a list of projects.

        Args:
            chain (str, optional):
                The chain that the server(s) should use to redirect the request.

        Returns:
            list(str): List of projects.

        Raises:
            - overlord.exceptions.InvalidArguments
            - overlord.exceptions.APIError
        """

        parsed = await self.__get_parsed("projects", chain=chain)
        projects = parsed.get("projects", [])

        return projects

    async def get_api_labels(self, chain=None):
        """
        Gets a list of API labels.

        Args:
            chain (str, optional):
                The chain that the server(s) should use to redirect the request.

        Returns:
            list(str): List of labels.

        Raises:
            - overlord.exceptions.InvalidArguments
            - overlord.exceptions.APIError
        """

        parsed = await self.__get_parsed("labels", chain=chain)
        labels = parsed.get("labels", [])

        return labels

    async def get_chains(self, chain=None):
        """
        Gets a list of chains.

        Args:
            chain (str, optional):
                The chain that the server(s) should use to redirect the request.

        Returns:
            list(str): List of chains.

        Raises:
            - overlord.exceptions.InvalidArguments
            - overlord.exceptions.APIError
        """

        parsed = await self.__get_parsed("chains", chain=chain)
        chains = parsed.get("chains", [])

        return chains

    async def get_info(self, name, type=OverlordEntityTypes.JAIL, chain=None):
        """
        Gets information from a jail or project.

        Args:
            name (str): Jail or project name.
            type (str): Entity type.
            chain (str, optional):
                The chain that the server(s) should use to redirect the request.

        Returns:
            dict(str, str): Entity information.

        Raises:
            - overlord.exceptions.InvalidArguments
            - overlord.exceptions.InvalidEntityTypes
            - overlord.exceptions.InvalidProjectName
            - overlord.exceptions.InvalidJailName
            - overlord.exceptions.APIError
        """

        if type == OverlordEntityTypes.PROJECT:
            if not overlord.director.check_project_name(name):
                raise overlord.exceptions.InvalidProjectName(f"{name}: Invalid project name.")

        elif type == OverlordEntityTypes.JAIL:
            if not overlord.jail.check_jail_name(name):
                raise overlord.exceptions.InvalidJailName(f"{name}: Invalid jail name.")

        return await self.__get_entity_parsed(name, "info", {}, type, chain)

    async def get_stats(self, name, type=OverlordEntityTypes.JAIL, chain=None):
        """
        Gets the stats provided by the rctl subsystem.

        Note:
            If an attempt is made to call this function with the ``type`` set in
            ``OverlordEntityTypes.PROJECT``, the ``overlord.exceptions.TypeNotAllowed``
            exception will be thrown.

        Args:
            name (str): Jail name.
            type (str): Entity type.
            chain (str, optional):
                The chain that the server(s) should use to redirect the request.

        Returns:
            dict(str, str): Stats.

        Raises:
            - overlord.exceptions.TypeNotAllowed
            - overlord.exceptions.InvalidArguments
            - overlord.exceptions.InvalidEntityTypes
            - overlord.exceptions.InvalidJailName
            - overlord.exceptions.APIError
        """

        if type == OverlordEntityTypes.PROJECT:
            raise overlord.exceptions.TypeNotAllowed("This type can't be used with this function.")

        elif type == OverlordEntityTypes.JAIL:
            if not overlord.jail.check_jail_name(name):
                raise overlord.exceptions.InvalidJailName(f"{name}: Invalid jail name.")

        return await self.__get_entity_parsed(name, "stats", {}, type, chain)

    async def get_cpuset(self, name, chain=None):
        """
        Gets the CPU list assigned to the jail.

        Args:
            name (str): Jail name.
            chain (str, optional):
                The chain that the server(s) should use to redirect the request.

        Returns:
            str: CPU list.

        Raises:
            - overlord.exceptions.InvalidArguments
            - overlord.exceptions.InvalidJailName
            - overlord.exceptions.APIError
        """

        if not overlord.jail.check_jail_name(name):
            raise overlord.exceptions.InvalidJailName(f"{name}: Invalid jail name.")

        return await self.__get_entity_parsed(name, "cpuset", None, chain=chain)

    async def get_devfs(self, name, chain=None):
        """
        Gets the DEVFS rules assigned to the jail.

        Args:
            name (str): Jail name.
            chain (str, optional):
                The chain that the server(s) should use to redirect the request.

        Returns:
            list(dict(str, str)): List of DEVFS rules.

        Raises:
            - overlord.exceptions.InvalidArguments
            - overlord.exceptions.InvalidJailName
            - overlord.exceptions.APIError
        """

        if not overlord.jail.check_jail_name(name):
            raise overlord.exceptions.InvalidJailName(f"{name}: Invalid jail name.")

        return await self.__get_entity_parsed(name, "devfs", [], chain=chain)

    async def get_expose(self, name, chain=None):
        """
        Gets the expose rules assigned to the jail.

        Args:
            name (str): Jail name.
            chain (str, optional):
                The chain that the server(s) should use to redirect the request.

        Returns:
            list(dict(str, str)): List of expose rules.

        Raises:
            - overlord.exceptions.InvalidArguments
            - overlord.exceptions.InvalidJailName
            - overlord.exceptions.APIError
        """

        if not overlord.jail.check_jail_name(name):
            raise overlord.exceptions.InvalidJailName(f"{name}: Invalid jail name.")

        return await self.__get_entity_parsed(name, "expose", [], chain=chain)

    async def get_healthcheck(self, name, chain=None):
        """
        Gets the healthcheckers assigned to the jail.

        Args:
            name (str): Jail name.
            chain (str, optional):
                The chain that the server(s) should use to redirect the request.

        Returns:
            list(dict(str, str)): List of healthcheckers.

        Raises:
            - overlord.exceptions.InvalidArguments
            - overlord.exceptions.InvalidJailName
            - overlord.exceptions.APIError
        """

        if not overlord.jail.check_jail_name(name):
            raise overlord.exceptions.InvalidJailName(f"{name}: Invalid jail name.")

        return await self.__get_entity_parsed(name, "healthcheck", [], chain=chain)

    async def get_limits(self, name, chain=None):
        """
        Gets the limits rules assigned to the jail.

        Args:
            name (str): Jail name.
            chain (str, optional):
                The chain that the server(s) should use to redirect the request.

        Returns:
            list(dict(str, str)): List of limits rules.

        Raises:
            - overlord.exceptions.InvalidArguments
            - overlord.exceptions.InvalidJailName
            - overlord.exceptions.APIError
        """
        
        if not overlord.jail.check_jail_name(name):
            raise overlord.exceptions.InvalidJailName(f"{name}: Invalid jail name.")

        return await self.__get_entity_parsed(name, "limits", [], chain=chain)

    async def get_fstab(self, name, chain=None):
        """
        Gets the fstab entries assigned to the jail.

        Args:
            name (str): Jail name.
            chain (str, optional):
                The chain that the server(s) should use to redirect the request.

        Returns:
            list(dict(str, str)): List of fstab entries.

        Raises:
            - overlord.exceptions.InvalidArguments
            - overlord.exceptions.InvalidJailName
            - overlord.exceptions.APIError
        """

        if not overlord.jail.check_jail_name(name):
            raise overlord.exceptions.InvalidJailName(f"{name}: Invalid jail name.")

        return await self.__get_entity_parsed(name, "fstab", [], chain=chain)

    async def get_labels(self, name, chain=None):
        """
        Gets the labels assigned to the jail.

        Args:
            name (str): Jail name.
            chain (str, optional):
                The chain that the server(s) should use to redirect the request.

        Returns:
            list(dict(str, str)): List of labels.

        Raises:
            - overlord.exceptions.InvalidArguments
            - overlord.exceptions.InvalidJailName
            - overlord.exceptions.APIError
        """

        if not overlord.jail.check_jail_name(name):
            raise overlord.exceptions.InvalidJailName(f"{name}: Invalid jail name.")
        
        return await self.__get_entity_parsed(name, "labels", [], chain=chain)

    async def get_nat(self, name, chain=None):
        """
        Gets the NAT rules assigned to the jail.

        Args:
            name (str): Jail name.
            chain (str, optional):
                The chain that the server(s) should use to redirect the request.

        Returns:
            list(dict(str, str)): List of NAT rules.

        Raises:
            - overlord.exceptions.InvalidArguments
            - overlord.exceptions.InvalidJailName
            - overlord.exceptions.APIError
        """

        if not overlord.jail.check_jail_name(name):
            raise overlord.exceptions.InvalidJailName(f"{name}: Invalid jail name.")

        return await self.__get_entity_parsed(name, "nat", [], chain=chain)

    async def get_volumes(self, name, chain=None):
        """
        Gets the volumes assigned to the jail.

        Args:
            name (str): Jail name.
            chain (str, optional):
                The chain that the server(s) should use to redirect the request.

        Returns:
            list(dict(str, str)): List of volumes.

        Raises:
            - overlord.exceptions.InvalidArguments
            - overlord.exceptions.InvalidJailName
            - overlord.exceptions.APIError
        """

        if not overlord.jail.check_jail_name(name):
            raise overlord.exceptions.InvalidJailName(f"{name}: Invalid jail name.")

        return await self.__get_entity_parsed(name, "volumes", [], chain=chain)

    async def get_all_chains(self, chain=None):
        """
        Gets all chains recursively.

        Args:
            chain (str, optional):
                The chain that the server(s) should use to redirect the request.

        Yields:
            str: The next chain.
        """

        try:
            chains = await self.get_chains(chain=chain)
            
        except Exception as err:
            error = overlord.util.get_error(err)
            error_type = error.get("type")
            error_message = error.get("message")

            logger.warning("Error obtaining the chains of entrypoint URL '%s' (chain:%s): %s: %s",
                           self.base_url, chain, error_type, error_message)

            return

        if chain is None:
            first_chain = []

        else:
            first_chain = [chain]

        for chain in chains:
            chain = overlord.chains.join_chain(first_chain + [chain])

            yield chain

            async for chain in self.get_all_chains(chain=chain):
                yield chain

    async def __post_parsed(self, path, *args, chain=None, **kwargs):
        return await self.__parsed("post", path, *args, chain=chain, **kwargs)

    async def __get_parsed(self, path, *args, chain=None, **kwargs):
        return await self.__parsed("get", path, *args, chain=chain, **kwargs)

    async def __parsed(self, method, path, *args, chain=None, **kwargs):
        if chain is None:
            url = f"/v1/{path}"

        else:
            if re.match(r"[/]", chain):
                raise overlord.exceptions.InvalidArguments(f"{chain}: The chain contains a character not allowed.")

            url = f"/v1/chain/{chain}/{path}"

        if method == "get":
            method = self.__get

        elif method == "post":
            method = self.__post

        request = await method(url, *args, **kwargs)

        return request.json()

    async def __get_entity(self, name, command, type=OverlordEntityTypes.JAIL, chain=None):
        if type == OverlordEntityTypes.JAIL:
            entity = "jail"

        elif type == OverlordEntityTypes.PROJECT:
            entity = "project"

        else:
            raise overlord.exceptions.InvalidEntityType("Invalid entity type.")

        if re.match(r"[/]", name):
            raise overlord.exceptions.InvalidArguments(f"{name}: Entity name contains a character not allowed.")
        
        return await self.__get_parsed(f"{entity}/{command}/{name}", chain=chain)

    async def __get_entity_parsed(self, name, key, default=None, type=OverlordEntityTypes.JAIL, chain=None):
        parsed = await self.__get_entity(name, key, type, chain)
        
        return parsed.get(key, default)

    async def __get(self, *args, **kwargs):
        return await self.__request(*args, method="get", **kwargs)

    async def __post(self, *args, **kwargs):
        return await self.__request(*args, method="post", **kwargs)

    async def __request(self, *args, method, **kwargs):
        request = await getattr(self, method)(*args, **kwargs)

        parsed = request.json()

        status_code = parsed.get("status_code", request.status_code)
        message = parsed.get("message", "Unknown error.")

        try:
            request.raise_for_status()

        except httpx.HTTPStatusError:
            raise overlord.exceptions.APIError(f"Error {status_code}: {message}")

        return request
