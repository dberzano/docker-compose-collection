Docker Compose
==============

This is a repository of services based on Docker Compose. Every directory
contains a `docker-compose.yml` file: `cd` there before running commands.

Start:

    docker-compose up --build [--detach]

where `--detach` runs services in background.

Stop:

    docker-compose down --remove-orphans

Prune unused stuff:

    docker system prune -f
