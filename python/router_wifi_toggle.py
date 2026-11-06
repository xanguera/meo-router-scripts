"""Python equivalent of router-wifi-toggle.sh (0|1|status)."""
import sys

from meo_gr241ag import run

if __name__ == "__main__":
    action = sys.argv[1] if len(sys.argv) > 1 else ""
    mapped = {"0": "off", "1": "on", "status": "status"}.get(action)
    if not mapped:
        sys.exit("Usage: py router_wifi_toggle.py <0|1|status> [--apply] [--host IP] [--user NAME]")
    sys.exit(run(["wifi", mapped, *sys.argv[2:]]))
