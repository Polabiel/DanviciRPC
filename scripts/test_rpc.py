import sys
import os
import traceback

# Ensure project root is on sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

print("TEST_RPC: about to import RPCClient")
try:
    from discord.rpc_client import RPCClient
    print("TEST_RPC: imported RPCClient")
except Exception:
    traceback.print_exc()
    raise

print("TEST_RPC: about to instantiate RPCClient")
try:
    rpc = RPCClient()
    print("TEST_RPC: instantiated RPCClient, connected=", rpc.connected)
except Exception:
    traceback.print_exc()
    raise
