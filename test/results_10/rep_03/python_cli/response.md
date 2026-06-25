La funzione:

1. **Normalizza** ogni coppia con `min/max` per gestire coppie invertite come `(5,1)`.
2. **Ordina** gli intervalli per punto di partenza.
3. **Unisce** iterativamente: se un intervallo si sovrappone o è adiacente (`start <= prev_end + 1`) al precedente, estende il massimo; altrimenti crea un nuovo intervallo.
4. **Non modifica** l'input (usa una generatore, non mutazione).
5. Gestisce correttamente lista vuota, duplicati e valori negativi.

Esempio: `[(5,1),(2,4),(10,10),(11,12)]` → normalizzati `[(1,5),(2,4),(10,10),(11,12)]` → ordinati → `(1,5)` assorbe `(2,4)`, `(10,10)` e `(11,12)` sono adiacenti → `[(1,5),(10,12)]`.