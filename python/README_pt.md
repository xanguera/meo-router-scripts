# MEO GR241AG — Ferramentas Python

*Also available in [English](README.md).*

Scripts Python para gerir o **MEO FiberGateway GR241AG**. Funcionam em Windows, Linux e macOS sem Bash, `curl`, `expect`, Homebrew ou WSL.

São uma versão em Python dos scripts Bash deste repositório e enviam os mesmos pedidos HTTP e comandos Telnet. Não é uma ferramenta oficial da MEO. Consulta o [ATTRIBUTION.md](ATTRIBUTION.md) para os créditos.

## Funcionalidades

| Funcionalidade | Comando | Protocolo |
|---|---|---|
| Ligar/desligar o Wi-Fi (2,4 + 5 GHz) | `wifi on/off` | HTTP local |
| Ligar/desligar o Smart Mesh | `mesh on/off` | HTTP local |
| Ligar/desligar o WPS | `wps on/off` | HTTP local |
| Ver o estado das bandas Wi-Fi | `wifi status` | Telnet |
| Ver/alterar o modo bridge na LAN 4 | `bridge status/on/off` | Telnet |

**Testado num router real (firmware `3RGW040E00r020`):** `wifi off` devolveu HTTP 200 com `{"code":0,"message":""}` e as redes Wi-Fi desapareceram. `mesh off` terminou com a ligação interrompida, por isso **não sabemos se foi aplicado**.

**Ainda não testado num router real:** `wifi on`, WPS, `wifi status` e os comandos bridge. Considera as funcionalidades Telnet (`wifi status`, `bridge`) experimentais. Os comandos bridge são os mesmos que o script Bash `router-bridge-mode.sh` envia. Os testes unitários apenas simulam o router.

## Requisitos

- Python 3.9 ou superior (`py --version` no Windows, `python3 --version` no Linux/macOS).
- Acesso ao endereço **privado** de gestão do router (por exemplo `192.168.1.254`).
- Para `wifi status` e os comandos bridge, que usam Telnet:

  ```powershell
  py -m pip install telnetlib3
  ```

- Para `wifi on/off`, `mesh on/off` e `wps on/off`, basta a biblioteca padrão do Python.

No Linux e no macOS, escreve `python3` onde estes exemplos dizem `py`, e `/` em vez de `\`.

## Utilização (Windows PowerShell)

Executa os comandos a partir desta pasta.

```powershell
# Simulação: sem ligação, nada é alterado
py .\meo_gr241ag.py wifi off

# Alteração real (sem confirmação adicional)
py .\meo_gr241ag.py wifi off --apply
py .\meo_gr241ag.py wifi on --apply
py .\meo_gr241ag.py mesh off --apply
py .\meo_gr241ag.py wps off --apply

# Estado (só leitura)
py .\meo_gr241ag.py wifi status
py .\meo_gr241ag.py bridge status
```

### IP, utilizador e password

Sempre que se liga ao router, o programa pergunta (as perguntas aparecem em inglês):

```text
FiberGateway IP [192.168.1.254]:
Username [meo]:
Password for meo@192.168.1.254 (not stored):
```

Prime **Enter** para aceitar os valores predefinidos. Para saltar as duas primeiras perguntas, indica ambos os valores nas opções. A password continua a ser pedida e não aparece no ecrã:

```powershell
py .\meo_gr241ag.py wifi on --apply --host 192.168.1.254 --user meo
```

Não há um passo de confirmação adicional, mas **as alterações continuam a exigir `--apply`**. Omite-o para fazer uma simulação. `--host` e `--user` são úteis para chamar a ferramenta a partir de outros scripts.

### Scripts com os mesmos argumentos que os Bash

```powershell
py .\router_wifi_toggle.py 0 --apply
py .\router_wifi_toggle.py 1 --apply
py .\router_mesh_toggle.py disable --apply
py .\router_wps_toggle.py disable --apply
py .\router_bridge_mode.py show
```

Também aceitam `--host`, `--user` e `--apply` (`--apply` não é preciso para ler um estado). Todos chamam o `meo_gr241ag.py`.

## Segurança e recuperação de acesso

- **Desligar o Wi-Fi pode cortar de imediato a ligação de gestão.** Confirma primeiro que consegues chegar ao router por cabo LAN. Se o gateway estiver em modo bridge, pode ser preciso mudar o cabo da LAN 4 para outra porta LAN e renovar a ligação no computador.
- **Smart Mesh não é o mesmo que Smart Wi-Fi.** Uma queda de ligação durante `mesh off` não quer dizer que tenha funcionado.
- Alterar o modo bridge pode afetar a ligação à Internet. Não o alteres se tudo já estiver a funcionar.
- A autenticação HTTP Basic e o Telnet **não são cifrados**. Usa-os apenas numa rede local de confiança e nunca exponhas estas portas à Internet. A ferramenta só aceita um endereço IPv4 privado ou local.
- O programa nunca escreve passwords nem cookies em ficheiros. Não publiques logs com IPs públicos, números de série, endereços MAC, nomes de redes privadas ou credenciais.
- Uma resposta HTTP 200, por si só, não prova que a alteração foi aplicada. Verifica sempre no router.

## API e CLI do router utilizadas

- HTTP (com o cookie de sessão `SESSIONID`): `PUT /locallmngt.cmd?request=/generic-wifi`, com `enableWifi` (`"0"`/`"1"`) e `privateNetwork.wps`.
- HTTP: `PUT /locallmngt.cmd?request=/settings`, com `smartMesh` (`"0"`/`"1"`).
- Telnet: `lan/bridge-mode/show`, `lan/bridge-mode/config --enable=...`, `/wireless/basic/show --wifi-index=0|1`.

## Testes

```powershell
py -m unittest discover -s tests -v
```

Os testes usam um servidor HTTP falso em `127.0.0.1`. **Nunca tocam no teu router.**

## Créditos

Versão Python contribuída por [joaoruimatos](https://github.com/joaoruimatos), com base nos pedidos HTTP e comandos Telnet dos scripts Bash originais de [Xavier Anguera](https://github.com/xanguera). Publicado sob a [licença MIT](../LICENSE).
