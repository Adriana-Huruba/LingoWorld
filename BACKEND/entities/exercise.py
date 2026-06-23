from dataclasses import dataclass
from typing import Optional

@dataclass
class Exercise:
    exercise_id: int
    language: str
    level: str
    type: str
    category: str
    topic: Optional[str]
    content: dict
    correct_answer: str
    elo_difficulty: Optional[int]
    source_manual: Optional[str]
    points: int = 10
    reason: Optional[str] = None

    @staticmethod
    def _normalize_content(content: dict, correct_answer: str = "") -> dict:
        if not isinstance(content, dict):
            return content

        if "questions" in content:
            return content

        if "question" in content:
            question = {
                "question": content.get("question", ""),
                "answer": content.get("answer", correct_answer),
                "options": content.get("options", []) or [],
            }
            normalized = {
                "exercise_title": content.get("exercise_title", ""),
                "questions": [question],
            }
            if "base_sentence" in content:
                normalized["base_sentence"] = content["base_sentence"]
            return normalized

        return content

    def from_row(row: dict) -> "Exercise":
        return Exercise(
            exercise_id = row["exercise_id"],
            language = row["language"],
            level = row["level"],
            type = row["type"],
            category = row.get("category", "general"),
            topic = row.get("topic"),
            content = Exercise._normalize_content(row["content"], row.get("correct_answer", "")),
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
            "content": Exercise._normalize_content(self.content, self.correct_answer),
            "correct_answer": self.correct_answer,
            "elo_difficulty": self.elo_difficulty,
            "source_manual": self.source_manual,
            "points": self.points,
            "reason": self.reason,
        }