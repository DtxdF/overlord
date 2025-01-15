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
import signal

import overlord.trap

from signal import (SIGALRM,
                   SIGVTALRM,
                   SIGPROF,
                   SIGUSR1,
                   SIGUSR2,
                   SIGHUP,
                   SIGINT,
                   SIGQUIT,
                   SIGTERM,
                   SIGXCPU,
                   SIGXFSZ)

IGNORED_SIGNALS = (SIGALRM, SIGVTALRM, SIGPROF, SIGUSR1, SIGUSR2)
HANDLER_SIGNALS = (SIGHUP, SIGINT, SIGQUIT, SIGTERM, SIGXCPU, SIGXFSZ)

def enable_handler(*args, **kwargs):
    for signum in HANDLER_SIGNALS:
        signal.signal(signum, overlord.trap.trap)

def disable_handler(*args, **kwargs):
    for signum in HANDLER_SIGNALS:
        signal.signal(signum, signal.SIG_IGN)

def ignore_other_signals(*args, **kwargs):
    for signum in IGNORED_SIGNALS:
        signal.signal(signum, signal.SIG_IGN)
