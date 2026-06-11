#!/bin/bash

PUID=${PUID:-1000}
PGID=${PGID:-1000}
OPENCODE_SERVER_PASSWORD=${OPENCODE_SERVER_PASSWORD:-}

if [ "$(id -g appuser)" -ne "$PGID" ]; then
    groupmod -o -g "$PGID" appuser
fi

if [ "$(id -u appuser)" -ne "$PUID" ]; then
    usermod -o -u "$PUID" appuser
fi

chown -R appuser:appuser /home/appuser/.local/share/opencode
chown -R appuser:appuser /home/appuser/.config/opencode
chown -R appuser:appuser /home/appuser/project

# Allow overriding via environment variables
PROXY_PORT=${OPENCODE_PROXY_PORT:-10000}
SERVER_PORT=${OPENCODE_SERVER_PORT:-10001}

if [[ "$1" == "opencode" && "$2" == "serve" ]]; then
    echo "Initializing opencode2api (Server + Python Proxy)"
    
    echo "Starting OpenCode Server on internal port ${SERVER_PORT}..."
    gosu appuser opencode serve --hostname 0.0.0.0 --port ${SERVER_PORT} &
    SERVER_PID=$!
    
    echo "Waiting for OpenCode Server to become available..."
    MAX_RETRIES=30
    COUNT=0
    while ! curl -s http://127.0.0.1:${SERVER_PORT}/health > /dev/null; do
        if [ $COUNT -ge $MAX_RETRIES ]; then
            echo "Timeout waiting for OpenCode Server."
            kill $SERVER_PID 2>/dev/null
            exit 1
        fi
        
        if ! kill -0 $SERVER_PID 2>/dev/null; then
            echo "OpenCode Server process died unexpectedly."
            exit 1
        fi
        
        sleep 1
        COUNT=$((COUNT+1))
    done
    echo "OpenCode Server is up!"

    echo "Starting Python Proxy on port ${PROXY_PORT}..."
    exec gosu appuser python3 -m uvicorn python_src.main:app --host 0.0.0.0 --port ${PROXY_PORT}
else
    exec gosu appuser "$@"
fi