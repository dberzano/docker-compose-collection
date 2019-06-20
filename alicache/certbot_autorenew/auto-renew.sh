#!/bin/sh -e
while true; do
  if openssl x509 -in /etc/letsencrypt/live/*/cert.pem -noout -checkend 2592000; then
    echo "`date` Certificate is still valid for the next 30 days"
    sleep 7200
  else
    echo "`date` We need to renew the certificate (expires before 30 days)"
    echo '**I WOULD RUN**' certbot renew --force-renewal && sleep 7200 || sleep 120
  fi
done
