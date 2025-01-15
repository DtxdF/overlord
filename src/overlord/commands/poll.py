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

import logging
import sys
import time

import click

import overlord.cache
import overlord.commands
import overlord.config
import overlord.director
import overlord.jail
import overlord.process
import overlord.util

from overlord.sysexits import EX_SOFTWARE, EX_UNAVAILABLE

logger = logging.getLogger(__name__)

@overlord.commands.cli.command(add_help_option=False)
def poll_jails():
    check_appjail()

    try:
        while True:
            (rc, jails) = overlord.jail.get_list()

            if rc != 0:
                logger.error("Error retrieving the list of jails - exit status code is %d", rc)
                sys.exit(rc)

            overlord.cache.gc_jails(jails)

            time.sleep(overlord.config.get_polling_jails() + overlord.util.get_skew())

    except Exception as err:
        error = overlord.util.get_error(err)
        error_type = error.get("type")
        error_message = error.get("message")

        logger.exception("%s: %s", error_type, error_message)

        sys.exit(EX_SOFTWARE)

@overlord.commands.cli.command(add_help_option=False)
def poll_jail_info():
    check_appjail()

    try:
        overlord.process.init()

        while True:
            jails = overlord.cache.get_jails()

            for jail in jails:
                (rc, info) = overlord.jail.info(jail)

                if rc != 0:
                    logger.warning("Error retrieving information about the jail '%s' - exit status code is %d", jail, rc)
                    continue

                overlord.cache.save_jail_info(jail, info)

            time.sleep(overlord.config.get_polling_jail_info() + overlord.util.get_skew())

    except Exception as err:
        error = overlord.util.get_error(err)
        error_type = error.get("type")
        error_message = error.get("message")

        logger.exception("%s: %s", error_type, error_message)

        sys.exit(EX_SOFTWARE)

@overlord.commands.cli.command(add_help_option=False)
@click.option("--item", default=[], multiple=True, type=click.Choice(("cpuset", "devfs", "expose", "healthcheck", "limits", "fstab", "label", "nat", "volume")))
def poll_jail_extras(item):
    check_appjail()

    try:
        overlord.process.init()

        flags = {
            "cpuset" : False,
            "devfs" : False,
            "expose" : False,
            "healthcheck" : False,
            "limits" : False,
            "fstab" : False,
            "label" : False,
            "nat" : False,
            "volume" : False
        }

        items = item

        if len(items) == 0:
            for item in flags:
                flags[item] = True

        for item in items:
            if item not in flags:
                logger.warning("Ignoring unknown item '%s'", item)
                continue

            flags[item] = True

        while True:
            jails = overlord.cache.get_jails()

            for jail in jails:
                if flags.get("cpuset") and overlord.jail.status(jail):
                    (rc, cpuset) = overlord.jail.get_cpuset(jail)

                    if rc != 0:
                        logger.warning("Error retrieving the CPU sets of jail '%s' - exit status code is %d", jail, rc)

                    else:
                        overlord.cache.save_jail_cpuset(jail, cpuset)

                if flags.get("devfs"):
                    (rc, nros) = overlord.jail.get_devfs_nros(jail)

                    if rc != 0:
                        logger.warning("Error retrieving the DEVFS NROs of jail '%s' - exit status code is %d", jail, rc)

                    else:
                        data = []

                        for nro in nros:
                            (rc, devfs) = overlord.jail.list_devfs(jail, nro)

                            if rc != 0:
                                logger.warning("Error retrieving the DEVFS rules of jail '%s' - exit status code is %d", jail, rc)

                            else:
                                data.append(devfs)

                        overlord.cache.save_jail_devfs(jail, data)

                if flags.get("expose"):
                    (rc, nros) = overlord.jail.get_expose_nros(jail)

                    if rc != 0:
                        logger.warning("Error retrieving the expose NROs of jail '%s' - exit status code is %d", jail, rc)

                    else:
                        data = []

                        for nro in nros:
                            (rc, expose) = overlord.jail.list_expose(jail, nro)

                            if rc != 0:
                                logger.warning("Error retrieving the expose rules of jail '%s' - exit status code is %d", jail, rc)

                            else:
                                data.append(expose)

                        overlord.cache.save_jail_expose(jail, data)

                if flags.get("healthcheck"):
                    (rc, nros) = overlord.jail.get_healthcheck_nros(jail)

                    if rc != 0:
                        logger.warning("Error retrieving the healthcheck NROs of jail '%s' - exit status code is %d")

                    else:
                        data = []

                        for nro in nros:
                            (rc, healthcheck) = overlord.jail.list_healthcheck(jail, nro)

                            if rc != 0:
                                logger.warning("Error retrieving the healthcheck rules of jail '%s' - exit status code is %d", jail, rc)

                            else:
                                data.append(healthcheck)

                        overlord.cache.save_jail_healthcheck(jail, data)

                if flags.get("limits"):
                    (rc, nros) = overlord.jail.get_limits_nros(jail)

                    if rc != 0:
                        logger.warning("Error retrieving the limits NROs of jail '%s' - exit status code is %d", jail, rc)

                    else:
                        data = []

                        for nro in nros:
                            (rc, limits) = overlord.jail.list_limits(jail, nro)

                            if rc != 0:
                                logger.warning("Error retrieving the limits rules of jail '%s' - exit status code is %d", jail, rc)

                            else:
                                data.append(limits)

                        overlord.cache.save_jail_limits(jail, data)

                if flags.get("fstab"):
                    (rc, nros) = overlord.jail.get_fstab_nros(jail)

                    if rc != 0:
                        logger.warning("Error retrieving the fstab NROs of jail '%s' - exit status code is %d", jail, rc)

                    else:
                        data = []

                        for nro in nros:
                            (rc, fstab) = overlord.jail.list_fstab(jail, nro)

                            if rc != 0:
                                logger.warning("Error retrieving the fstab entries of jail '%s' - exit status code is %d", jail, rc)

                            else:
                                data.append(fstab)

                        overlord.cache.save_jail_fstab(jail, data)

                if flags.get("label"):
                    (rc, labels) = overlord.jail.get_labels(jail)

                    if rc != 0:
                        logger.warning("Error retrieving the labels of jail '%s' - exit status code is %d", jail, rc)

                    else:
                        data = []

                        for label in labels:
                            (rc, label) = overlord.jail.list_label(jail, label)

                            if rc != 0:
                                logger.warning("Error retrieving the label of jail '%s' - exit status code is %d", jail, rc)

                            else:
                                data.append(label)

                        overlord.cache.save_jail_label(jail, data)

                if flags.get("nat"):
                    (rc, networks) = overlord.jail.get_nat_networks(jail)

                    if rc != 0:
                        logger.warning("Error retrieving the NAT networks of jail '%s' - exit status code is %d", jail, rc)

                    else:
                        data = []

                        for network in networks:
                            (rc, entries) = overlord.jail.list_nat(jail, network)

                            if rc != 0:
                                logger.warning("Error retrieving the NAT entries of jail '%s' - exit status code is %d", jail, rc)

                            else:
                                data.append(entries)

                        overlord.cache.save_jail_nat(jail, data)

                if flags.get("volume"):
                    (rc, volumes) = overlord.jail.get_volumes(jail)

                    if rc != 0:
                        logger.warning("Error retrieving the volumes of jail '%s' - exit status code is %d", jail, rc)

                    else:
                        data = []

                        for volume in volumes:
                            (rc, entries) = overlord.jail.list_volume(jail, volume)

                            if rc != 0:
                                logger.warning("Error retrieving the volume entries of jail '%s' - exit status code is %d", jail, rc)

                            else:
                                data.append(entries)

                        overlord.cache.save_jail_volume(jail, data)

            time.sleep(overlord.config.get_polling_jail_extras() + overlord.util.get_skew())

    except Exception as err:
        error = overlord.util.get_error(err)
        error_type = error.get("type")
        error_message = error.get("message")

        logger.exception("%s: %s", error_type, error_message)

        sys.exit(EX_SOFTWARE)

@overlord.commands.cli.command(add_help_option=False)
def poll_jail_stats():
    check_appjail()
    check_rctl()

    try:
        overlord.process.init()

        while True:
            jails = overlord.cache.get_jails()

            for jail in jails:
                if not overlord.jail.status(jail):
                    continue

                (rc, stats) = overlord.jail.stats(jail)

                if rc != 0:
                    logger.warning("Error retrieving stats about the jail '%s' - exit status code is %d", jail, rc)
                    continue

                overlord.cache.save_jail_stats(jail, stats)

            time.sleep(overlord.config.get_polling_jail_stats() + overlord.util.get_skew())

    except Exception as err:
        error = overlord.util.get_error(err)
        error_type = error.get("type")
        error_message = error.get("message")

        logger.exception("%s: %s", error_type, error_message)

        sys.exit(EX_SOFTWARE)

@overlord.commands.cli.command(add_help_option=False)
def poll_projects():
    check_director()

    try:
        while True:
            (rc, projects) = overlord.director.get_list()

            if rc != 0:
                logger.error("Error retrieving the list of projects - exit status code is %d", rc)
                sys.exit(rc)

            overlord.cache.gc_projects(projects)

            time.sleep(overlord.config.get_polling_projects() + overlord.util.get_skew())

    except Exception as err:
        error = overlord.util.get_error(err)
        error_type = error.get("type")
        error_message = error.get("message")

        logger.exception("%s: %s", error_type, error_message)

        sys.exit(EX_SOFTWARE)

@overlord.commands.cli.command(add_help_option=False)
def poll_project_info():
    check_director()

    try:
        overlord.process.init()

        while True:
            projects = overlord.cache.get_projects()

            for project in projects:
                (rc, info) = overlord.director.describe(project)

                if rc != 0:
                    logger.warning("Error retrieving information about the project '%s' - exit status code is %d", project, rc)
                    continue

                overlord.cache.save_project_info(project, info)

            time.sleep(overlord.config.get_polling_project_info() + overlord.util.get_skew())

    except Exception as err:
        error = overlord.util.get_error(err)
        error_type = error.get("type")
        error_message = error.get("message")

        logger.exception("%s: %s", error_type, error_message)

        sys.exit(EX_SOFTWARE)

def check_appjail():
    if not overlord.jail.check_dependency():
        logger.error("AppJail is not installed. Cannot continue ...")
        sys.exit(EX_UNAVAILABLE)

def check_rctl():
    proc = overlord.process.run(["sysctl", "-n", "kern.racct.enable"])

    rc = 0
    value = None

    for output in proc:
        if "rc" in output:
            rc = output["rc"]

        elif "line" in output:
            value = output["line"]
            value = int(value)

    if value == 0:
        logger.error("rctl(4) framework is not enabled. Cannot continue ...")
        sys.exit(EX_UNAVAILABLE)

def check_director():
    if not overlord.director.check_dependency():
        logger.error("Director is not installed. Cannot continue ...")
        sys.exit(EX_UNAVAILABLE)
