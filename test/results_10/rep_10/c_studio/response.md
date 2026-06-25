Compila senza warning. Ecco come funziona:

- **Scansiona** spazi iniziali con `isspace()`, poi legge un segno opzionale (`-`/`+`).
- **Accumula** la magnitudine in `uint32_t` per evitare signed-overflow UB. Prima di ogni moltiplicazione per 10, verifica che `result > (limit - digit) / 10`; se sì, c'è overflow/underflow e si rifiuta.
- **Trailing whitespace** è permesso, ma qualsiasi altro carattere extra causa rifiuto.
- **Stringa vuota**, nessun dígito, o input nullo restituiscono 0 senza modificare `*out`.
- `INT32_MIN` (-2147483648) è accettato perché `limit = INT32_MAX + 1 = 2147483648` quando `neg=1`.