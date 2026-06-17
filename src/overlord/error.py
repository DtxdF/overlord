# BSD 3-Clause License
#
# Copyright (c) 2026, Jesús Daniel Colmenares Oviedo <DtxdF@disroot.org>
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

def assert_type(name, document, type_):
    if isinstance(document, type_):
        return

    document_type = type(document)

    raise overlord.exceptions.InvalidSpec(f"{name}: requires '{type_.__name__}', given '{document_type.__name__}'.")

def assert_types(name, document, types):
    for type_ in types:
        if isinstance(document, type_):
            return

    document_type = type(document)

    types_str = ""
    first = True

    for type_ in types:
        if first:
            types_str = type_.__name__
            first = False

        elif type_ == types[-1]:
            types_str += f" or {type_.__name__}"

        else:
            types_str += f", {type_.__name__}"

    raise overlord.exceptions.InvalidSpec(f"{name}: requires '{types_str}', given '{document_type.__name__}'.")

def assert_parameter(name, document, keys=[], key_type=str):
    for index, key in enumerate(document):
        assert_type(f"{name}.<item#{index}>", key, key_type)

        if len(keys) > 0 and key not in keys:
            raise overlord.exceptions.InvalidSpec(f"{name}.{key}: invalid parameter.")

def assert_value(name, check, value, should_msg):
    if check(value):
        return

    raise ValueError(f"{name}: invalid value, should be '{should_msg}', given '{value}'.")

def assert_item(document, check, data=None):
    for index, item in enumerate(document):
        if data is not None:
            check(document, item, index, data)

        else:
            check(document, item, index)

def assert_required(name):
    raise overlord.exceptions.RequiredParameter(f"{name}: a required parameter has not been specified.")

def assert_len(name, document, length, check=lambda l, dl: l == dl, should_msg="of equal size"):
    document_length = len(document)

    if check(length, document_length):
        return

    raise overlord.exceptions.InvalidSpec(f"{name}: a length of '{length}' has been specified, but should be '{should_msg}'.")

def _validate1(document, prefix, name, type_, check=None, should_msg=None, required=False, multiple=False):
    value = document.get(name)

    if value is None:
        if required:
            overlord.error.assert_required(f"{prefix}{name}")

        else:
            return

    if multiple:
        overlord.error.assert_types(f"{prefix}{name}", value, type_)

    else:
        overlord.error.assert_type(f"{prefix}{name}", value, type_)

    if check is not None and should_msg is not None:
        overlord.error.assert_value(f"{prefix}{name}", check, value, should_msg)

    return value

def _validate2(document, prefix, name, keys=[], required=False, type_=dict):
    value = _validate1(document, prefix, name, type_, required=required)

    if value is None:
        return

    overlord.error.assert_parameter(f"{prefix}{name}", value, keys)

    return value
