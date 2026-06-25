<div align="center">

<img src="studio/web/icon.svg" width="120" alt="icona ccllrun Studio">

# ccllrun

**Claude Code su modelli locali. Senza cloud.**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Versione](https://img.shields.io/badge/versione-0.1-d97757)](#ccllrun-studio-app-macos)
[![Platform](https://img.shields.io/badge/platform-macOS%20Apple%20Silicon-black?logo=apple)](#requisiti)
[![100% Local](https://img.shields.io/badge/AI-100%25%20locale-success)](#)
[![Engine](https://img.shields.io/badge/engine-llama.cpp-blue)](https://github.com/ggml-org/llama.cpp)
[![MLX](https://img.shields.io/badge/backend-MLX-5E5CE6)](https://github.com/ml-explore/mlx)
[![Agent](https://img.shields.io/badge/agent-Claude%20Code-d97757)](https://docs.anthropic.com/claude-code)
[![Models](https://img.shields.io/badge/modelli-GGUF%20%C2%B7%20Qwen-purple)](#modelli)

🇬🇧 [Read it in English](README.md)

</div>

`ccllrun` è uno strumento pratico per usare [Claude Code](https://docs.anthropic.com/claude-code) con modelli locali in modo più usabile nella pratica quotidiana: abbastanza veloce, prevedibile, e con i controlli giusti esposti. Non è un nuovo motore di inferenza. Coordina runtime locali esistenti — **llama.cpp** per i modelli GGUF e **MLX** per le cartelle modello MLX — tramite un proxy che traduce le chiamate Anthropic di Claude Code in un'API locale OpenAI-compatibile.

L'obiettivo è semplice: eliminare i colli di bottiglia che rendono lente o fragili le sessioni locali di Claude Code, senza peggiorare la qualità delle risposte. Per riuscirci non basta avviare un modello: bisogna curare routing dei modelli, contesto, slot paralleli, batch e micro-batch di prefill, formato della KV cache, stabilità del prompt-cache, auto-compact, tool call, PDF/immagini, pulizia dei processi e configurazione.

Puoi usarlo da terminale, come Claude Code, oppure con **ccllrun Studio**, un'app macOS nativa che sta alla CLI come Claude Desktop sta a Claude Code: una superficie grafica per chat, stato dello stack, log, permessi e configurazione.

```
Claude Code ──ANTHROPIC_BASE_URL──▶ proxy.py (:8765) ──┬──▶ llama-server LLM GRANDE (:8001, es. Qwen3.6-35B-A3B)
                                                       └──▶ llama-server LLM PICCOLO (:8002, modello piccolo/veloce)
ccllrun Studio (:8770) ─── dashboard nativa: chat headless, stato, config, log
```

Tutto resta sulla tua macchina: di default l'engine ascolta solo su `127.0.0.1`, nessun dato esce.

Versione corrente di Studio: **0.1 (0.1)**. Autore/contatto: **Roberto Bissanti** — [roberto.bissanti@gmail.com](mailto:roberto.bissanti@gmail.com). Licenza: **MIT**.

## Partenza in 30 secondi

```bash
git clone https://github.com/robertobissanti/ccllrun.git
cd ccllrun && chmod +x ccllrun
sudo ln -sf "$PWD/ccllrun" /usr/local/bin/ccllrun
cp config.example.json ~/.ccllrun/config.json   # poi sistema i path dei GGUF
ccllrun                                          # avvia tutto e apre Claude Code
```

Al primo avvio il resto si crea da solo: `~/.ccllrun/`, il venv Python con le dipendenze del proxy, e `proxy.py` dal repo.

## Caratteristiche

- **CLI** (`ccllrun`): avvia LLM grande + LLM piccolo + proxy e apre Claude Code già puntato al modello locale; all'uscita il proxy si ferma e i server dei modelli possono restare caldi per il lancio successivo.
- **Studio** (`ccllrun Studio.app`): app macOS nativa per lo stesso stack: chat, avvio/arresto/riavvio, controlli di salute, log, permessi interattivi e configurazione grafica.
- **Doppio LLM**: un LLM grande per il lavoro vero, un LLM piccolo per le richieste rapide di Claude Code (`ANTHROPIC_SMALL_FAST_MODEL`). Internamente le chiavi di configurazione restano `big` e `small`.
- **Due backend**: `llama.cpp` per file GGUF e `mlx-lm` per cartelle MLX, selezionabili dalla stessa configurazione e dalla stessa UI.
- **Slot embedding/RAG**: un terzo server opzionale espone `/v1/embeddings` tramite il proxy per ricerca semantica su documenti, normative, datasheet o codice.
- **PDF**: il proxy converte i blocchi `document` in testo estratto o pagine rasterizzate (`text`/`image`/`hybrid`).
- **Visione**: con il projector `mmproj-*.gguf` accanto al GGUF, screenshot e immagini funzionano.
- **Context su misura**: la finestra di auto-compact di Claude Code viene allineata al contesto reale del modello (`CLAUDE_CODE_AUTO_COMPACT_WINDOW`), evitando gli out-of-memory su Metal.
- **Proxy consapevole del prompt-cache**: la serializzazione del prompt resta stabile, così llama-server può riusare il prefisso già processato tra un turno e il successivo.

## Requisiti

| Componente | Note | Installazione |
|---|---|---|
| macOS Apple Silicon | testato su Darwin 25 (M1 Ultra) | — |
| **llama.cpp** (`llama-server`) | build recente con Metal; servono `--reasoning-budget`, `--cache-reuse`, `-fa` | `brew install llama.cpp` |
| **Claude Code** (`claude`) | ≥ 2.x | `npm install -g @anthropic-ai/claude-code` |
| **Python** | ≥ 3.10 con `venv` | `brew install python@3.13` |
| Xcode CLT (`clang++`) | solo per compilare Studio | `xcode-select --install` |

I moduli Python del proxy (`aiohttp`, `pymupdf`) vengono installati **automaticamente** al primo avvio in `~/.ccllrun/venv`. Le dipendenze esterne (llama.cpp, Claude Code) non sono inglobate: sono progetti grossi con installer e cicli di rilascio propri — il *setup doctor* di Studio verifica che ci siano e suggerisce il comando di installazione per ciascuna.

Studio include **MathJax 3** localmente (`studio/web/vendor/mathjax/tex-svg.js`) per renderizzare le formule LaTeX nelle risposte della chat. Viene copiato nella `.app` da `make`, servito da `/vendor/...`, e non richiede accesso alla rete a runtime.

In `~/.claude/settings.json` aggiungi (lo script avvisa se manca):

```json
{ "env": { "CLAUDE_CODE_ATTRIBUTION_HEADER": "0" } }
```

### Memoria

Per il 35B-A3B Q4_K_XL: ~20 GB di pesi + KV cache (dipende da `ctx_big` e `kv_type`) + ~2 GB di mmproj + il modello small. Consigliati **≥ 48 GB** di memoria unificata con la config di default; con meno memoria riduci `ctx_big` o scegli un modello più piccolo.

## Modelli

ccllrun non impone un unico modello. Ragiona per ruoli: un **LLM grande** per il lavoro principale di codice/ragionamento, un **LLM piccolo** per le chiamate rapide di Claude Code, e opzionalmente un **modello embedding** per ricerca semantica e RAG. La configurazione sperimentale attuale usa questi modelli.

### GGUF / llama.cpp

| Ruolo | Modello | Chiave config | Link |
|---|---|---|---|
| **LLM grande** | Qwen3.6-35B-A3B, Q4_K_XL, con `mmproj-F32.gguf` per la visione | `big_gguf`, `mmproj` | [unsloth/Qwen3.6-35B-A3B-GGUF](https://huggingface.co/unsloth/Qwen3.6-35B-A3B-GGUF) |
| LLM grande alternativo | Qwen3.6-27B con MTP, utile per esperimenti di speculative decoding | `big_gguf` | [unsloth/Qwen3.6-27B-MTP-GGUF](https://huggingface.co/unsloth/Qwen3.6-27B-MTP-GGUF) |
| **LLM piccolo** | history-9b, Q4_K_M | `small_gguf` | [ghost-actual/Qwen3.6-9B-Heretic-History-Q4_K_M-GGUF](https://huggingface.co/ghost-actual/Qwen3.6-9B-Heretic-History-Q4_K_M-GGUF) |

Scarica i `.gguf` e indica i path in `~/.ccllrun/config.json`. Qualsiasi GGUF chat-instruct può essere usato, ma i default sono tarati su un Qwen grande più un modello piccolo e veloce. Se il nome contiene `MTP`, ccllrun attiva da solo lo speculative decoding.

### MLX

Il supporto MLX è implementato tramite `mlx_lm.server`: il proxy non carica direttamente file MLX. In pratica:

- imposta `"backend": "mlx-lm"`;
- imposta `big_mlx` e `small_mlx` a **cartelle modello**, non a singoli file `.safetensors`;
- tieni disponibili i path GGUF se vuoi tornare a `"backend": "llama.cpp"`;
- ricorda che parametri specifici di llama.cpp come `batch`, `ubatch`, `cache_reuse`, `kv_type` e `ngl` non diventano flag del server MLX.

Il proxy mantiene la stessa API verso Claude Code per entrambi i backend. Gestisce anche una particolarità di MLX: se il modello emette tool call come testo, il proxy prova a recuperarle e restituirle nel formato Anthropic-compatibile atteso da Claude Code.

Modelli usati nella sperimentazione MLX:

| Ruolo | Cartella modello / repo | Chiave config |
|---|---|---|
| **LLM grande** | `lmstudio-community/gemma-4-26B-A4B-it-QAT-MLX-4bit` | `big_mlx` |
| **LLM piccolo** | `lmstudio-community/gemma-4-E2B-it-MLX-4bit` | `small_mlx` |

### Embedding e RAG

ccllrun può avviare un server embedding dedicato oltre ai server LLM grande/piccolo. È separato dalla chat: gli embedding trasformano chunk di testo in vettori, utili per ricerca semantica, recupero documentale e workflow RAG.

| Ruolo | Modello | Chiave config | Link |
|---|---|---|---|
| **Embedding** | Qwen3-Embedding-8B, Q4_K_M | `embed_gguf` | [Qwen/Qwen3-Embedding-8B-GGUF](https://huggingface.co/Qwen/Qwen3-Embedding-8B-GGUF) |

Quando `embed_gguf` è valorizzato, ccllrun avvia un terzo `llama-server` su `embed_port` in modalità embedding, e il proxy lo espone come `/v1/embeddings` usando l'alias `model_embed` (`embed` di default). Questo è il percorso usato per esperimenti RAG su materiale tecnico: normative, datasheet, documenti di progetto e codice.

I modelli embedding sono protetti intenzionalmente: se un GGUF embedding viene configurato per errore come LLM grande o piccolo, ccllrun rifiuta di avviarlo lì. Un embedding non genera normali completamenti chat e può sembrare bloccato in loop.

## Riferimento CLI

```bash
ccllrun [opzioni ccllrun] [argomenti claude...]
```

Tutto ciò che ccllrun non riconosce viene passato a `claude`.

### Sottocomandi

| Comando | Cosa fa |
|---|---|
| `ccllrun` | avvia big + small + proxy (se non già attivi) e apre Claude Code |
| `ccllrun servers` | solo lo stack, senza Claude Code (usato da Studio) |
| `ccllrun stop` | ferma llama-server e proxy (pidfile + fallback sulle porte) |
| `ccllrun logs [big\|small\|proxy]` | segue il log indicato (`tail -f`, default: `big`) |
| `ccllrun --help-ccllrun` | aiuto |
| `ccllrun doctor` / `mcp` / `config` / `update` / `install` / `setup-token` / `--version` / `--help` | passano direttamente a `claude` senza avviare i server |

### Opzioni

| Flag | Descrizione |
|---|---|
| `--config <file>` | usa un config JSON alternativo |
| `--big-gguf <path>` | modello grande |
| `--small-gguf <path>` | modello piccolo (`""` per disattivarlo) |
| `--no-small` | non avviare il modello piccolo |
| `--ctx <n>` | contesto del big (default 98304) |
| `--batch-small <n>` | batch del modello small (default: come il big) |
| `--ubatch <n>` / `--ubatch-small <n>` | micro-batch di prefill (`-ub`, default: = batch); più piccolo = meno memoria di picco nel prefill. Deve essere ≤ batch |
| `--cache-reuse <n>` / `--cache-reuse-small <n>` | gap minimo per riusare la KV cache attorno a un buco (default 256) |
| `--kv <tipo>` | quantizzazione KV cache: `f16` \| `q8_0` \| `q4_0` |
| `--mmproj <path\|off>` | projector visione (default: autodetect accanto al GGUF big) |
| `--parallel <n>` | slot paralleli del big (**divide il contesto per slot**) |
| `--parallel-small <n>` | slot paralleli del small (default: come il big) |
| `--pdf-mode <m>` | `text` \| `image` \| `hybrid` |
| `--port <n>` | porta proxy (default 8765) |
| `--tool-search` / `--no-tool-search` | attiva/disattiva la tool search (scavalca il `settings.json` globale) |

### Osservare i log da un altro terminale

Mentre Claude Code gira, apri altre finestre di terminale per seguire cosa fanno i server:

```bash
ccllrun logs big       # modello principale: caricamento, token/s, errori di memoria
ccllrun logs small     # modello rapido
ccllrun logs proxy     # richieste Anthropic→OpenAI, conversioni PDF, errori 4xx/5xx
```

(equivale a `tail -f ~/.ccllrun/llama-big.log` ecc.; in alternativa c'è la pagina **Log** di Studio, che si aggiorna da sola). Utile in particolare `logs big` al primo avvio — il caricamento del modello può richiedere 1–2 minuti e lì si vede il progresso — e quando qualcosa non risponde: gli out-of-memory Metal e i `failed to parse grammar` compaiono solo lì.

## ccllrun Studio (app macOS)

Studio è il compagno grafico della CLI, nello stesso spirito di Claude Desktop accanto a Claude Code nel terminale. Non sostituisce la CLI: dà allo stesso stack locale una superficie macOS più comoda per l'uso quotidiano.

```bash
cd studio
make run        # compila e apre "ccllrun Studio.app"
make serve      # solo server su :8770 (sviluppo / LAN con STUDIO_HOST=0.0.0.0)
```

All'avvio Studio fa partire da solo lo stack (big + small + proxy), come la CLI; disattivabile con `"studio_autostart": false`.

La pagina Stato è volutamente operativa: se lo stack è vivo solo in parte, o se processi appesi occupano ancora le porte attese, Studio chiede a ccllrun di pulire e riavviare l'intero stack invece di fidarsi di uno stato incoerente. Nell'inferenza locale basta un server rimasto appeso per far sembrare viva la UI mentre Claude Code non può lavorare davvero.

### Compilazione e Gatekeeper (firma del codice)

L'app **non viene distribuita già compilata**: la costruisci tu con `make`. È una scelta voluta — aggira completamente il problema delle firme macOS:

- **Compilata dai sorgenti** (la via supportata): un'app costruita in locale non ha l'attributo di quarantena, e su Apple Silicon il linker applica da solo una firma ad-hoc. Si apre normalmente, senza avvisi.
- **Se la `.app` ti arriva da altrove** (zip, AirDrop, un altro Mac): macOS la mette in quarantena e Gatekeeper dirà che è *"danneggiata o di uno sviluppatore non identificato"*. O la ricompili dai sorgenti (consigliato), o togli la quarantena e ri-firmi ad-hoc:

  ```bash
  xattr -dr com.apple.quarantine "ccllrun Studio.app"
  codesign --force --deep -s - "ccllrun Studio.app"
  ```

- **Per chi volesse distribuire binari**: serve un certificato Apple Developer ID (`codesign -s "Developer ID Application: …"` + notarizzazione con `xcrun notarytool submit`). Fino ad allora, "compila dai sorgenti" è l'unica via senza attriti — e richiede secondi: il wrapper è un singolo piccolo file C++.

> Ricompilare dopo ogni `git pull` è comunque buona pratica: `make` aggiorna anche le copie di `server.py`, `ccllrun` e della web UI incorporate nell'app.

- **Chat** = Claude Code headless nella cartella di progetto che scegli (la prima è il cwd, le altre vanno in `--add-dir`). La conversazione prosegue con `--resume`.
- **Permessi**: selettore per chat (*modifiche file* / *tutto consentito* / *solo piano*). In modalità normale, quando Claude vuole eseguire un comando non coperto compare una **card di approvazione** con il comando esatto: *Consenti* (una volta), *Consenti sempre* (salva la regola, es. `Bash(gcc:*)`, in `.claude/settings.local.json` del progetto), *Nega*.
- **Markdown** nelle risposte (interruttore in Config → Studio); la copia restituisce sempre il markdown originale.
- **Formule LaTeX** nelle risposte tramite MathJax vendorizzato (`$...$`, `$$...$$`, `\(...\)`, `\[...\]`), renderizzate offline come SVG.
- **Comandi slash** con autocompletamento: `/context`, `/memory`, `/compact`, `/cost`, `/init`, più i comandi custom del progetto.
- **Stato**: toggle Avvia/Ferma + Riavvia, card di salute dei server, setup doctor con i rimedi.
- **Config**: editor grafico (o JSON raw) di `~/.ccllrun/config.json`, con sezioni Base/Avanzate, label e tooltip localizzati (`it`, `en`, `es`, `fr`, `de`, `pt`) e unità esplicite per token/slot. La UI usa "LLM grande" e "LLM piccolo", anche se le chiavi interne restano `big` e `small`. Dopo le modifiche ai parametri dei server: Riavvia.
- **Log** live di big/small/proxy.
- **Info** con versione 0.1, email dell'autore, copyright e licenza MIT.

## Configurazione

Precedenza (dal più debole al più forte): **default interni → `~/.ccllrun/config.json` → env `ccllrun_*` → flag CLI**. Tutte le chiavi sono opzionali, i path supportano `~`. Vedi `config.example.json`.

### Tutte le chiavi di configurazione

| Chiave | Env | CLI | Default | Descrizione |
|---|---|---|---|---|
| `big_gguf` | `ccllrun_GGUF_BIG` | `--big-gguf` | Qwen3.6-35B-A3B Q4_K_XL | file del LLM grande |
| `small_gguf` | `ccllrun_GGUF_SMALL` | `--small-gguf` | history-9b Q4_K_M | file del LLM piccolo (`""` per disattivare) |
| `backend` | `ccllrun_BACKEND` | `--backend` | `llama.cpp` | backend runtime (`llama.cpp` per GGUF, `mlx-lm` per cartelle MLX) |
| `big_mlx` | `ccllrun_MLX_BIG` | `--big-mlx` | `""` | cartella MLX del LLM grande |
| `small_mlx` | `ccllrun_MLX_SMALL` | `--small-mlx` | `""` | cartella MLX del LLM piccolo |
| `no_small` | — | `--no-small` | `false` | non avviare il LLM piccolo |
| `model_big` | `ccllrun_MODEL_BIG` | — | `qwen-big` | alias API del LLM grande |
| `model_small` | `ccllrun_MODEL_SMALL` | — | `small-fast` | alias API del LLM piccolo |
| `ctx_big` | `ccllrun_CTX_BIG` | `--ctx` | 98304 | contesto del LLM grande, in token (**diviso per `parallel`**) |
| `ctx_small` | — | — | 32768 | contesto del LLM piccolo, in token (**diviso per `parallel_small`**) |
| `batch` | — | — | 2048 | batch size del big (`-b`) |
| `batch_small` | — | `--batch-small` | `""` (= `batch`) | batch dello small; abbassalo per alleviare la pressione sulla KV cache dello small |
| `ubatch` | — | `--ubatch` | `""` (= `batch`) | micro-batch di prefill del big (`-ub`); abbassalo per ridurre la memoria di picco nel prefill |
| `ubatch_small` | — | `--ubatch-small` | `""` (= `batch_small`) | `-ub` dello small; **deve essere ≤ `batch_small`** (non eredita `ubatch`) |
| `cache_reuse` | — | `--cache-reuse` | 256 | gap minimo per riusare la KV cache attorno a un blocco rimosso/editato; alzalo solo se vedi cache-miss su conversazioni compattate |
| `cache_reuse_small` | — | `--cache-reuse-small` | `""` (= `cache_reuse`) | come sopra, per lo small |
| `kv_type` | `ccllrun_KV_TYPE` | `--kv` | `q8_0` | quantizzazione KV cache (`f16`/`q8_0`/`q4_0`) — `q8_0` dimezza la memoria |
| `ngl` | — | — | 99 | layer su GPU (99 = tutti) |
| `parallel` | — | `--parallel` | 1 | slot paralleli del big (>1 divide il contesto per slot) |
| `parallel_small` | — | `--parallel-small` | `""` (= `parallel`) | slot paralleli dello small; tienilo a 1 così ogni richiesta ha tutto `ctx_small` |
| `reasoning_budget` | — | — | 4096 | token massimi di ragionamento |
| `presence_penalty` | — | — | 1.5 | anti-ripetizione (abbassare se il codice esce degradato) |
| `mmproj` | `ccllrun_MMPROJ` | `--mmproj` | `""` (autodetect) | projector visione; `"off"` per disattivare |
| `pdf_mode` | `ccllrun_PDF_MODE` | `--pdf-mode` | `hybrid` | `text` / `image` / `hybrid` |
| `proxy_port` | `ccllrun_PROXY_PORT` | `--port` | 8765 | porta del proxy |
| `big_port` | `ccllrun_BIG_PORT` | — | 8001 | porta llama-server big |
| `small_port` | `ccllrun_SMALL_PORT` | — | 8002 | porta llama-server small |
| `embed_gguf` | — | — | `""` | GGUF di embedding opzionale; se valorizzato avvia un terzo server che espone `/v1/embeddings` via proxy (ricerca semantica / RAG). Un GGUF non-embedding qui viene solo segnalato, mentre in big/small viene rifiutato |
| `embed_port` | — | — | 8003 | porta llama-server embedding |
| `model_embed` | — | — | `embed` | alias API del modello embedding |
| `llama_bin` | `ccllrun_LLAMA_BIN` | — | `llama-server` | binario llama-server |
| `extra_big_flags` | — | — | `""` | flag extra per il big, es. `"--mlock --kv-unified"` |
| `cc_auto_compact_window` | — | — | 115000 | soglia di auto-compact di Claude Code (tienila **sotto `ctx_big`**) |
| `cc_max_output_tokens` | — | — | 32000 | output massimo di Claude Code |
| `cc_tool_search` | — | — | `false` | attiva la tool search di Claude Code (prefill più veloce con molti server MCP; opzione d'avvio) |
| `studio_markdown` | — | — | `true` | rendering markdown nella chat di Studio |
| `studio_autostart` | — | — | `true` | Studio avvia lo stack all'apertura |
| `studio_lan_enabled` | — | — | `false` | espone Studio sulla LAN al prossimo avvio; usare solo su reti fidate |

Il ragionamento dietro queste manopole — separazione big/small, la distinzione contesto/memoria/cache, la stabilità del prompt-cache e `cc_auto_compact_window` — è spiegato nelle **Note di design** più sotto.

> **Su `cc_tool_search`.** La tool search di Claude Code (`ENABLE_TOOL_SEARCH`) invia solo pochi tool per richiesta e carica gli altri su richiesta: con molti server MCP collegati il prefill diventa molto più veloce. Si attiva da sola solo su un endpoint first-party Anthropic, quindi dietro un proxy va abilitata a mano. Il proxy inoltra i blocchi `tool_reference` su cui la feature si basa, quindi funziona end-to-end. Si comporta come **opzione d'avvio**: nella chat di Studio il valore viene congelato al primo turno di una conversazione (cambiarlo a metà romperebbe le tool call in volo), e ccllrun imposta `ENABLE_TOOL_SEARCH` di conseguenza, scavalcando quanto presente nel `settings.json` globale. Default off — attivala se hai molti server MCP e vuoi un prefill più veloce.

### Note di design — a *cosa serve* ogni gruppo di opzioni

La tabella sopra è un elenco piatto; questa sezione spiega il ragionamento dietro ciascuna famiglia di opzioni, così le si regola con intenzione invece che per tentativi.

**Due LLM, due budget.** Claude Code parla con due endpoint: il *LLM grande* fa il ragionamento e il codice vero, mentre un *LLM piccolo* gestisce le sue chiamate frequenti e usa-e-getta (titoli delle conversazioni, sub-task economiche). Nel codice e nella configurazione si chiamano ancora `big` e `small`, ma nella UI utente vengono mostrati come LLM grande e LLM piccolo per chiarirne il ruolo. Hanno profili di carico molto diversi, perciò hanno **limiti indipendenti**: `ctx`, `batch`, `ubatch`, `parallel` e `cache_reuse` esistono in versione big e `*_small`. Le chiavi `*_small` ricadono sul valore del big quando vuote, così non si rompe nulla se le ignori. *Perché conta:* prima di questa separazione il LLM piccolo ereditava in silenzio le impostazioni del LLM grande — incluso un numero di slot `parallel` che divideva il suo `ctx_small`, già più piccolo, in fette troppo strette per i prompt reali, e questo emergeva come `Context size has been exceeded` in `llama-small.log`. Impostare `parallel_small: 1` dà a ogni richiesta del LLM piccolo tutto il contesto. Il vantaggio è un LLM piccolo che smette di crashare sotto carico, senza sacrificare il throughput del LLM grande.

**Contesto vs. memoria vs. cache — tre manopole indipendenti.** Sembrano simili ma risolvono problemi diversi, e confonderle è la causa tipica di una cattiva taratura:
- `ctx_*` è *quanta conversazione ci sta*. Con `parallel > 1` llama-server lo divide tra gli slot, quindi il contesto effettivo per richiesta è `ctx / parallel`.
- `ubatch` (micro-batch di prefill) è *la memoria di picco durante il prefill*. Abbassarlo scambia un po' di velocità di prefill con un picco di memoria più basso — la leva giusta quando i prompt lunghi causano `failed to find a memory slot`. Deve restare `≤ batch`, ed è per questo che `ubatch_small` ricade su `batch_small` invece di ereditare l'`ubatch` del big.
- `cache_reuse` è *il riuso del prefisso*. È il gap minimo che llama-server tollera per riusare la KV cache attorno a un blocco cambiato a metà conversazione (es. dopo un auto-compact). Migliora la latenza sulle storie editate e ha effetto quasi nullo quando il prefisso è già identico.

**Stabilità del prompt-cache (il guadagno invisibile).** Claude Code è stateless: rimanda l'intero transcript a ogni turno, e llama-server salta il ricalcolo solo del prefisso *identico byte-per-byte*. Il proxy ora rende la storia in forma canonica — le tool call sono serializzate con chiavi ordinate e **senza l'`id` opaco Anthropic** (che cambia tra le richieste e prima rompeva la corrispondenza). *Perché conta:* con un prefisso instabile, ogni turno ri-prefillava l'intero prompt; col fix, un secondo turno misurato è sceso da **~7957 a 17 token riprocessati (~0.2%)**. È latenza pura risparmiata su ogni sessione multi-turno, ed è ciò che rende sensato tarare `cache_reuse`. Vedi `test/PROMPTCACHE.md`.

**Contesto su misura (`cc_auto_compact_window`).** Claude Code assume una finestra da 200k per i modelli non-Anthropic. Un modello locale con contesto più piccolo riempirebbe oltre il limite mandando Metal in out-of-memory. Questa chiave fa compattare la conversazione *prima* del muro — tienila sotto `ctx_big`. È la differenza tra una compattazione graziosa e un crash secco della GPU.

**Due backend, un'unica interfaccia.** ccllrun esegue file GGUF via `llama.cpp` o cartelle MLX via `mlx_lm.server`, scelti con `backend`. I modelli GGUF e MLX si configurano separatamente (`*_gguf` vs `*_mlx`) e vengono validate solo le impostazioni del backend attivo. Le manopole `batch`/`ubatch`/`cache_reuse` sono **solo per llama.cpp** — `mlx_lm.server` non ha questi flag (batch dinamico, contesto dal modello), quindi su MLX l'unica leva sul contesto è `ctx_small` più `cc_auto_compact_window`. Il proxy fa anche da ponte sulle stranezze di MLX: recupera le tool call che il server MLX emette come testo semplice ed evita il parsing in streaming che le scarterebbe, così la tool use funziona allo stesso modo su entrambi i backend.

**Documenti e visione.** `pdf_mode` decide come i blocchi `document` raggiungono un modello locale solo-testo: `text` estrae il testo, `image` rasterizza le pagine, `hybrid` estrae il testo e rasterizza solo quando ce n'è troppo poco (`CCRUN_PDF_TEXT_MIN`). Immagini e screenshot funzionano quando un projector `mmproj-*.gguf` sta accanto al GGUF big — senza, l'input visivo viene scartato con un messaggio chiaro invece di fallire.

**Qualità di generazione.** `kv_type` quantizza la KV cache (`q8_0` ne dimezza la memoria con perdita trascurabile — il default che lascia spazio a un contesto più grande); `reasoning_budget` limita i token di ragionamento; `presence_penalty` combatte la ripetizione ma degrada il codice se spinto troppo, perciò è esposto per la taratura per-modello.

**Embedding e la guardia anti-embedding.** I modelli di embedding trasformano il testo in vettori invece di generare testo — non hanno un token di stop, quindi se ne metti uno come `big_gguf`/`small_gguf` non smette mai di generare e va in loop. ccllrun ora **rileva** un GGUF di embedding (dalla chiave di metadata `<arch>.pooling_type`) e si rifiuta di avviare lo slot big/small con esso, con un errore chiaro invece di un loop silenzioso; anche il setup doctor di Studio lo segnala. I modelli di embedding restano utili — ricerca semantica e RAG su normative, datasheet e codice — perciò hanno uno slot dedicato opt-in: imposta `embed_gguf` e ccllrun avvia un terzo server, esposto come `/v1/embeddings` via proxy (una richiesta a quel path restituisce `503` se nessun modello di embedding è configurato). Il vantaggio: lo stesso errore che causava il loop infinito diventa un endpoint di retrieval utilizzabile, su una porta sua, senza toccare la chat.

### Variabili d'ambiente del proxy

| Variabile | Default | Descrizione |
|---|---|---|
| `CCRUN_PDF_MAX_PAGES` | 10 | pagine massime nella rasterizzazione PDF |
| `CCRUN_PDF_DPI` | 150 | DPI di rasterizzazione |
| `CCRUN_PDF_TEXT_MIN` | 40 | caratteri minimi per tenere il testo estratto in modalità `hybrid` |

### Variabili d'ambiente di Studio

| Variabile | Default | Descrizione |
|---|---|---|
| `STUDIO_PORT` | 8770 | porta della dashboard |
| `STUDIO_HOST` | 127.0.0.1 | host di bind (`0.0.0.0` per l'accesso LAN) |
| `CCLLRUN_BIN` | autodetect | path dello script `ccllrun` |
| `CLAUDE_BIN` | autodetect | path del binario `claude` |

Dopo ogni modifica ai parametri dei server: `ccllrun stop` e riavvio (o Studio → Stato → Riavvia) — altrimenti il check di salute riusa i server attivi con i vecchi parametri.

## File e log

```
~/.ccllrun/                 ← creata automaticamente al primo avvio
├── proxy.py                # installato/aggiornato dal repo
├── config.json             # configurazione (opzionale)
├── venv/                   # creato al primo avvio
├── llama-big.log/.pid
├── llama-small.log/.pid
└── proxy.log
```

## Risoluzione problemi

- **`image input is not supported … mmproj`** → manca il projector: scarica `mmproj-*.gguf` nella cartella del GGUF big. Poi `ccllrun stop` e riavvia.
- **`exceeds the available context size` / `Context size has been exceeded` / `failed to find a memory slot` in `ccllrun logs big`** → `parallel > 1` divide `ctx_big` tra gli slot: riportalo a 1 o aumenta `ctx_big`.
- **stessi errori in `ccllrun logs small`** → lo small divide `ctx_small` tra gli slot `parallel_small` (eredita `parallel` se non impostato). Imposta `parallel_small: 1` così ogni richiesta ha tutto `ctx_small`, e/o abbassa `batch_small`/`ubatch_small`.
- **`qwen-big non pronto`** → guarda `ccllrun logs big` (spesso memoria insufficiente: riduci `ctx_big` o usa `kv_type: q8_0`; oppure path GGUF errato).
- **Errori `kIOGPUCommandBufferCallbackErrorOutOfMemory`** → contesto troppo grande per la memoria: riduci `ctx_big` e tieni `cc_auto_compact_window` sotto di esso.
- **I PDF arrivano come `[PDF rimosso]`** → `~/.ccllrun/venv/bin/pip install pymupdf`.
- **Output ripetitivo o codice degradato** → abbassa `presence_penalty` (1.0 o 0).
- **La UI di Studio sembra vecchia** → sidebar → *Ricarica UI*.

## Roadmap

- [ ] **Download dei modelli da Hugging Face dentro Studio**: ricerca dei GGUF, stima se il modello entra nella memoria della macchina (pesi + KV cache al contesto scelto), download con progresso e aggiornamento automatico della config.
- [ ] Cambio modello al volo senza riavvio dello stack.
- [ ] Supporto Linux (lo stack è già quasi tutto portabile; manca il wrapper nativo di Studio).

## Autore

**Roberto Bissanti** ([roberto.bissanti@gmail.com](mailto:roberto.bissanti@gmail.com)) è un ingegnere aerospaziale che lavora nel settore delle energie rinnovabili, con esperienza specifica nei sistemi stand-alone integrati multifonte. ccllrun nasce dall'esigenza pratica di usare Claude Code su hardware proprio (Mac Studio M1 Ultra), con documenti tecnici, dati di progetto e codice che non lasciano mai la macchina.

## Crediti e licenza

- Licenza **MIT** — vedi [LICENSE](LICENSE).
- Il wrapper nativo di Studio (launcher C++ + WKWebView, `studio/native/webview.h`) e l'impostazione della dashboard derivano da **[DStudio](https://github.com/sk8erboi17/DStudio)** di **Giuseppe Perrotta** (BSD-3-Clause, vedi `studio/native/LICENSE.DStudio`). Grazie!
- Studio include **MathJax 3** per il rendering SVG offline delle formule LaTeX nella chat.
- Motore: [llama.cpp](https://github.com/ggml-org/llama.cpp) · Agente: [Claude Code](https://docs.anthropic.com/claude-code) · Modelli: [Qwen](https://huggingface.co/Qwen) quantizzati da [unsloth](https://huggingface.co/unsloth).
