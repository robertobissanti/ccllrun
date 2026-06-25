# Test prompt-cache (proxy.py)

Verificano che il rendering dello storico verso il modello resti **byte-stabile**
tra i turni, condizione necessaria perche` llama-server riusi la KV cache
(`--cache-reuse`). Claude Code e` stateless e rimanda l'intero transcript a ogni
turno: se la serializzazione di `tool_use`/`tool_result` cambia byte (id opachi,
ordine chiavi non deterministico), il prefisso diverge e il prompt viene
ri-prefillato da capo.

## 1. Test puri (nessun modello richiesto)

```sh
python3 test/test_proxy_promptcache.py
```

Gira con qualunque Python (stub di aiohttp incluso). Verifica stabilita` del
prefisso, assenza di id `toolu_` nel rendering, JSON canonico dei `tool_result`,
e che il recupero tool-call-as-text (path MLX) accetti sia il formato Anthropic
pieno sia la forma canonica ridotta. **Esegui sempre questo dopo aver toccato
`proxy.py`.**

## 2. Test end-to-end (richiede il modello reale + stack avviato)

```sh
ccllrun servers                         # avvia big+small+proxy
jq --version                            # prerequisito (brew install jq)

./test/e2e_promptcache.sh               # testa il modello big
MODEL_ALIAS=small-fast ./test/e2e_promptcache.sh   # testa lo small
```

Manda due richieste `POST /v1/messages` con lo stesso lungo prefisso (system +
tool_use + tool_result) e solo l'ultima domanda diversa, poi legge da
`~/.ccllrun/llama-*.log` quanti token di *prompt processing* sono stati
riprocessati. **Atteso col fix**: turno 2 << turno 1 (riuso del prefisso).
Senza il fix: turno 2 ~ turno 1 (prefisso instabile, cache inefficace).

> Questo e` il test che misura il *beneficio* reale e va eseguito sulla macchina
> con i pesi caricati; i test puri (#1) verificano solo l'invariante di codice.
