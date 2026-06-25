File creato. La funzione:

1. **Normalizza** ogni coppia con `sorted()` (trasforma `(5,1)` in `(1,5)`)
2. **Deduplica** mantenendo l'ordine originale
3. **Ordina** per inizio, poi fine
4. **Unisce** intervalli sovrappesi o adiacenti (`start <= fine_precedente + 1`)

Gestisce lista vuota (ritorna `[]`), duplicati, valori negativi e coppie invertite. Complessità: O(n log n) per il sort.