import sys
import os
import logging
import traceback

# Ensure project root is on sys.path so resolve.* imports work regardless of
# the working directory from which this script is invoked.
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

logging.basicConfig(level=logging.INFO)

print("TEST: about to import ResolveClient")
try:
    from resolve.resolver import ResolveClient
    print("TEST: imported ResolveClient")
except Exception:
    traceback.print_exc()
    raise

print("TEST: about to instantiate ResolveClient")
try:
    rc = ResolveClient()
    print("TEST: instantiated ResolveClient, available=", rc.available)
except Exception:
    traceback.print_exc()
    raise
