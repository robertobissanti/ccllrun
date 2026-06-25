# Benchmark Claude Code: CLI vs Studio

Data: 2026-06-18. Modello e stack uguali; `llama-server` avviato con l'ultimo `--temp 0` (il log conferma che, in presenza del default precedente, viene usato l'ultimo valore). Reasoning budget: 7680. Un'esecuzione per caso e modalità, sempre CLI prima di Studio. La configurazione originale è stata ripristinata al termine.

## Risultati

| Test | CLI tempo | Studio tempo | CLI input/output | Studio input/output | Similarità artefatto (sequence/Jaccard) | Accuratezza CLI | Accuratezza Studio |
|---|---:|---:|---:|---:|---:|---|---|
| Poesia | 208.33 s | 51.54 s | 18,309 / 8,358 | 18,984 / 1,463 | 17.83% / 25.24% | 4/5 vincoli | 4/5 vincoli |
| Python | 38.95 s | 43.77 s | 18,952 / 710 | 19,218 / 1,119 | 95.82% / 88.68% | PASS | PASS |
| C | 52.22 s | 170.58 s | 19,478 / 1,213 | 24,625 / 6,461 | 16.72% / 36.49% | FAIL | PASS |

Medie: CLI 99.83 s, Studio 88.63 s. Queste medie non dimostrano che Studio sia più veloce: poesia CLI e C Studio hanno consumato quasi tutto il reasoning budget e dominano il dato.

I conteggi sopra sono quelli dichiarati da Claude Code. Cache-read separata: poesia 18,017/54,724; Python 55,185/73,950; C 74,742/271,940 (CLI/Studio). Non va sommata automaticamente a input+output come se fosse nuovo consumo fatturabile.

## Accuratezza

- Poesia: entrambi rispettano titolo, 12 versi, una occorrenza di `silicio` e due di `luna`; entrambi hanno versi con 5 parole, sotto il minimo 6. Il punteggio formale è quindi 4/5. La qualità estetica non è misurabile oggettivamente con questo singolo test.
- Python: entrambe le implementazioni superano tutti i test su normalizzazione, adiacenza, duplicati, negativi, immutabilità dell'input e tipo tuple. I file sono quasi identici; cambiano essenzialmente commenti.
- C: Studio supera compilazione rigorosa e 12 casi. CLI fallisce già sugli spazi ASCII intorno a `-42`; usa `isspace`, ma il calcolo dell'underflow è errato. Studio è corretto sui casi richiesti.

## Interpretazione

Temperatura 0 non rende equivalenti CLI e Studio. Nel test Python converge quasi allo stesso codice; poesia e C divergono nettamente. La causa osservabile non è solo il campionamento: Claude Code compie tool call e cicli di ragionamento diversi, con quantità di output molto differenti.

Questo è un benchmark esplorativo, non una misura statistica: un solo campione, ordine fisso e prompt-cache condivisa. Per affermare differenze prestazionali servono almeno 10 ripetizioni per cella, ordine randomizzato o alternato, cache controllata e intervalli di confidenza.

## Artefatti verificabili

- `results/*_comparison.json`: metriche complete.
- `results/*/raw.ndjson`: eventi originali Claude Code e usage.
- `results/*/response.md`: risposta finale.
- `results/python_*/solution.py`, `results/c_*/solution.c`: codice prodotto.
- `check_python.py`, `check_c.c`: test indipendenti usati per l'accuratezza.
