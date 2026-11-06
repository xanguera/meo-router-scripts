# MEO Router Scripts

A collection of scripts to control your MEO FiberGateway router (model GR241AG) from the command line. Useful for automating things the web interface makes difficult or impossible.

---

> ## Disclaimer
> **Use these scripts at your own risk.**
> Modifying router settings can result in loss of internet connectivity, network instability, or misconfiguration of your equipment. The author of these scripts is not responsible for any damage, data loss, or problems caused to your router or network. If you are unsure about what a script does, do not run it.

---

> **Requirement:** Your computer must be connected to the router's network (via Wi-Fi or ethernet cable) to use these scripts.

---

## Scripts

| Script | What it does |
|---|---|
| `router-wifi-toggle.sh` | Turn the router's Wi-Fi on or off |
| `router-wps-toggle.sh` | Enable or disable WPS (Wi-Fi Protected Setup) |
| `router-mesh-toggle.sh` | Enable or disable Smart Mesh |
| `router-bridge-mode.sh` | Enable, disable, or check the status of LAN bridge mode |

---

## Setup

### Step 1 — Get the scripts onto your computer

If you have Git installed, open a terminal and run:

```bash
git clone <this-repo-url>
cd <repo-folder>
```

Otherwise, download the ZIP from GitHub (green "Code" button → "Download ZIP"), unzip it, and open a terminal in that folder.

---

### Step 2 — Install the requirements

The scripts require two command-line tools: **curl** and **expect**.

#### macOS

`curl` is pre-installed. To install `expect`, first install [Homebrew](https://brew.sh) if you don't have it:

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

Then install `expect`:

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

The scripts are written for Bash, which does not run natively on Windows. You have two options:

**Option A — Windows Subsystem for Linux (WSL)** — recommended

1. Open PowerShell as Administrator and run:
   ```
   wsl --install
   ```
2. Restart your computer and finish the Ubuntu setup when prompted.
3. Open the "Ubuntu" app, then follow the **Linux (Ubuntu / Debian)** instructions above.

**Option B — Git Bash**

1. Download and install [Git for Windows](https://gitforwindows.org).
2. Open "Git Bash" from the Start menu.
3. `curl` is included. For `expect`, Git Bash does not support it natively — use WSL for `router-bridge-mode.sh`.

---

### Step 3 — Make the scripts executable

In your terminal, inside the repo folder, run:

```bash
chmod +x router-wifi-toggle.sh router-wps-toggle.sh router-mesh-toggle.sh router-bridge-mode.sh
```

You only need to do this once.

---

## Running the scripts

### Wi-Fi toggle

Turn Wi-Fi **off**:
```bash
./router-wifi-toggle.sh 0
```

Turn Wi-Fi **on**:
```bash
./router-wifi-toggle.sh 1
```

---

### WPS toggle

Enable WPS:
```bash
./router-wps-toggle.sh enable
```

Disable WPS:
```bash
./router-wps-toggle.sh disable
```

---

### Mesh toggle

Enable Smart Mesh:
```bash
./router-mesh-toggle.sh enable
```

Disable Smart Mesh:
```bash
./router-mesh-toggle.sh disable
```

> **Note:** Toggling mesh causes the router to restart. This is normal — you will lose internet access for about 1–2 minutes.

---

### Bridge mode

Check current status:
```bash
./router-bridge-mode.sh show
```

Enable bridge mode:
```bash
./router-bridge-mode.sh enable
```

Disable bridge mode:
```bash
./router-bridge-mode.sh disable
```

> **Note:** This script connects to the router via Telnet and requires the `expect` tool (see setup above).

---

## Troubleshooting

**"Permission denied" when running a script**

Run `chmod +x <script-name>.sh` and try again.

**"Login failed — no SESSIONID cookie received"**

Make sure your computer is connected to the router's network, and that the router is reachable at `http://192.168.1.254`.

**"command not found: expect"**

You need to install `expect` — see the setup instructions for your OS above. This only affects `router-bridge-mode.sh`.

**Wi-Fi was turned off and now I can't connect**

Connect your computer to the router with an ethernet cable, then run `./router-wifi-toggle.sh 1` to turn it back on.

### Python version (Windows/Linux/macOS)

A Python implementation of the original MEO Router Scripts is also available, supporting Windows, Linux and macOS.

See **[Python (Windows/Linux/macOS)](python/README.md)** for installation instructions, usage examples and supported features.

**Credits:** The original Bash scripts were developed by [xanguera](https://github.com/xanguera/meo-router-scripts). The Python implementation is based on their work, with adaptations for cross-platform compatibility.