"""Audit the pinned public archive without extracting files or training a model."""

import argparse
import csv
import hashlib
import io
import json
import zipfile
from collections import Counter
from pathlib import Path

from .data import REQUIRED_COLUMNS, validate_rows

ROOT = Path(__file__).resolve().parents[1]


def audit_archive(path: Path) -> dict:
    manifest = json.loads((ROOT / "data/manifest.json").read_text())
    archive = path.read_bytes()
    digest = hashlib.sha256(archive).hexdigest()
    if digest != manifest["archive_sha256"]:
        raise ValueError(
            "Archive checksum mismatch: stop and review the source version"
        )
    with zipfile.ZipFile(io.BytesIO(archive)) as zipped:
        if zipped.namelist() != [manifest["csv_filename"]]:
            raise ValueError("Unexpected archive contents")
        raw = zipped.read(manifest["csv_filename"])
    if hashlib.sha256(raw).hexdigest() != manifest["csv_sha256"]:
        raise ValueError("CSV checksum mismatch")
    reader = csv.DictReader(io.StringIO(raw.decode("utf-8-sig")))
    columns = reader.fieldnames or []
    missing = set(REQUIRED_COLUMNS) - set(columns)
    if missing:
        raise ValueError(f"Missing columns: {sorted(missing)}")
    rows = list(reader)
    accepted, rejected = validate_rows(rows)
    return {
        "source_url": manifest["source_url"],
        "dataset_version": manifest["dataset_version"],
        "archive_sha256": digest,
        "csv_sha256": manifest["csv_sha256"],
        "column_count": len(columns),
        "columns": columns,
        "raw_rows": len(rows),
        "accepted_rows": len(accepted),
        "quarantined_rows": rejected,
        "raw_missing_required_values": {
            field: sum(not (row.get(field) or "").strip() for row in rows)
            for field in REQUIRED_COLUMNS
        },
        "raw_season_counts": dict(Counter(row["Season Number"] for row in rows)),
        "accepted_outcome_counts": dict(
            sorted(Counter(p.got_deal for p in accepted).items())
        ),
        "pre_reveal_fields": list(accepted[0].pre_reveal()) if accepted else [],
        "scope": "Data integrity only; no model trained, no held-out score, no deployed API",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path)
    args = parser.parse_args()
    print(json.dumps(audit_archive(args.archive), indent=2))


if __name__ == "__main__":
    main()
