Il file `solution.py` esiste già con l'implementazione corretta. Tutti i test passano:

- **Esempio prompt**: `[(5,1),(2,4),(10,10),(11,12)]` → `[(1,5),(10,12)]` ✓
- **Lista vuota**: `[]` → `[]` ✓
- **Duplicati**: `[(1,3),(1,3),(2,4)]` → `[(1,4)]` ✓
- **Valori negativi**: `[-5,-2],[-3,0],[10,5]` → `[(-5,0),(5,10)]` ✓
- **Input non modificato**: la lista originale resta intatta ✓

**Spiegazione**: La funzione normalizza ogni coppia con `sorted()`, ordina per inizio, poi fonde in un solo passaggio gli intervalli sovrapposti o adiacenti (`start <= ultimo_end + 1`). Complessità O(n log n) per il sort, O(n) per la fusione. Usa solo libreria standard e non modifica l'input.