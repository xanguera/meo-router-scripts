# MEO Router Scripts

*Also available in [English](README.md).*

Uma coleção de scripts para controlar o teu router MEO FiberGateway (modelo GR241AG) a partir da linha de comandos. Úteis para automatizar coisas que a interface web torna difíceis ou impossíveis.

> **Versão Python para Windows, Linux e macOS:** as mesmas funcionalidades estão também disponíveis como scripts Python, que não precisam de Bash, `curl` nem `expect`. Consulta o **[python/README_pt.md](python/README_pt.md)**. Contribuição de [joaoruimatos](https://github.com/joaoruimatos).

---

> ## Aviso
> **Usa estes scripts por tua conta e risco.**
> Alterar as definições do router pode provocar perda de ligação à Internet, instabilidade na rede ou uma configuração incorreta do equipamento. O autor destes scripts não se responsabiliza por quaisquer danos, perda de dados ou problemas causados ao teu router ou à tua rede. Se não tens a certeza do que um script faz, não o executes.

---

> **Requisito:** o teu computador tem de estar ligado à rede do router (por Wi-Fi ou por cabo ethernet) para usar estes scripts.

---

## Scripts

| Script | O que faz |
|---|---|
| `router-wifi-toggle.sh` | Liga ou desliga o Wi-Fi do router |
| `router-wps-toggle.sh` | Ativa ou desativa o WPS (Wi-Fi Protected Setup) |
| `router-mesh-toggle.sh` | Ativa ou desativa o Smart Mesh |
| `router-bridge-mode.sh` | Ativa, desativa ou mostra o estado do modo bridge da LAN |

---

## Instalação

### Passo 1 — Copiar os scripts para o teu computador

Se tens o Git instalado, abre um terminal e executa:

```bash
git clone <this-repo-url>
cd <repo-folder>
```

Caso contrário, descarrega o ZIP a partir do GitHub (botão verde "Code" → "Download ZIP"), descompacta-o e abre um terminal nessa pasta.

---

### Passo 2 — Instalar os requisitos

Os scripts precisam de duas ferramentas de linha de comandos: **curl** e **expect**.

#### macOS

O `curl` já vem instalado. Para instalar o `expect`, instala primeiro o [Homebrew](https://brew.sh), se ainda não o tiveres:

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

Depois instala o `expect`:

```bash
brew install expect
```

#### Linux (Ubuntu / Debian)

```bash
sudo apt update
sudo apt install curl expect
```

#### Linux (Fedora / RHEL)

```bash
sudo dnf install curl expect
```

#### Windows

Os scripts foram escritos para Bash, que não corre nativamente no Windows. A opção mais simples é a [versão Python](python/README_pt.md), que corre nativamente no Windows. Para usar os scripts Bash, tens duas opções:

**Opção A — Windows Subsystem for Linux (WSL)** — recomendada

1. Abre o PowerShell como Administrador e executa:
   ```
   wsl --install
   ```
2. Reinicia o computador e conclui a configuração do Ubuntu quando te for pedido.
3. Abre a aplicação "Ubuntu" e segue as instruções de **Linux (Ubuntu / Debian)** acima.

**Opção B — Git Bash**

1. Descarrega e instala o [Git for Windows](https://gitforwindows.org).
2. Abre o "Git Bash" a partir do menu Iniciar.
3. O `curl` vem incluído. O Git Bash não suporta o `expect` nativamente — usa o WSL para o `router-bridge-mode.sh`.

---

### Passo 3 — Tornar os scripts executáveis

No terminal, dentro da pasta do repositório, executa:

```bash
chmod +x router-wifi-toggle.sh router-wps-toggle.sh router-mesh-toggle.sh router-bridge-mode.sh
```

Só precisas de fazer isto uma vez.

---

## Executar os scripts

### Ligar/desligar o Wi-Fi

**Desligar** o Wi-Fi:
```bash
./router-wifi-toggle.sh 0
```

**Ligar** o Wi-Fi:
```bash
./router-wifi-toggle.sh 1
```

---

### Ativar/desativar o WPS

Ativar o WPS:
```bash
./router-wps-toggle.sh enable
```

Desativar o WPS:
```bash
./router-wps-toggle.sh disable
```

---

### Ativar/desativar o Mesh

Ativar o Smart Mesh:
```bash
./router-mesh-toggle.sh enable
```

Desativar o Smart Mesh:
```bash
./router-mesh-toggle.sh disable
```

> **Nota:** alterar o mesh faz o router reiniciar. É normal — ficas sem Internet durante cerca de 1–2 minutos.

---

### Modo bridge

Ver o estado atual:
```bash
./router-bridge-mode.sh show
```

Ativar o modo bridge:
```bash
./router-bridge-mode.sh enable
```

Desativar o modo bridge:
```bash
./router-bridge-mode.sh disable
```

> **Nota:** este script liga-se ao router por Telnet e precisa da ferramenta `expect` (ver a instalação acima).

---

## Resolução de problemas

**"Permission denied" ao executar um script**

Executa `chmod +x <nome-do-script>.sh` e tenta novamente.

**"Login failed — no SESSIONID cookie received"**

Confirma que o teu computador está ligado à rede do router e que o router responde em `http://192.168.1.254`.

**"command not found: expect"**

Tens de instalar o `expect` — consulta as instruções de instalação para o teu sistema operativo acima. Isto só afeta o `router-bridge-mode.sh`.

**Desliguei o Wi-Fi e agora não consigo ligar-me**

Liga o computador ao router com um cabo ethernet e executa `./router-wifi-toggle.sh 1` para o voltar a ligar.

---

## Licença

Estes scripts são publicados sob a [licença MIT](LICENSE).
