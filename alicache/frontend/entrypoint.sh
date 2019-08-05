#!/bin/sh
set -e

# Set some defaults
: ${FRONTEND_EXTERNAL_HTTPS_PORT=443}
: ${FRONTEND_EXTERNAL_HTTP_PORT=80}
export FRONTEND_EXTERNAL_HTTPS_PORT FRONTEND_EXTERNAL_HTTP_PORT

rm -vf /etc/nginx/conf.d/*

# Try to guess the FQDN from the certbot certificate
CERT_FQDN=`ls -1d /etc/letsencrypt/live/*/ | head -n1`
CERT_FQDN=`basename $CERT_FQDN`
if [ x$CERT_FQDN = x ]; then
    echo "Cannot guess FQDN from the certbot directory, abort"
    exit 1
fi
env CERT_FQDN=$CERT_FQDN \
    DOLLAR='$' \
    envsubst < /frontend.conf.template > /etc/nginx/conf.d/frontend.conf
echo "===[nginx configuration]==="
cat /etc/nginx/conf.d/frontend.conf
echo "===[end of nginx configuration]==="
while :; do
    echo "Will ask nginx to reload configuration and certificates in 6 hours"
    sleep 6h &
    wait $!
    echo "Asking nginx to reload"
    nginx -s reload
done &
exec nginx -g 'daemon off;'
