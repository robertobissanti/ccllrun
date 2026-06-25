`solution.c` creata. Ecco la spiegazione:

**Come funziona:**
1. Salta gli spazi iniziali con `isspace()`. Rifiuta stringa vuota o solo-spazi.
2. Legge un segno opzionale (`+`/`-`), default positivo.
3. Accumula le cifre in un `uint32_t` per evitare undefined behavior da overflow signed.
4. Prima di ogni moltiplicazione+aggiunta, controlla se si supera `INT32_MAX` (soglia `214748364|4` per positivo, `214748364|8` per negativo).
5. Gli spazi finali sono permessi solo se seguiti da altro whitespace o EOF; qualsiasi altro carattere dopo whitespace causa rifiuto.
6. Caratteri non-digit, overflow, underflow e stringhe vuote restituiscono `0` senza modificare `*out`.