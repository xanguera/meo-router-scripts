"""Equivalente Python de router-wifi-toggle.sh (0=off, 1=on, status)."""
import sys
from meo_gr241ag import main, RouterError

if __name__ == "__main__":
    action = sys.argv[1] if len(sys.argv) > 1 else ""
    mapped = {"0": "off", "1": "on", "status": "status"}.get(action)
    if not mapped:
        sys.exit("Uso: py router_wifi_toggle.py <0|1|status> [--apply]")
    try:
        sys.exit(main(["wifi", mapped, *sys.argv[2:]]))
    except (RouterError, OSError, ConnectionError, TimeoutError) as exc:
        sys.exit(f"ERRO: {exc}")
