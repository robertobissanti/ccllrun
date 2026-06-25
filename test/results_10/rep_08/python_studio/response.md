Tutti i test passano. Ecco il riepilogo:

| Caso | Risultato |
|---|---|
| `[(5,1),(2,4),(10,10),(11,12)]` | `[(1,5),(10,12)]` |
| Lista vuota | `[]` |
| Duplicati | `[(1,2)]` |
| Valori negativi | `[-5,0),(4,6)]` |
| Entrambi invertiti | `[(1,7)]` |
| Adiacenti | `[(1,10)]` |
| Con gap | `[(1,5),(7,10)]` |

**Spiegazione (≤60 parole):**

La funzione normalizza ogni coppia con `sorted()` per garantire `(min, max)`, poi ordina per inizio. Scansiona in ordine: se l'intervallo corrente si sovrappone o è adiacente all'ultimo (`start ≤ last_end + 1`), unisce estendendo `end`; altrimenti aggiunge un nuovo intervallo. L'input non viene mai modificato grazie alla lista comprehension. Complessità: O(n log n) per l'ordinamento.