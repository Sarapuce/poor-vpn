#!/bin/sh

if [ -z "$1" ]; then
  echo "Usage: $0 <exit-node-ip>"
  exit 1
fi

echo test

tailscale up

timeout=30
while [ $timeout -gt 0 ]; do
  if tailscale status | grep "$1" | grep -q "offers exit node"; then
    echo found
    break
  fi
  sleep 1
  timeout=$((timeout - 1))
done

tailscale set --exit-node="$1"
