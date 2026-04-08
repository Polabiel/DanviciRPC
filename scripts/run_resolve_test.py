import os
import sys
import importlib
import traceback

def main():
    path = os.environ.get("RESOLVE_SCRIPT_PATH") or r"C:\ProgramData\Blackmagic Design\DaVinci Resolve\Support\Developer\Scripting\Modules"
    print("Using RESOLVE_SCRIPT_PATH:", path)

    if os.path.isdir(path):
        sys.path.insert(0, path)
        print("Added to sys.path")
    else:
        print("Path does not exist:", path)

    try:
        mod = importlib.import_module("DaVinciResolveScript")
        print("Imported DaVinciResolveScript:", mod)
        resolve = mod.scriptapp("Resolve")
        print("scriptapp returned:", resolve)
        if resolve is None:
            print("Resolve API returned None — ensure Resolve is running and allows scripting")
            return 2
        pm = resolve.GetProjectManager()
        if pm is None:
            print("ProjectManager is None")
            return 3
        proj = pm.GetCurrentProject()
        if proj is None:
            print("No current project")
            return 4
        name = proj.GetName()
        print("Project name:", name)
        return 0
    except Exception:
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
