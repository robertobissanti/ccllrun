<div align="center">

<img src="studio/web/icon.svg" width="120" alt="ccllrun Studio icon">

# ccllrun

**Claude Code on local models. No cloud.**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-0.1-d97757)](#ccllrun-studio-macos-app)
[![Platform](https://img.shields.io/badge/platform-macOS%20Apple%20Silicon-black?logo=apple)](#requirements)
[![100% Local](https://img.shields.io/badge/AI-100%25%20local-success)](#)
[![Engine](https://img.shields.io/badge/engine-llama.cpp-blue)](https://github.com/ggml-org/llama.cpp)
[![Agent](https://img.shields.io/badge/agent-Claude%20Code-d97757)](https://docs.anthropic.com/claude-code)
[![Models](https://img.shields.io/badge/models-GGUF%20%C2%B7%20Qwen-purple)](#models)

🇮🇹 [Leggilo in italiano](README_it.md)

</div>

`ccllrun` runs [Claude Code](https://docs.anthropic.com/claude-code) on open models served locally by **llama.cpp** (`llama-server`), through a proxy that translates the Anthropic API into an OpenAI-compatible one. It ships with **ccllrun Studio**, a native macOS app with chat, stack management, interactive permission approval and graphical configuration.

```
Claude Code ──ANTHROPIC_BASE_URL──▶ proxy.py (:8765) ──┬──▶ llama-server BIG   (:8001, e.g. Qwen3.6-35B-A3B)
                                                       └──▶ llama-server SMALL (:8002, small/fast model)
ccllrun Studio (:8770) ─── native dashboard: headless chat, status, config, logs
```

Everything stays on your machine: the engine listens on `127.0.0.1` only, no data ever leaves.

Current Studio version: **0.1 (0.1)**. Author/contact: **Roberto Bissanti** — [roberto.bissanti@gmail.com](mailto:roberto.bissanti@gmail.com). License: **MIT**.

## 30-second start

```bash
git clone https://github.com/robertobissanti/ccllrun.git
cd ccllrun && chmod +x ccllrun
sudo ln -sf "$PWD/ccllrun" /usr/local/bin/ccllrun
cp config.example.json ~/.ccllrun/config.json   # then fix the GGUF paths
ccllrun                                          # starts everything, opens Claude Code
```

First run bootstraps the rest by itself: `~/.ccllrun/`, the Python venv with the proxy dependencies, and `proxy.py` from the repo.

## Features

- **CLI** (`ccllrun`): starts big + small + proxy and opens Claude Code already pointed at the local model; on exit the proxy stops (llama-servers stay warm for the next launch).
- **Two models**: a big one for the real work, a small one for Claude Code's quick requests (`ANTHROPIC_SMALL_FAST_MODEL`).
- **PDF**: the proxy converts `document` blocks into extracted text or rasterized pages (`text`/`image`/`hybrid`).
- **Vision**: with the `mmproj-*.gguf` projector next to the GGUF, screenshots and images just work.
- **Right-sized context**: Claude Code's auto-compact window is aligned to the model's real context (`CLAUDE_CODE_AUTO_COMPACT_WINDOW`), preventing Metal out-of-memory crashes.
- **ccllrun Studio** (macOS app): a chat that *is* headless Claude Code (same tools, same permissions), **interactive permission approval** per command with persistent per-project rules, markdown rendering, slash commands with autocomplete (`/context`, `/memory`, `/compact`, …), stack autostart, setup doctor with remedies, config editor, live logs.

## Requirements

| Component | Notes | Install |
|---|---|---|
| macOS Apple Silicon | tested on Darwin 25 (M1 Ultra) | — |
| **llama.cpp** (`llama-server`) | recent build with Metal; needs `--reasoning-budget`, `--cache-reuse`, `-fa` | `brew install llama.cpp` |
| **Claude Code** (`claude`) | ≥ 2.x | `npm install -g @anthropic-ai/claude-code` |
| **Python** | ≥ 3.10 with `venv` | `brew install python@3.13` |
| Xcode CLT (`clang++`) | only to build Studio | `xcode-select --install` |

The proxy's Python modules (`aiohttp`, `pymupdf`) are installed **automatically** on first run into `~/.ccllrun/venv`. External dependencies (llama.cpp, Claude Code) are not vendored: they are large projects with their own installers and release cycles — Studio's *setup doctor* checks for them and suggests the install command for each.

Studio vendors **MathJax 3** locally (`studio/web/vendor/mathjax/tex-svg.js`) to render LaTeX equations in chat replies. It is bundled into the `.app` by `make`, served from `/vendor/...`, and does not require network access at runtime.

In `~/.claude/settings.json` add (the script warns if missing):

```json
{ "env": { "CLAUDE_CODE_ATTRIBUTION_HEADER": "0" } }
```

### Memory

For the 35B-A3B Q4_K_XL: ~20 GB of weights + KV cache (depends on `ctx_big` and `kv_type`) + ~2 GB for the mmproj + the small model. **≥ 48 GB** of unified memory recommended with the default config; with less, reduce `ctx_big` or pick a smaller model.

## Models

The ones used and tested by the author (Hugging Face links):

| Role | Model | Link |
|---|---|---|
| **big** | Qwen3.6-35B-A3B (MoE, Q4_K_XL) + mmproj for vision | [unsloth/Qwen3.6-35B-A3B-GGUF](https://huggingface.co/unsloth/Qwen3.6-35B-A3B-GGUF) |
| big (alternative) | Qwen3.6-27B with MTP (native speculative decoding) | [unsloth/Qwen3.6-27B-MTP-GGUF](https://huggingface.co/unsloth/Qwen3.6-27B-MTP-GGUF) |
| **small** | history-9b (Q4_K_M) | [ghost-actual/Qwen3.6-9B-Heretic-History-Q4_K_M-GGUF](https://huggingface.co/ghost-actual/Qwen3.6-9B-Heretic-History-Q4_K_M-GGUF) |

Download the `.gguf` files (and the optional `mmproj-*.gguf` into the big model's folder) and set the paths in `~/.ccllrun/config.json`. Any chat-instruct GGUF works; if the filename contains `MTP`, ccllrun enables speculative decoding by itself.

## CLI reference

```bash
ccllrun [ccllrun options] [claude arguments...]
```

Anything ccllrun doesn't recognize is passed through to `claude`.

### Subcommands

| Command | What it does |
|---|---|
| `ccllrun` | starts big + small + proxy (if not already up) and opens Claude Code |
| `ccllrun servers` | starts the stack only, without Claude Code (used by Studio) |
| `ccllrun stop` | stops llama-servers and proxy (pidfiles + port fallback) |
| `ccllrun logs [big\|small\|proxy]` | follows the given log (`tail -f`, default: `big`) |
| `ccllrun --help-ccllrun` | help |
| `ccllrun doctor` / `mcp` / `config` / `update` / `install` / `setup-token` / `--version` / `--help` | passed straight to `claude` without starting the servers |

### Options

| Flag | Description |
|---|---|
| `--config <file>` | use an alternative config JSON |
| `--big-gguf <path>` | big model |
| `--small-gguf <path>` | small model (`""` to disable) |
| `--no-small` | don't start the small model |
| `--ctx <n>` | big model context (default 98304) |
| `--kv <type>` | KV cache quantization: `f16` \| `q8_0` \| `q4_0` |
| `--mmproj <path\|off>` | vision projector (default: autodetect next to the big GGUF) |
| `--parallel <n>` | llama-server parallel slots (**divides the context per slot**) |
| `--pdf-mode <m>` | `text` \| `image` \| `hybrid` |
| `--port <n>` | proxy port (default 8765) |
| `--tool-search` / `--no-tool-search` | enable/disable tool search (overrides global `settings.json`) |

### Watching the logs from another terminal

While Claude Code is running, open other terminal windows to watch what the servers are doing:

```bash
ccllrun logs big       # main model: loading progress, tokens/s, memory errors
ccllrun logs small     # fast model
ccllrun logs proxy     # Anthropic→OpenAI requests, PDF conversions, 4xx/5xx
```

(equivalent to `tail -f ~/.ccllrun/llama-big.log` etc.; Studio's **Log** page does the same with auto-refresh). `logs big` is especially useful on first start — model loading can take 1–2 minutes and the progress shows there — and whenever something stops responding: Metal out-of-memory and `failed to parse grammar` errors only show up there.

## ccllrun Studio (macOS app)

```bash
cd studio
make run        # builds and opens "ccllrun Studio.app"
make serve      # server only on :8770 (development / LAN with STUDIO_HOST=0.0.0.0)
```

On launch Studio starts the stack by itself (big + small + proxy), just like the CLI; disable with `"studio_autostart": false`.

### Building and Gatekeeper (code signing)

The app is **not distributed pre-built**: you compile it yourself with `make`. This is deliberate — it sidesteps macOS code-signing entirely:

- **Built from source** (the supported path): a locally-built app carries no quarantine attribute, and on Apple Silicon the linker applies an ad-hoc signature automatically. It opens normally, no warnings.
- **If you ever get the `.app` from somewhere else** (zip, AirDrop, another machine): macOS quarantines it and Gatekeeper will claim it is *"damaged or from an unidentified developer"*. Either rebuild it from source (recommended), or remove the quarantine flag and re-sign ad-hoc:

  ```bash
  xattr -dr com.apple.quarantine "ccllrun Studio.app"
  codesign --force --deep -s - "ccllrun Studio.app"
  ```

- **For maintainers who want to distribute binaries**: you need an Apple Developer ID certificate (`codesign -s "Developer ID Application: …"` + `xcrun notarytool submit` for notarization). Until then, "build from source" is the only friction-free path — and it takes seconds, the wrapper is a single small C++ file.

> Rebuilding after every `git pull` is good practice anyway: `make` also refreshes the app's embedded copies of `server.py`, `ccllrun` and the web UI.

- **Chat** = headless Claude Code in the project folder you pick (first folder is the cwd, the others go to `--add-dir`). The conversation continues with `--resume`.
- **Permissions**: per-chat selector (*file edits* / *allow everything* / *plan only*). In normal mode, when Claude wants to run an uncovered command an **approval card** appears with the exact command: *Allow* (once), *Always allow* (saves the rule, e.g. `Bash(gcc:*)`, into the project's `.claude/settings.local.json`), *Deny*.
- **Markdown** in replies (toggle in Config → Studio); copying always returns the original markdown.
- **LaTeX math** in replies through vendored MathJax (`$...$`, `$$...$$`, `\(...\)`, `\[...\]`), rendered offline as SVG.
- **Slash commands** with autocomplete: `/context`, `/memory`, `/compact`, `/cost`, `/init`, plus the project's custom commands.
- **Status**: Start/Stop toggle + Restart, server health cards, setup doctor with remedies.
- **Config**: graphical (or raw JSON) editor for `~/.ccllrun/config.json`. After changing server parameters: Restart.
- **Live logs** for big/small/proxy.
- **Info** page with version 0.1, author email, copyright and MIT license.

## Configuration

Precedence (weakest to strongest): **built-in defaults → `~/.ccllrun/config.json` → `ccllrun_*` env vars → CLI flags**. Every key is optional, paths support `~`. See `config.example.json`.

### All config keys

| Key | Env | CLI | Default | Description |
|---|---|---|---|---|
| `big_gguf` | `ccllrun_GGUF_BIG` | `--big-gguf` | Qwen3.6-35B-A3B Q4_K_XL | main model |
| `small_gguf` | `ccllrun_GGUF_SMALL` | `--small-gguf` | history-9b Q4_K_M | fast model (`""` to disable) |
| `no_small` | — | `--no-small` | `false` | don't start the small model |
| `model_big` | `ccllrun_MODEL_BIG` | — | `qwen-big` | API alias of the big model |
| `model_small` | `ccllrun_MODEL_SMALL` | — | `small-fast` | API alias of the small model |
| `ctx_big` | `ccllrun_CTX_BIG` | `--ctx` | 98304 | big context (**divided by `parallel`**) |
| `ctx_small` | — | — | 32768 | small context |
| `batch` | — | — | 2048 | batch size (`-b`/`-ub`) |
| `kv_type` | `ccllrun_KV_TYPE` | `--kv` | `q8_0` | KV cache quantization (`f16`/`q8_0`/`q4_0`) — `q8_0` halves memory |
| `ngl` | — | — | 99 | layers offloaded to GPU (99 = all) |
| `parallel` | — | `--parallel` | 1 | parallel slots (>1 splits the context per slot) |
| `reasoning_budget` | — | — | 4096 | max reasoning tokens |
| `presence_penalty` | — | — | 1.5 | anti-repetition (lower it if code quality degrades) |
| `mmproj` | `ccllrun_MMPROJ` | `--mmproj` | `""` (autodetect) | vision projector; `"off"` to disable |
| `pdf_mode` | `ccllrun_PDF_MODE` | `--pdf-mode` | `hybrid` | `text` / `image` / `hybrid` |
| `proxy_port` | `ccllrun_PROXY_PORT` | `--port` | 8765 | proxy port |
| `big_port` | `ccllrun_BIG_PORT` | — | 8001 | big llama-server port |
| `small_port` | `ccllrun_SMALL_PORT` | — | 8002 | small llama-server port |
| `llama_bin` | `ccllrun_LLAMA_BIN` | — | `llama-server` | llama-server binary |
| `extra_big_flags` | — | — | `""` | extra flags for the big server, e.g. `"--mlock --kv-unified"` |
| `cc_auto_compact_window` | — | — | 115000 | Claude Code auto-compact threshold (keep it **below `ctx_big`**) |
| `cc_max_output_tokens` | — | — | 32000 | Claude Code max output |
| `cc_tool_search` | — | — | `false` | enable Claude Code tool search (faster prefill with many MCP servers; startup option) |
| `studio_markdown` | — | — | `true` | markdown rendering in Studio's chat |
| `studio_autostart` | — | — | `true` | Studio starts the stack on launch |

> **Why `cc_auto_compact_window`?** Claude Code assumes a 200k window for non-Anthropic models. On a local model with a smaller context it would fill past the limit and crash the GPU out of memory: this key makes it compact the conversation *before* hitting the wall.

> **About `cc_tool_search`.** Claude Code's tool search (`ENABLE_TOOL_SEARCH`) sends only a few tools per request and loads the rest on demand, which makes the prefill much faster when you have many MCP servers connected. It only activates by itself on a first-party Anthropic endpoint, so behind a proxy you must opt in. The proxy forwards the `tool_reference` blocks the feature relies on, so it works end-to-end. It behaves as a **startup option**: in Studio's chat the value is frozen at the first turn of a conversation (changing it mid-conversation would break in-flight tool calls), and ccllrun sets `ENABLE_TOOL_SEARCH` accordingly, overriding whatever is in your global `settings.json`. Default off — turn it on if you have many MCP servers and want a faster prefill.

### Proxy environment variables

| Variable | Default | Description |
|---|---|---|
| `CCRUN_PDF_MAX_PAGES` | 10 | max pages when rasterizing PDFs |
| `CCRUN_PDF_DPI` | 150 | rasterization DPI |
| `CCRUN_PDF_TEXT_MIN` | 40 | min chars to keep extracted text in `hybrid` mode |

### Studio environment variables

| Variable | Default | Description |
|---|---|---|
| `STUDIO_PORT` | 8770 | dashboard port |
| `STUDIO_HOST` | 127.0.0.1 | bind host (`0.0.0.0` for LAN access) |
| `CCLLRUN_BIN` | autodetect | path of the `ccllrun` script |
| `CLAUDE_BIN` | autodetect | path of the `claude` binary |

After changing server parameters: `ccllrun stop` and restart (or Studio → Status → Restart) — otherwise the health check reuses the running servers with the old parameters.

## Files and logs

```
~/.ccllrun/                 ← created automatically on first run
├── proxy.py                # installed/updated from the repo
├── config.json             # configuration (optional)
├── venv/                   # created on first run
├── llama-big.log/.pid
├── llama-small.log/.pid
└── proxy.log
```

## Troubleshooting

- **`image input is not supported … mmproj`** → the projector is missing: download `mmproj-*.gguf` into the big GGUF's folder. Then `ccllrun stop` and restart.
- **`exceeds the available context size`** → `parallel > 1` splits `ctx_big` across slots: set it back to 1 or raise `ctx_big`.
- **`qwen-big non pronto` / not ready** → check `ccllrun logs big` (usually out of memory: lower `ctx_big` or use `kv_type: q8_0`; or a wrong GGUF path).
- **`kIOGPUCommandBufferCallbackErrorOutOfMemory` errors** → context too large for memory: lower `ctx_big` and keep `cc_auto_compact_window` below it.
- **PDFs arrive as `[PDF rimosso]`** → `~/.ccllrun/venv/bin/pip install pymupdf`.
- **Repetitive output or degraded code** → lower `presence_penalty` (1.0 or 0).
- **Studio UI looks stale** → sidebar → *Reload UI*.

## Roadmap

- [ ] **Model downloads from Hugging Face inside Studio**: GGUF search, estimate whether the model fits the machine's memory (weights + KV cache at the chosen context), download with progress and automatic config update.
- [ ] On-the-fly model switching without restarting the stack.
- [ ] Linux support (the stack is mostly portable already; Studio's native wrapper is the missing piece).

## Author

**Roberto Bissanti** ([roberto.bissanti@gmail.com](mailto:roberto.bissanti@gmail.com)) — a photovoltaic-sector engineer who uses local AI for everyday technical work. ccllrun was born from the practical need of running Claude Code on his own hardware (Mac Studio M1 Ultra), with documents that never leave the machine.

## Credits and license

- **MIT** license — see [LICENSE](LICENSE).
- Studio's native wrapper (C++ launcher + WKWebView, `studio/native/webview.h`) and the dashboard approach derive from **[DStudio](https://github.com/sk8erboi17/DStudio)** by **Giuseppe Perrotta** (BSD-3-Clause, see `studio/native/LICENSE.DStudio`). Thank you!
- Studio vendors **MathJax 3** for offline SVG rendering of LaTeX math in chat replies.
- Engine: [llama.cpp](https://github.com/ggml-org/llama.cpp) · Agent: [Claude Code](https://docs.anthropic.com/claude-code) · Models: [Qwen](https://huggingface.co/Qwen) quantized by [unsloth](https://huggingface.co/unsloth).
