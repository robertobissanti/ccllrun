#!/usr/bin/env python3
import fcntl, json, os, random, subprocess, time, uuid
from pathlib import Path

ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/"experiment2"/"results"
REPS=10
SEED=20260619

def event(prompt,session_id):
    return {"type":"user","message":{"role":"user","content":prompt}}

def read_turn(proc,timeout=180):
    started=time.monotonic(); events=[]
    while time.monotonic()-started < timeout:
        line=proc.stdout.readline()
        if not line:
            err=proc.stderr.read() if proc.stderr else ""
            raise RuntimeError("EOF prima del result: "+err[-1200:])
        try: obj=json.loads(line)
        except Exception: continue
        events.append(obj)
        if obj.get("type")=="result": return events,obj
    raise TimeoutError("turn timeout")

def command(session_id,resume=None):
    cmd=["claude","-p","--input-format","stream-json","--output-format","stream-json","--verbose",
         "--replay-user-messages","--permission-mode","bypassPermissions","--tools","",
         "--effort","low","--bare","--setting-sources","","--disable-slash-commands",
         "--strict-mcp-config","--mcp-config",'{"mcpServers":{}}']
    if resume: cmd += ["--resume",resume]
    else: cmd += ["--session-id",session_id]
    return cmd

def env():
    e=os.environ.copy(); cfg=json.loads((Path.home()/".ccllrun/config.json").read_text())
    e.update({"ANTHROPIC_BASE_URL":f"http://127.0.0.1:{cfg['proxy_port']}",
      "ANTHROPIC_AUTH_TOKEN":e.get("ANTHROPIC_AUTH_TOKEN","sk-local"),
      "ANTHROPIC_API_KEY":"sk-local",
      "ANTHROPIC_MODEL":str(cfg.get("model_big","qwen-big")),
      "ANTHROPIC_SMALL_FAST_MODEL":str(cfg.get("model_small","small-fast")),
      "CLAUDE_CODE_AUTO_COMPACT_WINDOW":str(cfg.get("cc_auto_compact_window",115000)),
      "CLAUDE_CODE_MAX_OUTPUT_TOKENS":str(cfg.get("cc_max_output_tokens",32000)),
      "ENABLE_TOOL_SEARCH":""})
    return e

def prompts_for(rep):
    rng=random.Random(SEED+rep)
    values=[rng.randint(-50,50) for _ in range(9)]
    label=f"R{rep}-{rng.randrange(100000,999999)}"
    p1=f"Variabili temporanee di questa conversazione, da usare nei prossimi turni senza strumenti e senza salvarle su file: label={label}; valori={values}. Rispondi soltanto con JSON valido {{\"ack\":true,\"sum\":S}}, dove S e la somma."
    p2="Usando i valori originali del turno precedente, rispondi soltanto con JSON valido con chiavi sorted_unique (lista crescente senza duplicati) ed even_count (numero di elementi pari nella lista originale)."
    p3="Usando esclusivamente i dati originali memorizzati nei turni precedenti, rispondi soltanto con JSON valido con chiavi label, sum, sorted_unique, even_count e reversed (lista originale in ordine inverso). Nessun markdown o commento."
    return values,label,[p1,p2,p3]

def run_persistent(cwd,sid,prompts):
    p=subprocess.Popen(command(sid),cwd=cwd,env=env(),stdin=subprocess.PIPE,stdout=subprocess.PIPE,
                       stderr=subprocess.PIPE,text=True,bufsize=1)
    turns=[]
    try:
      for prompt in prompts:
        t=time.perf_counter(); p.stdin.write(json.dumps(event(prompt,sid))+"\n"); p.stdin.flush()
        events,result=read_turn(p); turns.append({"seconds":time.perf_counter()-t,"events":events,"result":result})
    finally:
      p.stdin.close();
      try:p.wait(10)
      except subprocess.TimeoutExpired:p.kill()
    return turns

def run_resume(cwd,sid,prompts):
    turns=[]
    for i,prompt in enumerate(prompts):
      p=subprocess.Popen(command(sid,sid if i else None),cwd=cwd,env=env(),stdin=subprocess.PIPE,
                         stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,bufsize=1)
      t=time.perf_counter(); p.stdin.write(json.dumps(event(prompt,sid))+"\n"); p.stdin.close()
      events,result=read_turn(p); p.wait(20)
      turns.append({"seconds":time.perf_counter()-t,"events":events,"result":result})
    return turns

def compact(turns):
    return [{"seconds":t["seconds"],"text":t["result"].get("result",""),
             "usage":t["result"].get("usage",{}),"session_id":t["result"].get("session_id")}
            for t in turns]

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    lock=(OUT/"runner.lock").open("w"); fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    warm=subprocess.run(["bash",str(ROOT/"ccllrun"),"servers"],cwd=ROOT,capture_output=True,text=True,timeout=600)
    (OUT/"stack_start.txt").write_text(warm.stdout+warm.stderr)
    if warm.returncode: raise RuntimeError("stack: "+warm.stdout+warm.stderr)
    schedule=[]
    for rep in range(1,REPS+1):
      order=["persistent","resume"]
      random.Random(SEED*100+rep).shuffle(order)
      schedule.append({"rep":rep,"condition_order":order})
    (OUT/"schedule.json").write_text(json.dumps(schedule,indent=2))
    progress=OUT/"runs.jsonl"; done=set()
    if progress.exists():
      for line in progress.read_text().splitlines():
        r=json.loads(line); done.add((r["rep"],r["condition"]))
    for item in schedule:
      rep=item["rep"]; values,label,prompts=prompts_for(rep)
      (OUT/f"rep_{rep:02d}_prompts.json").write_text(json.dumps({"values":values,"label":label,"prompts":prompts},indent=2,ensure_ascii=False))
      for condition in item["condition_order"]:
        if (rep,condition) in done: continue
        cwd=OUT/f"rep_{rep:02d}"/condition; cwd.mkdir(parents=True,exist_ok=True)
        sid=str(uuid.uuid4())
        turns=run_persistent(cwd,sid,prompts) if condition=="persistent" else run_resume(cwd,sid,prompts)
        row={"rep":rep,"condition":condition,"values":values,"label":label,"prompts":prompts,"turns":compact(turns)}
        (cwd/"events.json").write_text(json.dumps(turns,indent=2,ensure_ascii=False))
        with progress.open("a") as f:f.write(json.dumps(row,ensure_ascii=False)+"\n")
        print(f"rep {rep}/10 {condition}: "+", ".join(f"{t['seconds']:.2f}s" for t in row["turns"]),flush=True)

if __name__=="__main__":main()
