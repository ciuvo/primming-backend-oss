#!/bin/bash
# https://github.com/capripot/wait-for/blob/master/wait-for
WAITFOR_TIMEOUT=150
WAITFOR_QUIET=0
WAITFOR_RETRY_DELAY=0.1

echoerr() {
  if [ "$WAITFOR_QUIET" -ne 1 ]; then printf "%s\n" "$*" 1>&2; fi
}

usage() {
  exitcode="$1"
  cat << USAGE >&2
Usage:
  $cmdname host:port|url [-t timeout] [-- command args]
  -q | --quiet                        Do not output any status messages
  -t TIMEOUT | --timeout=timeout      Timeout in seconds, zero for no timeout
  -- COMMAND ARGS                     Execute command with args after the test finishes
USAGE
  exit "$exitcode"
}

wait_for() {
  for i in `seq $WAITFOR_TIMEOUT` ; do
    nc -z "$WAITFOR_HOST" "$WAITFOR_PORT" > /dev/null 2>&1

    result=$?
    if [ $result -eq 0 ] ; then
      if [ $# -gt 0 ] ; then
        exec "$@"
      fi
      exit 0
    fi
    sleep $WAITFOR_RETRY_DELAY
  done
  echo "Operation timed out" >&2
  exit 1
}

wait_for_http() {
  for i in `seq $WAITFOR_TIMEOUT` ; do
    wget --timeout=1 -q "$WAITFOR_URL" -O /dev/null > /dev/null 2>&1

    result=$?
    if [ $result -eq 0 ] ; then
      if [ $# -gt 0 ] ; then
        exec "$@"
      fi
      exit 0
    fi
    sleep $WAITFOR_RETRY_DELAY
  done
  echo "Operation timed out" >&2
  exit 1
}

while [ $# -gt 0 ]
do
  case "$1" in
    http*)
    WAITFOR_URL=$1
    shift 1
    ;;
    *:* )
    WAITFOR_HOST=$(printf "%s\n" "$1"| cut -d : -f 1)
    WAITFOR_PORT=$(printf "%s\n" "$1"| cut -d : -f 2)
    shift 1
    ;;
    -q | --quiet)
    WAITFOR_QUIET=1
    shift 1
    ;;
    -t)
    WAITFOR_TIMEOUT="$2"
    if [ "$WAITFOR_TIMEOUT" = "" ]; then break; fi
    shift 2
    ;;
    --timeout=*)
    WAITFOR_TIMEOUT="${1#*=}"
    shift 1
    ;;
    --)
    shift
    break
    ;;
    --help)
    usage 0
    ;;
    *)
    echoerr "Unknown argument: $1"
    usage 1
    ;;
  esac
done

if [ "$WAITFOR_HOST" = "" -o "$WAITFOR_PORT" = "" ] && [ "$WAITFOR_URL" = "" ]; then
  echoerr "Error: you need to provide a host and port OR an URL to test."
  usage 2
fi

if [ "$WAITFOR_URL" != "" ]; then
  wait_for_http "$@"
else
  wait_for "$@"
fi
