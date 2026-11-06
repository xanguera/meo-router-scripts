"""Equivalente Python de router-bridge-mode.sh (show/enable/disable)."""
import sys
from meo_gr241ag import main, RouterError

if __name__ == "__main__":
    action = sys.argv[1] if len(sys.argv) > 1 else ""
    mapped = {"show": "status", "enable": "on", "disable": "off"}.get(action)
    if not mapped:
        sys.exit("Uso: py router_bridge_mode.py <show|enable|disable> [--apply]")
    try:
        sys.exit(main(["bridge", mapped, *sys.argv[2:]]))
    except (RouterError, OSError, ConnectionError, TimeoutError) as exc:
        sys.exit(f"ERRO: {exc}")
