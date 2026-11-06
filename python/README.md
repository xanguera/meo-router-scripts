# MEO GR241AG — Python tools

Scripts Python para gerir o **MEO FiberGateway GR241AG**, com suporte a Windows, Linux e macOS sem Bash, `curl`, `expect`, Homebrew ou WSL.

**Projeto derivado/inspirado pelos comandos e scripts Bash de [xanguera/meo-router-scripts](https://github.com/xanguera/meo-router-scripts).** Consulta também [ATTRIBUTION.md](ATTRIBUTION.md). O código Python aqui incluído é uma reimplementação dos fluxos documentados nesse projeto; não é uma versão oficial da MEO.

## Funcionalidades

| Função | Comando | Protocolo |
|---|---|---|
| Ligar/desligar Wi-Fi (2,4 + 5 GHz) | `wifi on/off` | HTTP local |
| Ligar/desligar Smart Mesh | `mesh on/off` | HTTP local |
| Ligar/desligar WPS | `wps on/off` | HTTP local |
| Ver estado das bandas Wi-Fi | `wifi status` | Telnet |
| Ver/alterar bridge na LAN 4 | `bridge status/on/off` | Telnet |

**Testado num aparelho real:** pedido `wifi off` na versão `3RGW040E00r020`, com resposta HTTP 200/`{"code":0,"message":""}` e desaparecimento das redes Wi-Fi confirmado pelo utilizador. `mesh off` terminou com a ligação interrompida: **não sabemos se foi aplicado**. WPS, alterações de bridge e `wifi on` não foram testados neste aparelho; testes locais simulam a API.

## Requisitos

- Python 3.9+ (`py --version` no Windows).
- Acesso ao endereço **privado** de gestão do router (por exemplo `192.168.1.254`).
- Para `wifi status` ou comandos bridge via Telnet:

  ```powershell
  py -m pip install telnetlib3
  ```

- Para `wifi on/off`, `mesh on/off` ou `wps on/off`, basta Python com a biblioteca padrão.

## Utilização no Windows (PowerShell)

Executa os comandos a partir desta pasta.

```powershell
# Simulação: sem ligação e sem alterar nada
py .\meo_gr241ag.py wifi off

# Alteração real (sem pergunta CONFIRMO)
py .\meo_gr241ag.py wifi off --apply
py .\meo_gr241ag.py wifi on --apply
py .\meo_gr241ag.py mesh off --apply
py .\meo_gr241ag.py wps off --apply

# Estado (só leitura)
py .\meo_gr241ag.py wifi status
py .\meo_gr241ag.py bridge status
```

### IP, username e password

Em cada ligação real, o programa pergunta:

```text
IP do FiberGateway [192.168.1.254]:
Utilizador [meo]:
Password de meo@192.168.1.254 (nao e guardada):
```

Premir **Enter** aceita os defaults. Podes fornecer ambos diretamente para dispensar estas duas perguntas (continuará a pedir a password sem a mostrar):

```powershell
py .\meo_gr241ag.py wifi on --apply --host 192.168.1.254 --user meo
```

Não há confirmação adicional `CONFIRMO`; **`--apply` continua a ser obrigatório para alterações**. Omite-o para simular. Usar `--host` e `--user` é útil para execução assistida por scripts.

### Scripts equivalentes aos originais

```powershell
py .\router_wifi_toggle.py 0 --apply
py .\router_wifi_toggle.py 1 --apply
py .\router_mesh_toggle.py disable --apply
py .\router_wps_toggle.py disable --apply
py .\router_bridge_mode.py show
```

Aceitam igualmente `--host`, `--user` e `--apply` (exceto quando a operação é de leitura). Todos delegam a mesma lógica ao `meo_gr241ag.py`.

## Segurança e recuperação de acesso

- **Desligar o Wi-Fi pode cortar imediatamente a ligação de gestão.** Confirma primeiro um caminho alternativo por LAN. Se o gateway estiver em bridge, pode ser necessário mover temporariamente o cabo de LAN 4 para uma porta LAN não bridged e renovar a ligação do router/PC.
- **Smart Mesh não é sinónimo de Smart Wi-Fi.** Uma queda de ligação durante `mesh off` não confirma sucesso.
- Alterar bridge pode afetar a Internet; não o alteres se já estiver a funcionar.
- HTTP Basic e Telnet **não são cifrados**. Utiliza-os apenas numa rede local confiável; nunca exposes essas portas à Internet. Só é aceite um IPv4 local/privado.
- O programa não escreve passwords nem cookies em ficheiros. Evita publicar logs com IPs públicos, números de série, MACs, SSIDs privados ou credenciais.
- Uma resposta HTTP 200 não garante, isoladamente, que a alteração foi aplicada: verifica sempre no equipamento.

## API/CLI utilizadas

- HTTP (com sessão `SESSIONID`): `PUT /locallmngt.cmd?request=/generic-wifi`, com `enableWifi` (`"0"`/`"1"`) e `privateNetwork.wps`.
- HTTP: `PUT /locallmngt.cmd?request=/settings`, com `smartMesh` (`"0"`/`"1"`).
- Telnet: `/lan/bridge-mode/show`, `/lan/bridge-mode/config --enable=...`, `/wireless/basic/show --wifi-index=0|1`.

## Testes

```powershell
py -m unittest discover -s tests -v
```

Os testes usam um servidor HTTP falso em `127.0.0.1`; **não alteram o FiberGateway**.

## Contribuir / publicar como fork

Sugestão: criar um *fork* do repositório original e adicionar esta pasta, por exemplo sob `python/`, mantendo os scripts Bash originais intactos. Depois, abrir um *pull request*.

**Licença:** na consulta de 6/11/2026 não foi identificado um ficheiro `LICENSE` nem uma declaração de licença no repositório original. Um repositório público não equivale automaticamente a código open source licenciado. Solicita esclarecimento/autorizaçao ao autor antes de redistribuir como projeto independente e evita atribuir uma licença ao **conjunto** sem os direitos necessários.

## Créditos

API e fluxos de operações HTTP/Telnet documentados por **[xanguera/meo-router-scripts](https://github.com/xanguera/meo-router-scripts)**. Conversão e testes em Python elaborados para facilitar utilização em Windows e noutros sistemas com Python.
