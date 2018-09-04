FROM alpine:3.8
ENV VARNISH_VERSION='6.0.0-r1'
RUN apk add --update --no-cache varnish=$VARNISH_VERSION varnish-dev=$VARNISH_VERSION gettext wget && \
    wget --no-check-certificate https://github.com/Yelp/dumb-init/releases/download/v1.2.0/dumb-init_1.2.0_amd64 -O /usr/local/bin/dumb-init && \
    chmod +x /usr/local/bin/dumb-init && \
    apk del wget
COPY "entrypoint.sh" "/usr/local/bin/entrypoint.sh"
ENTRYPOINT [ "dumb-init" ]
CMD [ "/usr/local/bin/entrypoint.sh" ]
