#!/usr/bin/env python

import os
import sys
import requests

URL = "http://localhost/TARS/slc7_x86-64/GEANT4/GEANT4-v10.4.2-4.slc7_x86-64.tar.gz"
#URL = "http://localhost/TARS/slc7_x86-64/store/ec/ecd0e55c1aac610a658e461cf525e72607c5897f/autotools-v1.5.0-8.slc7_x86-64.tar.gz"
#URL = "http://localhost:8181/TARS/slc7_x86-64/store/ec/ecd0e55c1aac610a658e461cf525e72607c5897f/autotools-v1.5.0-8.slc7_x86-64.tar.gz"
#URL = "https://localhost/static/TARS/slc7_x86-64/store/ec/ecd0e55c1aac610a658e461cf525e72607c5897f/autotools-v1.5.0-8.slc7_x86-64.tar.gz"
#URL = "http://ali-ci.cern.ch/TARS/slc7_x86-64/store/ec/ecd0e55c1aac610a658e461cf525e72607c5897f/autotools-v1.5.0-8.slc7_x86-64.tar.gz"
DEST = "destination.tar.gz"

resp = requests.get(URL, stream=True, verify=False, headers={'Accept-Encoding': 'identity'})
try:
    os.unlink(DEST)
except:
    pass
resp.raise_for_status()
for k in resp.headers:
    print("[HEADER] %s: %s" % (k, resp.headers[k]))
with open(DEST, "wb") as dest_fp:
  for chunk in resp.iter_content(chunk_size=32768):
    if chunk:
      dest_fp.write(chunk)

print("Download completed to %s: %d B" % (DEST, os.stat(DEST).st_size))
