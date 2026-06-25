# Esempi: leggere documenti coi modelli locali

Due approcci, due casi d'uso diversi. **Spesso ti serve il primo, non il secondo.**

## 1. Leggere i PDF di una cartella progetto — *senza RAG*

```sh
./examples/1_leggi_pdf_progetto.sh /percorso/progetto "la tua domanda"
```

Claude Code apre i PDF coi suoi tool; il proxy li converte secondo `pdf_mode`.
Il modello vede i documenti **interi**. Nessuna pre-indicizzazione: aggiungi un
file e c'è subito. È l'approccio giusto per una cartella di progetto (decine di
file): più semplice e di solito più accurato del RAG su corpus piccoli.

## 2. RAG su un corpus grande e stabile — *con embedding*

```sh
# TEMPO 1 — indicizzazione (offline, una volta):
~/.ccllrun/venv/bin/python examples/2_rag_normative.py index /percorso/normative
# TEMPO 2 — query (runtime):
~/.ccllrun/venv/bin/python examples/2_rag_normative.py query "protezione di interfaccia CEI 0-21"
```

Il RAG ha **due tempi**: prima estrai+vettorizzi tutti i documenti e li salvi su
disco (lo fai tu, non il modello); poi a runtime vettorizzi la domanda, trovi i
chunk più simili (matematica, non LLM) e li passi al modello **big** che
risponde. L'embedding model produce solo vettori, non risponde.

**Richiede** `embed_gguf` configurato in `~/.ccllrun/config.json` (es. un
Qwen3-Embedding) e lo stack riavviato (`ccllrun stop && ccllrun servers`).
Senza, gli script escono con un messaggio chiaro.

Conviene solo quando il corpus è **troppo grande** per il contesto e **stabile**
(normative, manuali, centinaia di datasheet). Per una singola cartella di
progetto, usa l'esempio 1.
