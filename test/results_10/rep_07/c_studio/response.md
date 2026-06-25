Ecco la funzione implementata in `solution.c`.

**Spiegazione (≤60 parole):**

Scarta spazi iniziali/finali con `isspace`, legge un segno opzionale (`-`/`+`), poi accumula cifre con `isdigit`. Verifica overflow *prima* di moltiplicare e sommare, confrontando con `INT32_MAX` (o il limite negativo per il range completo a 32-bit). Rifiuta stringhe vuote, caratteri non-diga dopo il numero, e qualsiasi carattere extra non-spazio. Restituisce 1 solo se tutto è valido, scrivendo `*out` solo in quel caso.