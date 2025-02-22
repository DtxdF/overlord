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

MD=
MOUNTED=false
JAIL_PATH=
LOCKFILE=

EX_USAGE=64
EX_IOERR=74

IGNORED_SIGNALS="SIGALRM SIGVTALRM SIGPROF SIGUSR1 SIGUSR2"
HANDLER_SIGNALS="SIGHUP SIGINT SIGQUIT SIGTERM SIGXCPU SIGXFSZ"

set -T

main()
{
    local _o

    local arch=
    local entrypoint=
    local imagesdir=
    local image=
    local jail=
    local tag=

    while getopts ":a:i:I:e:j:t:" _o; do
        case "${_o}" in
            a)
                arch="${OPTARG}"
                ;;
            i)
                imagesdir="${OPTARG}"
                ;;
            I):
                image="${OPTARG}"
                ;;
            e)
                entrypoint="${OPTARG}"
                ;;
            j)
                jail="${OPTARG}"
                ;;
            t)
                tag="${OPTARG}"
                ;;
            *)
                usage
                exit ${EX_USAGE}
                ;;
        esac
    done
    shift $((OPTIND-1))

    if [ -z "${arch}" -o -z "${image}" -o -z "${imagesdir}" -o -z "${entrypoint}" -o -z "${jail}" -o -z "${tag}" ]; then
        usage
        exit ${EX_USAGE}
    fi

	trap '' ${IGNORED_SIGNALS}
	trap "ATEXIT_ERRLEVEL=\$?; cleanup; exit \${ATEXIT_ERRLEVEL}" EXIT
	trap "cleanup; exit 70" ${HANDLER_SIGNALS}

    JAIL_PATH=`appjail cmd local "${jail}" realpath .` || exit $?

    MD=`mdconfig -at vnode -f "${JAIL_PATH}/vm/${jail}/disk0.img"` || exit $?

    local scheme
    scheme=`head -1 -- "${JAIL_PATH}/metadata/overlord.diskLayout.disk.scheme"` || exit $?

    gpart create -s "${scheme}" "/dev/${MD}"

    local partition_prefix="${JAIL_PATH}/metadata/overlord.diskLayout.disk.partitions"

    local mount_index= index=1

    while :; do
        local extra_flags=

        local alignment="${partition_prefix}.${index}.alignment"

        if [ -f "${alignment}" ]; then
            alignment=`head -1 -- "${alignment}"` || exit $?

            extra_flags="-a \"${alignment}\""
        fi

        local start="${partition_prefix}.${index}.start"

        if [ -f "${start}" ]; then
            start=`head -1 -- "${start}"` || exit $?

            extra_flags="-b \"${start}\""
        fi

        local size="${partition_prefix}.${index}.size"

        if [ -f "${size}" ]; then
            size=`head -1 -- "${size}"` || exit $?

            extra_flags="-s \"${size}\""
        fi

        local label="${partition_prefix}.${index}.label"

        if [ -f "${label}" ]; then
            label=`head -1 -- "${label}"` || exit $?

            extra_flags="-l \"${label}\""
        fi

        local type="${partition_prefix}.${index}.type"
        
        if [ ! -f "${type}" ]; then
            break
        fi

        type=`head -1 -- "${type}"` || exit $?

        sh -c "gpart add -t \"${type}\" ${extra_flags} -i ${index} /dev/${MD}" || exit $?

        local format_flags="${partition_prefix}.${index}.format.flags"

        if [ -f "${format_flags}" ]; then
            format_flags=`head -1 -- "${format_flags}"` || exit $?

            sh -c "newfs ${format_flags} /dev/${MD}p${index}" || exit $?

            if [ -z "${mount_index}" ]; then
                mount_index="${index}"
            fi
        fi

        index=$((index+1))
    done

    if [ -f "${JAIL_PATH}/metadata/overlord.diskLayout.disk.bootcode.bootcode" ]; then
        local bootcode
        bootcode=`head -1 -- "${JAIL_PATH}/metadata/overlord.diskLayout.disk.bootcode.bootcode"` || exit $?

        gpart bootcode -b "${bootcode}" "/dev/${MD}" || exit $?
    fi

    if [ -f "${JAIL_PATH}/metadata/overlord.diskLayout.disk.bootcode.partcode" ]; then
        local partcode
        partcode=`head -1 -- "${JAIL_PATH}/metadata/overlord.diskLayout.disk.bootcode.partcode"` || exit $?

        local index
        index=`head -1 -- "${JAIL_PATH}/metadata/overlord.diskLayout.disk.bootcode.index"` || exit $?

        gpart bootcode -p "${partcode}" -i "${index}" "/dev/${MD}" || exit $?
    fi

    if [ -n "${mount_index}" ]; then
        MOUNTED=true

        mount "/dev/${MD}p${mount_index}" "${JAIL_PATH}/mnt" || exit $?
    fi

    LOCKFILE=`mktemp -t overlord` || exit $?

    lockf -sk "${LOCKFILE}" \
        appjail image import -a "${arch}" -t "${tag}" -n "${image}" -- "${entrypoint}" || exit $?

    local image_file="${imagesdir}/${image}/${tag}-${arch}-image.appjail"

    tar -C "${JAIL_PATH}/mnt" --strip-components=2 -xf "${image_file}" ./jail/ || exit $?

    local fstab_prefix="${JAIL_PATH}/metadata/overlord.diskLayout.disk.fstab"

    local index=0

    while :; do
        local device="${fstab_prefix}.${index}.device"

        if [ ! -f "${device}" ]; then
            break
        fi

        device=`head -1 -- "${device}"` || exit $?

        local mountpoint="${fstab_prefix}.${index}.mountpoint"
        mountpoint=`head -1 -- "${mountpoint}"` || exit $?

        local type="${fstab_prefix}.${index}.type"
        type=`head -1 -- "${type}"` || exit $?

        local options="${fstab_prefix}.${index}.options"
        options=`head -1 -- "${options}"` || exit $?

        local dump="${fstab_prefix}.${index}.dump"
        dump=`head -1 -- "${dump}" || exit $?`

        local pass="${fstab_prefix}.${index}.pass"
        pass=`head -1 -- "${pass}"` || exit $?

        printf "%s\t%s\t%s\t%s\t%s\%s\n" "${device}" "${mountpoint}" "${type}" "${options}" "${dump}" "${pass}" >> "${JAIL_PATH}/mnt/etc/fstab" || exit $?

        index=$((index+1))
    done

    if [ -x "${JAIL_PATH}/run.sh" ]; then
        appjail cmd jexec "${jail}" /run.sh || exit $?
    fi

    if ${MOUNTED}; then
        umount -- "${JAIL_PATH}/mnt"

        MOUNTED=false
    fi

    if [ -n "${MD}" ]; then
        mdconfig -du "${MD}"

        MD=
    fi

    appjail sysrc jail "${jail}" vm_list+="${jail}"
    appjail cmd jexec "${jail}" vm start "${jail}"
}

cleanup()
{
	# ignore
	trap '' ${HANDLER_SIGNALS} EXIT

    if ${MOUNTED}; then
        umount -- "${JAIL_PATH}/mnt"
    fi

    if [ -n "${MD}" ]; then
        mdconfig -du "${MD}"
    fi

    if [ -n "${LOCKFILE}" ]; then
        rm -f -- "${LOCKFILE}"
    fi

	# restore
	trap - ${IGNORED_SIGNALS} ${HANDLER_SIGNALS} EXIT
}

usage()
{
    echo "usage: vm-install-from-appjail-image.sh -a <arch> -i <imagesdir> -I <image> -e <entrypoint> -j <jail> -t <tag>"
}

main "$@"
