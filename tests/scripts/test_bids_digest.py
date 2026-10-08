"""Tests for skills/bids/scripts/bids_digest.py (stdlib unittest, fixtures written by the test)."""

from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "skills" / "bids" / "scripts" / "bids_digest.py"
_spec = importlib.util.spec_from_file_location("nf_bids_digest", SCRIPT)
bd = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = bd
_spec.loader.exec_module(bd)

SCHEMA = {
    "issues": {
        "issues": [
            {"code": "SIDECAR_KEY_REQUIRED", "subCode": "SoftwareFilters", "severity": "error",
             "location": f"/sub-0{i}/eeg/sub-0{i}_task-rest_eeg.json"} for i in range(1, 8)
        ] + [
            {"code": "SIDECAR_KEY_RECOMMENDED", "severity": "warning", "location": "/sub-01/eeg/x.json"},
            {"code": "README_FILE_MISSING", "severity": "warning"},
            {"code": "IGNORED_THING", "severity": "ignore", "location": "/x"},
        ],
        "codeMessages": {"SIDECAR_KEY_REQUIRED": "A data file's JSON sidecar is missing a key listed as required."},
    },
    "summary": {
        "subjects": ["01", "02", "03", "04", "05", "06", "07"], "sessions": [], "tasks": ["rest"],
        "modalities": ["EEG"], "totalFiles": 42, "size": 1000, "schemaVersion": "1.0",
        "subjectMetadata": [{"participantId": "sub-01", "age": 31, "sex": "F"}],
    },
}

LEGACY = {
    "issues": {
        "errors": [{"key": "MISSING_SESSION", "code": 38, "reason": "Not all subjects have the same sessions.",
                    "files": [{"file": {"relativePath": "/sub-02"}}], "additionalFileCount": 2}],
        "warnings": [{"key": "NO_AUTHORS", "code": 113, "reason": "No authors.", "files": []}],
    },
    "summary": {"subjects": ["01", "02"], "sessions": ["1", "2"], "tasks": [], "modalities": ["MRI"],
                "totalFiles": 9},
}


def run(*argv: str, stdin: str | None = None) -> tuple[int, str, str]:
    out, err = io.StringIO(), io.StringIO()
    old_stdin = sys.stdin
    if stdin is not None:
        sys.stdin = io.StringIO(stdin)
    try:
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = bd.main(list(argv))
    finally:
        sys.stdin = old_stdin
    return code, out.getvalue(), err.getvalue()


class BidsDigestTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self._tmp.name)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def write(self, data: dict) -> Path:
        path = self.dir / "validator.json"
        path.write_text(json.dumps(data), encoding="utf-8")
        return path

    def test_schema_format(self) -> None:
        code, out, err = run(str(self.write(SCHEMA)), "--locations", "3", "--json")
        self.assertEqual(code, 1, err)
        result = json.loads(out)
        self.assertEqual(result["format"], "schema")
        self.assertEqual(result["error_count"], 7)
        self.assertEqual(result["warning_count"], 2)
        err0 = result["errors"][0]
        self.assertEqual((err0["code"], err0["count"], len(err0["locations"])), ("SIDECAR_KEY_REQUIRED", 7, 3))
        self.assertEqual(result["summary"]["n_subjects"], 7)
        self.assertNotIn("subjectMetadata", json.dumps(result), "participant metadata must not be printed")

    def test_text_output_names_source_and_counts(self) -> None:
        path = self.write(SCHEMA)
        code, out, _ = run(str(path))
        self.assertIn("full output:", out)
        self.assertIn("SIDECAR_KEY_REQUIRED x7", out)
        self.assertIn("... 2 more", out)
        # the temporary folder's random name may contain digits: look at the lines after the "full output" path
        header = out.split("ERRORS")[0].split("
", 1)[1]
        self.assertNotIn("31", header)

    def test_legacy_format(self) -> None:
        code, out, _ = run(str(self.write(LEGACY)), "--json")
        result = json.loads(out)
        self.assertEqual(code, 1)
        self.assertEqual(result["format"], "legacy")
        self.assertEqual(result["errors"][0]["count"], 3)
        self.assertEqual(result["errors"][0]["locations"], ["/sub-02"])
        self.assertEqual(result["warning_count"], 1)

    def test_warnings_only_and_strict(self) -> None:
        data = {"issues": {"issues": [{"code": "README_FILE_MISSING", "severity": "warning"}], "codeMessages": {}},
                "summary": {}}
        path = self.write(data)
        self.assertEqual(run(str(path))[0], 0)
        self.assertEqual(run(str(path), "--strict")[0], 1)

    def test_stdin_and_bad_input(self) -> None:
        code, out, _ = run("-", stdin=json.dumps(LEGACY))
        self.assertEqual(code, 1)
        self.assertIn("<stdin>", out)
        self.assertEqual(run("-", stdin="not json")[0], 2)
        self.assertEqual(run("-", stdin=json.dumps({"x": 1}))[0], 2)
        self.assertEqual(run(str(self.dir / "missing.json"))[0], 2)


if __name__ == "__main__":
    unittest.main()
