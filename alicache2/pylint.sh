#!/bin/bash
cd "$(dirname "$0")"
docker run -it --rm -v "$PWD/revproxy:/revproxy:ro" alicache2_revproxy pylint /revproxy/revproxy.py
