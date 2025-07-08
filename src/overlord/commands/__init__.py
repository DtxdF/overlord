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
import logging
import signal
import sys

import click

import overlord.default
import overlord.config
import overlord.environment
import overlord.signals
import overlord.util

from overlord.sysexits import EX_SOFTWARE

logger = logging.getLogger(__name__)

@click.group(add_help_option=False)
@click.version_option()
@click.option("-e", "--env-file", default=overlord.default.ENV_FILE, help="Specify an alternate file to load environment variables.")
def cli(*args, **kwargs):
    """
    Overlord is a fast, distributed orchestrator for FreeBSD jails oriented to GitOps.
    You define a file with the service intended to run on your cluster and deployment
    takes seconds to minutes.
    """

    _cli(*args, **kwargs)

def _cli(env_file):
    _cli_load_environment(env_file)
    _cli_load_config()
    _cli_init()

def _cli_load_environment(env_file):
    overlord.environment.init(env_file)

def _cli_load_config():
    config = os.getenv("OVERLORD_CONFIG", overlord.default.CONFIG)

    if os.path.isfile(config):
        try:
            overlord.config.load(config)

        except Exception as err:
            error = overlord.util.get_error(err)
            error_type = error.get("type")
            error_message = error.get("message")

            logger.exception("%s: %s", error_type, error_message)

            sys.exit(EX_SOFTWARE)

        os.environ["OVERLORD_CONFIG"] = config

def _cli_init():
    overlord.signals.ignore_other_signals()
    overlord.signals.enable_handler()

    overlord.trap.add(overlord.signals.disable_handler)
