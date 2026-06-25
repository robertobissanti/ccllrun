File creato. La funzione:

1. **Normalizza** ogni coppia con `sorted()` (gestisce `(5,1)` → `(1,5)`)
2. **Ordina** per estremo sinistro
3. **Unisce** se `start <= ultimo_end + 1` (sovrapposti o adiacenti)
4. Restituisce lista di tuple ordinata

Gestisce lista vuota (ritorna `[]`), duplicati (fusi naturalmente), negativi e non modifica l'input originale.