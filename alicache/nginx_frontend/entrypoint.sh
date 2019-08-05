#!/bin/sh
set -e

# Set some defaults
: ${NGINX_EXTERNAL_HTTPS_PORT=443}
: ${NGINX_EXTERNAL_HTTP_PORT=80}
export NGINX_EXTERNAL_HTTPS_PORT NGINX_EXTERNAL_HTTP_PORT

env \
  CERT_FQDN=`ls -1 /etc/letsencrypt/live | head -n1` \
  DOLLAR='$' \
  envsubst < /etc/nginx/conf.d/my.conf.template > /etc/nginx/conf.d/my.conf
echo "=== nginx conf ==="
cat /etc/nginx/conf.d/my.conf
echo "=== end of nginx conf ==="
while true; do
  echo "Will ask nginx to reload in 8 hours"
  sleep 28800
  echo "Asking nginx to reload"
  nginx -s reload
done &
exec nginx -g 'daemon off;'
