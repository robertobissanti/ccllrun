File created and verified. Here's how it works:

1. **Normalizza** ogni coppia con `sorted()` per garantire `(min, max)`
2. **Ordina** per inizio, poi fine
3. **Unisce** sovrapposti o adiacenti (`start <= ultimo_end + 1`)
4. Restituisce lista di tuple ordinata

L'input non viene mai modificato: si creano nuove liste e tuple. Gestisce correttamente lista vuota, duplicati e valori negativi.