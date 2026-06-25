File creato. La funzione:

1. **Normalizza** ogni coppia `(a, b)` in `(min, max)` senza modificare l'input originale.
2. **Ordina** gli intervalli per punto di partenza.
3. **Unisce** in un solo passaggio: se l'intervallo corrente si sovrappone o tocca l'ultimo (`start <= last_end + 1`), estende il massimo; altrimenti aggiunge un nuovo intervallo.

Gestisce correttamente lista vuota, duplicati, valori negativi e adiacenza (es. `(1,3)` e `(4,6)` diventano `(1,6)`).