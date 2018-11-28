#!/bin/sh
set -e
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
