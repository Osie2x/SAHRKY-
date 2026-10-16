import hashlib
import io
import json
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

from sharktank.audit import audit_archive


class AuditTests(unittest.TestCase):
    def fixture(self, directory, csv_text):
        root = Path(directory)
        (root / "data").mkdir()
        raw = csv_text.encode()
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w") as archive:
            archive.writestr("synthetic.csv", raw)
        path = root / "synthetic.zip"
        path.write_bytes(buffer.getvalue())
        manifest = {
            "source_url": "synthetic-test-fixture",
            "dataset_version": 1,
            "csv_filename": "synthetic.csv",
            "archive_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "csv_sha256": hashlib.sha256(raw).hexdigest(),
        }
        (root / "data/manifest.json").write_text(json.dumps(manifest))
        return root, path

    def test_audit_separates_missing_label_and_never_exports_outcome_as_input(self):
        csv_text = (
            "Pitch Number,Season Number,Episode Number,Startup Name,Industry,"
            "Original Ask Amount,Original Offered Equity,Got Deal\n"
            "1,1,1,Synthetic A,Food,50000,10,1\n"
            "2,1,1,Synthetic B,Food,50000,10,\n"
        )
        with tempfile.TemporaryDirectory() as directory:
            root, path = self.fixture(directory, csv_text)
            with patch("sharktank.audit.ROOT", root):
                result = audit_archive(path)
        self.assertEqual(result["raw_rows"], 2)
        self.assertEqual(result["accepted_rows"], 1)
        self.assertEqual(len(result["quarantined_rows"]), 1)
        self.assertEqual(result["raw_missing_required_values"]["Got Deal"], 1)
        self.assertNotIn("got_deal", result["pre_reveal_fields"])

    def test_altered_download_is_rejected_before_parsing(self):
        with tempfile.TemporaryDirectory() as directory:
            root, path = self.fixture(directory, "not even a CSV")
            path.write_bytes(path.read_bytes() + b"changed")
            with (
                patch("sharktank.audit.ROOT", root),
                self.assertRaisesRegex(ValueError, "Archive checksum mismatch"),
            ):
                audit_archive(path)

    def test_bad_season_is_reported_without_crashing_the_summary(self):
        csv_text = (
            "Pitch Number,Season Number,Episode Number,Startup Name,Industry,"
            "Original Ask Amount,Original Offered Equity,Got Deal\n"
            "1,unknown,1,Synthetic A,Food,50000,10,1\n"
        )
        with tempfile.TemporaryDirectory() as directory:
            root, path = self.fixture(directory, csv_text)
            with patch("sharktank.audit.ROOT", root):
                result = audit_archive(path)
        self.assertEqual(result["accepted_rows"], 0)
        self.assertEqual(result["raw_season_counts"], {"unknown": 1})
        self.assertIn("Season Number", result["quarantined_rows"][0]["reason"])

    def test_missing_source_columns_stop_the_audit(self):
        with tempfile.TemporaryDirectory() as directory:
            root, path = self.fixture(directory, "Pitch Number\n1\n")
            with (
                patch("sharktank.audit.ROOT", root),
                self.assertRaisesRegex(ValueError, "Missing columns"),
            ):
                audit_archive(path)


if __name__ == "__main__":
    unittest.main()
