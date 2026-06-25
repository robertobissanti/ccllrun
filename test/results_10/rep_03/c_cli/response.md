Ecco il file `solution.c` creato.

**Spiegazione (≤60 parole):**

Scansiona gli spazi iniziali, legge un segno opzionale, poi accumera le cifre in `uint32_t` per evitare signed overflow UB. Prima di ogni moltiplicazione verifica che `acc` non superi `INT32_MAX/10` (o la soglia esatta per il caso negativo `INT32_MIN`). Rifiuta qualsiasi carattere non-digit, stringhe vuote o trailing characters. Restituisce 1 solo se tutto è valido.