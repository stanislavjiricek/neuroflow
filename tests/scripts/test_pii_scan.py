"""Tests for skills/phase-output/scripts/pii_scan.py (stdlib unittest, no network).

Token-shaped test strings are assembled at runtime so this file itself never
contains a secret-looking literal.
"""

from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

REPO = Path(__file__).resolve().parents[2]
SCRIPT = REPO / "skills" / "phase-output" / "scripts" / "pii_scan.py"


def load():
    name = "nf_test_pii_scan"
    spec = importlib.util.spec_from_file_location(name, SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


pii = load()
GH_TOKEN = "gh" + "p_" + "aB3dE5gH7jK9" * 3
PEM = "-----BEGIN " + "RSA PRIVATE KEY-----"


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def kinds(scanner, text: str) -> list[str]:
    return [k for _, k in scanner.scan_text(text)]


def run_main(args: list[str]) -> tuple[int, str]:
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(io.StringIO()):
        code = pii.main(args)
    return code, buf.getvalue()


class PatternTests(unittest.TestCase):
    def test_email(self):
        s = pii.Scanner()
        self.assertEqual(kinds(s, "write to jane.doe@uni-lab.org today"), ["email"])
        self.assertEqual(kinds(s, "a@example.com, git@github.com, x@users.noreply.github.com"), [])
        known = pii.Scanner(known_emails=["jane.doe@uni-lab.org"])
        self.assertEqual(kinds(known, "jane.doe@uni-lab.org"), [])
        allowed = pii.Scanner(allow_emails=["@uni-lab.org"])
        self.assertEqual(kinds(allowed, "bob@mail.uni-lab.org"), [])

    def test_phone(self):
        s = pii.Scanner()
        self.assertEqual(kinds(s, "call +44 20 7946 0958"), ["phone"])
        self.assertEqual(kinds(s, "+1 (555) 123-4567"), ["phone"])
        self.assertEqual(kinds(s, "effect +0.5, range +12 34, t = +2.31"), [])

    def test_configured_id_with_checksum(self):
        luhn = pii.IdPattern("card-like", pii.re.compile(r"\b\d{16}\b"), "luhn")
        mod11 = pii.IdPattern("ten-digit", pii.re.compile(r"\b\d{10}\b"), "mod11")
        s = pii.Scanner(id_patterns=[luhn, mod11])
        self.assertEqual(kinds(s, "4111111111111111"), ["id:card-like"])
        self.assertEqual(kinds(s, "4111111111111112"), [])
        self.assertEqual(kinds(s, "1234567890"), [])  # remainder 6 - fails the checksum
        self.assertEqual(kinds(s, "1234567884"), ["id:ten-digit"])  # 11 * 112233444

    def test_mod11_and_luhn_helpers(self):
        self.assertTrue(pii.mod11_ok("1234567884"))
        self.assertFalse(pii.mod11_ok("1234567890"))
        self.assertTrue(pii.luhn_ok("79927398713"))
        self.assertFalse(pii.luhn_ok("79927398710"))

    def test_secrets(self):
        s = pii.Scanner()
        self.assertEqual(kinds(s, f"token = {GH_TOKEN}"), ["secret:github-token"])
        self.assertEqual(kinds(s, PEM), ["secret:private-key"])
        self.assertEqual(kinds(s, '"api_key": "s3cr3tValue99"'), ["secret:assignment"])
        self.assertEqual(kinds(s, '"api_key": "<YOUR_API_KEY>"'), [])
        self.assertEqual(kinds(s, 'api_key = "YOUR_API_KEY_HERE"'), [])
        self.assertEqual(kinds(pii.Scanner(secrets=False), PEM), [])

    def test_no_values_in_findings(self):
        s = pii.Scanner()
        for _line, kind in s.scan_text("mail jane.doe@uni-lab.org"):
            self.assertNotIn("jane", kind)


class RosterTests(unittest.TestCase):
    def test_build_and_match_with_diacritics(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "proj"
            (root / ".neuroflow").mkdir(parents=True)
            names = Path(tmp) / "names.txt"
            names.write_text("# participants\nJosé Müller\nZoë Ångström-Lee\n", encoding="utf-8")
            out = Path(tmp) / "keys" / "roster.json"
            res = pii.build_roster(names, out, root)
            self.assertEqual(res["names"], 2)
            stored = out.read_text(encoding="utf-8")
            self.assertNotIn("Müller", stored)
            self.assertNotIn("muller", stored)
            roster = pii.load_roster(out)
            s = pii.Scanner(roster=roster)
            self.assertEqual(kinds(s, "Session with JOSE MULLER went fine"), ["roster-name"])
            self.assertEqual(kinds(s, "Jose was late"), [])

    def test_roster_refused_inside_memory(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".neuroflow").mkdir()
            names = root / "n.txt"
            names.write_text("A B\n", encoding="utf-8")
            with self.assertRaises(pii.ConfigError):
                pii.build_roster(names, root / ".neuroflow" / "roster.json", root)


class ConfigTests(unittest.TestCase):
    def test_bad_regex_and_checksum(self):
        with self.assertRaises(pii.ConfigError):
            pii.id_patterns_from({"id_patterns": [{"name": "x", "regex": "("}]})
        with self.assertRaises(pii.ConfigError):
            pii.id_patterns_from({"id_patterns": [{"name": "x", "regex": "\\d", "checksum": "crc"}]})

    def test_bad_config_exit_2(self):
        with tempfile.TemporaryDirectory() as tmp:
            cfg = Path(tmp) / "cfg.json"
            cfg.write_text("{not json", encoding="utf-8")
            code, _ = run_main(["--root", tmp, "--config", str(cfg), tmp])
            self.assertEqual(code, 2)


class FileScanTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        nf = self.root / ".neuroflow"
        write(nf / "project_config.md", "---\nproject_name: P\n---\ncollaborators:\n- email: pi@uni-lab.org\n")
        write(nf / "meetings" / "m.md", "Attendees: pi@uni-lab.org, stranger@other-lab.org\n")
        write(nf / "sessions" / "2026-10-07.md", "private@other-lab.org\n")
        (nf / "data").mkdir()
        (nf / "data" / "blob.bin").write_bytes(b"\0\1\2abc@other-lab.org")

    def tearDown(self):
        self.tmp.cleanup()

    def test_default_scans_team_tier_only(self):
        code, out = run_main(["--root", str(self.root), "--json"])
        self.assertEqual(code, 1)
        rep = json.loads(out)
        self.assertEqual([(f["path"], f["kind"]) for f in rep["findings"]],
                         [(".neuroflow/meetings/m.md", "email")])
        self.assertTrue(any(s["reason"] == "binary" for s in rep["skipped"]))
        self.assertNotIn("stranger", out)

    def test_folder_argument_and_include_local(self):
        code, out = run_main(["--root", str(self.root), str(self.root / ".neuroflow"), "--include-local", "--json"])
        self.assertEqual(code, 1)
        paths = {f["path"] for f in json.loads(out)["findings"]}
        self.assertIn(".neuroflow/sessions/2026-10-07.md", paths)

    def test_clean_exit_0(self):
        clean = self.root / "clean.md"
        clean.write_text("nothing personal here\n", encoding="utf-8")
        code, _ = run_main(["--root", str(self.root), str(clean)])
        self.assertEqual(code, 0)


@unittest.skipUnless(shutil.which("git"), "git not installed")
class StagedTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        base = Path(self.tmp.name)
        gitconfig = base / "gitconfig"
        gitconfig.write_text("", encoding="utf-8")
        self.env = mock.patch.dict(os.environ, {
            "GIT_CONFIG_GLOBAL": str(gitconfig), "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_CEILING_DIRECTORIES": str(base)})
        self.env.start()
        self.root = base / "repo"
        self.root.mkdir()
        subprocess.run(["git", "init", "-q", "-b", "main"], cwd=self.root, check=True)

    def tearDown(self):
        self.env.stop()
        self.tmp.cleanup()

    def test_staged_secret_and_local_tier(self):
        write(self.root / "config.py", f'TOKEN = "{GH_TOKEN}"\n')
        write(self.root / ".neuroflow" / "sessions" / "2026-10-07.md", "log\n")
        subprocess.run(["git", "add", "-f", "config.py", ".neuroflow/sessions/2026-10-07.md"], cwd=self.root, check=True)
        code, out = run_main(["--root", str(self.root), "--staged", "--json"])
        self.assertEqual(code, 1)
        found = {(f["path"], f["kind"]) for f in json.loads(out)["findings"]}
        self.assertIn(("config.py", "secret:github-token"), found)
        self.assertIn((".neuroflow/sessions/2026-10-07.md", "local-tier-staged"), found)
        self.assertNotIn(GH_TOKEN, out)

    def test_staged_clean(self):
        write(self.root / "a.txt", "hello\n")
        subprocess.run(["git", "add", "a.txt"], cwd=self.root, check=True)
        code, _ = run_main(["--root", str(self.root), "--staged"])
        self.assertEqual(code, 0)


if __name__ == "__main__":
    unittest.main()
