"""Tests for scripts/automation/mod_policy.py: inventory parsing, the policy comparison, the source scan."""

from __future__ import annotations

import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

from .helpers import load

mp = load("mod_policy")

MODULE = "./mod/neuroflow.ts"


def report(calls: str, state: str = "neuroflow.scope", env: str = "HOME", gating: list | None = None) -> dict:
    return {
        "success": True,
        "contents": [
            {"type": "plugin", "notes": ["types ./types/index.d.ts declares state: neuroflow.scope"], "gatingHooks": []},
            {
                "type": "hooks",
                "notes": [
                    f"{MODULE} hooks: session.start, tool.call{{tool=Write|Edit}}, command.run{{command=/\"^neuroflow:\"/}}",
                    f"{MODULE} calls: {calls}",
                    f"{MODULE} env writes: nothing",
                    f"{MODULE} env reads: {env}",
                    f"{MODULE} state writes: {state}",
                    f"{MODULE} state reads: neuroflow.scope",
                ],
                "gatingHooks": gating or [{"module": MODULE, "pattern": "tool.call", "hook": "tool.call{tool=Write|Edit}", "hasCatch": True}],
            },
        ],
    }


class InventoryTests(unittest.TestCase):
    def test_items_split_and_via_dropped(self):
        inv = mp.inventory(report("$.clock.now, $.fs.read (via ioOf, decide), $.ui.toast"))
        self.assertEqual(inv["calls"], ["$.clock.now", "$.fs.read", "$.ui.toast"])
        self.assertEqual(inv["envReads"], ["HOME"])
        self.assertEqual(inv["envWrites"], [])
        self.assertEqual(inv["stateWrites"], ["neuroflow.scope"])
        self.assertEqual(inv["gatingWithoutCatch"], [])

    def test_split_keeps_matchers_whole(self):
        self.assertEqual(
            mp.split_items('session.start, tool.call{tool=Write|Edit, x=1}, command.run{command=/"^a,b"/}'),
            ["session.start", "tool.call{tool=Write|Edit, x=1}", 'command.run{command=/"^a,b"/}'],
        )

    def test_a_shortened_note_is_detected(self):
        self.assertFalse(mp.truncated(report("$.clock.now")))
        self.assertTrue(mp.truncated(report("$.clock.now, $.fs.r… [+40 chars]")))


class CompareTests(unittest.TestCase):
    policy = {"events": ["tool.call"], "calls": ["$.clock.now", "$.fs.read"], "envReads": ["HOME"], "envWrites": [], "stateWrites": ["neuroflow.scope"]}

    def current(self, **over):
        base = {"events": ["tool.call"], "calls": ["$.clock.now", "$.fs.read"], "envReads": ["HOME"], "envWrites": [], "stateWrites": ["neuroflow.scope"], "gatingWithoutCatch": []}
        base.update(over)
        return base

    def test_within_policy(self):
        self.assertEqual(mp.compare(self.current(), self.policy), ([], []))

    def test_new_call_fails_and_unused_entry_is_a_note(self):
        failures, notes = mp.compare(self.current(calls=["$.clock.now", "$.http.fetch"]), self.policy)
        self.assertEqual(failures, ["calls: not in hooks/mod/policy.json: $.http.fetch"])
        self.assertEqual(notes, ["calls: listed in the policy but no longer used: $.fs.read"])

    def test_gating_hook_without_catch_fails(self):
        failures, _ = mp.compare(self.current(gatingWithoutCatch=["tool.call{tool=Bash}"]), self.policy)
        self.assertEqual(failures, ["gating hook without .catch: tool.call{tool=Bash}"])


class CliTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def run_main(self, *args):
        out = io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(out):
            code = mp.main(list(args))
        return code, out.getvalue()

    def test_write_then_check(self):
        saved = self.dir / "report.json"
        saved.write_text(json.dumps(report("$.clock.now, $.fs.read (via ioOf)")), encoding="utf-8")
        policy = self.dir / "policy.json"
        self.assertEqual(self.run_main("--report", str(saved), "--write", "--policy", str(policy))[0], 0)
        written = json.loads(policy.read_text(encoding="utf-8"))
        self.assertEqual(written["calls"], ["$.clock.now", "$.fs.read"])
        self.assertIn("session.start", written["events"])
        self.assertEqual(self.run_main("--report", str(saved), "--policy", str(policy))[0], 0)
        saved.write_text(json.dumps(report("$.clock.now, $.fs.read, $.http.fetch")), encoding="utf-8")
        code, out = self.run_main("--report", str(saved), "--policy", str(policy))
        self.assertEqual(code, 1)
        self.assertIn("$.http.fetch", out)

    def test_unreadable_report(self):
        bad = self.dir / "bad.json"
        bad.write_text("not json", encoding="utf-8")
        self.assertEqual(self.run_main("--report", str(bad))[0], 2)


class RepoPolicyTests(unittest.TestCase):
    def test_the_repo_policy_lists_every_hooked_event(self):
        policy = json.loads(mp.POLICY.read_text(encoding="utf-8"))
        self.assertEqual(sorted(policy["events"]), mp.source_events())
        self.assertEqual(policy["envWrites"], [])


if __name__ == "__main__":
    unittest.main()
