"""Pure review policy, independent of the terminal, SQLite and wall clock."""

from dataclasses import dataclass

REVIEW_INTERVALS = (600, 86400, 259200, 604800, 1209600, 2592000, 5184000)


@dataclass(frozen=True)
class ReviewSchedule:
    stage: int
    due: float


def schedule_review(stage: int, remembered: bool, now: float) -> ReviewSchedule:
    """Advance a successful due review, or reset a forgotten word to ten minutes."""
    next_stage = min(max(stage, 0) + 1, len(REVIEW_INTERVALS) - 1) if remembered else 0
    return ReviewSchedule(next_stage, now + REVIEW_INTERVALS[next_stage])
