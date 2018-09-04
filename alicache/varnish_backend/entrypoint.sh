#!/bin/sh
set -e

# Remove old cache file (cache is not persistent anyways)
rm -f "$VARNISH_STORAGE_FILE"

# Get volume of storage file, then available space
VOLUME=`dirname "$VARNISH_STORAGE_FILE"`
FREE=`df -P -B1 "$VOLUME" | awk 'NR==2 {print $4}'`
let FREE=$FREE-100000000

# Start Varnish with the given storage
set -x
exec varnishd -F -f /etc/varnish/default.vcl -a 0.0.0.0:80 -s file,${VARNISH_STORAGE_FILE},$FREE "$@"
