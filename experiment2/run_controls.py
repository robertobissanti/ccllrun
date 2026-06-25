#!/usr/bin/env python3
import json, random, subprocess, uuid
from pathlib import Path
import run_experiment as ex

ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/"experiment2"/"results"

def main():
    warm=subprocess.run(["bash",str(ROOT/"ccllrun"),"servers"],cwd=ROOT,capture_output=True,text=True,timeout=600)
    if warm.returncode: raise RuntimeError(warm.stdout+warm.stderr)
    progress=OUT/"control_runs.jsonl"; done=set()
    if progress.exists():
      for line in progress.read_text().splitlines():
        r=json.loads(line);done.add((r["rep"],r["condition"]))
    # L'ordine non cambia dentro una replica: persistent_control, poi resume_control.
    # Cambiano soltanto i dati generati tra repliche, già fissati dal seed principale.
    for rep in range(1,11):
      values,label,prompts=ex.prompts_for(rep)
      for condition in ("persistent_control","resume_control"):
        if (rep,condition) in done:continue
        cwd=OUT/f"rep_{rep:02d}"/condition;cwd.mkdir(parents=True,exist_ok=True)
        sid=str(uuid.uuid4())
        turns=ex.run_persistent(cwd,sid,prompts) if condition.startswith("persistent") else ex.run_resume(cwd,sid,prompts)
        row={"rep":rep,"condition":condition,"values":values,"label":label,"prompts":prompts,"turns":ex.compact(turns)}
        (cwd/"events.json").write_text(json.dumps(turns,indent=2,ensure_ascii=False))
        with progress.open("a") as f:f.write(json.dumps(row,ensure_ascii=False)+"\n")
        print(f"rep {rep}/10 {condition}: "+", ".join(f"{t['seconds']:.2f}s" for t in row["turns"]),flush=True)

if __name__=="__main__":main()
