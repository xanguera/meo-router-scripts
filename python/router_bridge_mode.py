"""Python equivalent of router-bridge-mode.sh (show|enable|disable)."""
import sys

from meo_gr241ag import run

if __name__ == "__main__":
    action = sys.argv[1] if len(sys.argv) > 1 else ""
    mapped = {"show": "status", "enable": "on", "disable": "off"}.get(action)
    if not mapped:
        sys.exit("Usage: py router_bridge_mode.py <show|enable|disable> [--apply] [--host IP] [--user NAME]")
    sys.exit(run(["bridge", mapped, *sys.argv[2:]]))
