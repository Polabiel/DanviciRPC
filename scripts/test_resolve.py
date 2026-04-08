import logging
import traceback

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
