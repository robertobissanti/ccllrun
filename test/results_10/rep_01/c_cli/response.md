`parse_int32` è stata scritta in `solution.c`. Ecco come funziona:

1. **Scarta gli spazi** iniziali con `isspace()`.
2. **Rifiuta stringa vuota** o solo-spazi controllando `'\0'` subito dopo lo skip.
3. **Legge il segno** (`-` o `+`), default positivo.
4. **Accumula le cifre** con overflow guard: prima di `acc = acc*10 + digit` confronta `acc` con `limit/10` (dove `limit` è `INT32_MAX` o `INT32_MIN`). Questo evita overflow senza undefined behavior.
5. **Rifiuta caratteri extra**: dopo le cifre, solo spazi bianchi o `'\0'` sono accettati.
6. Restituisce `1` su successo, `0` altrimenti; su errore `*out` non viene modificato.