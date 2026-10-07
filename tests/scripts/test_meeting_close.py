"""Tests for skills/phase-meeting/scripts/meeting_close.py (stdlib unittest, no network)."""

from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SCRIPT = REPO / "skills" / "phase-meeting" / "scripts" / "meeting_close.py"

spec = importlib.util.spec_from_file_location("nf_meeting_close_under_test", SCRIPT)
meeting_close = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = meeting_close
spec.loader.exec_module(meeting_close)

MEETING = """---
title: Weekly Lab Meeting
date: 2026-04-20T10:00:00
level: project
linked_tasks: []
calendar_event_id: ""
---

## Agenda

- [ ] not an action item (agenda checkbox)

## Notes

Talked about ICA.

## Action Items

- [ ] Fix RT pipeline → @stan [project/active]
- [ ] Update ethics form
- [ ] Review grant draft -> @jana due:2026-10-20 [flowie]
- [x] Book the room
- Bring the grand average
- [ ] Čistě přepsat preprocessing [review]

## Decisions

- [ ] not an action item either
"""


def run(*args: str) -> tuple[int, dict]:
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        code = meeting_close.main([*args, "--json", "--today", "2026-10-07"])
    return code, json.loads(out.getvalue())


def run_text(*args: str) -> tuple[int, str]:
    out = io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(io.StringIO()):
        code = meeting_close.main([*args, "--today", "2026-10-07"])
    return code, out.getvalue()


class MeetingCloseTest(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        base = Path(self._tmp.name)
        self.project = base / "study"
        self.nf = self.project / ".neuroflow"
        (self.nf / "meetings").mkdir(parents=True)
        (self.nf / "project_config.md").write_text(
            "---\nnf_schema: 1\nproject_name: Oddball EEG\n---\n", encoding="utf-8"
        )
        self.flowie = base / "home" / ".neuroflow" / "flowie"
        self.flowie.mkdir(parents=True)
        self.meeting = self.nf / "meetings" / "2026-04-20-weekly-lab.md"
        self.meeting.write_text(MEETING, encoding="utf-8")

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def close(self, *extra: str) -> tuple[int, dict]:
        return run(str(self.meeting), "--flowie-root", str(self.flowie), *extra)

    def test_dry_run_plans_items_and_writes_nothing(self) -> None:
        code, plan = self.close()
        self.assertEqual(code, 0)
        self.assertEqual(plan["source"], "project:meetings/2026-04-20-weekly-lab.md")
        items = {i["slug"]: i for i in plan["items"]}
        self.assertEqual(
            set(items),
            {
                "fix-rt-pipeline",
                "update-ethics-form",
                "review-grant-draft",
                "ciste-prepsat-preprocessing",
            },
        )
        fix = items["fix-rt-pipeline"]
        self.assertEqual(
            (fix["level"], fix["column"], fix["owner"], fix["title"]),
            ("project", "active", "stan", "Fix RT pipeline"),
        )
        grant = items["review-grant-draft"]
        self.assertEqual(
            (grant["level"], grant["column"], grant["owner"], grant["due"]),
            ("flowie", "inbox", "jana", "2026-10-20"),
        )
        self.assertEqual(items["update-ethics-form"]["column"], "inbox")
        self.assertEqual(items["ciste-prepsat-preprocessing"]["column"], "review")
        reasons = sorted(s["reason"] for s in plan["skipped"])
        self.assertEqual(reasons, ["checked", "not a checkbox"])
        self.assertFalse((self.nf / "tasks").exists())
        self.assertFalse((self.flowie / "tasks").exists())
        self.assertEqual(self.meeting.read_text(encoding="utf-8"), MEETING)

    def test_write_creates_task_files_and_updates_meeting(self) -> None:
        code, plan = self.close("--write")
        self.assertEqual(code, 0, plan)
        task = self.nf / "tasks" / "active" / "fix-rt-pipeline.md"
        text = task.read_text(encoding="utf-8")
        self.assertIn('title: "Fix RT pipeline"', text)
        self.assertIn("status: active", text)
        self.assertIn("owner: stan", text)
        self.assertIn("created: 2026-10-07", text)
        self.assertIn("updated: 2026-10-07", text)
        self.assertIn("source: project:meetings/2026-04-20-weekly-lab.md", text)
        self.assertNotIn("project:", text.split("source:")[0])
        flowie_task = (
            self.flowie / "tasks" / "inbox" / "review-grant-draft.md"
        ).read_text(encoding="utf-8")
        self.assertIn('project: "Oddball EEG"', flowie_task)
        self.assertIn("due: 2026-10-20", flowie_task)
        meeting = self.meeting.read_text(encoding="utf-8")
        self.assertIn(
            "linked_tasks: [project:fix-rt-pipeline, project:update-ethics-form, flowie:review-grant-draft, "
            "project:ciste-prepsat-preprocessing]",
            meeting,
        )
        self.assertIn("closed: 2026-10-07", meeting)
        self.assertEqual(len(plan["created"]), 4)

    def test_second_run_is_idempotent(self) -> None:
        self.close("--write")
        code, plan = self.close("--write")
        self.assertEqual(code, 0)
        self.assertEqual({i["action"] for i in plan["items"]}, {"exists"})
        self.assertEqual(plan["created"], [])
        self.assertEqual(len(list((self.nf / "tasks").rglob("*.md"))), 3)
        meeting = self.meeting.read_text(encoding="utf-8")
        self.assertEqual(meeting.count("project:fix-rt-pipeline"), 1)
        self.assertEqual(meeting.count("closed:"), 1)

    def test_moved_task_still_counts_as_existing(self) -> None:
        self.close("--write")
        src = self.nf / "tasks" / "active" / "fix-rt-pipeline.md"
        (self.nf / "tasks" / "done").mkdir()
        src.rename(self.nf / "tasks" / "done" / "fix-rt-pipeline.md")
        _, plan = self.close()
        fix = next(i for i in plan["items"] if i["title"] == "Fix RT pipeline")
        self.assertEqual((fix["action"], fix["column"]), ("exists", "done"))

    def test_unrelated_task_with_same_slug_gets_suffix(self) -> None:
        other = self.nf / "tasks" / "inbox"
        other.mkdir(parents=True)
        (other / "update-ethics-form.md").write_text(
            '---\ntitle: "Update ethics form"\nstatus: inbox\n---\n', encoding="utf-8"
        )
        _, plan = self.close()
        item = next(i for i in plan["items"] if i["title"] == "Update ethics form")
        self.assertEqual(
            (item["action"], item["slug"]), ("create", "update-ethics-form-2")
        )

    def test_errors_block_writing(self) -> None:
        self.meeting.write_text(
            MEETING.replace("[project/active]", "[team/inbox]"), encoding="utf-8"
        )
        code, plan = self.close("--write")
        self.assertEqual(code, 1)
        self.assertEqual(plan["errors"], 1)
        self.assertIn(
            "unknown level 'team'",
            next(i["message"] for i in plan["items"] if i["action"] == "error"),
        )
        self.assertFalse((self.nf / "tasks").exists())
        self.assertNotIn("closed:", self.meeting.read_text(encoding="utf-8"))

    def test_unknown_single_annotation_and_bad_due_are_errors(self) -> None:
        self.meeting.write_text(
            MEETING.replace("[review]", "[draft]").replace(
                "due:2026-10-20", "due:tomorrow"
            ),
            encoding="utf-8",
        )
        code, plan = self.close()
        self.assertEqual(code, 1)
        messages = " | ".join(
            i["message"] for i in plan["items"] if i["action"] == "error"
        )
        self.assertIn("unknown level or column 'draft'", messages)
        self.assertIn("due date 'tomorrow' is not YYYY-MM-DD", messages)

    def test_missing_level_storage_is_an_error(self) -> None:
        missing = Path(self._tmp.name) / "nowhere" / "flowie"
        code, plan = run(str(self.meeting), "--flowie-root", str(missing))
        self.assertEqual(code, 1)
        err = next(i for i in plan["items"] if i["action"] == "error")
        self.assertIn("flowie level not set up", err["message"])

    def test_hive_item_needs_hive_root(self) -> None:
        self.meeting.write_text(
            MEETING.replace("[flowie]", "[hive/inbox]"), encoding="utf-8"
        )
        code, plan = self.close()
        self.assertEqual(code, 1)
        self.assertIn(
            "--hive-root",
            next(i["message"] for i in plan["items"] if i["action"] == "error"),
        )
        hive = Path(self._tmp.name) / "home" / ".neuroflow" / "hives" / "acme-lab"
        hive.mkdir(parents=True)
        code, plan = self.close("--hive-root", str(hive), "--write")
        self.assertEqual(code, 0, plan)
        self.assertTrue((hive / "tasks" / "inbox" / "review-grant-draft.md").exists())

    def test_custom_columns_from_config(self) -> None:
        tasks = self.nf / "tasks"
        tasks.mkdir()
        (tasks / "config.json").write_text(
            json.dumps({"columns": [{"id": "inbox"}, {"id": "doing"}, {"id": "done"}]}),
            encoding="utf-8",
        )
        self.meeting.write_text(
            MEETING.replace("[project/active]", "[project/doing]"), encoding="utf-8"
        )
        code, plan = self.close()
        self.assertEqual(code, 1)  # [review] is not a column in this project's config
        fix = next(i for i in plan["items"] if i["title"] == "Fix RT pipeline")
        self.assertEqual((fix["action"], fix["column"]), ("create", "doing"))

    def test_missing_section_is_a_finding(self) -> None:
        self.meeting.write_text(
            MEETING.replace("## Action Items", "## Todo"), encoding="utf-8"
        )
        code, plan = self.close()
        self.assertEqual(code, 1)
        self.assertIn("no 'Action Items' heading", plan["items"][0]["message"])
        code, plan = self.close("--section", "Todo")
        self.assertEqual(code, 0)

    def test_missing_file_is_usage_error(self) -> None:
        code, _ = run_text(str(self.nf / "meetings" / "nope.md"))
        self.assertEqual(code, 2)

    def test_crlf_and_block_list_are_preserved(self) -> None:
        text = MEETING.replace(
            "linked_tasks: []", "linked_tasks:\n  - project:older-task"
        ).replace("\n", "\r\n")
        self.meeting.write_bytes(text.encode("utf-8"))
        code, _ = self.close("--write")
        self.assertEqual(code, 0)
        raw = self.meeting.read_bytes()
        self.assertNotIn(b"\n", raw.replace(b"\r\n", b""))
        self.assertIn(
            b"linked_tasks: [project:older-task, project:fix-rt-pipeline", raw
        )

    def test_template_comments_are_respected(self) -> None:
        text = MEETING.replace(
            "linked_tasks: []",
            "linked_tasks: []            # {level}:{slug} entries written by --close\n"
            'closed: ""                  # YYYY-MM-DD, stamped by --close',
        )
        self.meeting.write_text(text, encoding="utf-8")
        code, _ = self.close("--write")
        self.assertEqual(code, 0)
        meeting = self.meeting.read_text(encoding="utf-8")
        self.assertIn(
            "linked_tasks: [project:fix-rt-pipeline, project:update-ethics-form",
            meeting,
        )
        self.assertIn("]  # {level}:{slug} entries written by --close", meeting)
        self.assertIn("closed: 2026-10-07  # YYYY-MM-DD, stamped by --close", meeting)
        self.assertEqual(meeting.count("closed:"), 1)
        self.assertEqual(
            meeting_close.split_comment('"a # b"  # note'), ('"a # b"', "# note")
        )

    def test_text_output_mentions_dry_run(self) -> None:
        code, out = run_text(str(self.meeting), "--flowie-root", str(self.flowie))
        self.assertEqual(code, 0)
        self.assertIn("dry run", out)
        self.assertIn("--write", out)

    def test_slugify(self) -> None:
        self.assertEqual(
            meeting_close.slugify("Re-run ICA on sub-07!"), "re-run-ica-on-sub-07"
        )
        self.assertEqual(meeting_close.slugify("日本語"), "task")
        long = meeting_close.slugify(
            "a very long action item title that keeps going and going"
        )
        self.assertLessEqual(len(long), 40)
        self.assertFalse(long.endswith("-"))


if __name__ == "__main__":
    unittest.main()
