"""
Direct agent evaluation — bypasses HTTP, calls run_exercise_agent and
generate_worksheet_preview directly so we can see real output and errors.
Run from BACKEND folder: python test/eval_direct.py
"""
import sys, os, json, time, traceback
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.agent_service import run_exercise_agent
from services.didactic_agent import generate_worksheet_preview
from core.database import get_db_connection

RATE_LIMIT_DELAY = 13

ADULT_CASES = [
    ("english", "B2", "grammar", "multiple-choice", "romanian"),
    ("english", "B2", "vocabulary", "fill-in-the-blank", "romanian"),
    ("english", "B2", "writing", "translation", "romanian"),
    ("english", "B2", "communication", "match", "romanian"),
    ("french", "B1", "grammaire", "multiple-choice", "romanian"),
    ("french", "B1", "vocabulaire", "fill-in-the-blank", "romanian"),
    ("romanian", "A1", "gramatica", "multiple-choice", "english"),
    ("romanian", "A1", "vocabular", "translation", "english"),
]

print("=" * 60)
print("AGENT FOR ADULT LEARNER")
print("=" * 60)

adult_results = []
for lang, level, topic, ex_type, native in ADULT_CASES:
    print(f"\n[{ex_type:20s}] {lang} {level} '{topic}'")
    t0 = time.time()
    try:
        result = run_exercise_agent(
            user_id=0,
            topic=topic,
            level=level,
            exercise_type=ex_type,
            language=lang,
            skill_type=None,
            native_language=native,
            conn=None,
        )
        elapsed = round(time.time() - t0, 2)
        if result:
            print(f"OK ({elapsed}s)")
            print(f"type={result.get('type')} | answer={str(result.get('correct_answer',''))[:60]}")
            content = result.get("content", {})
            if isinstance(content, str):
                content = json.loads(content)
            q = content.get("question") or content.get("base_sentence") or ""
            print(f"question: {str(q)[:100]}")
            adult_results.append({"status": "OK", "lang": lang, "type": ex_type})
        else:
            print(f"NONE returned ({elapsed}s)")
            adult_results.append({"status": "NONE", "lang": lang, "type": ex_type})
    except Exception as e:
        elapsed = round(time.time() - t0, 2)
        print(f"EXCEPTION ({elapsed}s): {e}")
        traceback.print_exc()
        adult_results.append({"status": "ERROR", "lang": lang, "type": ex_type, "error": str(e)})
    time.sleep(RATE_LIMIT_DELAY)

print("\n\n" + "=" * 60)
print("AGENT FOR TEACHERS")
print("=" * 60)

TEACHER_CASES = [
    {
        "manual_id": 4, # english B2, teacher_id=2
        "teacher_id": 2,
        "topic": "grammar",
        "level": "B2",
        "language": "english",
        "native_language": "romanian",
        "exercise_counts": {
            "multiple-choice": 2,
            "fill-in-the-blank": 2,
            "translation": 1,
        }
    },
    {
        "manual_id": 6, # french B2, teacher_id=10
        "teacher_id": 10,
        "topic": "vocabulaire",
        "level": "B2",
        "language": "french",
        "native_language": "romanian",
        "exercise_counts": {
            "multiple-choice": 1,
            "translation": 1,
        }
    },
]

teacher_results = []
db_conn = None
try:
    db_conn = get_db_connection()
    print("DB connection OK")
except Exception as e:
    print(f"DB connection FAILED: {e}. Teacher agent tests will be skipped")

for case in TEACHER_CASES:
    if db_conn is None:
        teacher_results.append({"status": "ERROR", "error": "no DB connection"})
        continue
    print(f"\nManual {case['manual_id']} | {case['language']} {case['level']} '{case['topic']}'")
    t0 = time.time()
    try:
        preview = generate_worksheet_preview(
            manual_id=case["manual_id"],
            teacher_id=case["teacher_id"],
            topic=case["topic"],
            level=case["level"],
            language=case["language"],
            native_language=case["native_language"],
            exercise_counts=case["exercise_counts"],
            conn=db_conn,
        )
        elapsed = round(time.time() - t0, 2)
        items = preview.get("items", [])
        total = preview.get("total_requested", 0)
        ok = preview.get("generated_count", 0)
        failed = preview.get("failed_count", 0)
        print(f"Done ({elapsed}s): {ok}/{total} generated, {failed} failed")
        for i, item in enumerate(items):
            warns = item.get("warnings", [])
            w_str = f"Warning {'; '.join(warns)}" if warns else ""
            ans = str(item.get("correct_answer",""))[:50]
            print(f" [{i+1}] {item.get('exercise_type'):20s} ans={ans}{w_str}")
        teacher_results.append({"status": "OK", "ok": ok, "failed": failed, "items": len(items)})
    except Exception as e:
        elapsed = round(time.time() - t0, 2)
        print(f"EXCEPTION ({elapsed}s): {e}")
        traceback.print_exc()
        teacher_results.append({"status": "ERROR", "error": str(e)})

if db_conn:
    db_conn.close()

print("\n\n" + "=" * 60)
print("SUMMARY")
print("=" * 60)
ok_s = sum(1 for r in adult_results if r["status"] == "OK")
print(f"Agent for adult learner : {ok_s}/{len(adult_results)} OK")
for r in adult_results:
    icon = "ok" if r["status"] == "OK" else "x"
    err = f" - {r.get('error','')[:50]}" if r["status"] == "ERROR" else ""
    print(f"{icon} {r['type']:20s} {r['lang']}{err}")

print()
for r in teacher_results:
    if r["status"] == "OK":
        print(f"Agent for teachers: {r['ok']}/{r['items']} exercises generated correctly, {r['failed']} failed")
    else:
        print(f"Agent for teachers: ERROR - {r.get('error','')[:80]}")
