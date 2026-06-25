#!/usr/bin/env python3
"""
Test di regressione per la stabilita' del prefisso (prompt-cache) nel proxy.

Esegui:  python3 test/test_proxy_promptcache.py
Esce 0 se tutto passa, 1 al primo fallimento. Nessun modello richiesto:
sono test PURI sulle funzioni di proxy.py.

Contesto: Claude Code e' stateless e rimanda l'intero transcript a ogni turno.
llama-server riusa la KV cache solo per il PREFISSO byte-identico (--cache-reuse).
Se il rendering dello storico (tool_use / tool_result) cambia byte tra una
richiesta e la successiva, il prefisso diverge e tutto il suffisso viene
ri-prefillato. Questi test bloccano le regressioni che reintroducono
instabilita': id opachi nel prefisso, ordine-chiavi non deterministico,
serializzazione non-JSON dei tool_result.
"""
import importlib.util
import os
import sys
import types

# proxy.py importa aiohttp solo per il server runtime; questi test toccano solo
# funzioni pure. Stub minimale cosi' girano con qualunque Python, senza venv.
if importlib.util.find_spec("aiohttp") is None:
    stub = types.ModuleType("aiohttp")
    stub.ClientSession = object
    stub.ClientTimeout = object
    stub.web = types.SimpleNamespace()
    sys.modules["aiohttp"] = stub

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
spec = importlib.util.spec_from_file_location("proxy", os.path.join(ROOT, "proxy.py"))
proxy = importlib.util.module_from_spec(spec)
spec.loader.exec_module(proxy)

failures = []


def check(name, cond, detail=""):
    status = "ok " if cond else "FAIL"
    print(f"[{status}] {name}" + (f" — {detail}" if detail and not cond else ""))
    if not cond:
        failures.append(name)


# 1. Stessa tool call con id diversi + ordine chiavi diverso -> prefisso IDENTICO.
b1 = {"type": "tool_use", "id": "toolu_AAA",
      "name": "Bash", "input": {"command": "ls", "timeout": 5}}
b2 = {"type": "tool_use", "id": "toolu_ZZZ_different",
      "name": "Bash", "input": {"timeout": 5, "command": "ls"}}
t1, t2 = proxy.block_text(b1), proxy.block_text(b2)
check("tool_use: prefisso stabile tra id/ordine diversi", t1 == t2,
      f"{t1!r} != {t2!r}")

# 2. L'id opaco Anthropic NON deve finire nel prefisso.
check("tool_use: nessun id 'toolu_' nel prefisso", "toolu_" not in t1, t1)

# 3. Determinismo: render ripetuto dello stesso blocco -> identico.
check("tool_use: render ripetibile", proxy.block_text(b1) == proxy.block_text(b1))

# 4. tool_result con content NON stringa -> testo stabile (no repr Python tipo "{'type':...}").
r = {"type": "tool_result", "content": [{"type": "text", "text": "output riga"}]}
rt = proxy.block_text(r)
check("tool_result: niente repr Python", "{'type'" not in rt, rt)
check("tool_result: contenuto presente", "output riga" in rt, rt)

# 5. Recupero tool-call-as-text (path MLX): formato Anthropic pieno.
full = 'pre [tool_use]\n{"type":"tool_use","name":"Read","input":{"file":"x.py"}}'
_, tools_full = proxy.extract_text_tool_uses(full)
check("recover: formato Anthropic pieno",
      bool(tools_full) and tools_full[0]["name"] == "Read"
      and tools_full[0]["type"] == "tool_use")

# 6. Recupero: forma canonica ridotta {name,input} (quella che ora mostriamo nel
#    prefisso). Se il modello la imita in output va comunque recuperata.
mini = 'ok [tool_use]\n{"name":"Read","input":{"file":"x.py"}}'
_, tools_mini = proxy.extract_text_tool_uses(mini)
check("recover: forma canonica ridotta",
      bool(tools_mini) and tools_mini[0]["name"] == "Read"
      and tools_mini[0]["type"] == "tool_use")

# 7. Recupero: piu' tool call consecutive.
multi = '[tool_use]\n{"name":"A","input":{}} [tool_use]\n{"name":"B","input":{}}'
_, tools_multi = proxy.extract_text_tool_uses(multi)
check("recover: due tool call consecutive",
      [t["name"] for t in tools_multi] == ["A", "B"])

# 8. anthropic_tool_id: id gia' valido preservato (NON rigenerato a ogni chiamata).
check("tool_id: id valido preservato",
      proxy.anthropic_tool_id("toolu_keepme") == "toolu_keepme")

print()
if failures:
    print(f"{len(failures)} test falliti: {', '.join(failures)}")
    sys.exit(1)
print("tutti i test passati")
sys.exit(0)
