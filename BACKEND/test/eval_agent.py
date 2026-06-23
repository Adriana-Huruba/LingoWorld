"""
Evaluation script for LingoWorld exercise generation agent.
Tests all 4 exercise types across 2 languages and 2 levels.
Collects: success rate, retry rate, validation errors, structural correctness.
"""

import requests
import json
import time
from datetime import datetime

API_URL = "http://localhost:8000/api/generate-exercise"

TEST_CASES = [
    # (language, level, topic, type, native_language)
    # --- ENGLISH B2 (cel mai bine reprezentat in Qdrant) ---
    ("english", "B2", "grammar",          "multiple-choice",   "romanian"),
    ("english", "B2", "reading",          "multiple-choice",   "romanian"),
    ("english", "B2", "communication",    "multiple-choice",   "romanian"),
    ("english", "B2", "vocabulary",       "multiple-choice",   "romanian"),
    ("english", "B2", "writing",          "multiple-choice",   "romanian"),

    ("english", "B2", "grammar",          "fill-in-the-blank", "romanian"),
    ("english", "B2", "reading",          "fill-in-the-blank", "romanian"),
    ("english", "B2", "communication",    "fill-in-the-blank", "romanian"),
    ("english", "B2", "vocabulary",       "fill-in-the-blank", "romanian"),
    ("english", "B2", "writing",          "fill-in-the-blank", "romanian"),

    ("english", "B2", "grammar",          "translation",       "romanian"),
    ("english", "B2", "reading",          "translation",       "romanian"),
    ("english", "B2", "communication",    "translation",       "romanian"),
    ("english", "B2", "vocabulary",       "translation",       "romanian"),
    ("english", "B2", "writing",          "translation",       "romanian"),

    ("english", "B2", "grammar",          "match",             "romanian"),
    ("english", "B2", "reading",          "match",             "romanian"),
    ("english", "B2", "communication",    "match",             "romanian"),
    ("english", "B2", "vocabulary",       "match",             "romanian"),
    ("english", "B2", "writing",          "match",             "romanian"),

    # --- FRENCH B1 ---
    ("french", "B1", "grammaire",         "multiple-choice",   "romanian"),
    ("french", "B1", "vocabulaire",       "multiple-choice",   "romanian"),
    ("french", "B1", "communication",     "fill-in-the-blank", "romanian"),
    ("french", "B1", "grammaire",         "fill-in-the-blank", "romanian"),
    ("french", "B1", "vocabulaire",       "translation",       "romanian"),

    # --- ROMANIAN A1 (putine date, testeaza fallback) ---
    ("romanian", "A1", "gramatica",       "multiple-choice",   "english"),
    ("romanian", "A1", "vocabular",       "multiple-choice",   "english"),
    ("romanian", "A1", "comunicare",      "fill-in-the-blank", "english"),
    ("romanian", "A1", "gramatica",       "translation",       "english"),
    ("romanian", "A1", "vocabular",       "match",             "english"),

    # --- ENGLISH B1 ---
    ("english", "B1", "grammar",          "multiple-choice",   "romanian"),
    ("english", "B1", "communication",    "multiple-choice",   "romanian"),
    ("english", "B1", "vocabulary",       "fill-in-the-blank", "romanian"),
    ("english", "B1", "grammar",          "translation",       "romanian"),
    ("english", "B1", "communication",    "match",             "romanian"),

    # --- ENGLISH B2 extra pentru match ---
    ("english", "B2", "present simple",   "multiple-choice",   "romanian"),
    ("english", "B2", "past tense",       "fill-in-the-blank", "romanian"),
    ("english", "B2", "conditionals",     "translation",       "romanian"),
    ("english", "B2", "passive voice",    "match",             "romanian"),
    ("english", "B2", "modal verbs",      "multiple-choice",   "romanian"),
]

def validate_exercise(ex_type, content):
    """Client-side structural validation — mirrors what the agent does."""
    warnings = []

    if ex_type == "multiple-choice":
        opts = content.get("options", [])
        ans  = content.get("answer", "")
        q    = content.get("question", "")
        if len(opts) != 4:
            warnings.append(f"options count = {len(opts)} (expected 4)")
        if ans not in opts:
            warnings.append("answer not in options")
        if len(set(o.lower() for o in opts)) != len(opts):
            warnings.append("duplicate options")
        if not q:
            warnings.append("missing question")

    elif ex_type == "fill-in-the-blank":
        if not content.get("question"):
            warnings.append("missing question")
        if not content.get("answer"):
            warnings.append("missing answer")
        if "___" not in content.get("question", "") and "_" not in content.get("question", ""):
            warnings.append("no blank marker in question")

    elif ex_type == "translation":
        if not content.get("answer"):
            warnings.append("missing answer")
        if not content.get("base_sentence") and not content.get("question"):
            warnings.append("missing source sentence")

    elif ex_type == "match":
        pairs = content.get("pairs", [])
        if len(pairs) < 3:
            warnings.append(f"only {len(pairs)} pairs (expected ≥5)")
        for p in pairs:
            if not p.get("target") or not p.get("native"):
                warnings.append("incomplete pair")
                break

    return warnings


results = []
by_type = {t: {"total": 0, "success": 0, "warnings": 0, "failed": 0, "times": []}
           for t in ["multiple-choice", "fill-in-the-blank", "translation", "match"]}

print(f"Starting evaluation — {len(TEST_CASES)} test cases\n{'='*60}")

for i, (lang, level, topic, ex_type, native) in enumerate(TEST_CASES):
    payload = {
        "user_id": 0,
        "topic": topic,
        "level": level,
        "type": ex_type,
        "language": lang,
        "native_language": native,
        "skill_type": None
    }

    t0 = time.time()
    try:
        resp = requests.post(API_URL, json=payload, timeout=60)
        elapsed = round(time.time() - t0, 2)

        if resp.status_code != 200:
            status = "HTTP_ERROR"
            result_row = {
                "id": i+1, "language": lang, "level": level, "topic": topic,
                "type": ex_type, "status": status, "warnings": [],
                "http_code": resp.status_code, "time": elapsed, "content": {}
            }
            by_type[ex_type]["total"] += 1
            by_type[ex_type]["failed"] += 1
            results.append(result_row)
            print(f"[{i+1:02d}] {ex_type:20s} {lang:8s} {level} '{topic}' → HTTP {resp.status_code} ({elapsed}s)")
            time.sleep(1)
            continue

        data = resp.json()
        content_raw = data.get("content", {})
        # content may be a string (JSON-encoded) or dict
        if isinstance(content_raw, str):
            try:
                content = json.loads(content_raw)
            except Exception:
                content = {}
        else:
            content = content_raw

        # flatten: some exercises nest under "questions"
        if "questions" in content and isinstance(content["questions"], list) and content["questions"]:
            q0 = content["questions"][0]
            content = {**content, **q0}

        warnings = validate_exercise(ex_type, content)
        has_content = bool(content)

        if not has_content:
            status = "EMPTY"
        elif warnings:
            status = "WARN"
        else:
            status = "OK"

        by_type[ex_type]["total"] += 1
        if status == "OK":
            by_type[ex_type]["success"] += 1
        elif status == "WARN":
            by_type[ex_type]["warnings"] += 1
        else:
            by_type[ex_type]["failed"] += 1

        by_type[ex_type]["times"].append(elapsed)

        result_row = {
            "id": i+1, "language": lang, "level": level, "topic": topic,
            "type": ex_type, "status": status, "warnings": warnings,
            "http_code": resp.status_code, "time": elapsed, "content": content
        }
        results.append(result_row)
        warn_str = "; ".join(warnings) if warnings else "—"
        print(f"[{i+1:02d}] {ex_type:20s} {lang:8s} {level} '{topic}' → {status} ({elapsed}s) {warn_str}")

    except requests.exceptions.Timeout:
        elapsed = round(time.time() - t0, 2)
        by_type[ex_type]["total"] += 1
        by_type[ex_type]["failed"] += 1
        results.append({"id": i+1, "type": ex_type, "status": "TIMEOUT", "warnings": [], "time": elapsed, "content": {}})
        print(f"[{i+1:02d}] {ex_type:20s} {lang:8s} {level} '{topic}' → TIMEOUT")

    except Exception as e:
        elapsed = round(time.time() - t0, 2)
        by_type[ex_type]["total"] += 1
        by_type[ex_type]["failed"] += 1
        results.append({"id": i+1, "type": ex_type, "status": "ERROR", "warnings": [], "time": elapsed, "content": {}})
        print(f"[{i+1:02d}] {ex_type:20s} {lang:8s} {level} '{topic}' → ERROR: {e}")

    time.sleep(1.2)  # polite rate limiting

# ── SUMMARY ──────────────────────────────────────────────────────────────────
print(f"\n{'='*60}")
print("SUMMARY BY EXERCISE TYPE")
print(f"{'='*60}")
print(f"{'Type':<22} {'Total':>6} {'OK':>6} {'WARN':>6} {'FAIL':>6} {'OK%':>7} {'AvgTime':>9}")
print("-"*60)

for t, d in by_type.items():
    total = d["total"]
    ok    = d["success"]
    warn  = d["warnings"]
    fail  = d["failed"]
    pct   = round(ok / total * 100, 1) if total else 0
    avg_t = round(sum(d["times"]) / len(d["times"]), 2) if d["times"] else 0
    print(f"{t:<22} {total:>6} {ok:>6} {warn:>6} {fail:>6} {pct:>6}% {avg_t:>8}s")

print("-"*60)
total_all = sum(d["total"] for d in by_type.values())
ok_all    = sum(d["success"] for d in by_type.values())
warn_all  = sum(d["warnings"] for d in by_type.values())
fail_all  = sum(d["failed"] for d in by_type.values())
all_times = [t for d in by_type.values() for t in d["times"]]
print(f"{'TOTAL':<22} {total_all:>6} {ok_all:>6} {warn_all:>6} {fail_all:>6} {round(ok_all/total_all*100,1) if total_all else 0:>6}% {round(sum(all_times)/len(all_times),2) if all_times else 0:>8}s")

# ── WARNINGS BREAKDOWN ────────────────────────────────────────────────────────
warn_counts = {}
for r in results:
    for w in r.get("warnings", []):
        warn_counts[w] = warn_counts.get(w, 0) + 1

if warn_counts:
    print(f"\nWARNINGS BREAKDOWN")
    print("-"*40)
    for w, c in sorted(warn_counts.items(), key=lambda x: -x[1]):
        print(f"  {c:>3}x  {w}")

# ── SAVE FULL RESULTS ─────────────────────────────────────────────────────────
out_path = "eval_results.json"
with open(out_path, "w", encoding="utf-8") as f:
    json.dump({"timestamp": datetime.now().isoformat(), "results": results, "summary": by_type}, f, ensure_ascii=False, indent=2)
print(f"\nFull results saved to {out_path}")
