#!/usr/bin/env python3
import itertools,json,math,statistics
from pathlib import Path
OUT=Path(__file__).resolve().parent/"results"
main=[json.loads(x) for x in (OUT/"runs.jsonl").read_text().splitlines()]
ctrl=[json.loads(x) for x in (OUT/"control_runs.jsonl").read_text().splitlines()]
rows=main+ctrl

def obj(s):
    try:return json.loads(s.strip().removeprefix("```json").removesuffix("```").strip())
    except:return None
def get(rep,cond):return next(r for r in rows if r["rep"]==rep and r["condition"]==cond)
def compare(a,b):
    pairs=[]
    for rep in range(1,11):
      x,y=get(rep,a),get(rep,b)
      for turn,(tx,ty) in enumerate(zip(x["turns"],y["turns"]),1):
        pairs.append({"rep":rep,"turn":turn,"semantic_equal":obj(tx["text"])==obj(ty["text"]),
                      "text_equal":''.join(tx["text"].split())==''.join(ty["text"].split())})
    return {"semantic_equal":sum(x["semantic_equal"] for x in pairs),"text_equal":sum(x["text_equal"] for x in pairs),
            "total":len(pairs),"semantic_mismatches":[x for x in pairs if not x["semantic_equal"]]}
def expected(r):
    v=r["values"]
    return [{"ack":True,"sum":sum(v)},{"sorted_unique":sorted(set(v)),"even_count":sum(x%2==0 for x in v)},
      {"label":r["label"],"sum":sum(v),"sorted_unique":sorted(set(v)),"even_count":sum(x%2==0 for x in v),"reversed":v[::-1]}]
def metrics(cond):
    rs=[r for r in rows if r["condition"]==cond];correct=0;full=0;times=[]
    for r in rs:
      oks=[obj(t["text"])==e for t,e in zip(r["turns"],expected(r))]
      correct+=sum(oks);full+=all(oks);times.append(sum(t["seconds"] for t in r["turns"]))
    return {"correct_turns":correct,"total_turns":30,"fully_correct_replicas":full,
            "seconds_mean":statistics.mean(times),"seconds_median":statistics.median(times)}

result={"conditions":{c:metrics(c) for c in ("persistent","persistent_control","resume","resume_control")},
 "comparisons":{"persistent_vs_resume":compare("persistent","resume"),
                "persistent_repeatability":compare("persistent","persistent_control"),
                "resume_repeatability":compare("resume","resume_control")}}
(OUT/"control_analysis.json").write_text(json.dumps(result,indent=2,ensure_ascii=False));print(json.dumps(result,indent=2,ensure_ascii=False))
