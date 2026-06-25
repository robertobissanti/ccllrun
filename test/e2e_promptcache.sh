#!/usr/bin/env bash
# =============================================================================
# Test END-TO-END del prompt-cache con MODELLO REALE.  (per Codex / esecuzione
# locale: richiede i pesi configurati in ~/.ccllrun/config.json e i binari.)
#
# COSA VERIFICA
#   Claude Code e' stateless: rimanda l'intero transcript a ogni turno.
#   llama-server riusa la KV cache solo per il prefisso byte-identico
#   (--cache-reuse). Il fix in proxy.py rende la serializzazione dello storico
#   (tool_use/tool_result) canonica e senza id opachi, cosi' il prefisso resta
#   stabile tra i turni e il prompt processing del 2o turno riprocessa SOLO il
#   suffisso nuovo invece dell'intero prompt.
#
# SEGNALE MISURATO (dai log di llama-server, formato che produce gia':)
#   "slot print_timing: ... prompt processing, n_tokens = N, progress = ..."
#   - turno 1 (cache fredda): N grande  (prefilla quasi tutto)
#   - turno 2 (stesso prefisso + poco suffisso): N piccolo  => CACHE HIT
#   Atteso col fix: n_tokens(turno2) << n_tokens(turno1).
#   Senza il fix (id/ordine instabili): n_tokens(turno2) ~ n_tokens(turno1).
#
# COME ESEGUIRE
#   ./test/e2e_promptcache.sh            # usa il modello BIG di default
#   MODEL_ALIAS=small-fast ./test/e2e_promptcache.sh   # testa lo small
#
# Esce 0 se il 2o turno mostra riuso del prefisso, 1 altrimenti.
# =============================================================================
set -uo pipefail

CC_DIR="${CC_DIR:-$HOME/.ccllrun}"
PROXY_PORT="${PROXY_PORT:-8765}"
MODEL_ALIAS="${MODEL_ALIAS:-qwen-big}"      # qwen-big | small-fast (o i tuoi alias)
LOG="$CC_DIR/llama-big.log"
[[ "$MODEL_ALIAS" == *small* ]] && LOG="$CC_DIR/llama-small.log"
BASE="http://127.0.0.1:$PROXY_PORT"
RUN_ID="${RUN_ID:-$(date +%s)-$$}"
LONG_PREFIX="$(
  i=0
  while [[ "$i" -lt 200 ]]; do
    printf 'prefisso-stabile-%s blocco-%03d: alpha beta gamma delta epsilon zeta eta theta iota kappa. ' "$RUN_ID" "$i"
    i=$((i + 1))
  done
)"

say() { printf '\n=== %s ===\n' "$*"; }
fail() { echo "FAIL: $*" >&2; exit 1; }

# --- prerequisiti -----------------------------------------------------------
command -v curl >/dev/null || fail "curl mancante"
command -v jq   >/dev/null || fail "jq mancante (brew install jq)"
[[ -f "$LOG" ]] || fail "log non trovato: $LOG — lo stack e' avviato? (ccllrun servers)"

if [[ "$(curl -s -o /dev/null -w '%{http_code}' "$BASE/v1/models")" != "200" ]]; then
  fail "proxy non raggiungibile su $BASE — avvia: ccllrun servers"
fi

# Conta i token di prompt-processing comparsi DOPO una certa riga del log.
# Somma gli n_tokens di tutte le righe "prompt processing" recenti.
prompt_tokens_since() {  # <byte_offset>
  local off
  off=$(printf '%s' "$1" | tr -d '[:space:]')
  tail -c "+$off" "$LOG" \
    | awk '
        /prompt eval time =/ {
          for (i = 1; i <= NF; i++) {
            if ($i == "/" && $(i + 1) ~ /^[0-9]+$/) final = $(i + 1)
          }
        }
        /prompt processing, n_tokens =/ {
          for (i = 1; i <= NF; i++) {
            if ($i == "=" && $(i + 1) ~ /^[0-9]+$/) progress = $(i + 1)
          }
        }
        END {
          if (final != "") print final + 0
          else if (progress != "") print progress + 0
          else print 0
        }'
}

# Payload Anthropic /v1/messages con uno storico che contiene una tool call +
# tool_result (il caso che il fix stabilizza). Il 2o turno aggiunge solo una
# breve domanda in coda: stesso prefisso lungo, suffisso minimo.
mk_payload() {  # <suffix_user_text>
  jq -n --arg model "$MODEL_ALIAS" --arg run_id "$RUN_ID" --arg prefix "$LONG_PREFIX" --arg suffix "$1" '
  {
    model: $model, max_tokens: 64, stream: false,
    system: ("Sei un assistente di test. Rispondi brevissimo. run_id=" + $run_id),
    messages: [
      { role:"user", content:[{type:"text", text:$prefix}] },
      { role:"assistant", content:[{type:"text", text:"Prefisso ricevuto."}] },
      { role:"user", content:[{type:"text", text:"Elenca i file."}] },
      { role:"assistant", content:[
          {type:"text", text:"Eseguo."},
          {type:"tool_use", id:"toolu_fixed_001", name:"Bash",
           input:{command:"ls -la", timeout:5}} ] },
      { role:"user", content:[
          {type:"tool_result", tool_use_id:"toolu_fixed_001",
           content:[{type:"text", text:"a.txt\nb.txt\nc.txt"}]} ] },
      { role:"assistant", content:[{type:"text", text:"Ci sono 3 file."}] },
      { role:"user", content:[{type:"text", text:$suffix}] }
    ]
  }'
}

# --- TURNO 1: cache fredda --------------------------------------------------
say "Turno 1 (cache fredda)"
OFF1=$(wc -c < "$LOG")
curl -s "$BASE/v1/messages" -H 'content-type: application/json' \
  -d "$(mk_payload 'Qual e il primo file?')" >/dev/null || fail "richiesta 1 fallita"
sleep 2
N1=$(prompt_tokens_since "$OFF1")
echo "prompt tokens processati (turno 1): $N1"
[[ "$N1" -gt 0 ]] || fail "nessun prompt processing registrato nel log (turno 1)"

# --- TURNO 2: stesso prefisso, suffisso diverso -----------------------------
# Cambia SOLO l'ultima domanda. Il lungo prefisso (system + tool_use +
# tool_result) e' identico byte-per-byte SE il fix e' attivo.
say "Turno 2 (stesso prefisso, suffisso nuovo)"
OFF2=$(wc -c < "$LOG")
curl -s "$BASE/v1/messages" -H 'content-type: application/json' \
  -d "$(mk_payload 'E qual e lultimo file?')" >/dev/null || fail "richiesta 2 fallita"
sleep 2
N2=$(prompt_tokens_since "$OFF2")
echo "prompt tokens processati (turno 2): $N2"

# --- verdetto ---------------------------------------------------------------
say "Verdetto"
echo "turno1=$N1  turno2=$N2"
# Atteso: il turno 2 riprocessa una frazione del turno 1 (riuso del prefisso).
# Soglia prudente: < 60%. Con cache pienamente efficace e' tipicamente < 10%.
THRESHOLD=$(( N1 * 60 / 100 ))
if [[ "$N2" -lt "$THRESHOLD" && "$N2" -gt 0 ]]; then
  echo "PASS: il turno 2 ha riusato il prefisso (n2 < 60% di n1) — prompt-cache efficace."
  exit 0
elif [[ "$N2" -eq 0 ]]; then
  echo "PASS (riuso totale): nessun prompt processing al turno 2 — prefisso interamente in cache."
  exit 0
else
  echo "FAIL: il turno 2 ha riprocessato ~tutto il prompt (n2=$N2 >= 60% di n1=$N1)."
  echo "      -> il prefisso NON e' stabile: cache-reuse inefficace."
  echo "      Controlla che proxy.py renda tool_use/tool_result in forma canonica"
  echo "      e senza id opachi (vedi test/test_proxy_promptcache.py)."
  exit 1
fi
