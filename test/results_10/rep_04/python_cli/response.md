File creato. La funzione:

1. **Normalizza** ogni coppia con `sorted()` (garantisce `start <= end`)
2. **Ordina** per inizio, poi fine
3. **Unisce** in un solo passaggio: se l'intervallo corrente si sovrappone o tocca l'ultimo (`start <= ultimo_end + 1`), estende; altrimenti aggiunge un nuovo intervallo

Gestisce correttamente lista vuota, duplicati, valori negativi e coppie invertite.