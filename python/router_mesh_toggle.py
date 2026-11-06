"""Equivalente Python de router-mesh-toggle.sh (enable/disable)."""
import sys
from meo_gr241ag import main, RouterError

if __name__ == "__main__":
    action = sys.argv[1] if len(sys.argv) > 1 else ""
    mapped = {"enable": "on", "disable": "off"}.get(action)
    if not mapped:
        sys.exit("Uso: py router_mesh_toggle.py <enable|disable> [--apply]")
    try:
        sys.exit(main(["mesh", mapped, *sys.argv[2:]]))
    except (RouterError, OSError, ConnectionError, TimeoutError) as exc:
        sys.exit(f"ERRO: {exc}")
