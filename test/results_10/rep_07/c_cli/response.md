File corretto. Ecco il risultato:

**`solution.c`** — implementazione completa con:
- Skip spazi iniziali/finali (`isspace`)
- Segno opzionale (`+`/`-`)
- Rifiuto stringa vuota, caratteri non-digit, extra characters
- Overflow/underflow check safe (accumulo negativo per gestire `INT32_MIN`)
- Nessun uso di `strtol`/`strtoll`

**Spiegazione (60 parole):**

Accumulo sempre come valore negativo per evitare `abs(INT32_MIN)` non rappresentabile. Il controllo `acc < INT32_MIN/10 || (acc == INT32_MIN/10 && digit > 8)` previene underflow senza overflow intermedio. C11 definisce divisione intera truncata verso zero, quindi `INT32_MIN/10 = -214748364` e `INT32_MIN%10 = -8`. Dopo i digit, scarto spazi finali; qualsiasi carattere residuo causa rifiuto. `*out` non viene mai modificato in caso di errore.