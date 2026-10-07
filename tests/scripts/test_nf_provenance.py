"""Tests for skills/phase-data-analyze/scripts/nf_provenance.py (stdlib unittest, no network)."""

import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SCRIPT = REPO / "skills" / "phase-data-analyze" / "scripts" / "nf_provenance.py"

spec = importlib.util.spec_from_file_location("nf_provenance_under_test", SCRIPT)
prov = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = prov
spec.loader.exec_module(prov)

HAS_GIT = shutil.which("git") is not None


def git(cwd, *args):
    subprocess.run(["git", "-c", "user.name=Test", "-c", "user.email=test@example.org", *args], cwd=cwd,
                   check=True, capture_output=True)


class ProvenanceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.env = dict(os.environ, NF_PROVENANCE_CACHE=str(self.root / "cache.json"))
        self.scripts = self.root / "scripts" / "analysis"
        self.scripts.mkdir(parents=True)
        shutil.copy(SCRIPT, self.scripts / "nf_provenance.py")
        (self.root / "data").mkdir()
        (self.root / "data" / "in.csv").write_text("1,2,3\n", encoding="utf-8")

    def tearDown(self):
        self.tmp.cleanup()

    def write_script(self, name, body):
        path = self.scripts / name
        path.write_text(textwrap.dedent(body), encoding="utf-8")
        return path

    def py(self, *args):
        return subprocess.run([sys.executable, *map(str, args)], cwd=self.root, env=self.env,
                              capture_output=True, text=True, timeout=120)

    def records(self):
        return sorted((self.scripts / "provenance").glob("*.json"))

    def test_library_writes_environment_and_record(self):
        if HAS_GIT:
            git(self.root, "init", "-q")
            git(self.root, "add", "-A")
            git(self.root, "commit", "-qm", "init")
        self.write_script("ana.py", """
            import json, nf_provenance
            with nf_provenance.start(inputs=["data/in.csv", "data"], seeds={"perm": 42}) as run:
                json.dump({"d": 0.5}, open("results.json", "w"))
                run.output("results.json")
        """)
        proc = self.py(self.scripts / "ana.py")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        recs = self.records()
        self.assertEqual(len(recs), 1)
        rec = json.loads(recs[0].read_text(encoding="utf-8"))
        self.assertEqual(rec["status"], "ok")
        self.assertEqual(rec["script"], "scripts/analysis/ana.py")
        self.assertEqual(rec["seeds"], {"perm": 42})
        self.assertEqual(rec["inputs"][0]["path"], "data/in.csv")
        self.assertEqual(len(rec["inputs"][0]["sha256"]), 64)
        self.assertEqual(rec["inputs"][1]["kind"], "folder")
        self.assertEqual(rec["outputs"][0]["path"], "results.json")
        if HAS_GIT:
            self.assertEqual(len(rec["git"]["commit"]), 40)
            self.assertFalse(rec["git"]["dirty"])
        env = (self.scripts / "environment.md").read_text(encoding="utf-8")
        self.assertIn("<!-- nf-provenance:begin ana.py -->", env)
        self.assertIn("perm=42", env)
        dumped = json.dumps(rec)
        self.assertNotIn(Path.home().as_posix(), dumped)
        self.assertNotIn(json.dumps(str(Path.home()))[1:-1], dumped)

    def test_rerun_replaces_block_and_crash_is_recorded(self):
        self.write_script("ana.py", """
            import sys, nf_provenance
            run = nf_provenance.start()
            if len(sys.argv) > 1:
                raise ValueError("boom")
            run.finish()
        """)
        self.assertEqual(self.py(self.scripts / "ana.py").returncode, 0)
        self.assertNotEqual(self.py(self.scripts / "ana.py", "fail").returncode, 0)
        env = (self.scripts / "environment.md").read_text(encoding="utf-8")
        self.assertEqual(env.count("<!-- nf-provenance:begin ana.py -->"), 1)
        statuses = sorted(json.loads(p.read_text(encoding="utf-8"))["status"] for p in self.records())
        self.assertEqual(statuses, ["error", "ok"])
        errors = [json.loads(p.read_text(encoding="utf-8"))["error"] for p in self.records()]
        self.assertIn("ValueError: boom", errors)

    def test_missing_finish_is_recorded_as_unknown(self):
        self.write_script("nofinish.py", """
            import nf_provenance
            run = nf_provenance.start()
        """)
        self.assertEqual(self.py(self.scripts / "nofinish.py").returncode, 0)
        rec = json.loads(self.records()[0].read_text(encoding="utf-8"))
        self.assertEqual(rec["status"], "unknown")

    def test_hand_written_environment_is_kept(self):
        (self.scripts / "environment.md").write_text("# Notes by hand\n\nconda env eeg\n", encoding="utf-8")
        self.write_script("ana.py", "import nf_provenance\nnf_provenance.start().finish()\n")
        self.assertEqual(self.py(self.scripts / "ana.py").returncode, 0)
        env = (self.scripts / "environment.md").read_text(encoding="utf-8")
        self.assertTrue(env.startswith("# Notes by hand"))
        self.assertIn("<!-- nf-provenance:end ana.py -->", env)

    def test_record_cli_and_verify(self):
        cmd = [SCRIPT, "record", "--dir", self.scripts, "--output", "out.txt", "--",
               sys.executable, "-c", "open('out.txt', 'w').write('x')"]
        proc = self.py(*cmd)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        rec_path = self.records()[0]
        rec = json.loads(rec_path.read_text(encoding="utf-8"))
        self.assertIsNone(rec["packages"])
        self.assertEqual(rec["exit_code"], 0)
        self.assertEqual(self.py(SCRIPT, "verify", rec_path, "--root", self.root).returncode, 0)
        (self.root / "out.txt").write_text("changed", encoding="utf-8")
        proc = self.py(SCRIPT, "verify", rec_path, "--root", self.root)
        self.assertEqual(proc.returncode, 1)
        self.assertIn("changed", proc.stdout)

    def test_record_cli_failing_and_unstartable_commands(self):
        failing = self.py(SCRIPT, "record", "--dir", self.scripts, "--", sys.executable, "-c", "raise SystemExit(3)")
        self.assertEqual(failing.returncode, 1)
        rec = json.loads(self.records()[0].read_text(encoding="utf-8"))
        self.assertEqual(rec["status"], "error")
        self.assertEqual(rec["exit_code"], 3)
        missing = self.py(SCRIPT, "record", "--dir", self.root / "x", "--", "definitely-not-a-command-nf")
        self.assertEqual(missing.returncode, 2)
        self.assertFalse((self.root / "x" / "provenance").exists())

    def test_env_cli_json(self):
        proc = self.py(SCRIPT, "env", "--json")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        info = json.loads(proc.stdout)
        self.assertIn("version", info["python"])
        self.assertEqual(info["helper"], prov.__version__)

    def test_hash_path_and_cache(self):
        f = self.root / "data" / "in.csv"
        cache = prov.HashCache(self.root / "c.json")
        first = prov.hash_path(f, cache)
        cache.save()
        again = prov.hash_path(f, prov.HashCache(self.root / "c.json"))
        self.assertEqual(first, again)
        self.assertEqual(prov.hash_path(self.root / "nope"), {"missing": True})

    def test_home_is_shortened(self):
        home = Path.home().as_posix()
        self.assertEqual(prov._home_short(home + "/envs/eeg/python"), "~/envs/eeg/python")
        self.assertEqual(prov._home_short("/opt/python"), "/opt/python")

    def test_job_info_from_environment(self):
        old = {k: os.environ.pop(k, None) for k in ("SLURM_JOB_ID", "SLURM_ARRAY_TASK_ID", "PBS_JOBID")}
        try:
            self.assertIsNone(prov.job_info())
            os.environ["SLURM_JOB_ID"] = "812345"
            self.assertEqual(prov.job_info(), {"scheduler": "slurm", "id": "812345"})
        finally:
            os.environ.pop("SLURM_JOB_ID", None)
            for k, v in old.items():
                if v is not None:
                    os.environ[k] = v


if __name__ == "__main__":
    unittest.main()
