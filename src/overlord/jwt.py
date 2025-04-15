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

import os
import secrets

import jwt

import overlord.config

SECRET_KEY = None

def get_secret_key():
    global SECRET_KEY

    if SECRET_KEY is not None:
        return SECRET_KEY

    secret_key = overlord.config.get_secret_key()

    if secret_key is not None:
        return secret_key

    keylen = 64
    secret_keyfile = overlord.config.get_secret_keyfile()

    secret_keydir = os.path.dirname(secret_keyfile)

    if len(secret_keydir) > 0:
        os.makedirs(secret_keydir, exist_ok=True)

    if os.path.isfile(secret_keyfile):
        with open(secret_keyfile, "rb") as fd:
            secret_key = fd.read()

    if secret_key is None \
            or len(secret_key) != keylen:
        secret_key = secrets.token_bytes(keylen)

        with open(secret_keyfile, "wb") as fd:
            fd.write(secret_key)
            fd.flush()
            os.fsync(fd.fileno())

        os.chmod(secret_keyfile, 0o400)

    SECRET_KEY = secret_key

    return SECRET_KEY

def encode(payload):
    return jwt.encode(payload, get_secret_key(), algorithm="HS256")

def decode(encoded_jwt):
    return jwt.decode(encoded_jwt, get_secret_key(), algorithms=["HS256"])
