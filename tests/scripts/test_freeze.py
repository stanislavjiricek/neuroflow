"""Tests for skills/phase-preregistration/scripts/freeze.py (stdlib unittest, no network)."""

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
SCRIPT = ROOT / "skills" / "phase-preregistration" / "scripts" / "freeze.py"
_spec = importlib.util.spec_from_file_location("nf_freeze", SCRIPT)
freeze = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = freeze
_spec.loader.exec_module(freeze)

PREREG = "# Preregistration\n\nH1: the P300 is larger for targets.\n"


def run(*argv: str) -> tuple[int, str, str]:
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = freeze.main(list(argv))
    return code, out.getvalue(), err.getvalue()


class FreezeTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.pdir = self.root / ".neuroflow" / "preregistration"
        self.pdir.mkdir(parents=True)
        self.doc = self.pdir / "prereg-osf-2026-10-01.md"
        self.doc.write_bytes(PREREG.encode("utf-8"))

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_canonical_hash_ignores_crlf_bom_and_banner(self) -> None:
        plain = freeze.canonical_bytes(PREREG.encode())
        crlf = freeze.canonical_bytes(("﻿" + PREREG.replace("\n", "\r\n")).encode("utf-8"))
        banner = freeze.canonical_bytes(("> FROZEN 2026-10-01 — sha256 abc… — x\n\n" + PREREG).encode("utf-8"))
        self.assertEqual(plain, crlf)
        self.assertEqual(plain, banner)

    def test_freeze_writes_status_and_banner_and_verifies(self) -> None:
        before = freeze.file_hash(self.doc)
        code, out, err = run("freeze", str(self.doc), "--set-by", "person", "--registry", "OSF",
                             "--planned-n", "48", "--root", str(self.root), "--json")
        self.assertEqual(code, 0, err)
        payload = json.loads(out)
        self.assertEqual(payload["status"], "frozen")
        text = self.doc.read_text(encoding="utf-8")
        self.assertTrue(text.startswith("> FROZEN "))
        self.assertIn("do not edit; record changes in deviations.md", text.splitlines()[0])
        self.assertEqual(freeze.file_hash(self.doc), before, "banner must not change the hash")
        data, _ = freeze.parse_status((self.pdir / "status.md").read_text(encoding="utf-8"))
        self.assertEqual(data["status"], "frozen")
        self.assertEqual(data["set_by"], "person")
        self.assertEqual(data["planned_n"], 48)
        self.assertEqual(data["registry"], "OSF")
        self.assertEqual(data["nf_schema"], 1)
        self.assertEqual(data["files"], {".neuroflow/preregistration/prereg-osf-2026-10-01.md": before})
        code, out, _ = run("verify", "--root", str(self.root))
        self.assertEqual(code, 0, out)

    def test_verify_detects_edit_and_missing_banner(self) -> None:
        run("freeze", str(self.doc), "--set-by", "person", "--root", str(self.root))
        text = self.doc.read_text(encoding="utf-8")
        self.doc.write_text(text.replace("larger", "smaller"), encoding="utf-8")
        code, out, _ = run("verify", "--root", str(self.root), "--json")
        self.assertEqual(code, 1)
        kinds = {f["kind"] for f in json.loads(out)["findings"]}
        self.assertIn("changed", kinds)
        # Restore content but drop the banner: hash matches, banner finding remains.
        self.doc.write_text(PREREG, encoding="utf-8")
        code, out, _ = run("verify", "--root", str(self.root), "--json")
        self.assertEqual(code, 1)
        self.assertEqual({f["kind"] for f in json.loads(out)["findings"]}, {"banner-missing"})

    def test_crlf_checkout_still_verifies(self) -> None:
        run("freeze", str(self.doc), "--set-by", "person", "--root", str(self.root))
        data = self.doc.read_bytes().replace(b"\n", b"\r\n")
        self.doc.write_bytes(data)
        code, out, _ = run("verify", "--root", str(self.root))
        self.assertEqual(code, 0, out)

    def test_model_freeze_is_a_finding(self) -> None:
        run("freeze", str(self.doc), "--set-by", "model", "--root", str(self.root))
        code, out, _ = run("verify", "--root", str(self.root), "--json")
        self.assertEqual(code, 1)
        self.assertIn("unconfirmed-freeze", {f["kind"] for f in json.loads(out)["findings"]})

    def test_refreeze_by_person_refused(self) -> None:
        run("freeze", str(self.doc), "--set-by", "person", "--root", str(self.root))
        code, _, err = run("freeze", str(self.doc), "--set-by", "person", "--root", str(self.root))
        self.assertEqual(code, 2)
        self.assertIn("already frozen", err)

    def test_unfreeze_requires_person_and_logs_append_only(self) -> None:
        run("freeze", str(self.doc), "--set-by", "person", "--root", str(self.root))
        code, _, err = run("unfreeze", "--set-by", "model", "--reason", "typo", "--root", str(self.root))
        self.assertEqual(code, 2)
        self.assertIn("person", err)
        deviations = self.pdir / "deviations.md"
        deviations.write_text("# Deviations\n\n## 2026-09-01 — earlier entry\n", encoding="utf-8")
        code, _, err = run("unfreeze", "--set-by", "person", "--reason", "fix a typo before OSF submission",
                           "--root", str(self.root))
        self.assertEqual(code, 0, err)
        log = deviations.read_text(encoding="utf-8")
        self.assertTrue(log.startswith("# Deviations\n\n## 2026-09-01 — earlier entry\n"))
        self.assertIn("Preregistration unfrozen", log)
        self.assertIn("fix a typo before OSF submission", log)
        self.assertFalse(self.doc.read_text(encoding="utf-8").startswith("> FROZEN"))
        data, _ = freeze.parse_status((self.pdir / "status.md").read_text(encoding="utf-8"))
        self.assertEqual(data["status"], "draft")
        self.assertNotIn("files", data)
        code, out, _ = run("verify", "--root", str(self.root))
        self.assertEqual(code, 0, out)

    def test_status_body_is_preserved(self) -> None:
        status = self.pdir / "status.md"
        status.write_text("---\nnf_schema: 1\nstatus: draft\nregistry: OSF  # target\n---\n# My notes\n",
                          encoding="utf-8")
        run("freeze", str(self.doc), "--set-by", "person", "--root", str(self.root))
        text = status.read_text(encoding="utf-8")
        self.assertTrue(text.endswith("# My notes\n"))
        data, _ = freeze.parse_status(text)
        self.assertEqual(data["registry"], "OSF")

    def test_quoted_paths_round_trip(self) -> None:
        data = {"nf_schema": 1, "status": "frozen", "files": {"docs/my prereg.md": "ab12"}, "set_by": "person"}
        parsed, body = freeze.parse_status(freeze.render_status(data, ""))
        self.assertEqual(parsed["files"], {"docs/my prereg.md": "ab12"})
        self.assertIn("Preregistration status", body)

    def test_verify_without_status_is_clean(self) -> None:
        code, out, _ = run("verify", "--root", str(self.root))
        self.assertEqual(code, 0)
        self.assertIn("not frozen", out)

    def test_file_outside_root_is_usage_error(self) -> None:
        with tempfile.TemporaryDirectory() as other:
            outside = Path(other) / "x.md"
            outside.write_text("x\n", encoding="utf-8")
            code, _, err = run("freeze", str(outside), "--set-by", "person", "--root", str(self.root))
        self.assertEqual(code, 2)
        self.assertIn("outside the project root", err)


if __name__ == "__main__":
    unittest.main()
