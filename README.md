Collection of Docker compose manifests
======================================

This is a repository of services based on Docker Compose. Every directory contains a
`docker-compose.yml` file. The `docker-compose` command must be run in the directory containing the
aforementioned manifest.

Generic instructions
--------------------
Start (rebuild the containers, and start in background):

    docker-compose up --build --detach

Check status:

    docker-compose ps
    docker-compose logs

Stop:

    docker-compose down --remove-orphans

Remove stale resources from Docker (dangling images, unused networks...):

    docker system prune -f
