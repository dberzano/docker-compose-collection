#!/bin/sh
set -e
env \
  CERT_FQDN=`ls -1 /etc/letsencrypt/live | head -n1` \
  DOLLAR='$' \
  envsubst < /etc/nginx/conf.d/my.conf.template > /etc/nginx/conf.d/my.conf
echo "=== nginx conf ==="
cat /etc/nginx/conf.d/my.conf
echo "=== end of nginx conf ==="
exec nginx -g 'daemon off;'
