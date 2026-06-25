File creata e compilata senza warning.

**Spiegazione:** La funzione scarta spazi iniziali, legge un segno opzionale, poi accumula le cifre in un `int64_t` per rilevare overflow/underflow prima del cast a `int32_t`. Dopo le cifre scarta spazi finali; se resta qualsiasi altro carattere la stringa è rifiutata. `*out` non viene mai modificato in caso di errore.