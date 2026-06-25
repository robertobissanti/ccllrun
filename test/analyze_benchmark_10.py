#!/usr/bin/env python3
import itertools, json, math, statistics
from pathlib import Path
import run_benchmark as base

ROOT=Path(__file__).resolve().parent
OUT=ROOT/"results_10"
rows=[json.loads(x) for x in (OUT/"runs.jsonl").read_text().splitlines()]

def ci95(xs):
    n=len(xs); mean=statistics.mean(xs)
    return [mean-2.262*statistics.stdev(xs)/math.sqrt(n),mean+2.262*statistics.stdev(xs)/math.sqrt(n)]

def wilson(k,n,z=1.96):
    p=k/n; den=1+z*z/n; center=(p+z*z/(2*n))/den
    half=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/den
    return [center-half,center+half]

def paired_stats(kind,field):
    diffs=[]
    for rep in range(1,11):
        c=next(r for r in rows if r["rep"]==rep and r["test"]==kind and r["mode"]=="cli")
        s=next(r for r in rows if r["rep"]==rep and r["test"]==kind and r["mode"]=="studio")
        get=(lambda r:r["seconds"]) if field=="seconds" else (lambda r:r["usage"][field])
        diffs.append(get(s)-get(c))
    obs=abs(statistics.mean(diffs)); perms=[]
    for signs in itertools.product((-1,1),repeat=len(diffs)):
        perms.append(abs(statistics.mean(d*s for d,s in zip(diffs,signs))))
    return {"studio_minus_cli_mean":statistics.mean(diffs),"ci95":ci95(diffs),
            "exact_sign_flip_p_two_sided":sum(x>=obs-1e-12 for x in perms)/len(perms)}

summary={"n":len(rows),"groups":{},"paired_effects":{},"paired_similarity":{}}
for kind in ("poesia","python","c"):
  for mode in ("cli","studio"):
    rs=[r for r in rows if r["test"]==kind and r["mode"]==mode]
    sec=[r["seconds"] for r in rs]; inp=[r["usage"]["input_tokens"] for r in rs]
    out=[r["usage"]["output_tokens"] for r in rs]
    ok=[(r["accuracy"].get("formal_score",0)==1) if kind=="poesia" else bool(r["accuracy"].get("pass")) for r in rs]
    summary["groups"][f"{kind}_{mode}"]={"n":len(rs),"seconds_mean":statistics.mean(sec),
      "seconds_median":statistics.median(sec),"seconds_sd":statistics.stdev(sec),"seconds_ci95":ci95(sec),
      "input_mean":statistics.mean(inp),"output_mean":statistics.mean(out),"successes":sum(ok),
      "success_rate":sum(ok)/len(ok),"success_rate_wilson_ci95":wilson(sum(ok),len(ok)),
      "timeouts":sum(bool(r.get("run_error")) for r in rs)}
  summary["paired_effects"][kind]={f:paired_stats(kind,f) for f in ("seconds","input_tokens","output_tokens")}
  sims=[]
  for rep in range(1,11):
    a=(OUT/f"rep_{rep:02d}"/f"{kind}_cli"/"artifact.txt").read_text()
    b=(OUT/f"rep_{rep:02d}"/f"{kind}_studio"/"artifact.txt").read_text()
    sims.append(base.similarity(a,b))
  summary["paired_similarity"][kind]={k:statistics.mean(x[k] for x in sims) for k in sims[0]}
(OUT/"analysis.json").write_text(json.dumps(summary,indent=2,ensure_ascii=False))
print(json.dumps(summary,indent=2,ensure_ascii=False))
