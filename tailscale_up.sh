#!/bin/sh

if [ -z "$1" ]; then
  echo "Usage: $0 <exit-node-ip>"
  exit 1
fi

tailscale up
tailscale set --exit-node="$1"
