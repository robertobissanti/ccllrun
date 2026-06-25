# Benchmark randomizzato CLI vs Studio — 10 repliche

## Disegno sperimentale

- 3 compiti × 2 modalità × 10 repliche = 60 esecuzioni valide.
- Ordine completamente randomizzato con seed riproducibile `20260618`.
- Directory indipendente per ogni esecuzione; stesso modello, proxy, configurazione e macchina.
- Temperatura `0`; reasoning budget `1024`; tool search attiva; permessi bypass per eliminare attese umane.
- Stack avviato una sola volta prima delle misure. Timeout censurante a 180 s, contato come fallimento.
- Tempo wall-clock misurato attorno all'intera chiamata Claude Code.
- Accuratezza: vincoli formali per la poesia, test automatici indipendenti per Python e C.
- IC delle medie: t di Student 95% con n=10. Confronti appaiati Studio−CLI: test esatto a permutazione dei segni, bilaterale. Successi: IC Wilson 95% e McNemar esatto appaiato.

## Tempi

| Test | CLI media (IC95%) | Studio media (IC95%) | Differenza Studio−CLI (IC95%) | p esatto |
|---|---:|---:|---:|---:|
| Poesia | 44,24 s (39,32–49,16) | 53,59 s (42,06–65,12) | +9,35 s (−4,16–22,86) | 0,162 |
| Python | 37,24 s (30,62–43,86) | 41,95 s (38,45–45,45) | +4,72 s (−3,27–12,70) | 0,223 |
| C | 101,22 s (65,83–136,61) | 90,24 s (62,68–117,80) | −10,98 s (−64,60–42,64) | 0,645 |

Nessuna differenza temporale è statisticamente significativa a α=0,05. Un campione C CLI ha raggiunto il timeout di 180 s; nessun timeout Studio.

## Token medi dichiarati da Claude Code

| Test | CLI input/output | Studio input/output | Δ input (p) | Δ output (p) |
|---|---:|---:|---:|---:|
| Poesia | 18.303 / 954 | 18.628 / 1.558 | +324 (0,260) | +604 (0,041) |
| Python | 18.746 / 577 | 19.134 / 951 | +389 (0,082) | +374 (0,023) |
| C | 18.574 / 2.620 | 20.658 / 3.030 | +2.085 (0,398) | +410 (0,637) |

Studio ha prodotto significativamente più output token nei test poesia e Python in questo campione. Input token e caso C non mostrano differenze significative. I cache-read sono conservati nei dati grezzi ma non sommati agli input come nuovo consumo.

## Accuratezza

| Test | CLI successi | Studio successi | IC95% CLI | IC95% Studio | McNemar p |
|---|---:|---:|---:|---:|---:|
| Poesia | 4/10 | 6/10 | 16,8–68,7% | 31,3–83,2% | 0,625 |
| Python | 10/10 | 10/10 | 72,2–100% | 72,2–100% | 1,000 |
| C | 3/10 | 6/10 | 10,8–60,3% | 31,3–83,2% | 0,375 |

Studio mostra percentuali puntuali migliori per poesia e C, ma con 10 coppie la differenza non è statisticamente significativa. Python è equivalente sul test funzionale: 20/20 implementazioni corrette.

## Similarità media degli artefatti appaiati

| Test | Sequence ratio | Jaccard parole |
|---|---:|---:|
| Poesia | 13,0% | 25,6% |
| Python | 63,3% | 72,0% |
| C | 33,1% | 45,3% |

Temperatura zero non rende identici gli artefatti. La convergenza è maggiore nel compito Python, più vincolato e semplice; poesia e C divergono fortemente.

## Conclusione

Con questi dati non si può sostenere che CLI e Studio differiscano sistematicamente per velocità o accuratezza. Si può invece respingere l'ipotesi pratica che producano risultati identici: gli artefatti hanno similarità limitata e Studio usa più output token in due compiti su tre. Le due modalità sono funzionalmente comparabili, ma non esecuzioni equivalenti bit-per-bit o deterministicamente intercambiabili.

Il campione resta piccolo per rilevare differenze moderate di accuratezza. Per una potenza maggiore servirebbero almeno 30–50 repliche per compito, più prompt per ciascuna categoria e controllo separato della prompt cache.

## Riproducibilità

- `results_10/schedule.json`: ordine randomizzato.
- `results_10/runs.jsonl`: tutte le misure e gli esiti.
- `results_10/analysis.json`: statistiche strutturate.
- `results_10/rep_*/`: output NDJSON, risposte e artefatti.
- `run_benchmark_10.py`: runner con lock e timeout.
- `analyze_benchmark_10.py`: analisi statistica.

Il primo tentativo concorrente, escluso integralmente dall'analisi, è conservato in `results_10_contaminated_20260618_2233/` per audit.
