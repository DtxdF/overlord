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

import overlord.exceptions

CONFIG = {}

def get_appName():
    return CONFIG.get("appName")

def get_appFrom():
    return CONFIG.get("appFrom")

def get_appConfig():
    return CONFIG.get("appConfig", {})

def validate(document):
    global CONFIG

    if not isinstance(document, dict):
        raise overlord.exceptions.InvalidSpec("The document is invalid.")

    keys = (
        "kind",
        "datacenters",
        "deployIn",
        "maximumDeployments",
        "appName",
        "appFrom",
        "appConfig"
    )

    for key in document:
        if key not in keys:
            raise overlord.exceptions.InvalidSpec(f"{key}: this key is invalid.")

    validate_appName(document)
    validate_appFrom(document)
    validate_appConfig(document)

    CONFIG = document

def validate_appName(document):
    appName = document.get("appName")

    if appName is None:
        raise overlord.exceptions.InvalidSpec("'appName' is required but hasn't been specified.")

    if not isinstance(appName, str):
        raise overlord.exceptions.InvalidSpec(f"{appName}: invalid value type for 'appName'")

def validate_appFrom(document):
    appFrom = document.get("appFrom")

    if appFrom is None:
        raise overlord.exceptions.InvalidSpec("'appFrom' is required but hasn't been specified.")

    if not isinstance(appFrom, str):
        raise overlord.exceptions.InvalidSpec(f"{appFrom}: invalid value type for 'appFrom'")

def validate_appConfig(document):
    appConfig = document.get("appConfig")

    if appConfig is None:
        return

    if not isinstance(appConfig, dict):
        raise overlord.exceptions.InvalidSpec("'appConfig' is invalid.")

    for appConfig_name, appConfig_value in appConfig.items():
        if not isinstance(appConfig_name, str) \
                or not isinstance(appConfig_value, str):
            raise overlord.exceptions.InvalidSpec(f"Invalid appConfig name (appConfig.{appConfig_name}) or value (appConfig.{appConfig_value}).")
