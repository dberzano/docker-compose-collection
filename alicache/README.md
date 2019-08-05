alicache
========
This Docker compose configuration is a set of three services aiming to cache the large ALICE
precompiled tarballs in order to offload the build cluster services.

Calls to the backend are smart: in case of a connection interrupted, the caching proxy can resume
the download from where it left. This operation is completely transparent to the client, which will
only start to receive the file once it is fully retrieved.

The custom caching proxy runs using the [Klein web framework](https://github.com/twisted/klein),
based on [Twisted](https://github.com/twisted/twisted). It runs using Python 3 only and makes
extensive use of coroutines and non-blocking paradigms.

First time only: HTTPS certificate
----------------------------------
The service needs to be run on a machine with `docker-compose` available, and with ports 80 and 443
open and accessible from anywhere. This is required by [Let's Encrypt](https://letsencrypt.org/) for
requesting a certificate.

**The first time we run the service** we need to retrieve a certificate. Only that time, it is
required to run the `init-letsencrypt.sh` script. Run it like this:

    ./init-letsencrypt.sh alicache02.cern.ch alicache.cern.ch --email notify_this_address_on_expiry@cern.ch --production

Note that several domain names were specified. This is because the service may run on a certain node
(in our example, `alicache02.cern.ch`) and have a DNS alias (`alicache.cern.ch`). You can specify as
many aliases as you want, but they must be verifiable by Let's Encrypt.

The email address is important because this address will receive notifications in case of problems
and certificate expiration. Note that this configuration will renew the certificate automatically.

The `--production` switch obtains a real certificate using the production Let's Encrypt servers.
Those servers are rate-limited. In case you want to perform repeated testing, please remove the
`--production` switch. The staging servers will be used, and the certificate obtained will not be
recognized by your clients, but you won't be rate-limited.

Operate the services
--------------------
You must be in the directory containing the `docker-compose.yml` file to run the commands.

Start with:

    docker-compose up --build --detach

Services will start in the background. Check with:

    docker-compose ps
    docker-compose logs

Stop with:

    docker-compose down --remove-orphans

By default, images referred in the compose manifest and in the linked `Dockerfile` files are not
pulled if already cached. In order to make sure you are running the latest stable versions of the
associated services (in this case, nginx and certbot), periodically run:

    docker-compose pull

You may want to restart the services in case of an update.

Shell scripts
-------------
* `pylint.sh`: check `revproxy.py` with [pylint](https://www.pylint.org/) using the same container
  where it will run
* `init-letsencrypt.sh`: get a Let's Encrypt certificate for the first time, using a consistent
  environment as provided by containers
* `test-download.sh`: play with this script to test if the service works (you will need to edit it a
  lot, this is not meant for production)

Credits
-------
Credits for the whole `certbot` setup go to
[wmnnd/nginx-certbot](https://github.com/wmnnd/nginx-certbot/) and [this brilliant Medium
article](https://medium.com/@pentacent/nginx-and-lets-encrypt-with-docker-in-less-than-5-minutes-b4b8a60d3a71).
