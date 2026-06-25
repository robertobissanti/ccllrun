Ecco il file `solution.c` creato.

**Spiegazione (60 parole):**

La funzione scarta spazi iniziali/finali, legge un segno opzionale, poi accumera cifre in un `uint32_t` per evitare undefined behavior da overflow signed. Prima di ogni moltiplicazione verifica che `acc * 10 + digit` non superi `INT32_MAX` (2147483647) o `INT32_MIN` (−2147483648) separatamente. Rifiuta stringhe vuote, caratteri non digit, trailing characters e overflow/underflow. Restituisce 1 solo se l'intero input è valido.