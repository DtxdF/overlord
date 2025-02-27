#!/bin/sh
#
# Copyright (c) 2025, Jesús Daniel Colmenares Oviedo <DtxdF@disroot.org>
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# * Redistributions of source code must retain the above copyright notice, this
#   list of conditions and the following disclaimer.
#
# * Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.
#
# * Neither the name of the copyright holder nor the names of its
#   contributors may be used to endorse or promote products derived from
#   this software without specific prior written permission.
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

EX_USAGE=64
EX_IOERR=74

IGNORED_SIGNALS="SIGALRM SIGVTALRM SIGPROF SIGUSR1 SIGUSR2"
HANDLER_SIGNALS="SIGHUP SIGINT SIGQUIT SIGTERM SIGXCPU SIGXFSZ"

set -T

main()
{
    local _o

    local jail=

    while getopts ":j:" _o; do
        case "${_o}" in
            j)
                jail="${OPTARG}"
                ;;
            *)
                usage
                exit ${EX_USAGE}
                ;;
        esac
    done
    shift $((OPTIND-1))

    if [ -z "${jail}" ]; then
        usage
        exit ${EX_USAGE}
    fi

	trap '' ${IGNORED_SIGNALS}
	trap "ATEXIT_ERRLEVEL=\$?; cleanup; exit \${ATEXIT_ERRLEVEL}" EXIT
	trap "cleanup; exit 70" ${HANDLER_SIGNALS}

    appjail sysrc jail "${jail}" vm_list+="${jail}"
    appjail cmd jexec "${jail}" vm start "${jail}"
}

cleanup()
{
	# ignore
	trap '' ${HANDLER_SIGNALS} EXIT

	# restore
	trap - ${IGNORED_SIGNALS} ${HANDLER_SIGNALS} EXIT
}

usage()
{
    echo "usage: vm-start.sh -j <jail>"
}

main "$@"
