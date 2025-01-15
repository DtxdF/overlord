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
import traceback

import tornado.escape
import tornado.httpclient
import tornado.web

import overlord.config
import overlord.jwt

from jwt.exceptions import PyJWTError

class RequireArg(Exception):
    pass

_require_arg = RequireArg()

DEFAULT_HTTP_HEADERS = {
    "Access-Control-Allow-Origin"   : "*",
    "Access-Control-Allow-Headers"  : "*"
}

DEFAULT_METHODS = "POST, GET, PUT, DELETE, OPTIONS"

logger = logging.getLogger(__name__)

class JSONHandler(tornado.web.RequestHandler):
    async def prepare(self):
        if self.get_status() < 400:
            log_method = logger.info

        elif self.get_status() < 500:
            log_method = logger.warning

        else:
            log_method = logger.error

        request_time = 1000.0 * self.request.request_time()
        log_method(
            "%d %s %.2fms",
            self.get_status(),
            self._request_summary(),
            request_time,
        )

        self.request.json_arguments = {}
        body = self.request.body

        if body:
            try:
                json_data = tornado.escape.json_decode(body)

            except json.decoder.JSONDecodeError:
                self.write_template({
                    "message" : "Request has been received with an invalid format."
                }, status_code=400)

                self.finish()

                return

            if not isinstance(json_data, dict):
                self.write_template({
                    "message" : "A dictionary was expected but another value type was given."
                }, status_code=400)

                self.finish()

                return

            self.request.json_arguments.update(json_data)

    def _check_argument(
        self,
        name,
        value,
        value_type=None,
        valid_func=None,
        exceptions=(TypeError, ValueError)
    ):
        if value_type is not None:
            try:
                value = value_type(value)

            except exceptions:
                raise tornado.web.HTTPError(400, reason=f"'{name}' has an unexpected value type.")

        if valid_func is not None \
                and not valid_func(value):
            raise tornado.web.HTTPError(400, reason=f"'{name}' has an unexpected value.")

        return value

    def get_json_argument(
        self,
        name,
        default=_require_arg,
        strip=True,
        value_type=None,
        valid_func=None,
        exceptions=(TypeError, ValueError)
    ):
        try:
            value = self.request.json_arguments[name]

        except KeyError:
            if isinstance(default, RequireArg):
                raise tornado.web.HTTPError(400, reason=f"`{name}` is required but hasn't been specified.")

            return default

        if strip and isinstance(value, str):
            value = value.strip()

        value = self._check_argument(
            name, value, value_type, valid_func, exceptions
        )

        return value

    def __get_argument(
        self,
        get_arg_func,
        name,
        default=_require_arg,
        strip=True,
        **kwargs
    ):
        try:
            value = get_arg_func(name, strip=strip)

        except tornado.web.MissingArgumentError:
            if isinstance(default, RequireArg):
                raise tornado.web.HTTPError(400, reason=f"`{name}` is required but hasn't been specified.")

            return default

        value = self._check_argument(
            name, value, **kwargs
        )

        return value

    def get_argument(self, *args, **kwargs):
        return self.__get_argument(super().get_argument, *args, **kwargs)

    def get_query_argument(self, *args, **kwargs):
        return self.__get_argument(super().get_query_argument, *args, **kwargs)

    def get_body_argument(self, *args, **kwargs):
        return self.__get_argument(super().get_body_argument, *args, **kwargs)

    def write_error(self, status_code, **kwargs):
        body = {}
        trace = []
        body["message"] = self._reason

        for err in traceback.format_exception(*kwargs["exc_info"]):
            err = err.rstrip()

            logging.error(err)

            if overlord.config.get_debug():
                trace.append(err)
        
        if trace != []:
            body["trace"] = "\n".join(trace)

        self.write_template(body, status_code)

    def write_template(self, chunk, status_code=200, *args, **kwargs):
        response = {
            "status_code" : status_code
        }

        response.update(chunk)

        self.write_json(response, status_code, *args, **kwargs)

    def write_json(self, chunk, status_code=200):
        self.set_status(status_code)

        self.write(tornado.escape.json_encode(chunk))

    def set_default_headers(self):
        self.set_header("Content-Type", "application/json")

        for key, value in DEFAULT_HTTP_HEADERS.items():
            self.set_header(key, value)

    async def options(self, *args, **kwargs):
        self.set_header("Access-Control-Allow-Methods", DEFAULT_METHODS)

class JSONAuthHandler(JSONHandler):
    async def prepare(self):
        await super().prepare()

        authentication = self.request.headers.get("Authentication")

        if authentication is None:
            raise tornado.web.HTTPError(401, reason="'Authentication' header is required but hasn't been specified.")

        authentication = authentication.split(" ", 1)

        if len(authentication) != 2:
            raise tornado.web.HTTPError(400, reason="'Authentication' header is invalid for this entrypoint.")

        (scheme, token) = authentication

        if scheme != "Bearer":
            raise tornado.web.HTTPError(400, reason="Authentication scheme is invalid for this entrypoint.")

        try:
            self.jwt_payload = overlord.jwt.decode(token)

        except PyJWTError:
            raise tornado.web.HTTPError(401, reason="Error while decoding the JWT.")

        self.jwt_token = token

class NotFoundHandler(JSONHandler):
    def initialize(self, status_code, message):
        self.set_status(status_code, message)

    def prepare(self):
        raise tornado.web.HTTPError(
            self._status_code, self._reason
        )

class RequiredResourceHandler(JSONHandler):
    def prepare(self):
        self.write_template({
            "message" : "API resource must be specified but is missing."
        }, status_code=400)

    async def get(self):
        pass

    async def post(self):
        pass

    async def put(self):
        pass

    async def delete(self):
        pass
