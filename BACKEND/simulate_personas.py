import argparse
import json
import os
import random

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Optional

import matplotlib
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

CEFR_TO_ELO: dict[str, int] = {
    "A1": 200, "A2": 500, "B1": 700,
    "B2": 900, "C1": 1100, "C2": 1400,
}

CEFR_LEVELS: dict[str, tuple[int, int]] = {
    "A1": (0, 400), "A2": (400, 600),
    "B1": (600, 800), "B2": (800, 1000),
    "C1": (1000, 1200), "C2": (1200, 1600),
}

CEFR_ORDER = ["A1", "A2", "B1", "B2", "C1", "C2"]
ELO_K_NEW = 32
ELO_K_STABLE  = 16

EXPECTED_TIME_PER_TYPE = {
    "multiple-choice": 8,
    "fill-in-the-blank": 20,
    "translation": 35,
}


def elo_expected_score(user_elo: int, item_elo: int) -> float:
    return 1.0 / (1.0 + 10.0 ** ((item_elo - user_elo) / 400.0))


def calculate_new_elo(user_elo: int, item_elo: int, correct: bool, total_responses: int) -> int:
    k = ELO_K_NEW if total_responses < 20 else ELO_K_STABLE
    expected = elo_expected_score(user_elo, item_elo)
    actual = 1.0 if correct else 0.0
    new_elo = user_elo + k * (actual - expected)
    return max(0, min(1600, round(new_elo)))


def elo_to_cefr(elo: int) -> str:
    for level, (low, high) in CEFR_LEVELS.items():
        if low <= elo < high:
            return level
    return "C2"


def cefr_to_elo(level: str) -> int:
    return CEFR_TO_ELO.get(level, 200)


def get_target_levels(user_elo: int) -> list:
    current_level = elo_to_cefr(user_elo)
    index = CEFR_ORDER.index(current_level)
    low, high = CEFR_LEVELS[current_level]
    position  = (user_elo - low) / (high - low) if high > low else 0.5
    levels = [current_level]

    if position >= 0.80 and index < len(CEFR_ORDER) - 1:
        levels.append(CEFR_ORDER[index + 1])
    if position <= 0.20 and index > 0:
        levels.append(CEFR_ORDER[index - 1])
    return levels
 

def estimate_quality(is_correct: bool, used_hint: bool, response_time: float, exercise_type: str) -> int:
    """Map response quality to SM-2 q score (1-5)."""
    expected = EXPECTED_TIME_PER_TYPE.get(exercise_type, 15)
    ratio = response_time / expected
    if not is_correct:
        return 2 if ratio < 1.0 else 1
    if used_hint:
        return 3
    if ratio < 0.5: 
        return 5
    if ratio < 1.0:  
        return 4
    if ratio < 2.0:  
        return 3
    return 2


def calculate_next_review_sm2(is_correct, used_hint, response_time, exercise_type, consecutive_correct, easiness_factor, last_interval):
    q = estimate_quality(is_correct, used_hint, response_time, exercise_type)
    if q < 3:
        new_interval = 1
        new_ef = easiness_factor
    else:
        if consecutive_correct == 0: new_interval = 1
        elif consecutive_correct == 1: new_interval = 6
        else:
            new_interval = round(last_interval * easiness_factor)
        new_ef = easiness_factor + (0.1 - (5 - q) * (0.08 + (5 - q) * 0.02))
        new_ef = max(1.3, new_ef)
    next_review = datetime.now(timezone.utc) + timedelta(days=new_interval)
    return next_review, new_ef, new_interval, q

EXERCISE_TYPES = ["multiple-choice", "fill-in-the-blank", "translation"]
TOPICS = ["grammar", "vocabulary", "reading", "writing"]


def build_exercise_pool(n_per_level: int = 30) -> list:
    pool  = []
    ex_id = 1
    for level, (low, high) in CEFR_LEVELS.items():
        for _ in range(n_per_level):
            elo_difficulty = random.randint(low + 10, high - 10)
            pool.append({
                "exercise_id": ex_id,
                "level": level,
                "elo_difficulty": elo_difficulty,
                "type": random.choice(EXERCISE_TYPES),
                "topic": random.choice(TOPICS),
            })
            ex_id += 1
    return pool


def pick_new_exercise(user_elo: int, pool: list, introduced: set) -> Optional[dict]:
    """Pick an unseen exercise using ZPD logic (closest ELO within target levels)."""
    target_levels = get_target_levels(user_elo)
    candidates = [
        ex for ex in pool
        if ex["exercise_id"] not in introduced and ex["level"] in target_levels
    ]
    if not candidates:
        candidates = [ex for ex in pool if ex["exercise_id"] not in introduced]
    if not candidates:
        return None
    candidates.sort(key=lambda ex: abs(ex["elo_difficulty"] - user_elo))
    return candidates[0]


@dataclass
class Persona:
    name: str
    description: str
    starting_elo: int
    true_ability_elo: int
    consistency: float
    hint_rate: float
    time_style: str

    elo: int = field(init=False)
    total_responses: int = field(init=False, default=0)
    xp: int = field(init=False, default=0)

    sm2_state: dict = field(init=False, default_factory=dict)
    elo_history: list = field(init=False, default_factory=list)  # one entry per answered exercise
    events: list = field(init=False, default_factory=list)
    daily_stats: list = field(init=False, default_factory=list)  # one entry per day

    def __post_init__(self):
        self.elo = self.starting_elo
        self.elo_history.append(self.elo)

    def compute_response(self, exercise: dict) -> tuple:
        item_elo = exercise["elo_difficulty"]
        ex_type = exercise["type"]

        p_base = elo_expected_score(self.true_ability_elo, item_elo)
        p = self.consistency * p_base + (1 - self.consistency) * 0.5
        is_correct = random.random() < p
        gap = item_elo - self.elo

        p_hint = self.hint_rate * (1 + max(0, gap) / 400)
        used_hint = random.random() < min(p_hint, 0.9)
        expected  = EXPECTED_TIME_PER_TYPE.get(ex_type, 15)

        if self.time_style == "fast": 
            factor = random.uniform(0.3, 0.8)
        elif self.time_style == "slow": 
            factor = random.uniform(1.2, 2.5)
        else:                         
            factor = random.uniform(0.6, 1.4)
        if not is_correct:
            factor *= random.uniform(1.0, 1.5)
        response_time = round(expected * factor, 1)

        return is_correct, used_hint, response_time

    def apply_answer(self, exercise: dict, is_correct: bool, used_hint: bool, response_time: float, day: int) -> dict:
        ex_id = exercise["exercise_id"]
        ex_type = exercise["type"]
        item_elo = exercise["elo_difficulty"]

        state = self.sm2_state.get(ex_id, {"ef": 2.5, "interval": 1, "consecutive": 0})
        prev_consecutive = state["consecutive"] if is_correct else 0

        old_elo = self.elo
        new_elo = calculate_new_elo(self.elo, item_elo, is_correct, self.total_responses)
        old_cefr = elo_to_cefr(old_elo)
        new_cefr = elo_to_cefr(new_elo)

        new_consecutive = (prev_consecutive + 1) if is_correct else 0
        _, new_ef, new_interval, quality = calculate_next_review_sm2(
            is_correct=is_correct, used_hint=used_hint,
            response_time=response_time, exercise_type=ex_type,
            consecutive_correct=prev_consecutive,
            easiness_factor=state["ef"], last_interval=state["interval"],
        )

        expected_time = EXPECTED_TIME_PER_TYPE.get(ex_type, 15)
        if is_correct and response_time < expected_time * 0.5: 
            xp_gained = 15
        elif is_correct:                           
            xp_gained = 10
        else:                                                  
            xp_gained = 0

        self.elo = new_elo
        self.total_responses += 1
        self.xp += xp_gained
        self.elo_history.append(new_elo)
        self.sm2_state[ex_id] = {
            "ef": new_ef, "interval": new_interval, "consecutive": new_consecutive }

        event = {
            "day": day,
            "attempt": self.total_responses,
            "exercise_id": ex_id,
            "level": exercise["level"],
            "type": ex_type,
            "topic": exercise["topic"],
            "item_elo": item_elo,
            "old_elo": old_elo,
            "new_elo": new_elo,
            "delta_elo": new_elo - old_elo,
            "old_cefr": old_cefr,
            "new_cefr": new_cefr,
            "level_changed": new_cefr != old_cefr,
            "is_correct": is_correct,
            "used_hint":  used_hint,
            "response_time": response_time,
            "quality":  quality,
            "sm2_interval": new_interval,
            "xp_gained": xp_gained,
            "target_levels": get_target_levels(old_elo),
        }
        self.events.append(event)
        return event


PERSONAS = [
    Persona(
        name="Elena",
        description="True beginner — starts from scratch, steadily progresses toward B1",
        starting_elo=200, true_ability_elo=650,
        consistency=0.80, hint_rate=0.30, time_style="normal",
    ),
    Persona(
        name="Andrei",
        description="False beginner — misclassified as A1 by the quiz, actually B2; rapid progression",
        starting_elo=200, true_ability_elo=950,
        consistency=0.90, hint_rate=0.05, time_style="fast",
    ),
    Persona(
        name="Maria",
        description="Intermediate plateau — solid B1 but struggles when pushed into B2",
        starting_elo=700, true_ability_elo=780,
        consistency=0.65, hint_rate=0.40, time_style="slow",
    ),
    Persona(
        name="Radu",
        description="Advanced learner — C1 refining toward C2, very few mistakes",
        starting_elo=1100, true_ability_elo=1350,
        consistency=0.92, hint_rate=0.03, time_style="fast",
    ),
    Persona(
        name="Tudor",
        description="Inconsistent learner — highly variable; SM-2 forces useful repetition",
        starting_elo=500, true_ability_elo=600,
        consistency=0.40, hint_rate=0.50, time_style="slow",
    ),
]


def run_simulation(days: int = 60, per_day: int = 6, seed: int = 42) -> list:
    random.seed(seed)
    pool = build_exercise_pool(n_per_level=30)
    pool_map = {ex["exercise_id"]: ex for ex in pool}

    for persona in PERSONAS:
        introduced: set = set()
        review_schedule: dict = {}

        print(f"\n{'─'*60}")
        print(f"{persona.name} | {persona.description}")
        print(f"Starting ELO: {persona.starting_elo} ({elo_to_cefr(persona.starting_elo)})")
        print(f"{'─'*60}")

        for day in range(1, days + 1):
            due_ids = [eid for eid, due in review_schedule.items() if due <= day]

            due_ids.sort(key=lambda eid: (review_schedule[eid] - day,
                abs(pool_map[eid]["elo_difficulty"] - persona.elo)
            ))
            today_exercises = [pool_map[eid] for eid in due_ids[:per_day]]

            slots_left = per_day - len(today_exercises)
            for _ in range(slots_left):
                ex = pick_new_exercise(persona.elo, pool, introduced)
                if ex:
                    today_exercises.append(ex)
                    introduced.add(ex["exercise_id"])

            if not today_exercises:
                print(f"  Day {day:3d}: no exercises available")
                continue

            n_reviews = len(due_ids[:per_day])
            n_new = len(today_exercises) - n_reviews
            intervals_today = []

            for exercise in today_exercises:
                is_correct, used_hint, response_time = persona.compute_response(exercise)
                event = persona.apply_answer(exercise, is_correct, used_hint, response_time, day)

                review_schedule[exercise["exercise_id"]] = day + event["sm2_interval"]
                intervals_today.append(event["sm2_interval"])

                marker = "+" if is_correct else "-"
                hint_m = "[hint]" if used_hint else ""
                lvl_ch = f"LEVEL UP: {event['new_cefr']}!" if event["level_changed"] else ""
                print(
                    f"Day {day:3d} | {marker}{hint_m} | "
                    f"Ex #{exercise['exercise_id']:3d} {exercise['level']} "
                    f"(ELO {exercise['elo_difficulty']:4d}) | "
                    f"ELO: {event['old_elo']:4d} -> {event['new_elo']:4d} "
                    f"({event['delta_elo']:+3d}) | "
                    f"SM-2 q={event['quality']} interval={event['sm2_interval']}d"
                    f"{lvl_ch}"
                )

            avg_interval = round(sum(intervals_today) / len(intervals_today), 2)
            max_interval = max(intervals_today)
            persona.daily_stats.append({
                "day": day,
                "elo": persona.elo,
                "n_reviews": n_reviews,
                "n_new": n_new,
                "avg_interval": avg_interval,
                "max_interval": max_interval,
            })

        final_cefr = elo_to_cefr(persona.elo)
        start_cefr = elo_to_cefr(persona.starting_elo)
        correct = sum(1 for e in persona.events if e["is_correct"])
        total = len(persona.events)

        all_intervals = [s["ef"] for s in persona.sm2_state.values()]
        max_ef = round(max(all_intervals), 2) if all_intervals else 2.5
        print(f"\nResult: ELO {persona.starting_elo} ({start_cefr}) - {persona.elo} ({final_cefr})")
        print(f"Answers: {correct}/{total} correct ({100*correct//max(1,total)}%)")
        print(f"Total XP: {persona.xp} | Max easiness factor: {max_ef}")

    return PERSONAS

def save_report(personas: list, path: str):
    report = []
    for p in personas:
        level_changes = [
            {"day": e["day"], "from": e["old_cefr"], "to": e["new_cefr"]}
            for e in p.events if e["level_changed"]
        ]
        total_by_level   = {}
        correct_by_level = {}

        for e in p.events:
            lvl = e["level"]
            total_by_level[lvl] = total_by_level.get(lvl, 0) + 1
            if e["is_correct"]:
                correct_by_level[lvl] = correct_by_level.get(lvl, 0) + 1
                
        accuracy_by_level= {lvl: round(correct_by_level.get(lvl, 0) / total_by_level[lvl], 2) for lvl in total_by_level}
        
        report.append({
            "persona": p.name,
            "description": p.description,
            "starting_elo": p.starting_elo,
            "final_elo": p.elo,
            "elo_delta": p.elo - p.starting_elo,
            "starting_cefr": elo_to_cefr(p.starting_elo),
            "final_cefr": elo_to_cefr(p.elo),
            "total_attempts": len(p.events),
            "correct_answers": sum(1 for e in p.events if e["is_correct"]),
            "total_xp": p.xp,
            "level_changes": level_changes,
            "accuracy_by_level": accuracy_by_level,
            "elo_history": p.elo_history,
            "daily_stats": p.daily_stats,
        })

    with open(path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print(f"\n[OK] Report saved: {path}")

def plot_results(personas: list, output_dir: str):
    try:
        matplotlib.use("Agg")
    except ImportError:
        print("matplotlib is not installed")
        return

    COLORS = ["#2196F3", "#4CAF50", "#FF9800", "#9C27B0", "#F44336"]

    # ELO progress
    fig, ax = plt.subplots(figsize=(12, 6))
    cefr_band_colors = {
        "A1": "#ffeeba", "A2": "#d4edda", "B1": "#cce5ff",
        "B2": "#d1ecf1", "C1": "#e2d9f3", "C2": "#f8d7da",
    }
    for level, (low, high) in CEFR_LEVELS.items():
        ax.axhspan(low, high, alpha=0.15, color=cefr_band_colors[level])
        ax.text(0.5, (low + high) / 2, level, transform=ax.get_yaxis_transform(), fontsize=8, color="gray", va="center", ha="left")

    for persona, color in zip(personas, COLORS):
        ax.plot(persona.elo_history, label=persona.name, color=color, linewidth=2, marker="o", markersize=2, alpha=0.85)

    ax.set_title("ELO Progression (per exercise attempt)", fontsize=14, fontweight="bold")
    ax.set_xlabel("Exercise attempts", fontsize=11)
    ax.set_ylabel("ELO", fontsize=11)
    ax.legend(loc="upper left", fontsize=9)
    ax.set_ylim(0, 1600)
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    path1 = os.path.join(output_dir, "sim_elo_evolution.png")
    plt.savefig(path1, dpi=150)
    plt.close()
    print(f"[OK] ELO chart saved: {path1}")

    # accuracy per CEFR level
    fig, axes = plt.subplots(1, len(personas), figsize=(14, 5), sharey=True)
    for ax, persona, color in zip(axes, personas, COLORS):
        total_by_level = {}
        correct_by_level = {}
        for e in persona.events:
            lvl = e["level"]
            total_by_level[lvl] = total_by_level.get(lvl, 0) + 1
            if e["is_correct"]:
                correct_by_level[lvl] = correct_by_level.get(lvl, 0) + 1

        levels_present = [l for l in CEFR_ORDER if l in total_by_level]
        accuracies = [correct_by_level.get(l, 0) / total_by_level[l] for l in levels_present]
        bar_colors = ["#4CAF50" if a >= 0.7 else "#FF9800" if a >= 0.4 else "#F44336" for a in accuracies]
        bars = ax.barh(levels_present, accuracies, color=bar_colors, alpha=0.8)
        ax.set_xlim(0, 1)
        ax.set_title(persona.name, fontsize=10, fontweight="bold", color=color)
        ax.axvline(0.7, color="gray", linestyle="--", linewidth=0.8, alpha=0.6)

        for bar, acc in zip(bars, accuracies):
            ax.text(min(acc + 0.02, 0.92), bar.get_y() + bar.get_height() / 2, f"{acc:.0%}", va="center", fontsize=8)

    axes[0].set_ylabel("CEFR Level", fontsize=10)
    fig.suptitle("Accuracy per CEFR Level", fontsize=13, fontweight="bold")
    fig.text(0.5, 0.01, "Accuracy  (dashed = 70% threshold)", ha="center", fontsize=9, color="gray")
    legend_patches = [
        mpatches.Patch(color="#4CAF50", label=">= 70% (mastered)"),
        mpatches.Patch(color="#FF9800", label="40-70% (in progress)"),
        mpatches.Patch(color="#F44336", label="< 40% (struggling)"),
    ]
    fig.legend(handles=legend_patches, loc="lower right", fontsize=8)
    plt.tight_layout(rect=[0, 0.04, 1, 0.96])
    path2 = os.path.join(output_dir, "sim_accuracy_by_level.png")
    plt.savefig(path2, dpi=150)
    plt.close()
    print(f"[OK] Accuracy chart saved: {path2}")

    # sm2- avg interval & review load per day 
    fig, axes = plt.subplots(2, 3, figsize=(15, 9))
    axes = axes.flatten()

    for i, (persona, color) in enumerate(zip(personas, COLORS)):
        ax = axes[i]
        days = [s["day"] for s in persona.daily_stats]
        avg_interval = [s["avg_interval"] for s in persona.daily_stats]
        n_reviews = [s["n_reviews"] for s in persona.daily_stats]
        n_new = [s["n_new"] for s in persona.daily_stats]

        ax2 = ax.twinx()

        # reviewed ex vs new
        ax.bar(days, n_new, color="#90CAF9", alpha=0.7, label="New")
        ax.bar(days, n_reviews, color=color, alpha=0.7, label="Reviews", bottom=n_new)
        ax.set_ylabel("Exercises per day", fontsize=7)
        ax.set_ylim(0, max(max(n_new) + max(n_reviews) + 1, 8))
        ax.tick_params(axis="y", labelsize=7)

        # average SM2 interval
        ax2.plot(days, avg_interval, color="black", linewidth=1.5, linestyle="-", alpha=0.85)
        ax2.set_ylabel("Avg SM-2 interval (days)", fontsize=7, color="black")
        ax2.tick_params(axis="y", labelsize=7)

        ax.set_title(f"{persona.name}", fontsize=10, fontweight="bold", color=color)
        ax.set_xlabel("Day", fontsize=8)
        ax.tick_params(axis="x", labelsize=7)

        if i == 0:
            ax.legend(loc="upper left", fontsize=7)

    axes[-1].set_visible(False)
    fig.suptitle(
        "SM-2 Spaced Repetition: review load vs average interval per day\n"
        "(bars = exercise count | black line = avg days until next review)",
        fontsize=11, fontweight="bold")
    plt.tight_layout()
    path3 = os.path.join(output_dir, "sim_sm2_intervals.png")
    plt.savefig(path3, dpi=150)
    plt.close()
    print(f"[OK] SM-2 chart saved: {path3}")


def main():
    parser = argparse.ArgumentParser( description="Persona simulation - adaptive recommender")
    
    parser.add_argument("--days", type=int, default=60, help="Number of simulated days (default: 60)")
    parser.add_argument("--per-day", type=int, default=6, help="Max exercises per day (default: 6)")
    parser.add_argument("--seed", type=int, default=42, help="Random seed (default: 42)")
    parser.add_argument("--plot", action="store_true", help="Generate PNG charts (requires matplotlib)")
    parser.add_argument("--out", type=str, default=".", help="Output directory for report and charts")
    args = parser.parse_args()

    os.makedirs(args.out, exist_ok=True)

    print("=" * 60)
    print("RECOMMENDER SYSTEM SIMULATION")
    print(f"Days: {args.days} | Exercises/day: {args.per_day} | Seed: {args.seed}")
    print("=" * 60)

    personas = run_simulation(days=args.days, per_day=args.per_day, seed=args.seed)

    print("\n" + "=" * 60)
    print("FINAL SUMMARY")
    print("=" * 60)
    print(f"{'Persona':<10} {'Start':>7} {'Final':>7} {'Delta':>6} {'Start Lvl':>10} {'Final Lvl':>10} {'Correct':>8} {'XP':>6}")
    print(f"{'-'*10} {'-'*7} {'-'*7} {'-'*6} {'-'*10} {'-'*10} {'-'*8} {'-'*6}")

    for p in personas:
        correct = sum(1 for e in p.events if e["is_correct"])
        total = len(p.events)
        delta = p.elo - p.starting_elo
        print(
            f"{p.name:<10} {p.starting_elo:>7} {p.elo:>7} "
            f"{delta:>+6} "
            f"{elo_to_cefr(p.starting_elo):>10} {elo_to_cefr(p.elo):>10} "
            f"{correct:>4}/{total:<3} {p.xp:>6}"
        )

    report_path = os.path.join(args.out, "simulation_report.json")
    save_report(personas, report_path)

    if args.plot:
        plot_results(personas, args.out)

    print("\n Simulation is complete")


if __name__ == "__main__":
    main()
