File creato. La funzione:

1. **Normalizza** ogni coppia con `sorted()` (gestisce `(5,1)` → `(1,5)`)
2. **Ordina** per estremo sinistro
3. **Unisce** sovrapposti o adiacenti (`start <= prev_end + 1`)
4. **Restituisce** lista di tuple senza mutare l'input

Gestisce lista vuota, duplicati (fusi naturalmente), negativi e valori singoli come `(10,10)`.