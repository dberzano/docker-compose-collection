Simple Flask app
================

All operations need to be run from the directory containing this `README.md` file.

The `flask_backend/app` directory will contain your Python application.

The `nginx_frontend/letsencrypt` directory will contain your Let's Encrypt certificate (TODO).

Rebuild all containers (runs only if necessary):

    docker-compose build

Run your application:

    docker-compose up
