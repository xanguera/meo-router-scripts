"""Python equivalent of router-mesh-toggle.sh (enable|disable)."""
import sys

from meo_gr241ag import run

if __name__ == "__main__":
    action = sys.argv[1] if len(sys.argv) > 1 else ""
    mapped = {"enable": "on", "disable": "off"}.get(action)
    if not mapped:
        sys.exit("Usage: py router_mesh_toggle.py <enable|disable> [--apply] [--host IP] [--user NAME]")
    sys.exit(run(["mesh", mapped, *sys.argv[2:]]))
