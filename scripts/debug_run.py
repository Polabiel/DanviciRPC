import runpy
import sys
import os
import traceback

# Ensure project root is on sys.path so top-level imports (e.g. `config`) resolve
_project_root = os.path.dirname(os.path.dirname(__file__))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

try:
    runpy.run_path("main.py", run_name="__main__")
except SystemExit as e:
    print("SYSTEMEXIT CODE:", e.code)
    sys.exit(e.code if e.code is not None else 0)
except Exception:
    traceback.print_exc()
    sys.exit(1)
