#!/usr/bin/env python3
import difflib, json, os, re, shutil, subprocess, sys, time, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TEST = ROOT / "test"
RESULTS = TEST / "results"
PORT = 8870

def parse_ndjson(raw):
    events = []
    for line in raw.splitlines():
        try: events.append(json.loads(line))
        except Exception: pass
    result = next((e for e in reversed(events) if e.get("type") == "result"), {})
    text = result.get("result", "")
    usage = result.get("usage") or {}
    return text, usage, result, events

def run_cli(prompt, cwd):
    cmd = ["bash", str(ROOT / "ccllrun"), "-p", "--output-format", "stream-json",
           "--verbose", "--permission-mode", "bypassPermissions"]
    t = time.perf_counter()
    p = subprocess.run(cmd, input=prompt, text=True, cwd=cwd, capture_output=True, timeout=900)
    return time.perf_counter()-t, p.stdout, p.stderr, p.returncode

def run_studio(prompt, cwd):
    body = json.dumps({"prompt": prompt, "cwd": str(cwd), "permission_mode": "bypassPermissions",
                       "partial": False, "tool_search": True}).encode()
    req = urllib.request.Request(f"http://127.0.0.1:{PORT}/api/claude", body,
        {"Content-Type":"application/json", "X-Requested-With":"ccllrun-studio"})
    t = time.perf_counter()
    with urllib.request.urlopen(req, timeout=900) as r: raw = r.read().decode(errors="replace")
    return time.perf_counter()-t, raw, "", 0

def tokens(usage):
    keys = ("input_tokens", "output_tokens", "cache_creation_input_tokens", "cache_read_input_tokens")
    return {k:int(usage.get(k,0) or 0) for k in keys} | {"total_reported":sum(int(usage.get(k,0) or 0) for k in keys)}

def poetry_checks(text):
    lines = [x.strip() for x in text.splitlines() if x.strip()]
    title_ok = bool(lines and lines[0].strip("# ") == "Compilatore notturno")
    verses = lines[1:] if title_ok else lines
    words = [len(re.findall(r"\b[\wÀ-ÿ]+\b", x)) for x in verses]
    low = text.lower()
    return {"title":title_ok, "verses_12":len(verses)==12,
            "words_6_12":len(words)==12 and all(6 <= n <= 12 for n in words),
            "silicio_once":len(re.findall(r"\bsilicio\b",low))==1,
            "luna_twice":len(re.findall(r"\bluna\b",low))==2,
            "formal_score":sum([title_ok,len(verses)==12,len(words)==12 and all(6<=n<=12 for n in words),
                                len(re.findall(r"\bsilicio\b",low))==1,len(re.findall(r"\bluna\b",low))==2])/5}

def code_check(kind, cwd):
    if kind == "python":
        p=subprocess.run([sys.executable,str(TEST/"check_python.py"),str(cwd/"solution.py")],capture_output=True,text=True)
    else:
        exe=cwd/"check_c"
        cp=subprocess.run(["cc","-std=c11","-Wall","-Wextra","-Werror",str(cwd/"solution.c"),str(TEST/"check_c.c"),"-o",str(exe)],capture_output=True,text=True)
        if cp.returncode: return {"pass":False,"compile":cp.stderr}
        p=subprocess.run([str(exe)],capture_output=True,text=True)
        exe.unlink(missing_ok=True)
    return {"pass":p.returncode==0,"stdout":p.stdout,"stderr":p.stderr}

def similarity(a,b):
    norm=lambda s: re.sub(r"\s+"," ",s.strip().lower())
    aa,bb=norm(a),norm(b)
    sa,sb=set(re.findall(r"\w+",aa)),set(re.findall(r"\w+",bb))
    return {"sequence_ratio":difflib.SequenceMatcher(None,aa,bb).ratio(),
            "word_jaccard":len(sa&sb)/len(sa|sb) if sa|sb else 1.0}

def main():
    shutil.rmtree(RESULTS, ignore_errors=True); RESULTS.mkdir(parents=True)
    # Stack condiviso e preesistente: evita che la prima CLI possieda e arresti
    # il proxy, rendendo il confronto dipendente dall'ordine dei campioni.
    warm = subprocess.run(["bash", str(ROOT/"ccllrun"), "servers"], cwd=ROOT,
                          capture_output=True, text=True, timeout=900)
    (RESULTS/"stack_start.txt").write_text(warm.stdout + warm.stderr)
    if warm.returncode:
        raise RuntimeError(f"avvio stack fallito: {warm.stdout}{warm.stderr}")
    env=os.environ.copy(); env.update({"STUDIO_PORT":str(PORT),"STUDIO_HOST":"127.0.0.1",
        "CCLLRUN_BIN":str(ROOT/"ccllrun")})
    server=subprocess.Popen([str(Path.home()/".ccllrun/venv/bin/python"),str(ROOT/"studio/server.py")],env=env,
                            stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
    try:
        for _ in range(100):
            try: urllib.request.urlopen(f"http://127.0.0.1:{PORT}/api/status",timeout=.2); break
            except Exception: time.sleep(.1)
        else: raise RuntimeError("Studio server non pronto")
        allrows=[]
        for kind in ("poesia","python","c"):
            prompt=(TEST/"prompts"/f"{kind}.txt").read_text()
            pair={}
            for mode,runner in (("cli",run_cli),("studio",run_studio)):
                cwd=RESULTS/f"{kind}_{mode}"; cwd.mkdir()
                elapsed,raw,err,rc=runner(prompt,cwd)
                (cwd/"raw.ndjson").write_text(raw); (cwd/"stderr.txt").write_text(err)
                text,usage,result,_=parse_ndjson(raw); (cwd/"response.md").write_text(text)
                row={"test":kind,"mode":mode,"seconds":elapsed,"returncode":rc,"usage":tokens(usage),
                     "session_id":result.get("session_id"),"response":text}
                row["accuracy"]=poetry_checks(text) if kind=="poesia" else code_check(kind,cwd)
                pair[mode]=row; allrows.append(row)
            pair["similarity"]=similarity(pair["cli"]["response"],pair["studio"]["response"])
            (RESULTS/f"{kind}_comparison.json").write_text(json.dumps(pair,indent=2,ensure_ascii=False))
        (RESULTS/"summary.json").write_text(json.dumps(allrows,indent=2,ensure_ascii=False))
    finally:
        server.terminate()
        try: server.wait(10)
        except subprocess.TimeoutExpired: server.kill()

if __name__ == "__main__": main()
