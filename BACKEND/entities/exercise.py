from dataclasses import dataclass
from typing import Optional

@dataclass
class Exercise:
    exercise_id: int
    language: str
    level: str
    type: str
    category: str # skill_type (grammar, vocabulary etc.)
    topic: Optional[str]
    content: dict
    correct_answer: str
    elo_difficulty: Optional[int]
    source_manual: Optional[str]
    points: int = 10
    reason: Optional[str] = None  # spaced_repetition/new_exercise/reinforcement/ newly_generated

    @staticmethod
    def from_row(row: dict) -> "Exercise":
        return Exercise(
            exercise_id = row["exercise_id"],
            language = row["language"],
            level = row["level"],
            type = row["type"],
            category = row.get("category", "general"),
            topic = row.get("topic"),
            content = row["content"],
            correct_answer = row["correct_answer"],
            elo_difficulty = row.get("elo_difficulty"),
            source_manual = row.get("source_manual"),
            points = row.get("points", 10),
            reason = row.get("reason"),
        )

    def to_dict(self) -> dict:
        return {
            "exercise_id": self.exercise_id,
            "language": self.language,
            "level": self.level,
            "type": self.type,
            "skill_type": self.category,
            "topic": self.topic,
            "content": self.content,
            "correct_answer": self.correct_answer,
            "elo_difficulty": self.elo_difficulty,
            "source_manual": self.source_manual,
            "points": self.points,
            "reason": self.reason,
        }