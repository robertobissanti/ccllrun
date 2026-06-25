Compilato senza warning. Ecco la funzione in `solution.c`.

**Spiegazione (60 parole):**

La funzione scarta spazi iniziali/finali, gestisce un segno opzionale e accumula le cifre in un `int64_t` per evitare overflow durante la lettura. Dopo aver verificato che non ci siano caratteri extra, controlla che il valore rientri in `[INT32_MIN, INT32_MAX]` e scrive in `*out` solo se tutto è valido, restituendo 1 o 0.