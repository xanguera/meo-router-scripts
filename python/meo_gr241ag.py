#!/usr/bin/env python3
"""Local management client for the MEO FiberGateway GR241AG.

Python port of the Bash scripts in xanguera/meo-router-scripts.
Uses HTTP for Wi-Fi, WPS and Smart Mesh, and Telnet for bridge mode and radio status.
Makes no change without --apply, and asks for no further confirmation.
Asks for the router IP and username (Enter accepts the default) unless given as flags.

Python 3.9+. Telnet needs: py -m pip install telnetlib3
"""
from __future__ import annotations

import argparse
import asyncio
import base64
import getpass
import http.client
import http.cookiejar
import json
import re
import sys
import time
import urllib.error
import urllib.request
from ipaddress import ip_address

DEFAULT_HOST = "192.168.1.254"
DEFAULT_USER = "meo"
USER_AGENT = "Mozilla/5.0 (compatible; GR241AG-Python/1.1)"
PROMPT = re.compile(r"/cli(?:/[A-Za-z0-9_.:-]+)*>\s*$")
LOGIN = re.compile(r"(?:login|user\s*name|username|user)\s*:\s*$", re.I)
PASSWORD = re.compile(r"password\s*:\s*$", re.I)
ANSI = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]")


class RouterError(RuntimeError):
    pass


def valid_host(value: str) -> str:
    """Accept only private or loopback IPv4 addresses, so credentials never go to the Internet."""
    try:
        address = ip_address(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("Use a private IPv4 address, e.g. 192.168.1.254") from exc
    if address.version != 4 or not (address.is_private or address.is_loopback) or address.is_multicast:
        raise argparse.ArgumentTypeError("The target must be a private/local IPv4 address")
    return str(address)


def valid_username(value: str) -> str:
    """A plain username: no line breaks (Telnet) and no colon (HTTP Basic Auth separator)."""
    if not re.fullmatch(r"[A-Za-z0-9_.@-]{1,64}", value):
        raise argparse.ArgumentTypeError(
            "Invalid username: use 1-64 letters, digits, _, -, . or @"
        )
    return value


def prompt_connection(host_arg: str | None, user_arg: str | None) -> tuple[str, str]:
    """Ask for any value not given as a flag. Enter accepts the default.

    --host and --user skip the questions, which helps when calling from scripts.
    """
    if host_arg is None:
        while True:
            supplied = input(f"FiberGateway IP [{DEFAULT_HOST}]: ").strip()
            try:
                host = valid_host(supplied or DEFAULT_HOST)
                break
            except argparse.ArgumentTypeError as exc:
                print(f"ERROR: {exc}", file=sys.stderr)
    else:
        host = host_arg

    if user_arg is None:
        while True:
            supplied = input(f"Username [{DEFAULT_USER}]: ").strip()
            try:
                username = valid_username(supplied or DEFAULT_USER)
                break
            except argparse.ArgumentTypeError as exc:
                print(f"ERROR: {exc}", file=sys.stderr)
    else:
        username = user_arg
    return host, username


def http_request(opener, request: urllib.request.Request, *, timeout: float = 12.0):
    try:
        with opener.open(request, timeout=timeout) as response:
            body = response.read(128_000).decode("utf-8", errors="replace")
            return response.status, body
    except urllib.error.HTTPError as exc:
        body = exc.read(4096).decode("utf-8", errors="replace")
        raise RouterError(f"HTTP {exc.code}: {body[:250] or exc.reason}") from exc


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    """Do not follow redirects: urllib would resend the Authorization header to the new host.

    The 3xx response is returned as is, like curl without -L, so a SESSIONID cookie set on
    it still counts as a login (the Bash scripts only check for the cookie).
    """

    def http_error_302(self, req, fp, code, msg, headers):
        return fp

    http_error_301 = http_error_303 = http_error_307 = http_error_308 = http_error_302


def http_login(host: str, username: str, password: str, port: int = 80):
    root = f"http://{host}" if port == 80 else f"http://{host}:{port}"
    cookies = http.cookiejar.CookieJar()
    # Ignore proxies set in the environment: the credentials are for the local network only.
    opener = urllib.request.build_opener(
        urllib.request.ProxyHandler({}),
        _NoRedirect(),
        urllib.request.HTTPCookieProcessor(cookies),
    )
    token = base64.b64encode(f"{username}:{password}".encode("utf-8")).decode("ascii")
    req = urllib.request.Request(
        root + "/index.html",
        headers={"Authorization": "Basic " + token, "User-Agent": USER_AGENT},
        method="GET",
    )
    status, _ = http_request(opener, req)
    if status < 200 or status >= 400 or not any(cookie.name == "SESSIONID" for cookie in cookies):
        raise RouterError("HTTP login failed: no SESSIONID cookie received")
    return opener, root


def http_modify(host: str, username: str, password: str, feature: str, action: str,
                port: int = 80) -> int:
    opener, root = http_login(host, username, password, port)
    endpoint, payload = {
        "wifi": ("/generic-wifi", {"version": "1.0", "enableWifi": "1" if action == "on" else "0"}),
        "mesh": ("/settings", {"version": "1.0", "smartMesh": "1" if action == "on" else "0"}),
        "wps": ("/generic-wifi", {"version": "1.0", "privateNetwork": {"wps": action == "on", "wpsOptions": 3}}),
    }[feature]
    url = root + "/locallmngt.cmd?request=" + endpoint
    req = urllib.request.Request(
        url,
        data=json.dumps(payload, separators=(",", ":")).encode("utf-8"),
        headers={
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "pt-PT",
            "Content-Type": "application/json;charset=UTF-8",
            "Origin": root,
            "Referer": root + "/index.html",
            "User-Agent": USER_AGENT,
        },
        method="PUT",
    )
    try:
        status, body = http_request(opener, req, timeout=20)
    except (urllib.error.URLError, OSError, ConnectionError, TimeoutError,
            http.client.RemoteDisconnected, http.client.IncompleteRead) as exc:
        if feature == "mesh":
            print("The connection dropped during the request; the router may have restarted.")
            print("State UNKNOWN: check it once the connection is back.")
            return 3
        raise RouterError(f"Could not send the request: {exc}") from exc
    print(f"HTTP response: {status}")
    if body.strip():
        # The body may hold firmware-specific error messages.
        print("Router response (check it for private data before sharing):")
        print(body[:1500])
    if 200 <= status < 300:
        print("The HTTP server accepted the request. This does NOT confirm the setting was applied.")
        print("Check the state on the gateway afterwards.")
        return 0
    raise RouterError(f"Unexpected response: HTTP {status}")


def clean(text: str) -> str:
    return ANSI.sub("", text).replace("\r", "")


async def wait_for(reader, patterns: dict, timeout: float = 28.0):
    received = ""
    stop_at = time.monotonic() + timeout
    while time.monotonic() < stop_at:
        remaining = stop_at - time.monotonic()
        try:
            data = await asyncio.wait_for(reader.read(4096), timeout=max(0.1, remaining))
        except asyncio.TimeoutError as exc:
            raise RouterError("Telnet session timed out") from exc
        if not data:
            raise RouterError("The gateway closed the Telnet session")
        received += data
        if len(received) > 300_000:
            raise RouterError("Telnet output too large")
        current = clean(received)
        for name, pattern in patterns.items():
            if pattern.search(current):
                return name, current
    raise RouterError("The gateway did not answer in time")


async def telnet_commands(host: str, username: str, password: str, commands: list[str]):
    try:
        import telnetlib3
    except ImportError as exc:
        raise RouterError("telnetlib3 is missing. Install it with: py -m pip install telnetlib3") from exc
    reader, writer = await telnetlib3.open_connection(
        host, 23, encoding="utf8", encoding_errors="replace", connect_timeout=12
    )
    try:
        sent_user = sent_pass = False
        for _ in range(8):
            name, _ = await wait_for(reader, {"prompt": PROMPT, "login": LOGIN, "password": PASSWORD})
            if name == "prompt":
                break
            if name == "login" and not sent_user:
                writer.write(username + "\r\n")
                await writer.drain()
                sent_user = True
            elif name == "password" and not sent_pass:
                writer.write(password + "\r\n")
                await writer.drain()
                sent_pass = True
            else:
                raise RouterError("Telnet login failed")
        else:
            raise RouterError("Could not log in over Telnet")
        for command in commands:
            writer.write(command + "\r\n")
            await writer.drain()
            _, output = await wait_for(reader, {"prompt": PROMPT})
            print(f"\n$ {command}\n{output}")
            if "ERR::" in output or "Error:" in output:
                raise RouterError("The gateway returned an error; see the output above")
    finally:
        writer.close()
        try:
            await writer.wait_closed()
        except (AttributeError, OSError, ConnectionError):
            pass


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="GR241AG: Wi-Fi, Smart Mesh, WPS and bridge mode over HTTP/Telnet"
    )
    p.add_argument("feature", choices=["wifi", "mesh", "wps", "bridge"])
    p.add_argument("action", choices=["on", "off", "status"])
    p.add_argument("--host", type=valid_host, default=None,
                   help=f"Private IP of the FiberGateway (if omitted: asks, default {DEFAULT_HOST})")
    p.add_argument("--user", type=valid_username, default=None,
                   help=f"Username (if omitted: asks, default {DEFAULT_USER})")
    p.add_argument("--apply", action="store_true",
                   help="Make the requested change, with NO further confirmation")
    return p


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    if args.action == "status" and args.feature in {"mesh", "wps"}:
        print(f"There is no known way to read the {args.feature} status.")
        return 2
    if args.action != "status" and not args.apply:
        print("DRY RUN: nothing was sent to the router.")
        print(f"You asked for: {args.feature} {args.action}")
        print("Add --apply to make the change. There is no further confirmation.")
        return 0
    host, username = prompt_connection(args.host, args.user)
    if args.feature == "wifi" and args.action == "off":
        print("WARNING: turning Wi-Fi off may cut your only management connection.")
    elif args.feature == "mesh" and args.action != "status":
        print("WARNING: changing Smart Mesh may restart the gateway.")
    elif args.feature == "bridge" and args.action != "status":
        print("WARNING: changing bridge mode may interrupt the Internet connection.")
    password = getpass.getpass(f"Password for {username}@{host} (not stored): ")
    if not password:
        print("Empty password: cancelled.")
        return 1
    if args.feature == "bridge":
        # Same commands as router-bridge-mode.sh, which was tested on the router.
        if args.action == "status":
            commands = ["lan/bridge-mode/show"]
        else:
            state = "enable" if args.action == "on" else "disable"
            commands = [f"lan/bridge-mode/config --enable={state}", "lan/bridge-mode/show"]
        asyncio.run(telnet_commands(host, username, password, commands))
        return 0
    if args.feature == "wifi" and args.action == "status":
        asyncio.run(telnet_commands(host, username, password, [
            "/wireless/basic/show --wifi-index=0", "/wireless/basic/show --wifi-index=1"
        ]))
        return 0
    return http_modify(host, username, password, args.feature, args.action)


def run(argv=None) -> int:
    """Run main() and turn the expected failures into a message and an exit code."""
    try:
        return main(argv)
    except KeyboardInterrupt:
        print("\nInterrupted.", file=sys.stderr)
        return 130
    except EOFError:
        print("\nNo input available. Use --host and --user, or run interactively.", file=sys.stderr)
        return 2
    except (RouterError, OSError, urllib.error.URLError, TimeoutError, ConnectionError,
            asyncio.TimeoutError, http.client.HTTPException) as exc:
        # asyncio.TimeoutError is not TimeoutError before Python 3.11 (Telnet connect timeout).
        print("ERROR:", exc, file=sys.stderr)
        print("Check the gateway IP and that you are on its local network (Wi-Fi/LAN).", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(run())
