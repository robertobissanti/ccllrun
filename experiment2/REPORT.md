# Esperimento 2 — processo persistente contro `--resume`

## Domanda

Riavviare Claude Code a ogni turno con `--resume` cambia il risultato rispetto a mantenere un unico processo aperto?

## Disegno

- 10 repliche; ogni replica contiene tre turni dipendenti.
- I dati casuali cambiano solo tra repliche (`seed=20260619`). Dentro ogni replica, persistente e resume ricevono gli stessi prompt e valori byte-per-byte.
- Persistente: un solo PID `claude -p --input-format stream-json` per tre turni.
- Resume: tre PID distinti; turni 2 e 3 con `--resume` sul medesimo session ID.
- Stesso binario Claude Code 2.1.142, modello, proxy, ambiente, cwd isolata e argomenti.
- Temperatura 0, reasoning budget 512, effort low.
- Modalità `--bare`; tool, plugin, slash command, MCP, memoria automatica e setting sources disabilitati.
- Nessun accesso a filesystem, rete, clock o output esterno durante l'inferenza.
- Due controlli aggiuntivi sugli stessi dati: persistente ripetuto e resume ripetuto.

Totale: 40 conversazioni da tre turni, 120 inferenze osservate.

## Risultati principali

| Condizione | Turni corretti | Repliche interamente corrette | Tempo medio per 3 turni |
|---|---:|---:|---:|
| Persistente | 26/30 | 8/10 | 18,71 s |
| Persistente ripetuto | 28/30 | 9/10 | 19,20 s |
| Resume | 27/30 | 8/10 | 19,90 s |
| Resume ripetuto | 28/30 | 9/10 | 18,50 s |

## Equivalenza degli output

| Confronto appaiato | Semanticamente identici | Testualmente identici |
|---|---:|---:|
| Persistente vs resume | 27/30 | 26/30 |
| Persistente vs persistente ripetuto | 28/30 | 25/30 |
| Resume vs resume ripetuto | 29/30 | 26/30 |

Le tre differenze semantiche osservate nel confronto persistente-vs-resume sono:

- replica 8, turni 2 e 3: il ramo persistente omette `-20` dall'insieme ordinato;
- replica 9, turno 3: il ramo resume scambia due elementi nella lista invertita.

I controlli mostrano però esattamente le stesse divergenze:

- replica 8, turni 2 e 3 divergono anche tra due esecuzioni persistenti;
- replica 9, turno 3 diverge anche tra due esecuzioni resume.

Non rimane quindi alcuna divergenza osservata che sia specifica del confine di processo o di `--resume`.

## Interpretazione

In questo esperimento controllato, `--resume` ricostruisce uno stato conversazionale funzionalmente equivalente alla sessione mantenuta nello stesso processo. Le differenze viste tra i due rami non superano la variabilità di ripetizione presente dentro ciascuna modalità, nonostante temperatura 0.

Questo corregge la conclusione suggerita dal precedente confronto CLI-vs-Studio: quel benchmark misurava contemporaneamente lifecycle, headless mode, tool, MCP, permessi e orchestrazione. Isolando il solo lifecycle, non emerge un effetto attribuibile alla ripartenza.

La formulazione sostenuta dai dati è:

> Con Claude Code 2.1.142 e nelle condizioni testate, non abbiamo evidenza che riprendere con `--resume` alteri i risultati rispetto a mantenere un unico processo. Le rare differenze osservate sono compatibili con il non-determinismo residuo del backend.

Non è una prova matematica universale: l'esperimento riguarda questo modello, backend, versione e conversazioni senza tool. Sessioni con tool stateful, processi MCP o stato non persistito potrebbero comportarsi diversamente.

## Audit

- `results/runs.jsonl`: coppie principali.
- `results/control_runs.jsonl`: ripetizioni interne alle modalità.
- `results/control_analysis.json`: confronto finale.
- `results/rep_*_prompts.json`: randomizzazione per replica.
- `results/rep_*/`: eventi completi di ogni conversazione.
- `run_experiment.py`, `run_controls.py`, `analyze_controls.py`: codice riproducibile.
- `results_invalid_pilot/`: pilot escluso, che aveva attivato auto-memory/LSP; conservato per trasparenza.
