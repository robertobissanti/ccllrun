`solution.c` creata. Ecco il riepilogo:

**Spiegazione (max 60 parole):**

La funzione scarta spazi iniziali, legge un segno opzionale (`+`/`-`), poi accumera cifra per cifra verificando overflow/underflow *prima* di moltiplicare per 10 (evitando aritmetica signed overflow, UB in C). I limiti sono calcolati per entrambi i segni separatamente: `INT32_MAX` per positivo, `2147483648` per negativo (che ammette `-2147483648`). Dopo le cifre, scarta spazi finali e rifiuta qualsiasi carattere residuo. Restituisce 1 solo se l'intera stringa è valida.