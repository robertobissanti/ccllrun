File creato e testato con successo. Ecco i risultati:

- `[(5,1),(2,4),(10,10),(11,12)]` → `[(1,5),(10,12)]` ✓
- Lista vuota → `[]` ✓
- Duplicati → `[(1,4)]` ✓
- Valori negativi → `[-5,3]` ✓
- Singoli non adiacenti → `[(1,1),(3,3)]` ✓

**Spiegazione:** La funzione normalizza ogni coppia con `min/max`, ordina per inizio, poi scansiona unione gli intervalli sovrapposti o adiacenti (confine `start <= prev_end + 1`). Restituisce tuple ordinate, senza mutare l'input. Complessità: O(n log n) per l'ordinamento.