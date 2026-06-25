# Esperimento 2: processo persistente vs `--resume`

Esperimento appaiato che isola il ciclo di vita del processo Claude Code.

- `persistent`: un solo processo `claude -p --input-format stream-json`, tre turni.
- `resume`: un processo identico per turno; turni 2 e 3 usano `--resume`.
- Tool disabilitati, stesso ambiente, modello, prompt, session ID e directory isolate.
- La randomizzazione genera dati diversi **tra repliche**; nella stessa replica i due rami ricevono gli stessi prompt.

