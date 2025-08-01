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

class InvalidSpec(Exception):
    pass

class APIError(Exception):
    pass

class InvalidEntityType(Exception):
    pass

class InvalidChain(Exception):
    pass

class InvalidKind(InvalidSpec):
    pass

class KindNotDefined(Exception):
    pass

class TypeNotAllowed(Exception):
    pass

class InvalidProjectName(Exception):
    pass

class InvalidJailName(Exception):
    pass

class InvalidVMName(Exception):
    pass

class InvalidArguments(Exception):
    pass

class InterfaceNotFound(Exception):
    pass

class MissingServerID(Exception):
    pass

class EtcdException(Exception):
    pass

class InvalidKeyName(Exception):
    pass

class MetadataTooLong(Exception):
    pass

class MetadataNotFound(Exception):
    pass

class UnavailableChain(Exception):
    pass

class ConfigError(Exception):
    pass

class InvalidQueue(Exception):
    pass
