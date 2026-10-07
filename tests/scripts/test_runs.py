"""Tests for skills/phase-brain-run/scripts/runs.py (stdlib unittest, no network, no scheduler)."""

import contextlib
import importlib.util
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

REPO = Path(__file__).resolve().parents[2]
SCRIPT = REPO / "skills" / "phase-brain-run" / "scripts" / "runs.py"

spec = importlib.util.spec_from_file_location("nf_runs_under_test", SCRIPT)
runs = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = runs
spec.loader.exec_module(runs)


def run(*argv):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = runs.main([str(a) for a in argv])
    return code, out.getvalue(), err.getvalue()


class RunsTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.cwd = os.getcwd()
        os.chdir(self.root)
        self.file = Path(".neuroflow/brain-run/runs.md")

    def tearDown(self):
        os.chdir(self.cwd)
        self.tmp.cleanup()

    def add(self, *extra):
        return run("add", "--file", self.file, *extra)

    def status_of(self, run_id):
        return runs.Registry(self.file).run(run_id)["status"]

    def test_add_creates_registry_and_escapes_pipes(self):
        code, out, _ = self.add("--command", "python sim.py --cfg a|b.yaml", "--log", "res/r1/run.log",
                                "--output", "res/r1/m.json", "--output", "res/r1/spikes.npy", "--id", "r1")
        self.assertEqual(code, 0)
        text = self.file.read_text(encoding="utf-8")
        self.assertIn("| Run | Started (UTC) | Where | Command | Log | Expected outputs | Status | Note |", text)
        self.assertIn("a\\|b.yaml", text)
        r = runs.Registry(self.file).run("r1")
        self.assertEqual(r["command"], "python sim.py --cfg a|b.yaml")
        self.assertEqual(r["outputs"], ["res/r1/m.json", "res/r1/spikes.npy"])
        self.assertEqual(r["status"], "running")
        # duplicate ids get a suffix, rows are kept in order
        self.add("--command", "x", "--id", "r1")
        self.assertIn("r1-2", runs.Registry(self.file).rows)

    def test_job_id_needs_scheduler(self):
        self.assertEqual(self.add("--command", "x", "--job-id", "5")[0], 2)
        self.assertEqual(self.add("--command", "x", "--where", "slurm")[0], 2)
        self.assertEqual(self.add("--command", "sbatch j.sh", "--where", "slurm", "--job-id", "5")[0], 0)
        self.assertIn("queued", self.file.read_text(encoding="utf-8"))

    def test_exit_code_file_marks_done_or_failed(self):
        self.add("--command", "a", "--log", "res/a.log", "--id", "a")
        self.add("--command", "b", "--log", "res/b.log", "--id", "b")
        Path("res").mkdir()
        Path("res/a.log.exitcode").write_text("0\n")
        Path("res/b.log.exitcode").write_text("3 \r\n")
        code, out, _ = run("check", "--file", self.file)
        self.assertEqual(code, 1)
        self.assertEqual(self.status_of("a"), "done")
        self.assertEqual(self.status_of("b"), "failed")
        self.assertIn("exit code 3", out)
        run("set", "--file", self.file, "--id", "a", "--status", "reviewed")
        run("set", "--file", self.file, "--id", "b", "--status", "reviewed")
        code, out, _ = run("check", "--file", self.file)
        self.assertEqual(code, 0)
        self.assertIn("nothing finished", out)

    def test_pid_liveness(self):
        self.assertTrue(runs.pid_alive(os.getpid()))
        proc = subprocess.Popen([sys.executable, "-c", "pass"])
        proc.wait()
        self.assertFalse(runs.pid_alive(proc.pid))
        self.add("--command", "me", "--pid", str(os.getpid()), "--id", "alive")
        self.add("--command", "gone", "--pid", str(proc.pid), "--id", "gone")
        code, out, _ = run("check", "--file", self.file)
        self.assertEqual(code, 1)
        self.assertEqual(self.status_of("alive"), "running")
        self.assertEqual(self.status_of("gone"), "unknown")

    def test_no_liveness_info_is_reported_not_changed(self):
        self.add("--command", "mystery", "--id", "m")
        code, out, _ = run("check", "--file", self.file)
        self.assertEqual(code, 0)
        self.assertIn("not checked", out)
        self.assertEqual(self.status_of("m"), "running")

    def test_slurm_states(self):
        self.add("--command", "sbatch j.sh", "--where", "slurm", "--job-id", "812345", "--id", "s")
        which = lambda name: f"/usr/bin/{name}" if name in {"squeue", "sacct"} else None  # noqa: E731
        with mock.patch.object(runs.shutil, "which", which), \
                mock.patch.object(runs, "_run", side_effect=[(0, "RUNNING\n")]):
            self.assertEqual(run("check", "--file", self.file)[0], 0)
        self.assertEqual(self.status_of("s"), "running")
        with mock.patch.object(runs.shutil, "which", which), \
                mock.patch.object(runs, "_run", side_effect=[(0, ""), (0, "COMPLETED|0:0\n")]):
            code, out, _ = run("check", "--file", self.file)
        self.assertEqual(code, 1)
        self.assertEqual(self.status_of("s"), "done")

    def test_slurm_tools_missing_off_cluster(self):
        self.add("--command", "sbatch j.sh", "--where", "slurm", "--job-id", "7", "--id", "s")
        with mock.patch.object(runs.shutil, "which", lambda name: None):
            code, out, _ = run("check", "--file", self.file)
        self.assertEqual(code, 0)
        self.assertIn("run the check on the cluster", out)
        self.assertEqual(self.status_of("s"), "queued")

    def test_pbs_finished_job(self):
        self.add("--command", "qsub j.sh", "--where", "pbs", "--job-id", "123.server", "--id", "p")
        qstat = "Job Id: 123.server\n    job_state = F\n    Exit_status = 1\n"
        with mock.patch.object(runs.shutil, "which", lambda name: "/usr/bin/qstat" if name == "qstat" else None), \
                mock.patch.object(runs, "_run", return_value=(0, qstat)):
            code, _, _ = run("check", "--file", self.file)
        self.assertEqual(code, 1)
        self.assertEqual(self.status_of("p"), "failed")

    def test_list_discovers_registries_and_hides_reviewed(self):
        self.add("--command", "a", "--id", "a")
        run("add", "--file", ".neuroflow/data-preprocess/runs.md", "--command", "b", "--id", "b")
        run("set", "--file", self.file, "--id", "a", "--status", "reviewed")
        code, out, _ = run("list", "--json")
        self.assertEqual(code, 0)
        ids = [r["id"] for r in json.loads(out)]
        self.assertEqual(ids, ["b"])
        code, out, _ = run("list", "--all", "--json")
        self.assertEqual(sorted(r["id"] for r in json.loads(out)), ["a", "b"])

    def test_set_rejects_unknown_status_and_run(self):
        self.add("--command", "a", "--id", "a")
        self.assertEqual(run("set", "--file", self.file, "--id", "a", "--status", "great")[0], 2)
        self.assertEqual(run("set", "--file", self.file, "--id", "zzz", "--status", "done")[0], 2)

    def test_text_outside_the_table_is_preserved(self):
        self.add("--command", "a", "--id", "a")
        text = self.file.read_text(encoding="utf-8") + "\nNotes by hand below the table.\n"
        self.file.write_text(text, encoding="utf-8")
        self.add("--command", "b", "--id", "b")
        run("set", "--file", self.file, "--id", "a", "--status", "cancelled", "--note", "wrong config")
        final = self.file.read_text(encoding="utf-8")
        self.assertIn("Notes by hand below the table.", final)
        self.assertLess(final.index("| b |"), final.index("Notes by hand"))
        self.assertIn("| cancelled | wrong config |", final)


if __name__ == "__main__":
    unittest.main()
