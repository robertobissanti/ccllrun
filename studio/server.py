#!/usr/bin/env python3
"""ccllrun Studio — dashboard web per lo stack ccllrun (llama-server + proxy + Claude Code).

Ispirato a DStudio di Giuseppe Perrotta (https://github.com/sk8erboi17/DStudio, BSD-3).

Server locale che:
  - serve la single-page UI (web/index.html)
  - espone /api/status (setup doctor + salute dei server)
  - avvia/ferma lo stack via lo script `ccllrun` (sottocomandi `servers` / `stop`)
  - legge/scrive ~/.ccllrun/config.json
  - mostra i log (~/.ccllrun/*.log)
  - reverse-proxy /v1 verso il llama-server big (chat dalla UI, accesso LAN
    senza mai esporre l'engine: come DStudio, l'engine resta su 127.0.0.1)

Env:
  STUDIO_PORT  porta della dashboard (default 8770)
  STUDIO_HOST  host di bind (default 127.0.0.1; 0.0.0.0 per la LAN)
  CCLLRUN_BIN  path dello script ccllrun (default: ../ccllrun rispetto a questo file)
"""

import asyncio
import glob
import json
import os
import shutil
import sys
from pathlib import Path

from aiohttp import web, ClientSession, ClientTimeout

HERE = Path(__file__).resolve().parent
CC_DIR = Path.home() / ".ccllrun"
CONFIG_FILE = CC_DIR / "config.json"

# Lanciata dal Finder la .app eredita solo /usr/bin:/bin: arricchiamo il PATH
# del PROCESSO prima di risolvere qualsiasi binario (doctor compreso); i
# sottoprocessi lo ereditano.
os.environ["PATH"] = ":".join(
    ["/opt/homebrew/bin", "/usr/local/bin",
     str(Path.home() / "bin"), str(Path.home() / ".local/bin"),
     os.environ.get("PATH", "")])


def _find_bin(env_var, name, extra):
    cands = [os.environ.get(env_var), shutil.which(name)] + extra
    for c in cands:
        if c and Path(c).is_file():
            return c
    return name


# nel bundle .app lo script è in Resources/ (accanto a server.py); in repo è in ../
CCLLRUN_BIN = _find_bin("CCLLRUN_BIN", "ccllrun",
                        [str(HERE / "ccllrun"), str(HERE.parent / "ccllrun"), str(Path.home() / "bin/ccllrun")])
CLAUDE_BIN = _find_bin("CLAUDE_BIN", "claude",
                       [str(Path.home() / ".local/bin/claude"), "/opt/homebrew/bin/claude",
                        str(Path.home() / ".claude/local/claude")])
STUDIO_PORT = int(os.environ.get("STUDIO_PORT", "8770"))
STUDIO_HOST = os.environ.get("STUDIO_HOST", "127.0.0.1")

DEFAULTS = {
    "big_port": 8001, "small_port": 8002, "proxy_port": 8765,
    "model_big": "qwen-big", "model_small": "small-fast",
    "big_gguf": str(Path.home() / ".lmstudio/models/unsloth/Qwen3.6-35B-A3B-GGUF/Qwen3.6-35B-A3B-UD-Q4_K_XL.gguf"),
    "small_gguf": str(Path.home() / ".lmstudio/models/ghost-actual/Qwen3.6-9B-Heretic-History-Q4_K_M-GGUF/history-9b-Q4_K_M.gguf"),
    "studio_markdown": True,
    "studio_autostart": True,
    "cc_tool_search": False,
}

LOGS = {"big": "llama-big.log", "small": "llama-small.log", "proxy": "proxy.log"}


def aug_env():
    """Ambiente per i sottoprocessi (il PATH è già arricchito a livello processo)."""
    return os.environ.copy()


def load_config():
    cfg = dict(DEFAULTS)
    try:
        user = json.loads(CONFIG_FILE.read_text())
        for k, v in user.items():
            cfg[k] = os.path.expanduser(v) if isinstance(v, str) else v
    except FileNotFoundError:
        pass
    except Exception as exc:
        cfg["_config_error"] = str(exc)
    return cfg


async def http_json(url, timeout=2):
    try:
        async with ClientSession(timeout=ClientTimeout(total=timeout)) as s:
            async with s.get(url) as r:
                if r.status != 200:
                    return None
                return await r.json(content_type=None)
    except Exception:
        return None


def pid_alive(pidfile):
    try:
        pid = int((CC_DIR / pidfile).read_text().strip())
        os.kill(pid, 0)
        return pid
    except Exception:
        return None


# ---------------------------------------------------------------- /api/status
async def api_status(request):
    cfg = load_config()
    big_gguf = cfg.get("big_gguf", "")
    small_gguf = cfg.get("small_gguf", "")
    mmproj = cfg.get("mmproj") or ""
    if not mmproj and big_gguf:
        found = sorted(glob.glob(str(Path(big_gguf).parent / "mmproj-*.gguf")))
        mmproj = found[0] if found else ""

    # setup doctor — ogni check: ok / warn / fail + hint per sistemarlo
    def check(ok, label, detail, hint="", warn=False):
        return {"ok": bool(ok), "warn": bool(warn and not ok), "label": label,
                "detail": detail, "hint": "" if ok else hint}

    settings_ok = False
    try:
        settings_ok = "CLAUDE_CODE_ATTRIBUTION_HEADER" in (Path.home() / ".claude/settings.json").read_text()
    except Exception:
        pass

    doctor = [
        check(shutil.which("llama-server"), "llama-server", shutil.which("llama-server") or "non trovato nel PATH",
              "brew install llama.cpp"),
        check(shutil.which("claude"), "Claude Code", shutil.which("claude") or "non trovato nel PATH",
              "npm install -g @anthropic-ai/claude-code"),
        check((CC_DIR / "proxy.py").exists(), "proxy.py", str(CC_DIR / "proxy.py"),
              "copia proxy.py in ~/.ccllrun/"),
        check((CC_DIR / "venv/bin/python").exists(), "venv Python", str(CC_DIR / "venv"),
              "creato automaticamente al primo `ccllrun`", warn=True),
        check(Path(CCLLRUN_BIN).is_file(), "script ccllrun", CCLLRUN_BIN,
              "imposta CCLLRUN_BIN o reinstalla lo script"),
        check(big_gguf and Path(big_gguf).is_file(), "GGUF big", big_gguf or "non configurato",
              "imposta big_gguf in config.json"),
        check(small_gguf and Path(small_gguf).is_file(), "GGUF small", small_gguf or "non configurato",
              "opzionale: small_gguf in config.json (o no_small: true)", warn=True),
        check(mmproj and Path(mmproj).is_file(), "mmproj (visione)", mmproj or "non trovato",
              "opzionale: scarica mmproj-*.gguf accanto al GGUF big", warn=True),
        check(CONFIG_FILE.exists() and "_config_error" not in cfg, "config.json",
              cfg.get("_config_error") or str(CONFIG_FILE),
              "crea ~/.ccllrun/config.json (vedi config.example.json)", warn=not CONFIG_FILE.exists()),
        check(settings_ok, "settings Claude Code", "CLAUDE_CODE_ATTRIBUTION_HEADER",
              'aggiungi {"env":{"CLAUDE_CODE_ATTRIBUTION_HEADER":"0"}} in ~/.claude/settings.json', warn=True),
    ]

    big_port, small_port, proxy_port = (int(cfg.get(k, DEFAULTS[k])) for k in ("big_port", "small_port", "proxy_port"))
    big_health, big_props = await asyncio.gather(
        http_json(f"http://127.0.0.1:{big_port}/health"),
        http_json(f"http://127.0.0.1:{big_port}/props"),
    )
    small_health = await http_json(f"http://127.0.0.1:{small_port}/health")
    proxy_up = await http_json(f"http://127.0.0.1:{proxy_port}/v1/models") is not None

    servers = {
        "big": {"up": big_health is not None, "port": big_port, "alias": cfg.get("model_big"),
                "pid": pid_alive("llama-big.pid"),
                "ctx": (big_props or {}).get("default_generation_settings", {}).get("n_ctx"),
                "model_path": (big_props or {}).get("model_path") or big_gguf},
        "small": {"up": small_health is not None, "port": small_port, "alias": cfg.get("model_small"),
                  "pid": pid_alive("llama-small.pid")},
        "proxy": {"up": proxy_up, "port": proxy_port, "pid": pid_alive("proxy.pid")},
    }
    return web.json_response({"doctor": doctor, "servers": servers, "config": cfg,
                              "studio": {"host": STUDIO_HOST, "port": STUDIO_PORT}})


# ----------------------------------------------------- start/stop dello stack
def require_csrf(request):
    if request.headers.get("X-Requested-With") != "ccllrun-studio":
        raise web.HTTPForbidden(text="missing X-Requested-With header")


START_LOCK = asyncio.Lock()


async def api_start(request):
    require_csrf(request)
    if not Path(CCLLRUN_BIN).is_file():
        return web.json_response({"ok": False, "error": f"script non trovato: {CCLLRUN_BIN}"}, status=500)
    async with START_LOCK:
        proc = await asyncio.create_subprocess_exec(
            "bash", CCLLRUN_BIN, "servers", env=aug_env(),
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT)
        out, _ = await proc.communicate()
    return web.json_response({"ok": proc.returncode == 0, "output": out.decode(errors="replace")})


async def api_stop(request):
    require_csrf(request)
    proc = await asyncio.create_subprocess_exec(
        "bash", CCLLRUN_BIN, "stop", env=aug_env(),
        stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT)
    out, _ = await proc.communicate()
    return web.json_response({"ok": proc.returncode == 0, "output": out.decode(errors="replace")})


async def api_launch(request):
    """Apre Claude Code (ccllrun) in Terminal.app nella cartella di lavoro scelta."""
    require_csrf(request)
    data = await request.json()
    cwd = os.path.expanduser((data.get("cwd") or "").strip())
    if not cwd or not Path(cwd).is_dir():
        return web.json_response({"ok": False, "error": f"cartella non valida: {cwd or '(vuota)'}"}, status=400)
    add_dirs = []
    for d in data.get("add_dirs") or []:
        d = os.path.expanduser(str(d).strip())
        if not d or not Path(d).is_dir():
            return web.json_response({"ok": False, "error": f"cartella non valida: {d}"}, status=400)
        add_dirs.append(d)
    # quoting shell con shlex (un path con $ o ` dentro doppie virgolette espanderebbe),
    # poi escaping come stringa AppleScript ("\ e " vanno protetti)
    import shlex
    extra = "".join(" --add-dir " + shlex.quote(d) for d in add_dirs)
    shell_cmd = f"cd {shlex.quote(cwd)} && {shlex.quote(CCLLRUN_BIN)}{extra}"
    as_cmd = shell_cmd.replace("\\", "\\\\").replace('"', '\\"')
    proc = await asyncio.create_subprocess_exec(
        "osascript",
        "-e", f'tell application "Terminal" to do script "{as_cmd}"',
        "-e", 'tell application "Terminal" to activate',
        stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT)
    out, _ = await proc.communicate()
    return web.json_response({"ok": proc.returncode == 0,
                              "output": out.decode(errors="replace").strip()})


# ---------------------------------------- chat = Claude Code headless
# Ogni messaggio della chat esegue `claude -p --output-format stream-json`
# nella cartella della sessione, puntato allo stack locale via proxy: la chat
# È Claude Code (stessi tool, stessi permessi), non un surrogato.

CLAUDE_SEM = asyncio.Semaphore(3)   # max processi claude simultanei dall'API

# ------------------------------------------- approvazioni interattive (permtool)
# In headless non c'e' il prompt di Claude Code: `--permission-prompt-tool`
# fa passare ogni richiesta di permesso da permtool.py (MCP) -> /api/perm/ask.
# La richiesta resta qui in attesa finche' la GUI risponde via /api/perm/reply.
PERM_PENDING = {}    # id -> {"event": asyncio.Event, "reply": dict|None, "info": dict}
PERM_SEQ = 0


async def api_perm_ask(request):
    # chiamata da permtool.py (localhost), non dalla GUI: niente CSRF
    global PERM_SEQ
    data = await request.json()
    PERM_SEQ += 1
    pid = str(PERM_SEQ)
    entry = {"event": asyncio.Event(), "reply": None,
             "info": {"id": pid, "tool_name": data.get("tool_name") or "",
                      "input": data.get("input") or {}, "cwd": data.get("cwd") or ""}}
    PERM_PENDING[pid] = entry
    try:
        await asyncio.wait_for(entry["event"].wait(), timeout=600)
    except asyncio.TimeoutError:
        entry["reply"] = {"behavior": "deny", "message": "nessuna risposta dalla GUI (timeout)"}
    finally:
        PERM_PENDING.pop(pid, None)
    reply = entry["reply"] or {"behavior": "deny", "message": "annullato"}
    if reply.get("behavior") == "allow":
        reply.setdefault("updatedInput", entry["info"]["input"])
    return web.json_response(reply)


async def api_perm_pending(request):
    return web.json_response(
        {"pending": [e["info"] for e in PERM_PENDING.values() if e["reply"] is None]})


def add_allow_rule(cwd, rule):
    """Aggiunge una regola permissions.allow in .claude/settings.local.json del progetto."""
    p = Path(cwd) / ".claude" / "settings.local.json"
    try:
        cfg = json.loads(p.read_text())
    except Exception:
        cfg = {}
    allow = cfg.setdefault("permissions", {}).setdefault("allow", [])
    if rule not in allow:
        allow.append(rule)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(cfg, indent=2) + "\n")
    return rule


async def api_perm_reply(request):
    require_csrf(request)
    data = await request.json()
    entry = PERM_PENDING.get(str(data.get("id")))
    if not entry or entry["reply"] is not None:
        return web.json_response({"ok": False, "error": "richiesta scaduta"}, status=404)
    saved = ""
    if data.get("behavior") == "allow":
        entry["reply"] = {"behavior": "allow"}
        if data.get("always"):
            info = entry["info"]
            rule = info["tool_name"]
            if rule == "Bash":     # regola sul prefisso: Bash(gcc:*)
                first = str(info["input"].get("command", "")).strip().split(" ")[0]
                rule = f"Bash({first}:*)" if first else "Bash"
            try:
                saved = add_allow_rule(info["cwd"], rule)
            except Exception as exc:
                saved = f"(regola non salvata: {exc})"
    else:
        entry["reply"] = {"behavior": "deny",
                          "message": "L'utente ha negato il permesso da ccllrun Studio."}
    entry["event"].set()
    return web.json_response({"ok": True, "saved_rule": saved})


async def api_claude(request):
    require_csrf(request)
    data = await request.json()
    prompt = (data.get("prompt") or "").strip()
    if not prompt:
        return web.json_response({"ok": False, "error": "prompt vuoto"}, status=400)
    cwd = os.path.expanduser((data.get("cwd") or "").strip() or str(Path.home()))
    if not Path(cwd).is_dir():
        return web.json_response({"ok": False, "error": f"cartella non valida: {cwd}"}, status=400)
    add_dirs = []
    for d in data.get("add_dirs") or []:
        d = os.path.expanduser(str(d).strip())
        if d and Path(d).is_dir():
            add_dirs.append(d)

    cfg = load_config()
    if await http_json(f"http://127.0.0.1:{cfg['proxy_port']}/v1/models") is None:
        return web.json_response({"ok": False,
            "error": "proxy fermo: avvia i server da Sistema → Stato"}, status=409)

    env = aug_env()
    env.update({
        "ANTHROPIC_BASE_URL": f"http://127.0.0.1:{cfg['proxy_port']}",
        "ANTHROPIC_AUTH_TOKEN": env.get("ANTHROPIC_AUTH_TOKEN", "sk-local"),
        "ANTHROPIC_MODEL": str(cfg.get("model_big", "qwen-big")),
        "ANTHROPIC_SMALL_FAST_MODEL": str(cfg.get("model_small", "small-fast")),
        "CLAUDE_CODE_ATTRIBUTION_HEADER": "0",
        # Soglia di auto-compact: CC hardcoda la finestra a 200k per i modelli
        # non-Anthropic, quindi CLAUDE_CODE_MAX_CONTEXT_TOKENS viene ignorata.
        # L'unica leva efficace e' CLAUDE_CODE_AUTO_COMPACT_WINDOW = min(200k, val).
        # La teniamo sotto a ctx_big per compattare PRIMA dell'OOM Metal.
        # Output basso per lasciare spazio al contesto. Coerente con lo script ccllrun.
        "CLAUDE_CODE_AUTO_COMPACT_WINDOW": str(cfg.get("cc_auto_compact_window", 115000)),
        "CLAUDE_CODE_MAX_OUTPUT_TOKENS": str(cfg.get("cc_max_output_tokens", 32000)),
        # tool search (vedi cc_tool_search): "1" attiva, "" la disattiva anche se
        # presente nel settings.json globale. Sperimentale dietro proxy.
        "ENABLE_TOOL_SEARCH": "1" if cfg.get("cc_tool_search") else "",
    })
    perm_mode = data.get("permission_mode") or "acceptEdits"
    cmd = [CLAUDE_BIN, "-p", "--output-format", "stream-json", "--verbose",
           "--permission-mode", perm_mode]
    # approvazione interattiva: ogni permesso non coperto dalla modalita' passa
    # dalla card in chat (permtool MCP -> /api/perm/*); inutile in bypass
    if perm_mode != "bypassPermissions" and (HERE / "permtool.py").is_file():
        mcp_cfg = json.dumps({"mcpServers": {"studioperm": {
            "command": sys.executable, "args": [str(HERE / "permtool.py")],
            "env": {"STUDIO_PORT": str(STUDIO_PORT)}}}})
        cmd += ["--permission-prompt-tool", "mcp__studioperm__approve",
                "--mcp-config", mcp_cfg]
    if data.get("session_id"):
        cmd += ["--resume", data["session_id"]]
    for d in add_dirs:
        cmd += ["--add-dir", d]

    async with CLAUDE_SEM:
        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd, cwd=cwd, env=env,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE)
        except FileNotFoundError:
            return web.json_response({"ok": False, "error": f"claude non trovato ({CLAUDE_BIN})"}, status=500)
        proc.stdin.write(prompt.encode())
        await proc.stdin.drain()
        proc.stdin.write_eof()
        # stderr va drenato IN PARALLELO a stdout: se claude riempie il pipe
        # (64 KB) mentre leggiamo solo stdout, il processo si blocca (deadlock)
        stderr_task = asyncio.ensure_future(proc.stderr.read())

        resp = web.StreamResponse()
        resp.headers["Content-Type"] = "application/x-ndjson"
        await resp.prepare(request)
        try:
            while True:
                line = await proc.stdout.readline()
                if not line:
                    break
                await resp.write(line)
            await proc.wait()
            if proc.returncode != 0:
                err = (await stderr_task).decode(errors="replace")[-1500:]
                await resp.write((json.dumps({"type": "studio_error",
                    "error": f"claude è uscito con codice {proc.returncode}: {err.strip()}"}) + "\n").encode())
            else:
                stderr_task.cancel()
        except (ConnectionResetError, asyncio.CancelledError):
            proc.kill()       # il client ha chiuso (stop / pagina ricaricata): non lasciare orfani
            stderr_task.cancel()
            raise
        await resp.write_eof()
        return resp


# ------------------------------------------- comandi slash / skill disponibili
def _frontmatter_field(path, field, limit=2048):
    try:
        head = open(path, errors="replace").read(limit)
    except OSError:
        return ""
    inside = False
    lines = head.splitlines()
    for i, line in enumerate(lines):
        if line.strip() == "---":
            if inside:
                break
            inside = True
            continue
        if inside and line.lstrip().startswith(field + ":"):
            val = line.split(":", 1)[1].strip().strip("'\"")
            if val in ("|", ">", "|-", ">-"):     # YAML multilinea: prendi la prima riga indentata
                for nxt in lines[i + 1:]:
                    if nxt.strip():
                        return nxt.strip()
                return ""
            return val
    return ""


def _collect_commands(cwd):
    items, seen = [], set()

    def add(name, desc, src):
        if name and name not in seen:
            seen.add(name)
            items.append({"name": name, "desc": (desc or "")[:140], "src": src})

    roots = [(Path.home() / ".claude", "user")]
    if cwd and Path(cwd).is_dir():
        roots.append((Path(cwd) / ".claude", "progetto"))
    for root, src in roots:
        for f in sorted((root / "commands").glob("*.md")) if (root / "commands").is_dir() else []:
            add("/" + f.stem, _frontmatter_field(f, "description"), src)
        skills = root / "skills"
        if skills.is_dir():
            for d in sorted(skills.iterdir()):
                sk = d / "SKILL.md"
                if sk.is_file():
                    add("/" + (_frontmatter_field(sk, "name") or d.name),
                        _frontmatter_field(sk, "description"), src)
    # skill dei plugin (~/.claude/plugins/**/skills/*/SKILL.md)
    plugins = Path.home() / ".claude/plugins"
    if plugins.is_dir():
        for sk in sorted(plugins.glob("*/skills/*/SKILL.md")) + sorted(plugins.glob("*/*/skills/*/SKILL.md")):
            add("/" + (_frontmatter_field(sk, "name") or sk.parent.name),
                _frontmatter_field(sk, "description"), "plugin")
    items.sort(key=lambda c: c["name"])
    return items


async def api_commands(request):
    cwd = os.path.expanduser(request.query.get("cwd", ""))
    loop = asyncio.get_event_loop()
    items = await loop.run_in_executor(None, _collect_commands, cwd)
    return web.json_response({"ok": True, "commands": items})


# -------------------------------------------------------------- config & log
async def api_config_get(request):
    try:
        return web.json_response({"ok": True, "text": CONFIG_FILE.read_text()})
    except FileNotFoundError:
        example = HERE.parent / "config.example.json"
        text = example.read_text() if example.exists() else "{\n}\n"
        return web.json_response({"ok": True, "text": text, "missing": True})


async def api_config_put(request):
    require_csrf(request)
    text = await request.text()
    try:
        json.loads(text)
    except Exception as exc:
        return web.json_response({"ok": False, "error": f"JSON non valido: {exc}"}, status=400)
    CC_DIR.mkdir(exist_ok=True)
    CONFIG_FILE.write_text(text)
    return web.json_response({"ok": True})


async def api_logs(request):
    name = request.query.get("name", "big")
    lines = min(int(request.query.get("lines", "200")), 2000)
    path = CC_DIR / LOGS.get(name, LOGS["big"])
    try:
        with open(path, "rb") as f:
            f.seek(0, 2)
            size = f.tell()
            f.seek(max(0, size - 256 * 1024))
            tail = f.read().decode(errors="replace").splitlines()[-lines:]
    except FileNotFoundError:
        tail = ["(log non ancora creato)"]
    return web.json_response({"ok": True, "lines": tail})


# ------------------------------------------- reverse proxy /v1 -> big engine
async def v1_proxy(request):
    cfg = load_config()
    upstream = f"http://127.0.0.1:{cfg.get('big_port', 8001)}/{request.match_info['tail']}"
    body = await request.read()
    headers = {k: v for k, v in request.headers.items()
               if k.lower() in ("content-type", "accept", "authorization")}
    try:
        async with ClientSession(timeout=ClientTimeout(total=None, sock_connect=5)) as s:
            async with s.request(request.method, upstream, data=body or None, headers=headers) as up:
                resp = web.StreamResponse(status=up.status)
                ct = up.headers.get("Content-Type", "application/json")
                resp.headers["Content-Type"] = ct
                await resp.prepare(request)
                async for chunk in up.content.iter_any():
                    await resp.write(chunk)
                await resp.write_eof()
                return resp
    except Exception as exc:
        return web.json_response({"error": {"message": f"engine non raggiungibile: {exc}"}}, status=502)


# --------------------------------------------------------------------- pagine
async def index(request):
    # no-cache: senza Cache-Control la WKWebView applica la cache euristica e
    # puo' servire una index.html stantia senza interrogare il server
    return web.FileResponse(HERE / "web" / "index.html",
                            headers={"Cache-Control": "no-cache"})


async def mark_svg(request):
    # marchio dodecaedro della UI: file esterno (web/mark.svg), montato dal JS
    return web.FileResponse(HERE / "web" / "mark.svg",
                            headers={"Cache-Control": "no-cache",
                                     "Content-Type": "image/svg+xml"})


async def autostart_stack(app):
    """All'avvio di Studio avvia lo stack (big+small+proxy) come fa la CLI,
    se la config lo prevede e il proxy non e' gia' su. Non blocca la UI:
    gira in background, lo Stato si aggiorna da solo col polling."""
    cfg = load_config()
    if not cfg.get("studio_autostart", True) or not Path(CCLLRUN_BIN).is_file():
        return
    if await http_json(f"http://127.0.0.1:{cfg['proxy_port']}/v1/models") is not None:
        return                                    # gia' attivo

    async def run():
        proc = await asyncio.create_subprocess_exec(
            "bash", CCLLRUN_BIN, "servers", env=aug_env(),
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT)
        out, _ = await proc.communicate()
        print(f"[studio] autostart: {out.decode(errors='replace').strip()}", flush=True)
    asyncio.ensure_future(run())


def main():
    app = web.Application(client_max_size=64 * 1024 * 1024)
    app.on_startup.append(autostart_stack)
    app.router.add_get("/", index)
    app.router.add_get("/mark.svg", mark_svg)
    app.router.add_static("/vendor", HERE / "web" / "vendor")
    app.router.add_get("/api/status", api_status)
    app.router.add_post("/api/start", api_start)
    app.router.add_post("/api/stop", api_stop)
    app.router.add_post("/api/launch", api_launch)
    app.router.add_post("/api/claude", api_claude)
    app.router.add_post("/api/perm/ask", api_perm_ask)
    app.router.add_get("/api/perm/pending", api_perm_pending)
    app.router.add_post("/api/perm/reply", api_perm_reply)
    app.router.add_get("/api/commands", api_commands)
    app.router.add_get("/api/config", api_config_get)
    app.router.add_put("/api/config", api_config_put)
    app.router.add_get("/api/logs", api_logs)
    app.router.add_route("*", "/v1/{tail:.*}", v1_proxy)
    print(f"[studio] http://{STUDIO_HOST}:{STUDIO_PORT}", flush=True)
    web.run_app(app, host=STUDIO_HOST, port=STUDIO_PORT, print=None)


if __name__ == "__main__":
    sys.exit(main())
