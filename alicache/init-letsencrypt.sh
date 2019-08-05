#!/bin/bash -e

function log() {
    printf "\033[35m${1}\033[m\n" >&2
}

cd "$(dirname "$0")"

# Parse command-line args
EMAIL=
STAGING=1
DOMAINS=()
while [[ $# -gt 0 ]]; do
    case "$1" in
        --email)
            EMAIL=$2
            shift 2
        ;;
        --production)
            STAGING=
            shift
        ;;
        *)
            DOMAINS+=("$1")
            shift
        ;;
    esac
done

if [[ ! $EMAIL ]]; then
    log "Please specify an email address with --email"
    exit 1
fi
if [[ ${DOMAINS[0]} != *.* ]]; then
    log "Please specify the list of domains as arguments"
    exit 1
fi
for ((I=0; I<${#DOMAINS[@]}; I++)); do
    log "Domain: ${DOMAINS[$I]}"
done

DATA=$(dirname "$0")/data/certbot
if [[ -d "$DATA" ]]; then
    VDATE=$(date +%Y%m%d-%H%M%S)
    DATA=$(cd "$DATA"; pwd)
    mv "$DATA" "${DATA}.${VDATE}"
    log "Back up old data to ${DATA}.${VDATE}"
fi
mkdir -p "${DATA}/conf" "${DATA}/www"
DATA=$(cd "$DATA"; pwd)

log "Getting recommended SSL configuration"
BASE_CERTBOT_URL="https://raw.githubusercontent.com/certbot/certbot/master/"
curl -s $BASE_CERTBOT_URL/certbot-nginx/certbot_nginx/tls_configs/options-ssl-nginx.conf > "${DATA}/conf/options-ssl-nginx.conf"
curl -s $BASE_CERTBOT_URL/certbot/ssl-dhparams.pem > "${DATA}/conf/ssl-dhparams.pem"

log "Creating dummy certificate for ${DOMAINS[0]}"
mkdir -p "${DATA}/conf/live/${DOMAINS[0]}"
DOCK_PATH="/etc/letsencrypt/live/${DOMAINS[0]}"
docker-compose run --rm --entrypoint "\
  openssl req -x509 -nodes -newkey rsa:1024 -days 1 \
    -keyout '${DOCK_PATH}/privkey.pem' \
    -out '${DOCK_PATH}/fullchain.pem' \
    -subj '/CN=localhost'" certbot

log "Stopping all services"
docker-compose stop

log "Starting the revproxy and the nginx frontend only"
docker-compose up --force-recreate --no-deps -d revproxy
docker-compose up --force-recreate --no-deps -d frontend

log "Removing dummy certificate"
docker-compose run --rm --entrypoint "rm -rf /etc/letsencrypt/live/${DOMAINS[0]}" certbot

log "Requesting certificate${STAGING:+ (NOTE: we are in staging mode, override with --production)}"
docker-compose run --rm --entrypoint "\
  certbot certonly --webroot -w /var/www/certbot \
    ${STAGING:+--staging} \
    --email $EMAIL \
    $(for D in "${DOMAINS[@]}"; do echo -d $D; done) \
    --rsa-key-size 4096 \
    --agree-tos \
    --no-eff-email \
    --force-renewal" certbot

log "Stopping all services again"
docker-compose stop

log "All done"
