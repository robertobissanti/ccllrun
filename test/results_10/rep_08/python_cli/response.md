`solution.py` creata e verificata. La funzione:

1. **Normalizza** ogni coppia con `sorted()` per garantire `(min, max)`
2. **Deduplica** mantenendo l'ordine
3. **Ordina** per estremo sinistro
4. **Unisce** intervalli sovrappesi o adiacenti (`start <= last_end + 1`) in un unico passaggio lineare

Restituisce una lista di tuple. Gestisce correttamente lista vuota, duplicati, valori negativi e coppie invertite. Usa solo libreria standard.