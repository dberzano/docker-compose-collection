#!/bin/bash
cd "$(dirname "$0")"
docker-compose run --rm -v "$PWD/revproxy:/revproxy:ro" --entrypoint 'pylint /revproxy/revproxy.py' revproxy
