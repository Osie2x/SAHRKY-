"""Validate source rows and explicitly separate pre-reveal data from outcomes."""

import math
from dataclasses import asdict, dataclass
from typing import Iterable

REQUIRED_COLUMNS = (
    "Pitch Number",
    "Season Number",
    "Episode Number",
    "Startup Name",
    "Industry",
    "Original Ask Amount",
    "Original Offered Equity",
    "Got Deal",
)


@dataclass(frozen=True)
class Pitch:
    pitch_id: int
    season: int
    episode: int
    startup_name: str
    industry: str
    ask_amount_usd: float
    offered_equity_percent: float


@dataclass(frozen=True)
class LabeledPitch:
    pitch: Pitch
    got_deal: int

    def pre_reveal(self) -> dict:
        # Explicit construction ignores every other source column, including outcomes.
        return asdict(self.pitch)


def _text(row: dict[str, str], field: str) -> str:
    value = row.get(field)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field}: missing value")
    return value.strip()


def _positive_int(row: dict[str, str], field: str) -> int:
    try:
        value = int(_text(row, field))
    except ValueError as error:
        raise ValueError(f"{field}: expected a positive integer") from error
    if value <= 0:
        raise ValueError(f"{field}: expected a positive integer")
    return value


def _positive_number(row: dict[str, str], field: str) -> float:
    try:
        value = float(_text(row, field))
    except ValueError as error:
        raise ValueError(f"{field}: expected a finite positive number") from error
    if not math.isfinite(value) or value <= 0:
        raise ValueError(f"{field}: expected a finite positive number")
    return value


def validate_row(row: dict[str, str]) -> LabeledPitch:
    label = _text(row, "Got Deal")
    if label not in ("0", "1"):
        raise ValueError("Got Deal: expected exactly 0 or 1")
    equity = _positive_number(row, "Original Offered Equity")
    if equity > 100:
        raise ValueError("Original Offered Equity: cannot exceed 100 percent")
    pitch = Pitch(
        pitch_id=_positive_int(row, "Pitch Number"),
        season=_positive_int(row, "Season Number"),
        episode=_positive_int(row, "Episode Number"),
        startup_name=_text(row, "Startup Name"),
        industry=_text(row, "Industry"),
        ask_amount_usd=_positive_number(row, "Original Ask Amount"),
        offered_equity_percent=equity,
    )
    return LabeledPitch(pitch, int(label))


def validate_rows(
    rows: Iterable[dict[str, str]],
) -> tuple[list[LabeledPitch], list[dict]]:
    accepted = []
    rejected = []
    seen = set()
    for line, row in enumerate(rows, start=2):
        try:
            value = validate_row(row)
            if value.pitch.pitch_id in seen:
                raise ValueError(
                    "Pitch Number: duplicate ID after first accepted occurrence"
                )
            seen.add(value.pitch.pitch_id)
            accepted.append(value)
        except ValueError as error:
            rejected.append(
                {
                    "csv_line": line,
                    "pitch_id": row.get("Pitch Number"),
                    "reason": str(error),
                }
            )
    return accepted, rejected
