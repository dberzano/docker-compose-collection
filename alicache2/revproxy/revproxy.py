#!/usr/bin/env python

# What is left TODO, what was already done
# - [X] handle 206
# - [ ] handle 206 when they are not supported by the backend!
# - [ ] serve cached content if file exists
# - [ ] automatically kill/restart the service from time to time
# - [ ] manage cache growth in a smart way
# - [ ] make requests wait if same file is already being downloaded
# - [ ] clean up all .tmp at start
# - [ ] handle requests in parallel, maybe with a thread pool?

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
HTTP_CONN_RETRIES = 10
HTTP_BACKOFF = 0.4
HTTP_TIMEOUT_SEC = 15

def robust_get(url, dest):
    log.msg(f"Robust request: {url} -> {dest}")

    # Prepare the cache directory
    destDir = os.path.dirname(dest)
    try:
        os.makedirs(destDir)
    except OSError as exc:
        if not os.path.isdir(destDir) or exc.errno != errno.EEXIST:
            raise exc

    # File will be downloaded here first. Clean up stale, create dummy
    destTmp = dest + ".tmp"
    try:
        os.unlink(destTmp)
    except:
        pass
    with open(destTmp, "wb"):
        pass

    # Download file in streaming mode
    szFinal = -1
    for i in range(HTTP_CONN_RETRIES):
        if i > 0:
            pauseSec = HTTP_BACKOFF * (2 ** (i - 1))
            log.msg(f"Robust {url} -> {dest} failed, retrying in {pauseSec:.2f} s")
            time.sleep(pauseSec)
        try:
            # Determine the size of the file already downloaded
            szOnDisk = os.stat(destTmp).st_size
            log.msg(f"Robust {url} -> {dest}: attempt {i+1}/{HTTP_CONN_RETRIES}. "
                    "Already downloaded: {szOnDisk} bytes")
            if szFinal != -1:
                rangeHeader = {"Range": f"bytes={szOnDisk}-{szFinal}"}
            else:
                rangeHeader = {}
            resp = requests.get(url, stream=True, timeout=HTTP_TIMEOUT_SEC, headers=rangeHeader)
            szPartial = int(resp.headers.get("Content-Length", "-1"))
            if szFinal == -1:
                szFinal = szPartial
            log.msg(f"Robust {url} -> {dest}: gave {resp.status_code}. Left: {szPartial} bytes. "
                    "Range: bytes={szOnDisk}-{szFinal}")
            resp.raise_for_status()
            szDownloaded = 0
            with open(destTmp, "ab") as destFp:
                for chunk in resp.iter_content(chunk_size=32768):
                    if chunk:
                        destFp.write(chunk)
                        szDownloaded += len(chunk)
            if szPartial not in [szDownloaded, -1]:
                raise RequestException  # file was only partially downloaded
            os.rename(destTmp, dest)  # it should not cause any error
            log.msg(f"Robust {url} -> {dest}: OK")
            return True
        except RequestException as exc:
            if i == HTTP_CONN_RETRIES - 1:
                log.msg(f"Robust {url} -> {dest}: failed for good")
            try:
                unlink(destTmp)
            except:
                pass

    return False  # if we are here there is an error


@APP.route("/", branch=True)
def process(req):
    uri = req.uri.decode("utf-8")
    uriComp = [x for x in uri.split("/") if x]
    if len(uriComp) == 0 or uriComp[0] != "TARS":
        # Illegal URL: redirect to the ALICE institutional website
        req.setResponseCode(301)  # moved permanently
        req.setHeader("Location", REDIRECT_INVALID_TO)
        return ""

    uri = "/".join(uriComp)  # normalized
    localPath = os.path.join(LOCAL_ROOT, uri)
    uri = "/" + uri
    backendUri = BACKEND + uri

    if uriComp[-1].endswith(".tar.gz"):
        # Probably a file. Cache it
        if robust_get(backendUri, localPath):
            log.msg(f"Requested file downloaded to {localPath}")
        return File(LOCAL_ROOT)
    else:
        # Probably a JSON. Do not cache it
        backendUri = backendUri + "/"
        localPath = os.path.join(localPath, "index.json")
        if robust_get(backendUri, localPath):
            log.msg(f"Requested directory listing downloaded to {localPath}")
        req.setHeader("Content-Type", "application/json")
        with open(localPath) as jsonFp:
            cont = jsonFp.read()
        return cont

def main():

    conf = {"REDIRECT_INVALID_TO": None,
            "BACKEND_PREFIX": None,
            "LOCAL_ROOT": None,
            "HOST": "0.0.0.0",
            "PORT": 8181}
    invalid = False

    for k in conf:
        conf[k] = os.environ.get(f"REVPROXY_{k}", conf[k])
        if conf[k] is None:
            print(f"ERROR in configuration: REVPROXY_{k} must be set and it is missing")
            invalid = True
        else:
            print(f"Configuration: REVPROXY_{k} = {conf[k]}")

    if invalid:
        print("ABORTING due to configuration errors, check the environment")
        sys.exit(1)

    APP.run(host=conf["HOST"], port=int(conf["PORT"]))

main()
