#!/bin/sh
set -e

if [ -z "$TUNNEL_TOKEN" ]; then
  echo "TUNNEL_TOKEN is not set"
  exit 1
fi

# Start cloudflared service
cloudflared service install ${TUNNEL_TOKEN}

# Start python server
exec python server.py
