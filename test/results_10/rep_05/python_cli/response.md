Tutti i test passano. Ecco il riepilogo:

- **Normalizzazione**: `tuple(sorted(pair))` garantisce `(min, max)` anche per coppie invertite.
- **Ordinamento**: `sort()` ordina per start poi end, fondamentale per la fusione lineare.
- **Fusione**: se `start <= prev_end + 1` (sovrapposti o adiacenti), si unisce con `max(prev_end, end)`.
- **Immutabilità**: list comprehension e `sorted()` creano nuovi oggetti, l'input non è mai modificato.
- **Complessità**: O(n log n) per ordinamento, O(n) per fusione. Solo libreria standard.