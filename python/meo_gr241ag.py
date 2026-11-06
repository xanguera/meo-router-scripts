#!/usr/bin/env python3
"""Cliente de administracao local para MEO FiberGateway GR241AG.

Adaptacao independente dos scripts Bash do projeto xanguera/meo-router-scripts.
HTTP para wifi, WPS e Smart Mesh; Telnet para bridge e estado dos radios.
Nao executa alteracoes sem --apply; sem confirmacao "CONFIRMO".
Pede IP e utilizador (com defaults), exceto se fornecidos nas flags.

Python 3.9+; Telnet requer: py -m pip install telnetlib3
"""
from __future__ import annotations

import argparse
import asyncio
import base64
import getpass
import http.cookiejar
import http.client
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
    """Restringir credenciais a IPs privados/loopback: nunca enviar para a Internet."""
    try:
        address = ip_address(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("Usa um endereco IPv4 privado, ex.: 192.168.1.254") from exc
    if address.version != 4 or not (address.is_private or address.is_loopback) or address.is_multicast:
        raise argparse.ArgumentTypeError("O destino tem de ser um IPv4 privado/local")
    return str(address)


def valid_username(value: str) -> str:
    """Username simples, sem quebras de linha nem separador de Basic Auth."""
    if not re.fullmatch(r"[A-Za-z0-9_.@-]{1,64}", value):
        raise argparse.ArgumentTypeError(
            "Utilizador invalido: usa 1-64 letras, numeros, _, -, . ou @"
        )
    return value


def prompt_connection(host_arg: str | None, user_arg: str | None) -> tuple[str, str]:
    """Pedir valores em falta, aceitando Enter para os predefinidos.

    --host e --user evitam perguntas e facilitam utilizacao em scripts.
    """
    if host_arg is None:
        while True:
            supplied = input(f"IP do FiberGateway [{DEFAULT_HOST}]: ").strip()
            try:
                host = valid_host(supplied or DEFAULT_HOST)
                break
            except argparse.ArgumentTypeError as exc:
                print(f"ERRO: {exc}", file=sys.stderr)
    else:
        host = host_arg

    if user_arg is None:
        while True:
            supplied = input(f"Utilizador [{DEFAULT_USER}]: ").strip()
            try:
                username = valid_username(supplied or DEFAULT_USER)
                break
            except argparse.ArgumentTypeError as exc:
                print(f"ERRO: {exc}", file=sys.stderr)
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


def http_login(host: str, username: str, password: str):
    root = f"http://{host}"
    cookies = http.cookiejar.CookieJar()
    # Desativar proxies do ambiente: as credenciais sao so para a rede local.
    opener = urllib.request.build_opener(
        urllib.request.ProxyHandler({}),
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
        raise RouterError("Autenticacao HTTP falhou: nao foi recebido o cookie SESSIONID")
    return opener, root


def http_modify(host: str, username: str, password: str, feature: str, action: str) -> int:
    opener, root = http_login(host, username, password)
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
            print("A ligacao terminou durante o pedido; o router podera ter reiniciado.")
            print("Estado INDETERMINADO: verifica depois de recuperar a ligacao.")
            return 3
        raise RouterError(f"Falha ao enviar o pedido: {exc}") from exc
    print(f"Resposta HTTP: {status}")
    if body.strip():
        # O corpo da resposta pode conter mensagens de erro especificas do firmware.
        print("Resposta do router (verifica dados sensiveis antes de partilhar):")
        print(body[:1500])
    if 200 <= status < 300:
        print("Pedido aceite pelo servidor HTTP. Isto NAO confirma que a configuracao foi aplicada.")
        print("Confirma posteriormente o estado no gateway.")
        return 0
    raise RouterError(f"Resposta inesperada: HTTP {status}")


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
            raise RouterError("Timeout da sessao Telnet") from exc
        if not data:
            raise RouterError("O gateway fechou a sessao Telnet")
        received += data
        if len(received) > 300_000:
            raise RouterError("Saida Telnet demasiado grande")
        current = clean(received)
        for name, pattern in patterns.items():
            if pattern.search(current):
                return name, current
    raise RouterError("O gateway nao respondeu dentro do tempo definido")


async def telnet_commands(host: str, username: str, password: str, commands: list[str]):
    try:
        import telnetlib3
    except ImportError as exc:
        raise RouterError("Falta telnetlib3. Instala com: py -m pip install telnetlib3") from exc
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
                raise RouterError("Autenticacao Telnet falhou")
        else:
            raise RouterError("Nao foi possivel autenticar por Telnet")
        for command in commands:
            writer.write(command + "\r\n")
            await writer.drain()
            _, output = await wait_for(reader, {"prompt": PROMPT})
            print(f"\n$ {command}\n{output}")
            if "ERR::" in output or "Error:" in output:
                raise RouterError("O gateway devolveu um erro; verifica a saida acima")
    finally:
        writer.close()
        try:
            await writer.wait_closed()
        except (AttributeError, OSError, ConnectionError):
            pass


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="GR241AG: Wi-Fi, Smart Mesh, WPS e bridge via HTTP/Telnet"
    )
    p.add_argument("feature", choices=["wifi", "mesh", "wps", "bridge"])
    p.add_argument("action", choices=["on", "off", "status"])
    p.add_argument("--host", type=valid_host, default=None,
                   help="IP privado do FiberGateway (omitido: pede, padrao 192.168.1.254)")
    p.add_argument("--user", type=valid_username, default=None,
                   help="Utilizador (omitido: pede, padrao meo)")
    p.add_argument("--apply", action="store_true",
                   help="Executa a alteracao solicitada SEM confirmacao adicional")
    return p


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    if args.action == "status" and args.feature in {"mesh", "wps"}:
        print(f"Nao existe leitura de estado {args.feature} confirmada nestes scripts originais.")
        return 2
    if args.action != "status" and not args.apply:
        print("MODO DE SIMULACAO: nenhum comando foi enviado ao router.")
        print(f"Pretendias: {args.feature} {args.action}")
        print("Para aplicar, acrescenta --apply. Nao pede confirmacao adicional.")
        return 0
    host, username = prompt_connection(args.host, args.user)
    if args.feature == "wifi" and args.action == "off":
        print("ATENCAO: desligar Wi-Fi pode cortar a unica ligacao de gestao.")
    elif args.feature == "mesh" and args.action != "status":
        print("ATENCAO: alterar Smart Mesh pode reiniciar o gateway.")
    elif args.feature == "bridge" and args.action != "status":
        print("ATENCAO: alterar o bridge pode interromper a Internet.")
    password = getpass.getpass(f"Password de {username}@{host} (nao e guardada): ")
    if not password:
        print("Password vazia: cancelado.")
        return 1
    if args.feature == "bridge":
        if args.action == "status":
            commands = ["/lan/bridge-mode/show"]
        else:
            state = "enable" if args.action == "on" else "disable"
            commands = [f"/lan/bridge-mode/config --enable={state}", "/lan/bridge-mode/show"]
        asyncio.run(telnet_commands(host, username, password, commands))
        return 0
    if args.feature == "wifi" and args.action == "status":
        asyncio.run(telnet_commands(host, username, password, [
            "/wireless/basic/show --wifi-index=0", "/wireless/basic/show --wifi-index=1"
        ]))
        return 0
    return http_modify(host, username, password, args.feature, args.action)


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\nInterrompido.", file=sys.stderr)
        sys.exit(130)
    except EOFError:
        print("\nEntrada indisponivel. Usa --host e --user ou executa interativamente.", file=sys.stderr)
        sys.exit(2)
    except (RouterError, OSError, urllib.error.URLError, TimeoutError, ConnectionError) as exc:
        print("ERRO:", exc, file=sys.stderr)
        print("Confirma o IP do gateway e o acesso pela rede local (Wi-Fi/LAN).", file=sys.stderr)
        sys.exit(2)
