#!/bin/sh
set -e

# Set some defaults
: ${FRONTEND_EXTERNAL_HTTPS_PORT=443}
: ${FRONTEND_EXTERNAL_HTTP_PORT=80}
export FRONTEND_EXTERNAL_HTTPS_PORT FRONTEND_EXTERNAL_HTTP_PORT

rm -vf /etc/nginx/conf.d/*
env \
  CERT_FQDN=`ls -1 /letsencrypt/live | head -n1` \
  DOLLAR='$' \
  envsubst < /frontend.conf.template > /etc/nginx/conf.d/frontend.conf
echo "=== nginx conf ==="
cat /etc/nginx/conf.d/frontend.conf
echo "=== end of nginx conf ==="
while true; do
  echo "Will ask nginx to reload in 8 hours"
  sleep 28800
  echo "Asking nginx to reload"
  nginx -s reload
done &
exec nginx -g 'daemon off;'
