# Attribution and origin

The Python tools in this folder were contributed by [joaoruimatos](https://github.com/joaoruimatos). They are based on the HTTP API and Telnet commands used by the original Bash scripts in this repository, by [Xavier Anguera](https://github.com/xanguera):

- `router-wifi-toggle.sh`, `router-wps-toggle.sh`, `router-mesh-toggle.sh`, `router-bridge-mode.sh`.

The Python version follows the same steps as those scripts and adds:

- Windows support without Bash or `expect`.
- Router IP and username set by a question or a flag.
- A hidden password prompt.
- A dry run unless `--apply` is given.
- Local tests that need no real router.

**Test note:** turning Wi-Fi off was confirmed on a GR241AG with firmware `3RGW040E00r020`. Other commands and firmware versions may behave differently.

The whole repository, including this folder, is released under the [MIT license](../LICENSE).
