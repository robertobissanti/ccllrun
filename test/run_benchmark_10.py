#!/usr/bin/env python3
"""60-run randomized CLI vs Studio benchmark, resumable and reproducible."""
import fcntl, json, os, random, shutil, statistics, subprocess, sys, time, urllib.request
from pathlib import Path

import run_benchmark as base

ROOT = Path(__file__).resolve().parent.parent
TEST = ROOT / "test"
OUT = TEST / "results_10"
PORT = 8871
SEED = 20260618
REPS = 10

def wait_studio():
    for _ in range(200):
        try:
            urllib.request.urlopen(f"http://127.0.0.1:{PORT}/api/status", timeout=.2)
            return
        except Exception: time.sleep(.1)
    raise RuntimeError("Studio server non pronto")

def run_cli(prompt, cwd):
    cmd=["bash",str(ROOT/"ccllrun"),"-p","--output-format","stream-json","--verbose",
         "--permission-mode","bypassPermissions"]
    t=time.perf_counter(); p=subprocess.run(cmd,input=prompt,text=True,cwd=cwd,capture_output=True,timeout=180)
    return time.perf_counter()-t,p.stdout,p.stderr,p.returncode

def run_studio(prompt,cwd):
    body=json.dumps({"prompt":prompt,"cwd":str(cwd),"permission_mode":"bypassPermissions",
                     "partial":False,"tool_search":True}).encode()
    req=urllib.request.Request(f"http://127.0.0.1:{PORT}/api/claude",body,
        {"Content-Type":"application/json","X-Requested-With":"ccllrun-studio"})
    t=time.perf_counter()
    with urllib.request.urlopen(req,timeout=180) as r: raw=r.read().decode(errors="replace")
    return time.perf_counter()-t,raw,"",0

def artifact(kind,cwd,response):
    name={"poesia":"compilatore_notturno.txt","python":"solution.py","c":"solution.c"}[kind]
    p=cwd/name
    return p.read_text(errors="replace") if p.exists() else response

def assess(kind,cwd,response):
    if kind=="poesia": return base.poetry_checks(artifact(kind,cwd,response))
    try: return base.code_check(kind,cwd)
    except Exception as exc: return {"pass":False,"error":repr(exc)}

def main():
    OUT.mkdir(exist_ok=True)
    lock=(OUT/"runner.lock").open("w")
    try: fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    except BlockingIOError: raise RuntimeError("un altro benchmark e gia in esecuzione")
    progress=OUT/"runs.jsonl"
    completed={}
    if progress.exists():
        for line in progress.read_text().splitlines():
            row=json.loads(line); completed[(row["rep"],row["test"],row["mode"])]=row

    jobs=[(rep,kind,mode) for rep in range(1,REPS+1)
          for kind in ("poesia","python","c") for mode in ("cli","studio")]
    random.Random(SEED).shuffle(jobs)
    (OUT/"schedule.json").write_text(json.dumps(jobs,indent=2))

    warm=subprocess.run(["bash",str(ROOT/"ccllrun"),"servers"],cwd=ROOT,capture_output=True,text=True,timeout=600)
    (OUT/"stack_start.txt").write_text(warm.stdout+warm.stderr)
    if warm.returncode: raise RuntimeError("stack: "+warm.stdout+warm.stderr)
    env=os.environ.copy(); env.update({"STUDIO_PORT":str(PORT),"STUDIO_HOST":"127.0.0.1",
                                      "CCLLRUN_BIN":str(ROOT/"ccllrun")})
    server=subprocess.Popen([str(Path.home()/".ccllrun/venv/bin/python"),str(ROOT/"studio/server.py")],
        env=env,stdout=(OUT/"studio-server.log").open("a"),stderr=subprocess.STDOUT,text=True)
    try:
        wait_studio()
        for index,(rep,kind,mode) in enumerate(jobs,1):
            if (rep,kind,mode) in completed: continue
            cwd=OUT/f"rep_{rep:02d}"/f"{kind}_{mode}"; cwd.mkdir(parents=True,exist_ok=True)
            prompt=(TEST/"prompts"/f"{kind}.txt").read_text()
            runner=run_cli if mode=="cli" else run_studio
            started=time.perf_counter()
            try:
                elapsed,raw,err,rc=runner(prompt,cwd)
                run_error=""
            except Exception as exc:
                elapsed=time.perf_counter()-started; raw=""; err=repr(exc); rc=124; run_error=repr(exc)
            (cwd/"raw.ndjson").write_text(raw); (cwd/"stderr.txt").write_text(err)
            response,usage,result,_=base.parse_ndjson(raw); (cwd/"response.md").write_text(response)
            art=artifact(kind,cwd,response); (cwd/"artifact.txt").write_text(art)
            row={"index":index,"rep":rep,"test":kind,"mode":mode,"seconds":elapsed,"returncode":rc,
                 "usage":base.tokens(usage),"accuracy":assess(kind,cwd,response),
                 "session_id":result.get("session_id"),"artifact":str(cwd/"artifact.txt"),"run_error":run_error}
            with progress.open("a") as f: f.write(json.dumps(row,ensure_ascii=False)+"\n")
            print(f"[{index:02d}/60] rep={rep} {kind} {mode}: {elapsed:.2f}s",flush=True)
    finally:
        server.terminate()
        try: server.wait(10)
        except subprocess.TimeoutExpired: server.kill()

if __name__=="__main__": main()
