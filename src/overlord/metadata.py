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
import pathlib
import re

import aiofiles

import overlord.config
import overlord.exceptions

REGEX_KEY = r"([a-zA-Z][a-zA-Z0-9]*(?:(?:\.|-)?[a-zA-Z][a-zA-Z0-9]*)*)"

def _raise_invalid_keyname(key):
    if not check_keyname(key):
        raise overlord.exceptions.InvalidKeyName(f"{key}: invalid key name.")

async def set(key, value, sync=True):
    _raise_invalid_keyname(key)

    length = len(value)
    metadata_size = overlord.config.get_metadata_size()

    if length > metadata_size:
        raise overlord.exceptions.MetadataTooLong(f"{key}: metadata too long - {length} > {metadata_size}")

    metadata_location = overlord.config.get_metadata_location()

    os.makedirs(metadata_location, exist_ok=True)

    metadata = os.path.join(metadata_location, key)

    async with aiofiles.open(metadata, "wb", buffering=0) as fd:
        await fd.write(value.encode())
        await fd.flush()

        if sync:
            os.fsync(fd.fileno())

async def get(key):
    _raise_invalid_keyname(key)

    metadata_location = overlord.config.get_metadata_location()

    metadata = os.path.join(metadata_location, key)

    if not os.path.isfile(metadata):
        raise overlord.exceptions.MetadataNotFound(f"{key}: metadata not found.")

    async with aiofiles.open(metadata, "r") as fd:
        content = await fd.read()

        return content

def glob(pattern):
    metadata_location = overlord.config.get_metadata_location()

    if not os.path.isdir(metadata_location):
        return

    files = pathlib.Path(metadata_location)

    return files.glob(pattern)

def delete(key):
    _raise_invalid_keyname(key)

    metadata_location = overlord.config.get_metadata_location()

    metadata = os.path.join(metadata_location, key)

    if not os.path.isfile(metadata):
        raise overlord.exceptions.MetadataNotFound(f"{key}: metadata not found.")

    os.remove(metadata)

def check(key):
    _raise_invalid_keyname(key)

    metadata_location = overlord.config.get_metadata_location()

    metadata = os.path.join(metadata_location, key)

    result = os.path.isfile(metadata)

    return result

def check_keyname(key):
    match = re.match(REGEX_KEY, key)

    if match is None:
        return False

    return match.group(1) == key
