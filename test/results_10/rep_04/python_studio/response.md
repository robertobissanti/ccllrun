`solution.py` creato e verificato. Ecco il riepilogo dei test:

| Input | Output |
|---|---|
| `[(5,1),(2,4),(10,10),(11,12)]` | `[(1,5),(10,12)]` ✓ |
| `[]` | `[]` ✓ |
| `[(1,1),(1,1),(1,1)]` | `[(1,1)]` ✓ |
| `[(-5,-2),(-3,0),(4,6)]` | `[(-5,0),(4,6)]` ✓ |
| `[(3,1),(7,2)]` | `[(1,7)]` ✓ |

**Spiegazione (max 60 parole):**

La funzione normalizza ogni coppia con `sorted()` garantendo `(min, max)`, poi ordina gli intervalli per inizio. Scansiona in ordine: se l'inizio corrente è ≤ fine precedente + 1, sovrapposizione o adiacenza → estende l'ultimo intervallo con `max()`. Altrimenti aggiunge un nuovo intervallo. Non modifica l'input, gestisce negativi, duplicati e lista vuota, usa solo libreria standard. Complessità: O(n log n) per il sort.