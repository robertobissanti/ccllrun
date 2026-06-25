Tutti i test passano. La funzione:

1. **Normalizza** ogni coppia con `sorted()` (gestisce `(5,1)` → `(1,5)`)
2. **Ordina** per estremo sinistro
3. **Unisce** se `start <= prev_end + 1` (sovrapposizione o adiacenza)
4. Restituisce tuple, non modifica l'input, gestisce vuoti, duplicati e negativi.