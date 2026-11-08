"""chase_judge.py - triage chase candidates with a local LLM, one hit per request (no tools, no agent).

Input: JSONL from chase_candidates.py, one candidate per line:
  {"id": "F-18#0007", "row": "F-18", "member": "StrafeForce", "owner": "RVehicleBatmobileBase",
   "offset": "0x11f8", "type": "float", "source": "exe 0x14123abcd" | "<package/ini path>:<offset>",
   "snippet": "<disassembly window or text context, <= ~4k tokens>"}
Output: JSONL verdicts appended to --out, one per candidate:
  {"id": ..., "found": true|false|null, "value": ..., "why": ..., "raw": <model text if unparsable>}
found=null means the model gave no usable JSON (treat as unjudged). Verdicts are triage only:
every found=true must be verified against the source address/offset before it enters FOOTAGE.md (R4).

Resumable: ids already in --out are skipped.

Usage:
  python Tools/scripts/chase/chase_judge.py --in candidates.jsonl --out verdicts.jsonl
         [--url http://127.0.0.1:8080/v1/chat/completions] [--model qwen3.5-4b] [--limit N]
"""
import argparse
import json
import re
import sys
import urllib.request

PROMPT = """You check ONE search hit. Answer ONLY with one JSON object, nothing else.

Question: does this snippet SET the default value of the member `{member}` (declared on `{owner}`, type {type}, \
field offset {offset})?

NEVER a default, whatever the snippet seems to show:
- a number equal (or close) to the field offset, e.g. {offset}=4200 shown as 4200: that is an offset table, \
not a value;
- a count (how many files or packages contain the name, `"{member}": 1`);
- a value that comes from a register or from memory with no constant visible in the snippet;
- a store into a stack frame (`[rsp+...]`, `[rbp+...]`, or a register loaded from rsp/rbp): that is a local, \
not the object;
- the field's own value changed (`+=`, `-=`, multiplied by a delta time, `movss xmm, [reg+{offset}]` then \
arithmetic then store): a per-frame update;
- a JSON/analysis record written by the search tool (offset maps, name counts, verdicts), not a game file.

found=true requires ALL of:
- the literal value is visible in the snippet, on the store's own line or in the instruction/line that loaded \
it (the annotate comment `; [0x...] = float X` counts as visible);
- that literal is stored into `[reg+{offset}]` (for text: a `key=value` / script assignment of `{member}`);
- the surrounding code looks like object initialisation (constructor / defaults), not a per-frame update.

If unsure, found=false. Never guess a value that is not written in the snippet.

Source: {source}
Snippet:
{snippet}

Reply exactly: {{"found": true or false, "value": "<literal from the snippet or empty>", "why": "<one short sentence>"}}"""


def ask(url, model, text):
    body = json.dumps({"model": model, "messages": [{"role": "user", "content": text}],
                       "temperature": 0, "max_tokens": 400,
                       "chat_template_kwargs": {"enable_thinking": False}}).encode()
    req = urllib.request.Request(url, body, {"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=600) as r:
        return json.load(r)["choices"][0]["message"]["content"]


def parse(raw):
    m = re.search(r"\{.*\}", raw, re.S)
    if not m:
        return None
    try:
        v = json.loads(m.group(0))
    except json.JSONDecodeError:
        return None
    return v if isinstance(v.get("found"), bool) else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="inp", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--url", default="http://127.0.0.1:8080/v1/chat/completions")
    ap.add_argument("--model", default="qwen3.5-4b")
    ap.add_argument("--limit", type=int, default=0)
    a = ap.parse_args()
    done = set()
    try:
        with open(a.out, encoding="utf8") as f:
            done = {json.loads(l)["id"] for l in f if l.strip()}
    except FileNotFoundError:
        pass
    n = hits = bad = 0
    with open(a.inp, encoding="utf8") as f, open(a.out, "a", encoding="utf8") as out:
        for line in f:
            if not line.strip():
                continue
            c = json.loads(line)
            if c["id"] in done:
                continue
            raw = ask(a.url, a.model, PROMPT.format(**{k: c.get(k, "?") for k in
                      ("member", "owner", "type", "offset", "source", "snippet")}))
            v = parse(raw)
            rec = {"id": c["id"], "row": c.get("row"), "source": c.get("source")}
            rec.update(v if v else {"found": None, "raw": raw[:500]})
            out.write(json.dumps(rec) + "\n")
            out.flush()
            n += 1
            hits += rec["found"] is True
            bad += rec["found"] is None
            print(f"{c['id']}: {rec['found']} {rec.get('value', '')}", flush=True)
            if a.limit and n >= a.limit:
                break
    print(f"judged {n}: {hits} found, {bad} unparsable", file=sys.stderr)


if __name__ == "__main__":
    main()
