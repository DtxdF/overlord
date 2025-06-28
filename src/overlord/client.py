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
import ssl

import httpx

import overlord.chains
import overlord.config
import overlord.director
import overlord.jail
import overlord.metadata
import overlord.util
import overlord.exceptions
import overlord.vm

from httpx_retries import RetryTransport, Retry

logger = logging.getLogger(__name__)

class OverlordEntityTypes(enum.Enum):
    JAIL = 1
    PROJECT = 2
    METADATA = 3
    VMJAIL = 4

class OverlordAuth(httpx.Auth):
    def __init__(self, token):
        self.token = token

    def auth_flow(self, request):
        request.headers["Authentication"] = f"Bearer {self.token}"

        yield request

class OverlordClient(httpx.AsyncClient):
    def __init__(self, base_url, access_token, pretty_exc=True, *args, **kwargs):
        """
        Create a new instance of an Overlord client. This class inherits all the methods
        and properties of ``httpx.AsyncClient`` so you can take advantage of this.

        Any other arguments or parameters are passed to the parent method ``__init__``.

        Args:
            base_url (str): A URL to use as the base when building request URLs.
            access_token (str): Access token for the server to allow access to the client.
            pretty_exc (bool, optional): By throwing an HTTPX exception, make it look friendlier.
        """

        self.__pretty_exc = pretty_exc

        auth = OverlordAuth(access_token)

        super().__init__(
            *args,
            base_url=base_url,
            auth=auth,
            **kwargs)

    async def up(self, name, director_file, environment={}, restart=False, reserve_port={}, chain=None):
        """
        Create a new project.

        Args:
            name (str): Project name.
            director_file (str):
                Project file. Represents the contents of the file, not the
                file name or path.
            environment (dict(str, str), optional):
                A dictionary with additional environments to include when creating the project.
            restart (bool, optional):
                Restart the project if it exists.
            reserve_port (dict(str, str), optional):
                A dictionary where each key is an interface name and optionally its value with
                a network address. It is used to obtain an IP address to be used when reserving
                the port.
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
            "environment" : environment,
            "restart" : restart,
            "reserve_port" : reserve_port
        })

        return parsed

    async def down(self, name, environment={}, force=False, chain=None):
        """
        Destroy a project.

        Args:
            name (str): Project name.
            environment (dict(str, str), optional):
                A dictionary with additional environments to include when destroying the project.
            force (bool, optional):
                Force the destruction of a project without running the special labels. If a special
                label has been previously run using ``up``, be careful when using this option, as it
                may cause undefined behavior in the integration (e.g., pointing to a nonexistent
                service on the load balancer).
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
            "environment" : environment,
            "force" : force
        })

        return parsed

    async def cancel(self, name, chain=None):
        """
        Terminate a project in progress.

        Args:
            name (str): Project name.
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

        parsed = await self.__post_parsed(f"project/cancel/{name}", chain=chain)

        return parsed

    async def get_status_up(self, name, chain=None):
        """
        Gets the status of the operation created by the ``up`` method.

        Args:
            name (str): Project name.
            chain (str, optional):
                The chain that the server(s) should use to redirect the request.

        Returns:
            dict: Dictionary representing the information created by ``up``.

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
            dict: Dictionary representing the information created by ``down``.

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

    async def get_status_autoscale(self, name, chain=None):
        """
        If the project was created by autoscaling, it reveals the information created by
        this operation.

        Args:
            name (str): Project name.
            chain (str, optional):
                The chain that the server(s) should use to redirect the request.

        Returns:
            dict: Dictionary representing the information created by autoscaling.

        Raises:
            - overlord.exceptions.InvalidProjectName
            - overlord.exceptions.InvalidEntityType
            - overlord.exceptions.InvalidArguments
            - overlord.exceptions.APIError
        """

        if not overlord.director.check_project_name(name):
            raise overlord.exceptions.InvalidProjectName(f"{name}: Invalid project name.")

        parsed = await self.__get_entity(name, "autoscale", OverlordEntityTypes.PROJECT, chain)

        return parsed.get("status", {})

    async def get_status_vm(self, name, chain=None):
        """
        Gets the status of the operation created by the ``create_vm`` method.

        Args:
            name (str): VM name.
            chain (str, optional):
                The chain that the server(s) should use to redirect the request.

        Returns:
            dict: Dictionary representing the information created by ``create_vm``.

        Raises:
            - overlord.exceptions.InvalidVMName
            - overlord.exceptions.InvalidEntityType
            - overlord.exceptions.InvalidArguments
            - overlord.exceptions.APIError
        """

        if not overlord.vm.check_vm_name(name):
            raise overlord.exceptions.InvalidVMName(f"{name}: Invalid VM name.")

        parsed = await self.__get_entity(name, type=OverlordEntityTypes.VMJAIL, chain=chain)

        return parsed.get("status", {})

    async def create_vm(self, name, profile, chain=None):
        """
        Create a new VM.

        Args:
            name (str): VM name.
            profile (dict):
                A profile is a dictionary that follows the same specification as the ``vmJail`` kind
                in a deployment file, excluding ``vmName`` which is implicitly set.
            chain (str, optional):
                The chain that the server(s) should use to redirect the request.

        Returns:
            dict:
                dict: Dictionary containing the key ``job_id`` representing the job identifier
                in beanstalkd, which is mostly useful for debugging.

        Raises:
            - overlord.exceptions.InvalidVMName
            - overlord.exceptions.InvalidArguments
            - overlord.exceptions.APIError
        """

        if not overlord.vm.check_vm_name(name):
            raise overlord.exceptions.InvalidVMName(f"{name}: Invalid VM name.")

        parsed = await self.__post_parsed(f"vm/{name}", chain=chain, json=profile)

        return parsed

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
            - overlord.exceptions.InvalidEntityType
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

    async def check(self, name, type=OverlordEntityTypes.JAIL, chain=None):
        if re.match(r"[/]", name):
            raise overlord.exceptions.InvalidArguments(f"{name}: The project name contains a character not allowed.")

        if not overlord.director.check_project_name(name):
            raise overlord.exceptions.InvalidKeyName(f"{name}: Invalid project name.")

        if type == OverlordEntityTypes.PROJECT:
            entity = "project"

        elif type == OverlordEntityTypes.JAIL:
            entity = "jail"

        else:
            raise overlord.exceptions.InvalidEntityType("Invalid entity type.")

        if chain is None:
            url = f"/v1/{entity}/info/{name}"

        else:
            if re.match(r"[/]", chain):
                raise overlord.exceptions.InvalidArguments(f"{chain}: The chain contains a character not allowed.")

            url = f"/v1/chain/{chain}/{entity}/info/{name}"

        request = await self.head(url)

        status_code = request.status_code

        if status_code == 200:
            return True

        elif status_code == 404:
            return False

        else:
            reason = request.reason_phrase

            try:
                request.raise_for_status()

            except httpx.HTTPStatusError:
                raise overlord.exceptions.APIError(f"Error {status_code}: {reason}")

    async def get_server_stats(self, chain=None):
        """
        List server metrics.

        Args:
            chain (str, optional):
                The chain that the server(s) should use to redirect the request.

        Returns:
            dict(str, int): Metrics.

        Raises:
            - overlord.exceptions.InvalidArguments
            - overlord.exceptions.APIError
        """

        parsed = await self.__get_parsed("stats", chain=chain)
        stats = parsed.get("stats", {})

        return stats

    async def ping(self, chain=None):
        """
        Ping a chain.

        Args:
            chain (str, optional):
                The chain that the server(s) should use to redirect the request.

        Returns:
            str: An "OK" string.

        Raises:
            - overlord.exceptions.InvalidArguments
            - overlord.exceptions.APIError
        """

        parsed = await self.__get_parsed("ping", chain=chain)
        status = parsed.get("status", "OK")

        return status

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
            - overlord.exceptions.InvalidEntityType
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

    async def get_all_chains(self, chain=None, on_fail=None):
        """
        Gets all chains recursively.

        Args:
            chain (list(str), optional):
                The chain that the server(s) should use to redirect the request.
            on_fail (callable, optional):
                Function called when an error is detected. The first argument is the chain (str),
                the second is the type of error (str), the third is the error description (str)
                and the fourth is the exception (object).

        Yields:
            str: The next chain.
        """

        try:
            chains = await self.get_chains(chain=chain)
            
        except Exception as err:
            error = overlord.util.get_error(err)
            error_type = error.get("type")
            error_message = error.get("message")

            if on_fail is not None:
                on_fail(chain, error_type, error_message, err)

            logger.warning("(entrypoint:%s, chain:%s, exception:%s) error obtaining the chains: %s",
                           self.base_url, chain, error_type, error_message)

            return

        if chain is None:
            first_chain = []

        else:
            first_chain = [chain]

        for chain in chains:
            chain = overlord.chains.join_chain(first_chain + [chain])

            yield chain

            async for chain in self.get_all_chains(chain=chain, on_fail=on_fail):
                yield chain

    async def metadata_set(self, key, value, chain=None):
        """
        Create a new metadata file or update an existing one.

        Args:
            key (str): Metadata identifier.
            value (str): Metadata content.
            chain (str, optional):
                The chain that the server(s) should use to redirect the request.

        Returns:
            str: Message indicating whether metadata has been created or updated.

        Raises:
            - overlord.exceptions.InvalidArguments
            - overlord.exceptions.InvalidKeyName
            - overlord.exceptions.APIError
        """

        if await self.metadata_check(key, chain=chain):
            response = await self.__put_parsed(f"metadata/{key}", chain=chain, json={
                "value" : value
            })

        else:
            response = await self.__post_parsed(f"metadata/{key}", chain=chain, json={
                "value" : value
            })

        return response.get("message")

    async def metadata_get(self, key, chain=None):
        """
        Obtain the content of a metadata.

        Args:
            key (str): Metadata identifier.
            chain (str, optional):
                The chain that the server(s) should use to redirect the request.

        Returns:
            str: Metadata content.

        Raises:
            - overlord.exceptions.InvalidArguments
            - overlord.exceptions.InvalidEntityType
            - overlord.exceptions.InvalidKeyName
            - overlord.exceptions.APIError
        """

        response = await self.__get_entity(key, type=OverlordEntityTypes.METADATA, chain=chain)

        value = response.get("metadata")
        
        return value

    async def metadata_delete(self, key, chain=None):
        """
        Delete an existing metadata.

        Args:
            key (str): Metadata identifier.
            chain (str, optional):
                The chain that the server(s) should use to redirect the request.

        Returns:
            bool:
                True if the metadata has been deleted succesfully or thown an exception if an
                unexpected status code is detected.

        Raises:
            - overlord.exceptions.InvalidArguments
            - overlord.exceptions.InvalidKeyName
            - overlord.exceptions.APIError
        """

        if re.match(r"[/]", key):
            raise overlord.exceptions.InvalidArguments(f"{key}: The key contains a character not allowed.")

        if not overlord.metadata.check_keyname(key):
            raise overlord.exceptions.InvalidKeyName(f"{key}: Invalid key name.")

        if chain is None:
            url = f"/v1/metadata/{key}"

        else:
            if re.match(r"[/]", chain):
                raise overlord.exceptions.InvalidArguments(f"{chain}: The chain contains a character not allowed.")

            url = f"/v1/chain/{chain}/metadata/{key}"

        request = await self.delete(url)

        status_code = request.status_code

        if status_code == 204:
            return True

        else:
            reason = request.reason_phrase

            try:
                request.raise_for_status()

            except httpx.HTTPStatusError:
                raise overlord.exceptions.APIError(f"Error {status_code}: {reason}")

    async def metadata_check(self, key, chain=None):
        """
        Checks for the existence of a metadata.

        Args:
            key (str): Metadata identifier.
            chain (str, optional):
                The chain that the server(s) should use to redirect the request.

        Returns:
            bool:
                True if the metadata exists or False if not. An exception is thrown if unexpected
                status code is detected.

        Raises:
            - overlord.exceptions.InvalidArguments
            - overlord.exceptions.InvalidEntityType
            - overlord.exceptions.InvalidKeyName
            - overlord.exceptions.APIError
        """

        if re.match(r"[/]", key):
            raise overlord.exceptions.InvalidArguments(f"{key}: The key contains a character not allowed.")

        if not overlord.metadata.check_keyname(key):
            raise overlord.exceptions.InvalidKeyName(f"{key}: Invalid key name.")

        if chain is None:
            url = f"/v1/metadata/{key}"

        else:
            if re.match(r"[/]", chain):
                raise overlord.exceptions.InvalidArguments(f"{chain}: The chain contains a character not allowed.")

            url = f"/v1/chain/{chain}/metadata/{key}"

        request = await self.head(url)

        status_code = request.status_code

        if status_code == 200:
            return True

        elif status_code == 404:
            return False

        else:
            reason = request.reason_phrase

            try:
                request.raise_for_status()

            except httpx.HTTPStatusError:
                raise overlord.exceptions.APIError(f"Error {status_code}: {reason}")

    async def metadata_list(self, chain=None):
        """
        List all currently stored metadata.

        Args:
            chain (str, optional):
                The chain that the server(s) should use to redirect the request.

        Returns:
            list(str): Metadata.

        Raises:
            - overlord.exceptions.InvalidArguments
            - overlord.exceptions.APIError
        """

        parsed = await self.__get_parsed("metadata", chain=chain)
        metadata = parsed.get("metadata", [])

        return metadata

    async def __post_parsed(self, path, *args, chain=None, **kwargs):
        return await self.__parsed("post", path, *args, chain=chain, **kwargs)

    async def __put_parsed(self, path, *args, chain=None, **kwargs):
        return await self.__parsed("put", path, *args, chain=chain, **kwargs)

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

        elif method == "put":
            method = self.__put

        request = await method(url, *args, **kwargs)

        return request.json()

    async def __get_entity(self, name, command=None, type=OverlordEntityTypes.JAIL, chain=None):
        if type == OverlordEntityTypes.JAIL:
            entity = "jail"

        elif type == OverlordEntityTypes.PROJECT:
            entity = "project"

        elif type == OverlordEntityTypes.METADATA:
            entity = "metadata"

        elif type == OverlordEntityTypes.VMJAIL:
            entity = "vm"

        else:
            raise overlord.exceptions.InvalidEntityType("Invalid entity type.")

        if re.match(r"[/]", name):
            raise overlord.exceptions.InvalidArguments(f"{name}: Entity name contains a character not allowed.")
        
        if command is None:
            result = await self.__get_parsed(f"{entity}/{name}", chain=chain)

        else:
            result = await self.__get_parsed(f"{entity}/{command}/{name}", chain=chain)

        return result

    async def __get_entity_parsed(self, name, key=None, default=None, type=OverlordEntityTypes.JAIL, chain=None):
        parsed = await self.__get_entity(name, key, type, chain)
        
        return parsed.get(key, default)

    async def __get(self, *args, **kwargs):
        return await self.__request(*args, method="get", **kwargs)

    async def __post(self, *args, **kwargs):
        return await self.__request(*args, method="post", **kwargs)

    async def __put(self, *args, **kwargs):
        return await self.__request(*args, method="put", **kwargs)

    async def __request(self, *args, method, **kwargs):
        request = await getattr(self, method)(*args, **kwargs)

        if self.__pretty_exc:
            try:
                request.raise_for_status()

            except httpx.HTTPStatusError:
                raise overlord.exceptions.APIError("(status:%d, reason:%s) %s" % (request.status_code, request.reason_phrase, request.text))

        else:
            request.raise_for_status()

        return request

def get_chain(chain):
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

    retry_policy = {
        "total" : overlord.config.get_chain_retry_total(chain),
        "max_backoff_wait" : overlord.config.get_chain_retry_max_backoff_wait(chain),
        "backoff_factor" : overlord.config.get_chain_retry_backoff_factor(chain),
        "respect_retry_after_header" : overlord.config.get_chain_retry_respect_retry_after_header(chain),
        "backoff_jitter" : overlord.config.get_chain_retry_backoff_jitter(chain)
    }

    entrypoint = overlord.config.get_chain_entrypoint(chain)
    access_token = overlord.config.get_chain_access_token(chain)

    kwargs = {}

    cacert = overlord.config.get_chain_cacert(chain)

    if cacert is not None:
        ctx = ssl.create_default_context(cafile=cacert)

        kwargs["verify"] = ctx

    client = overlord.client.OverlordClient(
        entrypoint,
        access_token,
        pretty_exc=False,
        limits=httpx.Limits(**limits_settings),
        timeout=httpx.Timeout(**timeout_settings),
        transport=RetryTransport(retry=Retry(**retry_policy)),
        **kwargs
    )

    return client
