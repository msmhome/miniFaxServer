#!/bin/sh

# Start cloudflared service
cloudflared service install ${TUNNEL_TOKEN}

# Start python server
exec python server.py
