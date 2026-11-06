# MEO GR241AG — Python tools

*Também disponível em [português](README_pt.md).*

Python scripts to manage the **MEO FiberGateway GR241AG**. They run on Windows, Linux and macOS without Bash, `curl`, `expect`, Homebrew or WSL.

They are a Python port of the Bash scripts in this repository and follow the same HTTP requests and Telnet commands. This is not an official MEO tool. See [ATTRIBUTION.md](ATTRIBUTION.md) for credits.

## Features

| Feature | Command | Protocol |
|---|---|---|
| Turn Wi-Fi on/off (2.4 + 5 GHz) | `wifi on/off` | Local HTTP |
| Turn Smart Mesh on/off | `mesh on/off` | Local HTTP |
| Turn WPS on/off | `wps on/off` | Local HTTP |
| Show the state of the Wi-Fi bands | `wifi status` | Telnet |
| Show/change bridge mode on LAN 4 | `bridge status/on/off` | Telnet |

**Tested on a real router (firmware `3RGW040E00r020`):** `wifi off` returned HTTP 200 with `{"code":0,"message":""}`, and the Wi-Fi networks disappeared. `mesh off` ended with the connection dropping, so **we do not know whether it was applied**.

**Not yet tested on a real router:** `wifi on`, WPS, `wifi status` and the bridge commands. Treat the Telnet features (`wifi status`, `bridge`) as experimental. The bridge commands are the same ones the Bash script `router-bridge-mode.sh` sends. The unit tests only simulate the router.

## Requirements

- Python 3.9 or newer (`py --version` on Windows, `python3 --version` on Linux/macOS).
- Access to the router's **private** management address (for example `192.168.1.254`).
- For `wifi status` and the bridge commands, which use Telnet:

  ```powershell
  py -m pip install telnetlib3
  ```

- For `wifi on/off`, `mesh on/off` and `wps on/off`, Python's standard library is enough.

On Linux and macOS, write `python3` where these examples say `py`, and `/` instead of `\`.

## Usage (Windows PowerShell)

Run the commands from this folder.

```powershell
# Dry run: no connection, nothing changes
py .\meo_gr241ag.py wifi off

# Real change (no further confirmation)
py .\meo_gr241ag.py wifi off --apply
py .\meo_gr241ag.py wifi on --apply
py .\meo_gr241ag.py mesh off --apply
py .\meo_gr241ag.py wps off --apply

# Status (read only)
py .\meo_gr241ag.py wifi status
py .\meo_gr241ag.py bridge status
```

### IP, username and password

Each time it connects to the router, the program asks:

```text
FiberGateway IP [192.168.1.254]:
Username [meo]:
Password for meo@192.168.1.254 (not stored):
```

Press **Enter** to accept the defaults. To skip the first two questions, give both values as flags. The password is still asked for, and is not shown as you type:

```powershell
py .\meo_gr241ag.py wifi on --apply --host 192.168.1.254 --user meo
```

There is no extra confirmation step, but **changes still need `--apply`**. Leave it out to do a dry run. `--host` and `--user` are useful when calling the tool from other scripts.

### Scripts with the same arguments as the Bash ones

```powershell
py .\router_wifi_toggle.py 0 --apply
py .\router_wifi_toggle.py 1 --apply
py .\router_mesh_toggle.py disable --apply
py .\router_wps_toggle.py disable --apply
py .\router_bridge_mode.py show
```

They also accept `--host`, `--user` and `--apply` (`--apply` is not needed to read a status). They all call `meo_gr241ag.py`.

## Safety and getting access back

- **Turning Wi-Fi off can cut your management connection immediately.** Make sure you can also reach the router over a LAN cable first. If the gateway is in bridge mode, you may need to move the cable from LAN 4 to another LAN port and renew the connection on your computer.
- **Smart Mesh is not the same as Smart Wi-Fi.** A dropped connection during `mesh off` does not mean it worked.
- Changing bridge mode can affect your Internet connection. Do not change it if everything already works.
- HTTP Basic authentication and Telnet are **not encrypted**. Use them only on a trusted local network, and never expose these ports to the Internet. The tool only accepts a private or local IPv4 address.
- The program never writes passwords or cookies to files. Do not publish logs that contain public IPs, serial numbers, MAC addresses, private network names or credentials.
- An HTTP 200 response alone does not prove the change was applied. Always check on the router.

## Router API and CLI used

- HTTP (with a `SESSIONID` session cookie): `PUT /locallmngt.cmd?request=/generic-wifi`, with `enableWifi` (`"0"`/`"1"`) and `privateNetwork.wps`.
- HTTP: `PUT /locallmngt.cmd?request=/settings`, with `smartMesh` (`"0"`/`"1"`).
- Telnet: `lan/bridge-mode/show`, `lan/bridge-mode/config --enable=...`, `/wireless/basic/show --wifi-index=0|1`.

## Tests

```powershell
py -m unittest discover -s tests -v
```

The tests use a fake HTTP server on `127.0.0.1`. **They never touch your router.**

## Credits

Python version contributed by [joaoruimatos](https://github.com/joaoruimatos), based on the HTTP requests and Telnet commands of the original Bash scripts by [Xavier Anguera](https://github.com/xanguera). Released under the [MIT license](../LICENSE).
