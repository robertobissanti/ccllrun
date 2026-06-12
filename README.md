# ccllrun

Esegui **Claude Code** su modelli locali serviti da **llama.cpp** (`llama-server`), tramite un proxy che traduce l'API Anthropic in API OpenAI-compatibile.

```
Claude Code ──ANTHROPIC_BASE_URL──▶ proxy.py (:8765) ──┬──▶ llama-server BIG   (:8001, es. Qwen3.6-35B-A3B)
                                                       └──▶ llama-server SMALL (:8002, modello piccolo/veloce)
```

Lo script `ccllrun`:

1. avvia (se non già attivi) i due `llama-server` — un modello "big" per il lavoro principale e un modello "small" per le richieste rapide (`ANTHROPIC_SMALL_FAST_MODEL`);
2. avvia il proxy (`~/.ccllrun/proxy.py`) che converte le richieste Anthropic → OpenAI, instrada le richieste small sul server piccolo e converte i PDF in testo o immagini;
3. lancia `claude` puntato al proxy;
4. all'uscita ferma il proxy (i llama-server restano attivi per i lanci successivi: `ccllrun stop` per fermarli).

## Requisiti

### Software

| Componente | Versione / note | Installazione |
|---|---|---|
| macOS Apple Silicon | testato su Darwin 25 (arm64) | — |
| **llama.cpp** (`llama-server`) | build recente (≥ b9xxx) con supporto Metal; servono i flag `--reasoning-budget`, `--cache-reuse`, `-fa` | `brew install llama.cpp` |
| **Claude Code** (`claude`) | ≥ 2.x | `npm install -g @anthropic-ai/claude-code` oppure installer ufficiale |
| **Python** | ≥ 3.10 con modulo `venv` | `brew install python@3.13` |
| **curl** | qualsiasi (incluso in macOS) | — |

### Moduli Python (proxy)

Installati automaticamente al primo avvio nel venv `~/.ccllrun/venv`:

- `aiohttp` — server/client HTTP asincrono del proxy
- `pymupdf` (fitz) — estrazione testo e rasterizzazione dei PDF (senza, i PDF vengono rimossi dalle richieste)

Inoltre `python3` di sistema viene usato dallo script per leggere il config JSON (solo stdlib).

### File necessari

- `~/.ccllrun/proxy.py` — il proxy (obbligatorio)
- un **GGUF "big"** — es. `Qwen3.6-35B-A3B-UD-Q4_K_XL.gguf` (unsloth)
- *(opzionale)* un **GGUF "small"** — modello piccolo per le richieste rapide
- *(opzionale, per la visione)* il **projector multimodale** `mmproj-*.gguf` nella stessa cartella del GGUF big — necessario per input immagine (screenshot, PDF rasterizzati). Senza, llama-server risponde `image input is not supported`.

### Memoria

Indicativamente per il 35B-A3B Q4_K_XL: ~20 GB di pesi + KV cache (dipende da `ctx_big` e `kv_type`; con `q8_0` a 131k token diversi GB in meno rispetto a `f16`) + ~1-2 GB per l'mmproj + il modello small. Consigliati ≥ 48 GB di memoria unificata per la config di default.

### Impostazioni Claude Code

In `~/.claude/settings.json`:

```json
{ "env": { "CLAUDE_CODE_ATTRIBUTION_HEADER": "0" } }
```

(lo script avvisa se manca).

## Installazione

```bash
chmod +x ccllrun
ln -sf "$PWD/ccllrun" ~/bin/ccllrun        # o altra dir nel PATH
cp config.example.json ~/.ccllrun/config.json   # opzionale
```

Verifica che `~/bin` sia nel PATH (`export PATH="$HOME/bin:$PATH"` nel `.zshrc`) e che non esista una vecchia funzione/alias `ccllrun` nella shell (`type ccllrun` deve indicare il file).

> **Nota:** se lo script vive su un volume esterno/cloud (es. kDrive), il volume deve essere montato al lancio; in alternativa copialo in `~/.ccllrun/`.

## Uso

```bash
ccllrun                         # avvia tutto e apre Claude Code
ccllrun -c "fix the bug"        # gli argomenti non riconosciuti vanno a claude
ccllrun --ctx 131072 --kv f16   # override al volo dei parametri llama-server
ccllrun --no-small              # senza modello piccolo
ccllrun --pdf-mode text         # PDF solo come testo estratto
ccllrun stop                    # ferma i llama-server
ccllrun --help-ccllrun          # aiuto
```

I sottocomandi `claude` puri (`doctor`, `mcp`, `config`, `update`, `--version`, …) vengono passati direttamente senza avviare i server.

## Configurazione

Precedenza (dal più debole al più forte): **default interni → `~/.ccllrun/config.json` → variabili d'ambiente `ccllrun_*` → flag CLI**.

Tutte le chiavi del JSON sono opzionali; i path supportano `~`. Vedi `config.example.json`. Le principali:

| Chiave JSON | Env | CLI | Default | Descrizione |
|---|---|---|---|---|
| `big_gguf` | `ccllrun_GGUF_BIG` | `--big-gguf` | Qwen3.6-35B-A3B Q4_K_XL | modello principale |
| `small_gguf` | `ccllrun_GGUF_SMALL` | `--small-gguf` | history-9b Q4_K_M | modello rapido (`""` per disattivare) |
| `no_small` | — | `--no-small` | `false` | non avviare lo small |
| `ctx_big` | `ccllrun_CTX_BIG` | `--ctx` | 98304 | context del big (totale: viene **diviso per `parallel`**) |
| `ctx_small` | — | — | 32768 | context dello small |
| `kv_type` | `ccllrun_KV_TYPE` | `--kv` | `q8_0` | quantizzazione KV cache (`f16`/`q8_0`/`q4_0`) |
| `ngl` | — | — | 99 | layer offloadati su GPU (99 = tutti) |
| `parallel` | — | `--parallel` | 1 | slot paralleli; >1 dimezza il contesto per richiesta |
| `mmproj` | `ccllrun_MMPROJ` | `--mmproj` | `""` (autodetect) | projector visione; `"off"` per disattivare |
| `pdf_mode` | `ccllrun_PDF_MODE` | `--pdf-mode` | `hybrid` | `text` / `image` / `hybrid` |
| `reasoning_budget` | — | — | 4096 | budget di reasoning token |
| `presence_penalty` | — | — | 1.5 | anti-ripetizione (abbassare a 1.0/0 se il codice esce strano) |
| `batch` | — | — | 2048 | batch size (`-b`/`-ub`) |
| `proxy_port` / `big_port` / `small_port` | `ccllrun_PROXY_PORT` / `ccllrun_BIG_PORT` / `ccllrun_SMALL_PORT` | `--port` (proxy) | 8765 / 8001 / 8002 | porte |
| `model_big` / `model_small` | `ccllrun_MODEL_BIG` / `ccllrun_MODEL_SMALL` | — | `qwen-big` / `small-fast` | alias modelli |
| `llama_bin` | `ccllrun_LLAMA_BIN` | — | `llama-server` | binario llama-server |
| `extra_big_flags` | — | — | `""` | flag extra per il big, es. `"--mlock --kv-unified"` |

Variabili del proxy passabili via env: `CCRUN_PDF_MAX_PAGES` (10), `CCRUN_PDF_DPI` (150), `CCRUN_PDF_TEXT_MIN` (40).

**Dopo ogni modifica ai parametri dei server: `ccllrun stop` e riavvio** — altrimenti il check di salute riusa i server già attivi con i vecchi parametri.

## File e log

```
~/.ccllrun/
├── proxy.py            # proxy Anthropic → OpenAI (obbligatorio)
├── config.json         # configurazione (opzionale)
├── venv/               # creato al primo avvio
├── llama-big.log/.pid
├── llama-small.log/.pid
└── proxy.log
```

## ccllrun Studio (app macOS)

In `studio/` c'è una dashboard web in stile [DStudio](https://github.com/sk8erboi17/DStudio) impacchettata come app nativa:

```bash
cd studio
make run        # costruisce e apre "ccllrun Studio.app"
make serve      # solo server su :8770 (sviluppo / headless)
```

Funzioni: **Stato** (setup doctor con rimedi + salute big/small/proxy + avvia/ferma stack), **Chat** diretta col modello big in streaming (reasoning visibile, tok/s), **Config** (editor di `~/.ccllrun/config.json` con validazione), **Log** live. Il pulsante "Avvia server" usa `ccllrun servers` (nuovo sottocomando: avvia big+small+proxy senza Claude Code); l'engine resta sempre su 127.0.0.1, la pagina parla solo con la dashboard (reverse proxy `/v1`). Per l'accesso LAN: `STUDIO_HOST=0.0.0.0 make serve`.

Requisiti extra: Xcode Command Line Tools (`clang++`). Il wrapper nativo (`studio/native/webview.h`, approccio launcher+WKWebView) deriva da DStudio di Giuseppe Perrotta, BSD-3-Clause — vedi `studio/native/LICENSE.DStudio`.

## Risoluzione problemi

- **`image input is not supported … mmproj`** → manca il projector: scarica `mmproj-*.gguf` nella cartella del GGUF big (autodetect) o indica il path con `mmproj`. Poi `ccllrun stop` e riavvia.
- **`exceeds the available context size`** con contesto dimezzato → `parallel > 1` divide `ctx_big` tra gli slot: riporta `parallel` a 1 o raddoppia `ctx_big`.
- **`qwen-big non pronto`** → guarda `~/.ccllrun/llama-big.log` (spesso: memoria insufficiente → riduci `ctx_big` o usa `kv_type: q8_0`; o path GGUF errato).
- **I PDF arrivano come `[PDF rimosso: PyMuPDF non installato]`** → `~/.ccllrun/venv/bin/pip install pymupdf`.
- **`ccllrun not found` o si comporta come la vecchia funzione** → `unfunction ccllrun; hash -r`, verifica con `type ccllrun`, controlla che la dir del link sia nel PATH.
- **Output ripetitivo o codice degradato** → abbassa `presence_penalty` (1.0 o 0).
