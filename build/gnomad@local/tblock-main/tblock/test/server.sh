#!/bin/sh

set -e

_start_server()
{
  if ! [ -f "$(dirname "$0")/srv/pid" ]; then
    echo "starting production server..."
    /usr/bin/python3 -m http.server \
      --directory="$(dirname "$0")/srv" \
      --bind=127.0.0.1 \
      --cgi 12345 \
      &>/dev/null &
    echo "$!" > "$(dirname "$0")/srv/pid"
    echo "production server started."
  else
    echo "production server already started; nothing to do."
  fi
}

_stop_server()
{
  if [ -f "$(dirname "$0")/srv/pid" ]; then
    echo "stopping production server..."
    kill "$(cat "$(dirname "$0")/srv/pid")"
    rm -f "$(dirname "$0")/srv/pid"
    echo "production server stopped."
  else
    echo "production server already stopped; nothing to do."
  fi
}

case "$1" in
  "--start")
    _start_server
  ;;
  "--stop")
    _stop_server
  ;;
  "--restart")
    _stop_server && _start_server
  ;;
  *)
    echo "usage: $0 [--start|--stop|--restart]"
esac
