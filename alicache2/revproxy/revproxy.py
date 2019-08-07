#!/usr/bin/env python

"""revproxy.py -- smart reverse proxy smoothing out backend errors.

   What is left TODO, what was already done
   - [X] handle 206
   - [ ] handle 206 when they are not supported by the backend!
   - [ ] serve cached content if file exists
   - [ ] automatically kill/restart the service from time to time
   - [ ] manage cache growth in a smart way
   - [ ] make requests wait if same file is already being downloaded
   - [ ] clean up all .tmp at start
   - [ ] handle requests in parallel, maybe with a thread pool?
"""

import os
import sys
import time
import errno
import requests
from requests.exceptions import RequestException
from klein import Klein
from twisted.web.static import File
from twisted.python import log

APP = Klein()

# Standard HTTP client retry parameters
HTTP_CONN_RETRIES = 10
HTTP_BACKOFF = 0.4
HTTP_TIMEOUT_SEC = 15

# Configurable by the user
CONF = {"REDIRECT_INVALID_TO": None,
        "BACKEND_PREFIX": None,
        "LOCAL_ROOT": None,
        "HOST": "0.0.0.0",
        "PORT": 8181}

def robust_get(url, dest):
    """Download `url` to local file `dest`. Returns `True` in case of success, `False` in case of
       a failure. The function is robust and will retry several times, with the appropriate backoff.
       In case of an interrupted download, it will attempt to resume it upon failure.
    """

    log.msg(f"Robust request: {url} -> {dest}")

    # Prepare the cache directory
    dest_dir = os.path.dirname(dest)
    try:
        os.makedirs(dest_dir)
    except OSError as exc:
        if not os.path.isdir(dest_dir) or exc.errno != errno.EEXIST:
            raise exc

    # File will be downloaded here first. Clean up stale, create dummy
    dest_tmp = dest + ".tmp"
    try:
        os.unlink(dest_tmp)
    except OSError:
        pass
    with open(dest_tmp, "wb"):
        pass

    # Download file in streaming mode
    size_final = -1
    for i in range(HTTP_CONN_RETRIES):
        if i > 0:
            pause_sec = HTTP_BACKOFF * (2 ** (i - 1))
            log.msg(f"Robust {url} -> {dest} failed, retrying in {pause_sec:.2f} s")
            time.sleep(pause_sec)
        try:
            # Determine the size of the file already downloaded
            size_ondisk = os.stat(dest_tmp).st_size
            log.msg(f"Robust {url} -> {dest}: attempt {i+1}/{HTTP_CONN_RETRIES}. "
                    "Already downloaded: {size_ondisk} bytes")
            if size_final != -1:
                range_header = {"Range": f"bytes={size_ondisk}-{size_final}"}
            else:
                range_header = {}
            resp = requests.get(url, stream=True, timeout=HTTP_TIMEOUT_SEC, headers=range_header)
            size_partial = int(resp.headers.get("Content-Length", "-1"))
            if size_final == -1:
                size_final = size_partial
            log.msg(f"Robust {url} -> {dest}: gave {resp.status_code}. Left: {size_partial} bytes. "
                    "Range: bytes={size_ondisk}-{size_final}")
            resp.raise_for_status()
            size_downloaded = 0
            with open(dest_tmp, "ab") as dest_fp:
                for chunk in resp.iter_content(chunk_size=32768):
                    if chunk:
                        dest_fp.write(chunk)
                        size_downloaded += len(chunk)
            if size_partial not in [size_downloaded, -1]:
                raise RequestException  # file was only partially downloaded
            os.rename(dest_tmp, dest)  # it should not cause any error
            log.msg(f"Robust {url} -> {dest}: OK")
            return True
        except RequestException as exc:
            if i == HTTP_CONN_RETRIES - 1:
                log.msg(f"Robust {url} -> {dest}: failed for good")
            try:
                os.unlink(dest_tmp)
            except OSError:
                pass

    return False  # if we are here there is an error


@APP.route("/", branch=True)
def process(req):
    """Process every URL.
    """

    uri = req.uri.decode("utf-8")
    uri_comp = [x for x in uri.split("/") if x]
    if not uri_comp or uri_comp[0] != "TARS":
        # Illegal URL: redirect to the ALICE institutional website
        req.setResponseCode(301)  # moved permanently
        req.setHeader("Location", CONF["REDIRECT_INVALID_TO"])
        return ""

    uri = "/".join(uri_comp)  # normalized
    local_path = os.path.join(CONF["LOCAL_ROOT"], uri)
    uri = "/" + uri
    backend_uri = CONF["BACKEND_PREFIX"] + uri

    if uri_comp[-1].endswith(".tar.gz"):
        # Probably a file. Cache it
        if robust_get(backend_uri, local_path):
            log.msg(f"Requested file downloaded to {local_path}")
        return File(CONF["LOCAL_ROOT"])

    # Probably a JSON. Do not cache it
    backend_uri = backend_uri + "/"
    local_path = os.path.join(local_path, "index.json")
    if robust_get(backend_uri, local_path):
        log.msg(f"Requested directory listing downloaded to {local_path}")
    req.setHeader("Content-Type", "application/json")
    with open(local_path) as json_fp:
        cont = json_fp.read()
    return cont

def main():
    """Entry point. Sets configuration variables from the environment, checks them, and starts the
       web server.
    """

    invalid = False

    for k in CONF:
        CONF[k] = os.environ.get(f"REVPROXY_{k}", CONF[k])
        if CONF[k] is None:
            print(f"ERROR in CONFiguration: REVPROXY_{k} must be set and it is missing")
            invalid = True
        else:
            print(f"Configuration: REVPROXY_{k} = {CONF[k]}")

    if invalid:
        print("ABORTING due to CONFiguration errors, check the environment")
        sys.exit(1)

    APP.run(host=CONF["HOST"], port=int(CONF["PORT"]))

main()
