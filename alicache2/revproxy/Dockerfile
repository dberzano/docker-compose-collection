FROM python
RUN curl -L --output /usr/local/bin/certbot-auto https://dl.eff.org/certbot-auto && \
    chmod +x /usr/local/bin/certbot-auto && \
    /usr/local/bin/certbot-auto --non-interactive --install-only && \
    rm -rf /var/lib/apt/lists/*
RUN pip install twisted klein requests pylint && \
    rm -rf /root/.cache
