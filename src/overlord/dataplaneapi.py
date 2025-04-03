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

import json
import logging

import httpx

logger = logging.getLogger(__name__)

class DataPlaneAPIClientv3(httpx.AsyncClient):
    def __init__(self, base_url, username, password, *args, **kwargs):
        auth = httpx.BasicAuth(
            username=username,
            password=password
        )
        
        super().__init__(
            *args,
            base_url=base_url,
            auth=auth
        )

    async def commit_transaction(self, id, force_reload=False, *, _raise_for_status=True):
        params = {
            "force_reload" : force_reload
        }

        request = await self.put(f"/v3/services/haproxy/transactions/{id}",
                                 params=params, headers={ "Content-Type" : "application/json" })

        if _raise_for_status:
            request.raise_for_status()

        logger.debug("(code:%d, reason:%s) response: %s",
                     request.status_code, request.reason_phrase, json.dumps(request.json(), indent=4))

        return request

    async def get_transaction_id(self, version, *, _raise_for_status=True):
        params = {
            "version" : version
        }

        request = await self.post(f"/v3/services/haproxy/transactions",
                                  params=params, headers={ "Content-Type" : "application/json" })

        if _raise_for_status:
            request.raise_for_status()

        logger.debug("(code:%d, reason:%s) response: %s",
                     request.status_code, request.reason_phrase, json.dumps(request.json(), indent=4))

        return request

    async def get_configuration_version(self, transaction_id=None, *, _raise_for_status=True):
        params = {}

        if transaction_id is not None:
            params["transaction_id"] = transaction_id

        request = await self.get("/v3/services/haproxy/configuration/version", params=params)

        if _raise_for_status:
            request.raise_for_status()

        version = request.json()

        logger.debug("(code:%d, reason:%s) response: %s",
                     request.status_code, request.reason_phrase, json.dumps(request.json(), indent=4))

        return int(version)

    async def get_backend(self, name, transaction_id=None, full_section=False, *, _raise_for_status=True):
        params = {
            "full_section" : full_section
        }

        if transaction_id is not None:
            params["transaction_id"] = transaction_id

        request = await self.get(f"/v3/services/haproxy/configuration/backends/{name}", params=params)

        if _raise_for_status:
            request.raise_for_status()

        logger.debug("(code:%d, reason:%s) response: %s",
                     request.status_code, request.reason_phrase, json.dumps(request.json(), indent=4))

        return request

    async def get_server(self, name, parent_name, transaction_id=None, *, _raise_for_status=True):
        params = {}

        if transaction_id is not None:
            params["transaction_id"] = transaction_id

        request = await self.get(f"/v3/services/haproxy/configuration/backends/{parent_name}/servers/{name}", params=params)

        if _raise_for_status:
            request.raise_for_status()

        logger.debug("(code:%d, reason:%s) response: %s",
                     request.status_code, request.reason_phrase, json.dumps(request.json(), indent=4))

        return request

    async def replace_server(
        self,
        name,
        parent_name,
        transaction_id=None,
        version=None,
        force_reload=False,
        body={},
        *, _raise_for_status=True
    ):
        params = {
            "force_reload" : force_reload
        }

        if transaction_id is not None:
            params["transaction_id"] = transaction_id

        if version is not None:
            params["version"] = version

        if body:
            body = json.dumps(body)

        request = await self.put(f"/v3/services/haproxy/configuration/backends/{parent_name}/servers/{name}",
                                 params=params, data=body, headers={ "Content-Type" : "application/json" })

        if _raise_for_status:
            request.raise_for_status()

        logger.debug("(code:%d, reason:%s) response: %s",
                     request.status_code, request.reason_phrase, json.dumps(request.json(), indent=4))

        return request

    async def add_server(
        self,
        parent_name,
        transaction_id=None,
        version=None,
        force_reload=False,
        body={},
        *, _raise_for_status=True
    ):
        params = {
            "force_reload" : force_reload
        }

        if transaction_id is not None:
            params["transaction_id"] = transaction_id

        if version is not None:
            params["version"] = version

        if body:
            body = json.dumps(body)

        request = await self.post(f"/v3/services/haproxy/configuration/backends/{parent_name}/servers",
                                  params=params, data=body, headers={ "Content-Type" : "application/json" })

        if _raise_for_status:
            request.raise_for_status()

        logger.debug("(code:%d, reason:%s) response: %s",
                     request.status_code, request.reason_phrase, json.dumps(request.json(), indent=4))

        return request

    async def delete_server(
        self,
        name,
        parent_name,
        transaction_id=None,
        version=None,
        force_reload=False,
        *, _raise_for_status=True
    ):
        params = {
            "force_reload" : force_reload
        }

        if transaction_id is not None:
            params["transaction_id"] = transaction_id

        if version is not None:
            params["version"] = version

        request = await self.delete(f"/v3/services/haproxy/configuration/backends/{parent_name}/servers/{name}", params=params)

        if _raise_for_status:
            request.raise_for_status()

        return request
