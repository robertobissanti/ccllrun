#!/usr/bin/env python3
import difflib,json,math,re,statistics
from pathlib import Path
OUT=Path(__file__).resolve().parent/"results"
rows=[json.loads(x) for x in (OUT/"runs.jsonl").read_text().splitlines()]

def parse(s):
    try:return json.loads(s.strip().removeprefix("```json").removesuffix("```").strip())
    except:return None
def expected(r):
    v=r["values"]
    return [{"ack":True,"sum":sum(v)},
      {"sorted_unique":sorted(set(v)),"even_count":sum(x%2==0 for x in v)},
      {"label":r["label"],"sum":sum(v),"sorted_unique":sorted(set(v)),"even_count":sum(x%2==0 for x in v),"reversed":v[::-1]}]
def ci(xs):
    m=statistics.mean(xs); h=2.262*statistics.stdev(xs)/math.sqrt(len(xs)); return [m-h,m+h]

result={"conditions":{},"paired":{},"exact_matches":[]}
for cond in ("persistent","resume"):
 rs=[r for r in rows if r["condition"]==cond]
 times=[sum(t["seconds"] for t in r["turns"]) for r in rs]
 outputs=[sum(int(t["usage"].get("output_tokens",0) or 0) for t in r["turns"]) for r in rs]
 correct=[]
 for r in rs:
   exp=expected(r); correct.append(sum(parse(t["text"])==e for t,e in zip(r["turns"],exp)))
 result["conditions"][cond]={"n":len(rs),"total_seconds_mean":statistics.mean(times),"total_seconds_ci95":ci(times),
   "output_tokens_mean":statistics.mean(outputs),"correct_turns":sum(correct),"total_turns":len(rs)*3,
   "fully_correct_replicas":sum(x==3 for x in correct)}
for rep in range(1,11):
 a=next(r for r in rows if r["rep"]==rep and r["condition"]=="persistent")
 b=next(r for r in rows if r["rep"]==rep and r["condition"]=="resume")
 for i,(x,y) in enumerate(zip(a["turns"],b["turns"]),1):
   aa=re.sub(r"\s+","",x["text"]);bb=re.sub(r"\s+","",y["text"])
   result["exact_matches"].append({"rep":rep,"turn":i,"exact":aa==bb,"sequence":difflib.SequenceMatcher(None,aa,bb).ratio()})
result["paired"]={"exact_output_matches":sum(x["exact"] for x in result["exact_matches"]),"comparisons":30,
 "mean_sequence_similarity":statistics.mean(x["sequence"] for x in result["exact_matches"])}
(OUT/"analysis.json").write_text(json.dumps(result,indent=2,ensure_ascii=False));print(json.dumps(result,indent=2,ensure_ascii=False))
