#!/bin/bash -e

# You need to run this script in order to obtain the certificates the first
# time. That time, domain verification is performed, therefore make sure you
# have ports 80 and 443 accessible from outside.

DRYRUN=
[[ $1 != --for-real ]] && DRYRUN="echo Dry run (use --for-real as first param to override): " || shift
$DRYRUN docker run -it --rm -v /docker/letsencrypt:/etc/letsencrypt:rw -p 80:80 -p 443:443 certbot/certbot certonly -d $(hostname -f) -d alicache.cern.ch --standalone "$@"
