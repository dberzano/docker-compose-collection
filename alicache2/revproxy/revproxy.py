#!/usr/bin/env python

"""revproxy.py -- smart reverse proxy smoothing out backend errors.

   What is left TODO, what was already done
   - [X] handle 206
   - [ ] handle 206 when they are not supported by the backend!
   - [X] serve cached content if file exists
   - [ ] automatically kill/restart the service from time to time
   - [ ] manage cache growth in a smart way
   - [X] make requests wait if same file is already being downloaded
   - [X] clean up all .tmp at start
   - [X] handle caching in a non-blocking way (async/await)
   - [ ] remove return bool from `robust_get` (it is not used in any case)
"""

import os
import sys
import time
import glob
import errno
import requests
from requests.exceptions import RequestException
from klein import Klein
from twisted.python import log
from twisted.web.static import File
from twisted.internet import threads, reactor
from twisted.internet.task import deferLater, LoopingCall
from twisted.internet.defer import ensureDeferred

APP = Klein()

# Configurable by the user
CONF = {"REDIRECT_INVALID_TO": None,
        "BACKEND_PREFIX": None,
        "LOCAL_ROOT": None,
        "HTTP_CONN_RETRIES": 20,
        "HTTP_TIMEOUT_SEC": 15,
        "CACHE_INDEX_DURATION": 60,
        "CACHE_FILE_DURATION": 1209600,
        "HOST": "0.0.0.0",
        "PORT": 8181}

async def robust_get(url, dest):
    """Download `url` to local file `dest`. Returns when done, even on failure. No return value.
       The function is robust and will retry several times, with the appropriate backoff. In case of
       an interrupted download, it will attempt to resume it upon failure.
    """

    # File was cached already
    if os.path.isfile(dest):
        log.msg(f"{url} -> {dest}: cache hit")
        return

    # File will be downloaded to `.tmp` first. This part is deliberately blocking
    dest_tmp = dest + ".tmp"
    if os.path.isfile(dest_tmp):
        log.msg(f"{url} -> {dest}: being cached: waiting")
        while os.path.isfile(dest_tmp):
            await ensureDeferred(deferLater(reactor, 1, lambda: None))  # non-blocking sleep
        return  # note: disappearance of `.tmp` may also mean failure (it's handled outside)

    # Placeholder is not there: we create it (safe, because it's blocking so far)
    dest_dir = os.path.dirname(dest)
    try:
        os.makedirs(dest_dir)
    except OSError as exc:
        if not os.path.isdir(dest_dir) or exc.errno != errno.EEXIST:
            raise exc
    with open(dest_tmp, "wb"):
        pass

    # Non-blocking part: run in a thread
    await ensureDeferred(threads.deferToThread(robust_get_sync, url, dest, dest_tmp))

def robust_get_sync(url, dest, dest_tmp):
    """Synchronous part of `robust_get()`. Takes three arguments: the `url` to download, the `dest`,
       and the `dest_tmp`. File will be downloaded to `dest_tmp` first, and then it will be moved
       with an atomic operation to `dest` when done. In case of errors, it will be deleted instead.
       Returns `True` on success, `False` on unrecoverable download failure.
    """

    # Download file in streaming mode
    size_final = -1
    for i in range(CONF["HTTP_CONN_RETRIES"]):
        if i > 0:
            pause_sec = 0.4 * (1.4 ** (i - 1))
            log.msg(f"{url} -> {dest} failed: retrying in {pause_sec:.2f} s")
            time.sleep(pause_sec)
        try:
            # Determine the size of the file already downloaded
            size_ondisk = os.stat(dest_tmp).st_size
            log.msg(f"{url} -> {dest}: attempt {i+1}/{CONF['HTTP_CONN_RETRIES']}: "
                    f"{size_ondisk} bytes already there")
            if size_final != -1:
                range_header = {"Range": f"bytes={size_ondisk}-{size_final}"}
            else:
                range_header = {}
            resp = requests.get(url, stream=True,
                                timeout=CONF["HTTP_TIMEOUT_SEC"], headers=range_header)
            size_partial = int(resp.headers.get("Content-Length", "-1"))
            if size_final == -1:
                size_final = size_partial
            log.msg(f"{url} -> {dest}: had {resp.status_code}, {size_partial} bytes left. "
                    f"Range: bytes={size_ondisk}-{size_final}")
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
            log.msg(f"{url} -> {dest}: OK")
            return True
        except RequestException as exc:
            try:
                status_code = exc.response.status_code
            except AttributeError:
                status_code = -1
            if status_code == 404 or i == CONF["HTTP_CONN_RETRIES"] - 1:
                log.msg(f"{url} -> {dest}: giving up (last status code: {status_code})")
                try:
                    os.unlink(dest_tmp)
                except OSError:
                    pass
                return False

    return False  # if we are here there is an error

def atouch(file_name):
    """Update file access time.
    """
    try:
        os.utime(file_name, (time.time(), os.stat(file_name).st_mtime))
    except OSError:
        pass

@APP.route("/", branch=True)
async def process(req):
    """Process every URL.
    """

    orig_uri = req.uri.decode("utf-8")
    uri_comp = [x for x in orig_uri.split("/") if x]
    if not uri_comp or uri_comp[0] != "TARS":
        # Illegal URL: redirect to a fallback site
        req.setResponseCode(301)  # moved permanently
        req.setHeader("Location", CONF["REDIRECT_INVALID_TO"])
        return ""

    uri = "/".join(uri_comp)  # normalized
    local_path = os.path.join(CONF["LOCAL_ROOT"], uri)
    uri = "/" + uri
    if uri != orig_uri:
        # Return a permanent redirect to the normalized URL
        log.msg(f"URI was normalized, {orig_uri} != {uri}: redirecting")
        req.setResponseCode(301)
        req.setHeader("Location", uri)
        return ""  # empty body

    backend_uri = CONF["BACKEND_PREFIX"] + uri

    if "." in uri_comp[-1]:
        # Heuristics: has an extension ==> treat as file
        await robust_get(backend_uri, local_path)
        atouch(local_path)
        return File(CONF["LOCAL_ROOT"])

    # No extension -> treat as directory index in JSON
    backend_uri = backend_uri + "/"
    local_path = os.path.join(local_path, "index.json")
    req.setHeader("Content-Type", "application/json")
    await robust_get(backend_uri, local_path)
    try:
        with open(local_path) as json_fp:
            return json_fp.read()
    except OSError:
        req.setResponseCode(404)
        return "{}"

def clean_cache():
    """Scan cache for old files and remove them. What is removed:
       * Directory indices (`.json`) modified more than one minute ago
       * All other files accessed more than 2 weeks ago
       Please note the difference between "modified" and "accessed"!
    """

    now = time.time()
    size_saved = 0
    size_used = 0

    for file_name in glob.iglob(os.path.join(CONF["LOCAL_ROOT"], "**"), recursive=True):
        if os.path.isdir(file_name) or file_name.endswith(".tmp"):
            continue
        try:
            sta = os.stat(file_name)
            a_ago = int(now - sta.st_atime)
            m_ago = int(now - sta.st_mtime)
            remove = False
            if os.path.basename(file_name) == "index.json":
                if m_ago > CONF["CACHE_INDEX_DURATION"]:
                    remove = True
                    log.msg(f"{file_name} modified {m_ago} s ago: erased {sta.st_size} bytes")
            elif a_ago > CONF["CACHE_FILE_DURATION"]:
                remove = True
                log.msg(f"{file_name} accessed {a_ago} s ago: erased {sta.st_size} bytes")
            if remove:
                os.unlink(file_name)
                size_saved += sta.st_size
            else:
                size_used += sta.st_size
        except OSError:
            pass

    log.msg(f"Cache: {size_used} bytes used, cleanup freed {size_saved} bytes")

def sanitize_cache():
    """Cleanup cache directory from spurious `.tmp` files.
    """
    for file_name in glob.iglob(os.path.join(CONF["LOCAL_ROOT"], "**/*.tmp"), recursive=True):
        print(f"Removing spurious {file_name}")
        try:
            os.unlink(file_name)
        except OSError:
            pass

def main():
    """Entry point. Sets configuration variables from the environment, checks them, and starts the
       web server.
    """

    invalid = False
    conf_keys_to_int = ["HTTP_CONN_RETRIES", "HTTP_TIMEOUT_SEC",
                        "CACHE_INDEX_DURATION", "CACHE_FILE_DURATION"]

    for k in CONF:
        CONF[k] = os.environ.get(f"REVPROXY_{k}", CONF[k])
        print(f"Configuration: REVPROXY_{k} = {CONF[k]}")
        if CONF[k] is None:
            print(f"ERROR in configuration: REVPROXY_{k} must be set and it is missing")
            invalid = True
        elif k in conf_keys_to_int:
            try:
                CONF[k] = int(CONF[k])
            except ValueError:
                print(f"ERROR in configuration: REVPROXY_{k} must be an integer")
                invalid = True

    if invalid:
        print("ABORTING due to configuration errors, check the environment")
        sys.exit(1)

    sanitize_cache()

    reactor.callLater(1, LoopingCall(clean_cache).start, 60)  # pylint: disable=no-member
    APP.run(host=CONF["HOST"], port=int(CONF["PORT"]))

if __name__ == "__main__":
    main()
