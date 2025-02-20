#!/bin/sh

# Signals
SIGNALS_IGNORED="SIGALRM SIGVTALRM SIGPROF SIGUSR1 SIGUSR2"
SIGNALS_HANDLED="SIGHUP SIGINT SIGQUIT SIGTERM SIGXCPU SIGXFSZ"

# Globals
PID=

# sysexits(3)
EX_OK=0
EX_USAGE=64

set -T

main()
{
    if [ $# -lt 1 ]; then
        usage
        exit ${EX_USAGE}
    fi

    handle_signals

    "$@" &

    PID=$!

    wait

    sleep 1

    kill_proc_tree "${PID}"

    return ${EX_OK}
}

handle_signals()
{
    trap '' ${SIGNALS_IGNORED}
    trap "_ERRLEVEL=\$?; cleanup; exit \${_ERRLEVEL}" EXIT
    trap "cleanup; exit 70" ${SIGNALS_HANDLED}
}

ignore_all_signals()
{
    trap '' ${SIGNALS_HANDLED} EXIT
}

restore_signals()
{
    trap - ${SIGNALS_HANDLED} ${SIGNALS_IGNORED} EXIT
}

cleanup()
{
    ignore_all_signals

    if [ -n "${PID}" ]; then
        kill_proc_tree "${PID}"
    fi

    restore_signals
}

random_number()
{
    if [ $# -lt 2 ]; then
        echo "usage: random_number <begin> <end>"
        exit ${EX_USAGE}
    fi

    local begin
    begin="$1"

    local end
    end="$2"

    jot -r 1 "${begin}" "${end}"
}

kill_proc_tree()
{
    if [ $# -lt 1 ]; then
        echo "usage: kill_proc_tree <pid>"
        exit ${EX_USAGE}
    fi

    local pid
    pid="$1"

    local tokill
    for tokill in `get_proc_tree "${pid}" | tail -r`; do
        safest_kill "${tokill}"
    done

    safest_kill "${pid}"
}

safest_kill()
{   
    if [ $# -lt 1 ]; then
        echo "usage: safest_kill <pid>"
        exit ${EX_USAGE}
    fi

    local pid
    pid=$1

    local retry=1
    local total=3

    while [ ${retry} -le ${total} ]; do
        kill ${pid} > /dev/null 2>&1

        if ! check_proc ${pid}; then
            return 0
        fi

        sleep `random_number 1 3`.`random_number 3 9`

        retry=$((retry+1))
    done

    if check_proc ${pid}; then
        kill -KILL ${pid} > /dev/null 2>&1
    fi
}

get_proc_tree()
{
    if [ $# -lt 1 ]; then
        echo "usage: get_proc_tree <ppid>"
        exit ${EX_USAGE}
    fi

    local ppid
    ppid=$1

    local pid
    for pid in `pgrep -P ${ppid}`; do
        echo ${pid}

        get_proc_tree ${pid}
    done
}

check_proc()
{
    if [ $# -lt 1 ]; then
        echo "usage: check_proc <pid>"
        exit ${EX_USAGE}
    fi

    local pid
    pid=$1

    if [ `ps -o pid -p ${pid} | wc -l` -eq 2 ]; then
        return 0
    else
        return 1
    fi
}

usage()
{
    echo "usage: safe-exc.sh <cmd> [<args> ...]"
}

main "$@"
