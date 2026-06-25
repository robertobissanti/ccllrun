Funziona correttamente su tutti i casi. Ecco la spiegazione:

La funzione normalizza ogni coppia in `(min, max)`, ordina per inizio, poi scansiona unione gli intervalli sovrapposti o adiacenti (`start <= prev_end + 1`). Restituisce tuple ordinate, gestisce input vuoto, duplicati e negativi senza mutare l'originale.