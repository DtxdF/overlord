# BSD 3-Clause License
#
# Copyright (c) 2025-2026, Jesús Daniel Colmenares Oviedo <DtxdF@disroot.org>
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

import overlord.error

CONFIG = {}

def get_appName():
    return CONFIG.get("appName")

def get_appFrom():
    return CONFIG.get("appFrom")

def get_appConfig():
    return CONFIG.get("appConfig", {})

def validate(document):
    global CONFIG

    _name = "<root:appConfig>"
    overlord.error.assert_type(_name, document, dict)

    keys = (
        "kind",
        "datacenters",
        "deployIn",
        "maximumDeployments",
        "appName",
        "appFrom",
        "appConfig"
    )

    overlord.error.assert_parameter(_name, document, keys)

    validate_appName(document)
    validate_appFrom(document)
    validate_appConfig(document)

    CONFIG = document

def validate_appName(document):
    overlord.error._validate1(document, "", "appName", str, required=True)

def validate_appFrom(document):
    overlord.error._validate1(document, "", "appFrom", str, required=True)

def validate_appConfig(document):
    _value = overlord.error._validate1(document, "", "appConfig", dict)

    if _value is None:
        return

    overlord.error.assert_item(_value, validate_appConfig_item)

def validate_appConfig_item(appConfig, parameter, index):
    overlord.error.assert_type(f"appConfig.<item#{index}>", parameter, str)
    overlord.error.assert_type(f"appConfig.{parameter}", appConfig[parameter], str)
