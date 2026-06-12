# ccllrun — Riflessioni sul progetto

## Cos'è

ccllrun permette di eseguire **Claude Code** su modelli open locali (Qwen3.6-35B-A3B + Qwen3.6-9B) tramite `llama.cpp`, con un proxy che traduce l'API Anthropic in API OpenAI-compatibile.

```
Claude Code → proxy (:8765) → llama-server BIG (:8001) + SMALL (:8002)
```

## Architettura

| Componente | Ruolo |
|---|---|
| `ccllrun` (shell) | Launcher: avvia server, proxy, lancia `claude`, gestisce stop |
| `~/.ccllrun/proxy.py` | Proxy Anthropic→OpenAI, instradamento big/small, gestione PDF |
| `studio/server.py` | Server web aiohttp per la dashboard |
| `studio/native/app.cc` | Wrapper C++ WKWebView per app macOS nativa |
| `studio/web/index.html` | Single-page UI (chat, stato, config, log) |
| `config.json` | Configurazione: path GGUF, context, kv_type, porte |

## Punti di forza

1. **La chat è Claude Code vero** — ogni messaggio esegue `claude -p --output-format stream-json` come subprocess. Non è un surrogato: ha gli stessi tool, stessi permessi, stessa logica.
2. **Separazione delle responsabilità pulita** — launcher → proxy → server. Ogni componente ha un ruolo chiaro.
3. **Doctor system** — verifica automatica dei requisiti con hint per risolverli.
4. **Security-by-design** — l'engine resta su 127.0.0.1, la UI fa reverse proxy. Il proxy filtra gli headers. CSRF protection base su `X-Requested-With`.
5. **Streaming** — la chat usa `StreamResponse` con NDJSON, il log legge solo gli ultimi 256KB.
6. **Config gerarchica** — default → JSON → env → CLI. Precedenza chiara.
7. **Documentazione** del README completa e ben strutturata.

## Problemi

### Critici
- **proxy.py non è nel repo** — il cuore della traduzione Anthropic→OpenAI manca. Il progetto è incompleto se clonato pulito.
- **Race condition in `api_claude`** (linee 290-293) — dopo `proc.wait()`, `proc.stderr.read()` è già chiuso. L'errore post-wait raramente funziona.

### Significativi
- **`api_start` blocca la response** — `ccllrun servers` torna subito ma il big ci mette 1-2 minuti per caricare. L'utente vede "fatto" ma il modello non è pronto.
- **Nessuna protezione contro chiamate multiple** a `/api/claude` — la UI può lanciare 10 processi `claude` simultanei.
- **AppleScript escaping parziale** in `api_launch` — gestisce `\` e `"` ma non `'` o `$`. Path con caratteri speciali rompono il comando.
- **`pid_alive` fragile** — se il PID è stato riutilizzato dal sistema, dice "alive" falsamente.

### Minori
- `load_config` chiamata ad ogni richiesta senza caching.
- Path hardcoded nel `config.example.json` non portabili.
- `api_claude` non controlla se `proc.stdin` è None prima di scrivere.

## Valutazione complessiva

Progetto ben ingegnerizzato per uso personale di uno studio professionale. L'approccio "Claude Code headless dalla UI" è intelligente e la separazione delle responsabilità è pulita. Il punto debole principale è che il proxy core non è nel repo, rendendo il progetto incompleto. I problemi di concorrenza e race condition sono gestibili ma andrebbero risolti prima di un uso più ampio.

**Requisiti:** macOS Apple Silicon, 48 GB RAM consigliati, `llama.cpp` con Metal, Claude Code, Python 3.10+.
