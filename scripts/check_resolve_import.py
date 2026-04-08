import importlib
import traceback

print('CHECK: attempting to import DaVinciResolveScript')
try:
    m = importlib.import_module('DaVinciResolveScript')
    print('CHECK: imported', m)
except Exception:
    traceback.print_exc()
    raise
