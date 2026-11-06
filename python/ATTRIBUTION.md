# Atribuição e origem

O projeto Python nesta pasta foi desenvolvido a partir do comportamento da API HTTP e dos comandos Telnet descritos no projeto original:

- **Autor e projeto original:** [xanguera/meo-router-scripts](https://github.com/xanguera/meo-router-scripts)
- Scripts Bash originais: `router-wifi-toggle.sh`, `router-wps-toggle.sh`, `router-mesh-toggle.sh`, `router-bridge-mode.sh`.
- A nova versão em Python mantém os mesmos fluxos funcionais, mas não inclui os ficheiros Bash originais.
- Melhorias: compatibilidade com Windows sem Bash/expect, IP e utilizador configuráveis por perguntas ou opções, password oculta, `--apply` para ações e testes locais sem router real.

**Nota sobre licenciamento:** o repositório original não apresentava um ficheiro ou declaração de licença no momento da consulta (6 de novembro de 2026). O código-fonte publicamente visível não deve ser presumido livre para redistribuição irrestrita. Para contribuir, prefere um fork e um pull request no GitHub e pede ao autor que esclareça a licença. Este documento de créditos não concede licenças sobre trabalho de terceiros.

**Nota de teste:** o pedido de desativação de Wi-Fi foi confirmado num GR241AG com firmware `3RGW040E00r020`. Outros comandos e firmwares podem comportar-se de modo diferente.
