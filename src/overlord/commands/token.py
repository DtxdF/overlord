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

import datetime
import secrets
import sys

import click

import overlord.commands
import overlord.jwt
import overlord.version

from overlord.sysexits import EX_DATAERR

@overlord.commands.cli.command(add_help_option=False)
@click.option("--metadata", multiple=True, default=[])
@click.option("--expire", type=int)
@click.option("--expire-type", default="hours", type=click.Choice(("seconds", "minutes", "hours", "days", "weeks")))
def gen_token(metadata, expire, expire_type):
    metadata_info = {}

    for s in metadata:
        info = s.split("=", 1)

        if len(info) == 1:
            (key, value) = (info[0], "")
        elif len(info) == 2:
            (key, value) = info

        if key.strip() == "":
            continue

        metadata_info[key] = value

    metadata_info["overlord.version"] = overlord.version.get_version()

    payload = {
        "metadata" : metadata_info,
        "random_chunk" : secrets.token_hex(8)
    }

    if expire is not None \
            and expire > 0:
        payload["exp"] = datetime.datetime.now(tz=datetime.timezone.utc)

        if expire_type == "seconds":
            payload["exp"] += datetime.timedelta(seconds=expire)
        elif expire_type == "minutes":
            payload["exp"] += datetime.timedelta(minutes=expire)
        elif expire_type == "hours":
            payload["exp"] += datetime.timedelta(hours=expire)
        elif expire_type == "days":
            payload["exp"] += datetime.timedelta(days=expire)
        elif expire_type == "weeks":
            payload["exp"] += datetime.timedelta(weeks=expire)

    token = overlord.jwt.encode(payload)

    print(token)
