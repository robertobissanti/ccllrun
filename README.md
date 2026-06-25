<div align="center">

<img src="studio/web/icon.svg" width="120" alt="ccllrun Studio icon">

# ccllrun

**Claude Code on local models. No cloud.**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-0.1-d97757)](#ccllrun-studio-macos-app)
[![Platform](https://img.shields.io/badge/platform-macOS%20Apple%20Silicon-black?logo=apple)](#requirements)
[![100% Local](https://img.shields.io/badge/AI-100%25%20local-success)](#)
[![Engine](https://img.shields.io/badge/engine-llama.cpp-blue)](https://github.com/ggml-org/llama.cpp)
[![MLX](https://img.shields.io/badge/backend-MLX-5E5CE6)](https://github.com/ml-explore/mlx)
[![Agent](https://img.shields.io/badge/agent-Claude%20Code-d97757)](https://docs.anthropic.com/claude-code)
[![Models](https://img.shields.io/badge/models-GGUF%20%C2%B7%20Qwen-purple)](#models)

🇮🇹 [Leggilo in italiano](README_it.md)

</div>

`ccllrun` is a practical tool for using [Claude Code](https://docs.anthropic.com/claude-code) with local models in a way that feels usable every day: fast enough, predictable enough, and with the right controls exposed. It is not a new inference engine. It coordinates existing local runtimes — **llama.cpp** for GGUF models and **MLX** for MLX model directories — through a proxy that translates Claude Code's Anthropic API calls into an OpenAI-compatible local API.

The goal is simple: remove the bottlenecks that make local Claude Code sessions feel slow or fragile, without reducing answer quality. That means taking care of the whole path, not just starting a model: model routing, context size, parallel slots, prefill batch and micro-batch, KV cache format, prompt-cache stability, auto-compaction, tool calls, PDF/image handling, process cleanup and the configuration UI.

It can be used from the terminal, like Claude Code itself, or through **ccllrun Studio**, a native macOS app with the same role that Claude Desktop has next to the Claude CLI: a graphical surface for chat, stack status, logs, permissions and configuration.

```
Claude Code ──ANTHROPIC_BASE_URL──▶ proxy.py (:8765) ──┬──▶ llama-server LARGE LLM (:8001, e.g. Qwen3.6-35B-A3B)
                                                       └──▶ llama-server SMALL LLM (:8002, small/fast model)
ccllrun Studio (:8770) ─── native dashboard: headless chat, status, config, logs
```

Everything stays on your machine: by default the engine listens on `127.0.0.1` only, no data ever leaves.

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

- **CLI** (`ccllrun`): starts large LLM + small LLM + proxy and opens Claude Code already pointed at the local model; on exit the proxy stops and the model servers can stay warm for the next launch.
- **Studio** (`ccllrun Studio.app`): a native macOS companion app for the same stack: chat, start/stop/restart, health checks, logs, interactive permissions and graphical configuration.
- **Two LLMs**: a large LLM for the real work, a small LLM for Claude Code's quick requests (`ANTHROPIC_SMALL_FAST_MODEL`). Internally the config keys still use `big` and `small`.
- **Two backends**: `llama.cpp` for GGUF files and `mlx-lm` for MLX directories, selected with the same config and UI.
- **Embedding/RAG slot**: an optional third llama.cpp server exposes `/v1/embeddings` through the proxy for semantic search over documents, standards, datasheets or code.
- **PDF**: the proxy converts `document` blocks into extracted text or rasterized pages (`text`/`image`/`hybrid`).
- **Vision**: with the `mmproj-*.gguf` projector next to the GGUF, screenshots and images just work.
- **Right-sized context**: Claude Code's auto-compact window is aligned to the model's real context (`CLAUDE_CODE_AUTO_COMPACT_WINDOW`), preventing Metal out-of-memory crashes.
- **Prompt-cache aware proxy**: prompt rendering is kept stable so llama-server can reuse the already processed prefix between turns.

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

ccllrun does not require one fixed model. It is built around roles: a **large LLM** for the main coding/reasoning work, a **small LLM** for Claude Code's faster auxiliary calls, and optionally an **embedding model** for semantic search/RAG. The current experimental setup uses the following models.

### GGUF / llama.cpp

| Role | Model | Config key | Link |
|---|---|---|---|
| **Large LLM** | Qwen3.6-35B-A3B, Q4_K_XL, with `mmproj-F32.gguf` for vision | `big_gguf`, `mmproj` | [unsloth/Qwen3.6-35B-A3B-GGUF](https://huggingface.co/unsloth/Qwen3.6-35B-A3B-GGUF) |
| Large LLM alternative | Qwen3.6-27B with MTP, useful for speculative decoding experiments | `big_gguf` | [unsloth/Qwen3.6-27B-MTP-GGUF](https://huggingface.co/unsloth/Qwen3.6-27B-MTP-GGUF) |
| **Small LLM** | history-9b, Q4_K_M | `small_gguf` | [ghost-actual/Qwen3.6-9B-Heretic-History-Q4_K_M-GGUF](https://huggingface.co/ghost-actual/Qwen3.6-9B-Heretic-History-Q4_K_M-GGUF) |

Download the `.gguf` files and set the paths in `~/.ccllrun/config.json`. Any chat-instruct GGUF can be used, but the defaults are tuned around a large Qwen model plus a smaller fast model. If the filename contains `MTP`, ccllrun enables speculative decoding by itself.

### MLX

MLX support is implemented through `mlx_lm.server`, not by loading MLX files directly in the proxy. In practice:

- set `"backend": "mlx-lm"`;
- set `big_mlx` and `small_mlx` to **model directories**, not to individual `.safetensors` files;
- keep GGUF paths available if you switch back to `"backend": "llama.cpp"`;
- remember that llama.cpp-only knobs such as `batch`, `ubatch`, `cache_reuse`, `kv_type` and `ngl` do not map to MLX server flags.

The proxy keeps the same Claude Code-facing API for both backends. It also handles MLX-specific tool-call behavior: when an MLX model emits tool calls as text, the proxy recovers them and returns them in the Anthropic-compatible shape Claude Code expects.

Models used in the MLX experiments:

| Role | Model directory / repo | Config key |
|---|---|---|
| **Large LLM** | `lmstudio-community/gemma-4-26B-A4B-it-QAT-MLX-4bit` | `big_mlx` |
| **Small LLM** | `lmstudio-community/gemma-4-E2B-it-MLX-4bit` | `small_mlx` |

### Embeddings and RAG

ccllrun can start a dedicated embedding server in addition to the large/small LLM servers. This is separate from chat generation: embeddings turn text chunks into vectors for semantic search, document retrieval and RAG workflows.

| Role | Model | Config key | Link |
|---|---|---|---|
| **Embedding** | Qwen3-Embedding-8B, Q4_K_M | `embed_gguf` | [Qwen/Qwen3-Embedding-8B-GGUF](https://huggingface.co/Qwen/Qwen3-Embedding-8B-GGUF) |

When `embed_gguf` is set, ccllrun starts a third `llama-server` on `embed_port` with embedding mode enabled, and the proxy exposes it as `/v1/embeddings` using the alias `model_embed` (`embed` by default). This is the path used for RAG experiments over technical material such as standards, datasheets, project documents and code.

Embedding models are guarded deliberately: if an embedding GGUF is accidentally configured as the large or small LLM, ccllrun refuses to start it there. Embedding models do not generate normal chat completions and can otherwise appear to loop forever.

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
| `--batch-small <n>` | small model batch (default: same as the big model) |
| `--ubatch <n>` / `--ubatch-small <n>` | prefill micro-batch (`-ub`, default: = batch); lower it to cut peak prefill memory. Must be ≤ batch |
| `--cache-reuse <n>` / `--cache-reuse-small <n>` | min gap to reuse KV cache around a hole (default 256) |
| `--kv <type>` | KV cache quantization: `f16` \| `q8_0` \| `q4_0` |
| `--mmproj <path\|off>` | vision projector (default: autodetect next to the big GGUF) |
| `--parallel <n>` | big-model parallel slots (**divides the context per slot**) |
| `--parallel-small <n>` | small-model parallel slots (default: same as the big model) |
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

Studio is the graphical companion to the CLI, in the same spirit as Claude Desktop next to Claude Code in the terminal. It does not replace the CLI: it gives the same local stack a native macOS surface for daily use.

```bash
cd studio
make run        # builds and opens "ccllrun Studio.app"
make serve      # server only on :8770 (development / LAN with STUDIO_HOST=0.0.0.0)
```

On launch Studio starts the stack by itself (big + small + proxy), just like the CLI; disable with `"studio_autostart": false`.

The Status page is intentionally operational: if the stack is only partially alive, or if stale processes are still bound to the expected ports, Studio asks ccllrun to clean up and restart the whole stack instead of trusting an inconsistent state. This is important for local inference, where a single stuck server can make the UI look alive while Claude Code cannot actually work.

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
- **Config**: graphical (or raw JSON) editor for `~/.ccllrun/config.json`, with Basic/Advanced sections, localized labels/tooltips (`it`, `en`, `es`, `fr`, `de`, `pt`) and explicit units for token/slot values. The UI uses "large LLM" and "small LLM" labels even though the underlying config keys remain `big` and `small`. After changing server parameters: Restart.
- **Live logs** for big/small/proxy.
- **Info** page with version 0.1, author email, copyright and MIT license.

## Configuration

Precedence (weakest to strongest): **built-in defaults → `~/.ccllrun/config.json` → `ccllrun_*` env vars → CLI flags**. Every key is optional, paths support `~`. See `config.example.json`.

### All config keys

| Key | Env | CLI | Default | Description |
|---|---|---|---|---|
| `big_gguf` | `ccllrun_GGUF_BIG` | `--big-gguf` | Qwen3.6-35B-A3B Q4_K_XL | large LLM file |
| `small_gguf` | `ccllrun_GGUF_SMALL` | `--small-gguf` | history-9b Q4_K_M | small LLM file (`""` to disable) |
| `backend` | `ccllrun_BACKEND` | `--backend` | `llama.cpp` | runtime backend (`llama.cpp` for GGUF, `mlx-lm` for MLX directories) |
| `big_mlx` | `ccllrun_MLX_BIG` | `--big-mlx` | `""` | large LLM MLX directory |
| `small_mlx` | `ccllrun_MLX_SMALL` | `--small-mlx` | `""` | small LLM MLX directory |
| `no_small` | — | `--no-small` | `false` | don't start the small LLM |
| `model_big` | `ccllrun_MODEL_BIG` | — | `qwen-big` | API alias of the large LLM |
| `model_small` | `ccllrun_MODEL_SMALL` | — | `small-fast` | API alias of the small LLM |
| `ctx_big` | `ccllrun_CTX_BIG` | `--ctx` | 98304 | large LLM context, in tokens (**divided by `parallel`**) |
| `ctx_small` | — | — | 32768 | small LLM context, in tokens (**divided by `parallel_small`**) |
| `batch` | — | — | 2048 | big-model batch size (`-b`/`-ub`) |
| `batch_small` | — | `--batch-small` | `""` (= `batch`) | small-model batch size; lower it to ease KV-cache pressure on the small model |
| `ubatch` | — | `--ubatch` | `""` (= `batch`) | big-model prefill micro-batch (`-ub`); lower it to cut peak prefill memory |
| `ubatch_small` | — | `--ubatch-small` | `""` (= `batch_small`) | small-model `-ub`; **must be ≤ `batch_small`** (does not inherit `ubatch`) |
| `cache_reuse` | — | `--cache-reuse` | 256 | min gap to reuse KV cache around a removed/edited block; raise it only if you see cache misses on compacted conversations |
| `cache_reuse_small` | — | `--cache-reuse-small` | `""` (= `cache_reuse`) | same, for the small model |
| `kv_type` | `ccllrun_KV_TYPE` | `--kv` | `q8_0` | KV cache quantization (`f16`/`q8_0`/`q4_0`) — `q8_0` halves memory |
| `ngl` | — | — | 99 | layers offloaded to GPU (99 = all) |
| `parallel` | — | `--parallel` | 1 | big-model parallel slots (>1 splits the context per slot) |
| `parallel_small` | — | `--parallel-small` | `""` (= `parallel`) | small-model parallel slots; keep it at 1 so each request gets the full `ctx_small` |
| `reasoning_budget` | — | — | 4096 | max reasoning tokens |
| `presence_penalty` | — | — | 1.5 | anti-repetition (lower it if code quality degrades) |
| `mmproj` | `ccllrun_MMPROJ` | `--mmproj` | `""` (autodetect) | vision projector; `"off"` to disable |
| `pdf_mode` | `ccllrun_PDF_MODE` | `--pdf-mode` | `hybrid` | `text` / `image` / `hybrid` |
| `proxy_port` | `ccllrun_PROXY_PORT` | `--port` | 8765 | proxy port |
| `big_port` | `ccllrun_BIG_PORT` | — | 8001 | big llama-server port |
| `small_port` | `ccllrun_SMALL_PORT` | — | 8002 | small llama-server port |
| `embed_gguf` | — | — | `""` | optional embedding GGUF; if set, starts a third server exposing `/v1/embeddings` through the proxy (semantic search / RAG). A non-embedding GGUF here is rejected for big/small but only warned about here |
| `embed_port` | — | — | 8003 | embedding llama-server port |
| `model_embed` | — | — | `embed` | API alias of the embedding model |
| `llama_bin` | `ccllrun_LLAMA_BIN` | — | `llama-server` | llama-server binary |
| `extra_big_flags` | — | — | `""` | extra flags for the big server, e.g. `"--mlock --kv-unified"` |
| `cc_auto_compact_window` | — | — | 115000 | Claude Code auto-compact threshold (keep it **below `ctx_big`**) |
| `cc_max_output_tokens` | — | — | 32000 | Claude Code max output |
| `cc_tool_search` | — | — | `false` | enable Claude Code tool search (faster prefill with many MCP servers; startup option) |
| `studio_markdown` | — | — | `true` | markdown rendering in Studio's chat |
| `studio_autostart` | — | — | `true` | Studio starts the stack on launch |
| `studio_lan_enabled` | — | — | `false` | expose Studio on the LAN on the next launch; use only on trusted networks |

The reasoning behind these knobs — big/small split, the context/memory/cache distinction, prompt-cache stability and `cc_auto_compact_window` — is explained in **Design notes** below.

> **About `cc_tool_search`.** Claude Code's tool search (`ENABLE_TOOL_SEARCH`) sends only a few tools per request and loads the rest on demand, which makes the prefill much faster when you have many MCP servers connected. It only activates by itself on a first-party Anthropic endpoint, so behind a proxy you must opt in. The proxy forwards the `tool_reference` blocks the feature relies on, so it works end-to-end. It behaves as a **startup option**: in Studio's chat the value is frozen at the first turn of a conversation (changing it mid-conversation would break in-flight tool calls), and ccllrun sets `ENABLE_TOOL_SEARCH` accordingly, overriding whatever is in your global `settings.json`. Default off — turn it on if you have many MCP servers and want a faster prefill.

### Design notes — what each group of options is *for*

The config table above is a flat list; this section explains the reasoning behind each family of options, so you can tune them with intent instead of trial and error.

**Two LLMs, two budgets.** Claude Code talks to two endpoints: the *large LLM* does the real reasoning and coding, while a *small LLM* handles its frequent throwaway calls (conversation titles, cheap sub-tasks). The code and config still call them `big` and `small`, but the user-facing UI now uses "large LLM" and "small LLM" to make the roles explicit. They have very different load profiles, so they get **independent limits**: `ctx`, `batch`, `ubatch`, `parallel` and `cache_reuse` all exist in a big and a `*_small` variant. The `*_small` keys fall back to the big value when empty, so nothing breaks if you ignore them. *Why it matters:* before this split the small LLM silently inherited the large LLM's settings — including a `parallel` slot count that divided its smaller `ctx_small` into pieces too small for real prompts, which surfaced as `Context size has been exceeded` in `llama-small.log`. Setting `parallel_small: 1` gives every small-LLM request the full context. The benefit is a small LLM that stops crashing under load, without sacrificing throughput on the large one.

**Context vs. memory vs. cache — three independent knobs.** These look similar but solve different problems, and conflating them is the usual cause of mis-tuning:
- `ctx_*` is *how much conversation fits*. With `parallel > 1` llama-server splits it across slots, so the effective per-request context is `ctx / parallel`.
- `ubatch` (prefill micro-batch) is *peak memory during prefill*. Lowering it trades a bit of prefill speed for a lower memory spike — the right lever when long prompts trigger `failed to find a memory slot`. It must stay `≤ batch`, which is why `ubatch_small` falls back to `batch_small` rather than inheriting the big `ubatch`.
- `cache_reuse` is *prefix reuse*. It's the minimum gap llama-server tolerates to reuse the KV cache around a block that changed mid-conversation (e.g. after an auto-compact). It improves latency on edited histories and has almost no effect when the prefix is already identical.

**Prompt-cache stability (the invisible win).** Claude Code is stateless: it resends the whole transcript every turn, and llama-server only skips re-computing the *byte-identical* prefix. The proxy now renders the conversation history canonically — tool calls are serialized with sorted keys and **without their opaque Anthropic `id`** (which changes between requests and used to break the match). *Why it matters:* with an unstable prefix, every turn re-prefilled the entire prompt; with the fix, a measured second turn dropped from **~7957 to 17 re-processed tokens (~0.2%)**. This is pure latency saved on every multi-turn session, and it's what makes `cache_reuse` worth tuning at all. See `test/PROMPTCACHE.md`.

**Right-sized context (`cc_auto_compact_window`).** Claude Code assumes a 200k window for non-Anthropic models. A local model with a smaller context would fill past its limit and crash Metal out of memory. This key makes Claude Code compact the conversation *before* it hits the wall — keep it below `ctx_big`. It's the difference between a graceful compaction and a hard GPU crash.

**Two backends, one interface.** ccllrun runs either GGUF files via `llama.cpp` or MLX directories via `mlx_lm.server`, selected by `backend`. GGUF and MLX models are configured separately (`*_gguf` vs `*_mlx`) and only the active backend's settings are validated. The `batch`/`ubatch`/`cache_reuse` knobs are **llama.cpp-only** — `mlx_lm.server` has no such flags (its batch is dynamic and context comes from the model), so on MLX the only context lever is `ctx_small` plus `cc_auto_compact_window`. The proxy also bridges MLX's quirks: it recovers tool calls that the MLX server emits as plain text and avoids streaming tool-parsing that would discard them, so tool use works the same on both backends.

**Documents and vision.** `pdf_mode` decides how `document` blocks reach a text-only local model: `text` extracts text, `image` rasterizes pages, `hybrid` extracts text and only rasterizes when there's too little of it (`CCRUN_PDF_TEXT_MIN`). Images and screenshots work when an `mmproj-*.gguf` projector sits next to the big GGUF — without it, vision input is dropped with a clear message instead of failing.

**Generation quality.** `kv_type` quantizes the KV cache (`q8_0` halves its memory for a negligible quality loss — the default that lets a larger context fit); `reasoning_budget` caps thinking tokens; `presence_penalty` fights repetition but degrades code if pushed too high, so it's exposed for per-model tuning.

**Embeddings and the embedding guard.** Embedding models turn text into vectors instead of generating text — they have no stop token, so if one is set as `big_gguf`/`small_gguf` it never stops generating and spins forever. ccllrun now **detects** an embedding GGUF (via the `<arch>.pooling_type` metadata key) and refuses to start the big/small slot with one, with a clear error instead of a silent loop; the Studio setup doctor flags it too. Embedding models are still useful — semantic search and RAG over standards, datasheets and code — so they get their own opt-in slot: set `embed_gguf` and ccllrun starts a third server, exposed as `/v1/embeddings` through the proxy (a request to that path returns `503` when no embedding model is configured). The benefit: the same mistake that caused the infinite loop now turns into a usable retrieval endpoint, on its own port, without touching chat.

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
- **`exceeds the available context size` / `Context size has been exceeded` / `failed to find a memory slot` in `ccllrun logs big`** → `parallel > 1` splits `ctx_big` across slots: set it back to 1 or raise `ctx_big`.
- **same errors in `ccllrun logs small`** → the small model splits `ctx_small` across `parallel_small` slots (it inherits `parallel` when unset). Set `parallel_small: 1` so each request gets the full `ctx_small`, and/or lower `batch_small`.
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

**Roberto Bissanti** ([roberto.bissanti@gmail.com](mailto:roberto.bissanti@gmail.com)) is an aerospace engineer working in renewable energy, with expertise in integrated multi-source stand-alone systems. ccllrun was born from the practical need to use Claude Code on his own hardware (Mac Studio M1 Ultra), with technical documents, project data and code that never leave the machine.

## Credits and license

- **MIT** license — see [LICENSE](LICENSE).
- Studio's native wrapper (C++ launcher + WKWebView, `studio/native/webview.h`) and the dashboard approach derive from **[DStudio](https://github.com/sk8erboi17/DStudio)** by **Giuseppe Perrotta** (BSD-3-Clause, see `studio/native/LICENSE.DStudio`). Thank you!
- Studio vendors **MathJax 3** for offline SVG rendering of LaTeX math in chat replies.
- Engine: [llama.cpp](https://github.com/ggml-org/llama.cpp) · Agent: [Claude Code](https://docs.anthropic.com/claude-code) · Models: [Qwen](https://huggingface.co/Qwen) quantized by [unsloth](https://huggingface.co/unsloth).
