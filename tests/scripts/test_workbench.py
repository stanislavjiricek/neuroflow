"""Tests for skills/neuroflow-core/scripts/workbench.py (the claude.ai workbench: export, guard, intents, apply, gc)."""
from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import os
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

REPO = Path(__file__).resolve().parents[2]
SCRIPT = REPO / "skills" / "neuroflow-core" / "scripts" / "workbench.py"
FIXTURES = REPO / "tests" / "fixtures" / "workbench"
spec = importlib.util.spec_from_file_location("nf_workbench_under_test", SCRIPT)
wb = importlib.util.module_from_spec(spec)
spec.loader.exec_module(wb)

GIT_ENV = {"GIT_AUTHOR_NAME": "Test", "GIT_AUTHOR_EMAIL": "test@example.org", "GIT_COMMITTER_NAME": "Test",
           "GIT_COMMITTER_EMAIL": "test@example.org", "GIT_CONFIG_NOSYSTEM": "1"}
NOW = "2026-10-21T10:00:00Z"


def git(cwd: Path, *args: str) -> str:
    env = dict(os.environ, **GIT_ENV)
    return subprocess.run(["git", "-c", "core.autocrlf=false", "-c", "commit.gpgsign=false", "-c", "init.defaultBranch=main",
                           *args], cwd=cwd, env=env, check=True, capture_output=True, text=True).stdout


def run(*argv: str) -> tuple[int, dict | str]:
    out = io.StringIO()
    err = io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = wb.main(list(argv))
    text = out.getvalue()
    try:
        return code, json.loads(text)
    except ValueError:
        return code, text + err.getvalue()


def task(title: str, status: str, **keys: str) -> str:
    lines = ["---", f"title: {title}", f"status: {status}", *[f"{k}: {v}" for k, v in keys.items()], "---", ""]
    return "\n".join(lines)


class Home(unittest.TestCase):
    """A temporary home with a flowie, a hive and a project, each optionally a real git clone."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.base = Path(self._tmp.name)
        self.home = self.base / "home"
        self.flowie = self.home / ".neuroflow" / "flowie"
        self.hive = self.home / ".neuroflow" / "hives" / "lab-folder"
        self.project = self.base / "work" / "oddball"
        self.scratch = self.base / "scratch"
        self.scratch.mkdir()
        self.user_yaml('workbench: on\nworkbench_machine: laptop\nflowie_handle: alice\n'
                       'workbench_levels: ["flowie", "hive+example-lab+hive", "project+oddball-eeg"]\n')

    def tearDown(self) -> None:
        def retry(func, name, _info):
            os.chmod(name, 0o700)
            func(name)
        shutil.rmtree(self.base, onerror=retry)

    def write(self, path: Path, text: str) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(text.encode("utf-8"))
        return path

    def user_yaml(self, text: str) -> None:
        self.write(self.home / ".neuroflow" / "user.yaml", text)

    def wb(self, *argv: str) -> tuple[int, dict | str]:
        return run(*argv, "--home", str(self.home), "--root", str(self.project), "--now", NOW, "--json")

    # levels -------------------------------------------------------------------------------------

    def make_flowie(self, git_repo: bool = False) -> None:
        self.write(self.flowie / "tasks" / "inbox" / "read-paper.md", task("Read the paper", "inbox", created="2026-10-01"))
        self.write(self.flowie / "tasks" / "active" / "write-intro.md", task("Write the intro", "active", created="2026-10-02"))
        if git_repo:
            self.clone_of(self.flowie, "alice/flowie")

    def make_hive(self, policy: str | None = "allow", git_repo: bool = False) -> None:
        front = f"---\nworkbench_mirror: {policy}\n---\n" if policy else ""
        self.write(self.hive / "hive.md", front + "# Example Lab\n\n## Norms\nReview first.\n")
        self.write(self.hive / "members.md", "| name | email | github | role |\n|---|---|---|---|\n"
                                             "| Jana Example | jana@uni.example.org | jana | postdoc |\n")
        self.write(self.hive / "tasks" / "inbox" / "fix-map.md", task("Fix the map", "inbox", owner="jana", created="2026-10-01"))
        self.write(self.hive / "tasks" / "active" / "rerun-ica.md", task("Rerun ICA", "active", created="2026-10-01"))
        if git_repo:
            self.clone_of(self.hive, "example-lab/hive")
        else:
            self.write(self.hive / ".git" / "config", '[remote "origin"]\n\turl = https://github.com/example-lab/hive.git\n')
            self.write(self.hive / ".git" / "HEAD", "ref: refs/heads/main\n")

    def make_project(self, policy: str | None = "allow", git_repo: bool = False, card: bool = True) -> None:
        front = f"workbench_mirror: {policy}\n" if policy else ""
        self.write(self.project / ".neuroflow" / "project_config.md",
                   f"---\nnf_schema: 1\nproject_name: Oddball EEG\nactive_phase: data\n{front}---\n")
        self.write(self.project / ".neuroflow" / "tasks" / "review" / "qc-report.md", task("QC report", "review", created="2026-10-03"))
        if card:
            self.write(self.home / ".neuroflow" / "local-projects.json",
                       json.dumps({"projects": [{"name": "oddball-eeg", "path": str(self.project)}]}))
        if git_repo:
            self.clone_of(self.project, "example-lab/oddball")

    def clone_of(self, folder: Path, name: str) -> None:
        """Make `folder` a clone of a bare repository (so it has an upstream), with its files committed."""
        bare = self.base / "remotes" / f"{name.replace('/', '-')}.git"
        bare.mkdir(parents=True)
        git(bare, "init", "--bare", "-q")
        git(folder, "init", "-q")
        git(folder, "remote", "add", "origin", str(bare))
        git(folder, "add", "-A")
        git(folder, "commit", "-q", "-m", "start")
        git(folder, "push", "-q", "-u", "origin", "main")
        # the key comes from a remote URL, not the local bare path: point origin at the hosted name, push by path
        git(folder, "remote", "set-url", "origin", f"https://github.com/{name}.git")
        git(folder, "remote", "set-url", "--push", "origin", str(bare))
        git(folder, "config", f"url.{bare.as_posix()}.insteadOf", f"https://github.com/{name}.git")


class KeyTests(Home):
    def test_level_keys_come_from_remotes_or_cards_never_folders(self) -> None:
        self.assertEqual(wb.hive_key("git@github.com:Example-Lab/Hive.git"), "hive+example-lab+hive")
        self.assertEqual(wb.hive_key("https://github.com/example-lab/hive"), "hive+example-lab+hive")
        self.assertIsNone(wb.hive_key("C:/Users/alice/hive"))
        self.assertEqual(wb.project_key("oddball-eeg", None), "project+oddball-eeg")
        self.assertRegex(wb.project_key("Oddball EEG", None), r"^project\+oddball~20eeg~~[0-9a-f]{8}$")
        self.assertNotEqual(wb.project_key("Oddball", None), wb.project_key("oddball", None))
        self.assertEqual(wb.project_key("a+b~c", None), "project+a~2bb~7ec")
        self.assertEqual(wb.project_key(None, "git@github.com:org/repo.git"), "project+github.com+org+repo")
        self.assertIsNone(wb.project_key(None, None))
        long_key = wb.project_key("x" * 300, None)
        self.assertTrue(long_key.startswith("project+~~") and len(long_key) <= 200)
        self.assertEqual(wb.project_key("study-2024.", None), "project+study-2024~2e")  # Windows drops a last dot
        self.assertEqual(wb.project_key("a..", None), "project+a.~2e")
        for key in ("flowie", "hive+example-lab+hive", wb.project_key("Oddball EEG", None), "project+github.com+org+repo", long_key,
                    wb.project_key("study-2024.", None), wb.project_key("v1.0 .", None)):
            self.assertTrue(wb.valid_level_key(key), key)
            # a key is a valid file name everywhere: an ArtifactData listing saved with out_dir names files after it
            self.assertIsNone(re.search(r'[<>:"/\\|?*A-Z]', key), key)
            self.assertFalse(key.endswith((".", " ")), key)
        for key in ("prefs", "inbox", "project+a b", "hive", "../x", "", "hive:example-lab:hive"):
            self.assertFalse(wb.valid_level_key(key), key)

    def test_a_hive_is_keyed_by_its_origin_and_a_project_without_card_or_remote_gets_no_tab(self) -> None:
        self.make_hive()
        self.make_project(card=False)
        code, result = self.wb("levels")
        keys = {row["level"]: row for row in result["levels"]}
        self.assertIn("hive+example-lab+hive", keys)
        self.assertEqual(keys["hive+example-lab+hive"]["board"], "hive:lab-folder")
        self.assertEqual([item["kind"] for item in result["unkeyed"]], ["project"])
        self.assertIn("neither a registry card nor an origin remote", result["unkeyed"][0]["reason"])


class PathParityTests(unittest.TestCase):
    """Even segment counts are documents, odd ones collections (the store's grammar): every path the script builds."""

    def test_every_path_has_the_right_parity(self) -> None:
        for key in ("flowie", "hive+example-lab+hive", "project+github.com+org+repo"):
            self.assertTrue(wb.is_collection(wb.meta_collection()))
            self.assertTrue(wb.is_document(f"{wb.meta_collection()}/{key}"), key)                 # 4: the level's meta
            self.assertTrue(wb.is_collection(wb.parts_collection(key)), key)                     # 5
            self.assertTrue(wb.is_document(f"{wb.parts_collection(key)}/core"), key)             # 6: a part
        self.assertTrue(wb.is_collection(wb.intents_collection()))                                # 5
        self.assertTrue(wb.is_document(f"{wb.intents_collection()}/i-abc123-x7y8"))              # 6: an intent
        self.assertTrue(wb.INTENT_ID.match("i-k3j2h1g0-a9b8c7d6e5f4"))  # the page's ids: random letters, no time
        self.assertTrue(wb.is_document(f"{wb.meta_collection()}/{wb.PREFS_DOC}"))                # 4: the preferences
        self.assertEqual(wb.segments(f"{wb.parts_collection('flowie')}/core"), 6)
        self.assertEqual(wb.segments(wb.meta_collection("u_abc")), 3)

    def test_the_capabilities_are_owner_only_and_nothing_else(self) -> None:
        self.assertEqual(wb.CAPABILITIES, {"db": {"rules": [{"path": "", "read": "owner", "write": "owner"}]}, "user": {}})


class ExportTests(Home):
    def export(self, *extra: str) -> tuple[int, dict]:
        return self.wb("export", "--out", str(self.scratch / "up"), *extra)

    def doc(self, key: str, name: str) -> dict:
        return json.loads((self.scratch / "up" / "docs" / key.replace(":", "_") / f"{name}.json").read_text(encoding="utf-8"))

    def test_only_levels_the_team_and_the_person_allow_are_exported(self) -> None:
        self.make_flowie()
        self.make_hive(policy=None)
        self.make_project(policy="forbid")
        code, result = self.export()
        self.assertEqual([row["level"] for row in result["levels"]], ["flowie"])
        reasons = {row["level"]: row["reason"] for row in result["not_mirrored"]}
        self.assertIn("has not opted in", reasons["hive+example-lab+hive"])
        self.assertIn("forbids", reasons["project+oddball-eeg"])
        self.user_yaml("workbench: off\nworkbench_machine: laptop\nworkbench_levels: [\"flowie\"]\n")
        self.assertEqual(self.export()[1]["levels"], [])
        self.user_yaml("workbench: on\nworkbench_machine: laptop\nworkbench_levels: [\"project+oddball-eeg\"]\n")
        self.assertEqual(self.export()[1]["levels"], [])

    def test_no_machine_label_is_a_usage_error(self) -> None:
        self.make_flowie()
        self.user_yaml("workbench: on\nworkbench_levels: [\"flowie\"]\n")
        code, result = self.export()
        self.assertEqual(code, 2)
        self.assertIn("workbench_machine", result["error"])

    def test_what_leaves_is_the_allowlist_and_nothing_else(self) -> None:
        self.make_flowie()
        self.write(self.flowie / "tasks" / "inbox" / "mail.md",
                   task("Mail jana@uni.example.org", "inbox") + "\nCall +420 777 123 456 or write to bob@uni.example.org.\n")
        self.write(self.flowie / "tasks" / "inbox" / "secret.md", task("Rotate", "inbox") + '\napi_key = "s3cr3t-value-123"\n')
        self.write(self.flowie / "wellbeing" / "2026-10-20.json", '{"anxiety": 9}\n')
        self.write(self.flowie / "profile.md", "## Identity\nemail: alice@uni.example.org\n")
        self.write(self.flowie / "notes" / "2026-10-05-talk.md", "# Talk\n\nprivate notes body\n")
        self.write(self.flowie / "meetings" / "2026-10-22-pi.md", "---\ntitle: PI\ndate: 2026-10-22\nattendees: [pi@uni.example.org]\n---\nagenda body\n")
        code, result = self.export()
        self.assertEqual(code, 1)  # an item was held back
        flowie = result["levels"][0]
        self.assertEqual(flowie["withheld"], [{"source": "tasks", "item": "inbox/secret.md", "reason": "secret-like text"}])
        everything = "".join(path.read_text(encoding="utf-8") for path in (self.scratch / "up").rglob("*.json"))
        for leak in ("jana@", "bob@", "777 123", "anxiety", "alice@", "private notes body", "agenda body", "pi@",
                     "s3cr3t", str(self.home), self.home.as_posix()):
            self.assertNotIn(leak, everything, leak)
        cards = {card["slug"]: card for card in self.doc("flowie", "cards-000")["cards"]}
        self.assertEqual(cards["mail"]["title"], "Mail [email removed]")
        self.assertIn("[phone removed]", cards["mail"]["notes"])
        self.assertNotIn("secret", cards)
        core = self.doc("flowie", "core")
        self.assertEqual(core["panel"]["notes"], [{"file": "2026-10-05-talk.md", "title": "Talk", "date": "2026-10-05"}])
        self.assertEqual(core["panel"]["meetings"][0]["title"], "PI")

    def test_reserved_example_addresses_are_not_personal_data(self) -> None:
        self.make_flowie()
        self.write(self.flowie / "tasks" / "inbox" / "docs.md", task("Write to help@example.org", "inbox"))
        self.export()
        cards = {card["slug"]: card for card in self.doc("flowie", "cards-000")["cards"]}
        self.assertEqual(cards["docs"]["title"], "Write to help@example.org")

    def test_people_are_handles_unless_the_team_allows_names(self) -> None:
        self.make_hive(policy="allow")
        self.export()
        self.assertEqual(self.doc("hive+example-lab+hive", "core")["people"], [{"handle": "jana"}])
        self.make_hive(policy="allow-names")
        self.export()
        self.assertEqual(self.doc("hive+example-lab+hive", "core")["people"],
                         [{"handle": "jana", "name": "Jana Example", "role": "postdoc"}])

    def test_wiki_links_resolve_and_local_files_are_named_not_uploaded(self) -> None:
        self.make_flowie()
        pages = self.flowie / "wiki" / "pages"
        self.write(pages / "concepts" / "n2pc.md", "---\ntitle: N2pc\ntype: concept\n---\n\n[[Alpha Oscillations|alpha]], "
                   "[[alpha-oscillations#Peak]], [[Nowhere]], ![[fig.png]], ![plot](raw/assets/plot.png), "
                   "[ICA](../methods/ica.md), [web](https://example.org/a)\n")
        self.write(pages / "concepts" / "alpha-oscillations.md", "---\ntitle: Alpha Oscillations\n---\nbody\n")
        self.write(pages / "methods" / "ica.md", "---\ntitle: ICA\n---\nbody\n")
        self.write(self.flowie / "wiki" / "raw" / "paper.md", "raw source text\n")
        self.export()
        body = next(page for page in self.doc("flowie", "wiki-000")["pages"] if page["id"] == "concepts/n2pc")["body"]
        self.assertIn("[[concepts/alpha-oscillations|alpha]]", body)
        self.assertIn("[[concepts/alpha-oscillations|alpha-oscillations]]", body)
        self.assertIn("[[|Nowhere]]", body)
        self.assertIn("[local file, not mirrored: fig.png]", body)
        self.assertIn("[local file, not mirrored: plot.png]", body)
        self.assertIn("[[methods/ica|ICA]]", body)
        self.assertIn("[web](https://example.org/a)", body)
        self.assertNotIn("raw source text", json.dumps(self.doc("flowie", "wiki-000")))

    def test_index_only_drops_the_bodies(self) -> None:
        self.make_flowie()
        self.write(self.flowie / "wiki" / "pages" / "concepts" / "x.md", "---\ntitle: X\n---\nthe body\n")
        self.user_yaml('workbench: on\nworkbench_machine: laptop\nworkbench_levels: ["flowie"]\nworkbench_index_only: ["flowie"]\n')
        code, result = self.export()
        page = self.doc("flowie", "wiki-000")["pages"][0]
        self.assertNotIn("body", page)
        self.assertTrue(result["levels"][0]["index_only"])

    def test_parts_stay_under_the_cap_and_their_hashes_match_the_meta(self) -> None:
        self.make_flowie()
        for n in range(30):
            self.write(self.flowie / "wiki" / "pages" / "concepts" / f"p{n:02d}.md", f"---\ntitle: Page {n}\n---\n" + ("word " * 4000))
        for n in range(400):
            self.write(self.flowie / "tasks" / "inbox" / f"t{n:03d}.md", task(f"Task {n}", "inbox") + ("note " * 150))
        code, result = self.export()
        meta = self.doc("flowie", "meta")
        ids = [part["id"] for part in meta["parts"]]
        self.assertGreater(len([i for i in ids if i.startswith("wiki-")]), 1)
        self.assertGreater(len([i for i in ids if i.startswith("cards-")]), 1)
        for part in meta["parts"]:
            doc = self.doc("flowie", part["id"])
            self.assertLessEqual(part["bytes"], wb.PART_MAX)
            self.assertEqual(doc["sha256"], part["sha256"])
            self.assertEqual(wb.with_hash(doc)["sha256"], doc["sha256"])
        self.assertEqual(sum(len(self.doc("flowie", i)["cards"]) for i in ids if i.startswith("cards-")), 402)

    def test_a_level_too_large_for_one_part_is_trimmed_and_never_stops_the_others(self) -> None:
        self.make_flowie()
        self.make_hive(policy="allow")
        self.write(self.flowie / "ideas.md", "idea " * 12_000)              # 60,000 characters
        self.write(self.flowie / "ideas-inbox.md", "注意" * 30_000)          # 60,000 CJK characters: 180 KB
        for n in range(800):
            self.write(self.flowie / "notes" / f"note-{n:04d}.md", f"# Note {n}\n")
        self.write(self.flowie / "tasks" / "inbox" / "huge.md", task("x" * 250_000, "inbox"))
        code, result = self.export()
        self.assertEqual(code, 1)
        self.assertEqual([row["level"] for row in result["levels"]], ["flowie", "hive+example-lab+hive"])
        core = self.doc("flowie", "core")
        self.assertLessEqual(wb.doc_bytes(core), wb.PART_MAX)
        self.assertLessEqual(len(core["panel"]["ideas_inbox"].encode("utf-8")), wb.TEXT_MAX + 4)
        self.assertEqual(len(core["panel"]["notes"]), wb.LIST_MAX)
        self.assertEqual(core["panel"]["notes"][-1]["file"], "note-0799.md")  # the newest stay
        withheld = result["levels"][0]["withheld"]
        self.assertIn({"source": "notes", "item": "600 older", "reason": "the panel lists the newest 200"}, withheld)
        self.assertIn({"source": "tasks", "item": "inbox/huge.md", "reason": "larger than one part (200 KB)"}, withheld)
        self.assertNotIn("huge", {card["slug"] for card in self.doc("flowie", "cards-000")["cards"]})
        # a registry too large to share the core with the panel goes, said why; the level is still exported
        self.write(self.flowie / "projects" / "projects.json", json.dumps({"projects": [
            {"id": f"p{n:03d}", "description": "d" * 1000} for n in range(400)]}))
        code, result = self.export()
        self.assertEqual(self.doc("flowie", "core")["registry"], [])
        self.assertIn({"source": "registry", "item": "the project registry",
                       "reason": "larger than one part (200 KB) with the rest of the level"}, result["levels"][0]["withheld"])
        self.assertEqual(result["skipped"], [])
        # a level whose columns and people alone overflow a part is skipped with its reason; the others still go up
        self.make_hive(policy="allow-names")
        self.write(self.hive / "members.md", "| name | email | github | role |\n|---|---|---|---|\n" + "".join(
            f"| Name {n} | m{n}@example.org | user{n} | role {n} |\n" for n in range(4000)))
        code, result = self.export()
        self.assertEqual(code, 1)
        self.assertEqual([row["level"] for row in result["levels"]], ["flowie"])
        self.assertEqual([(row["level"], row["reason"]) for row in result["skipped"]],
                         [("hive+example-lab+hive", "its columns and people alone are larger than one part (200 KB)")])

    def test_every_exported_field_is_in_the_allowlist(self) -> None:
        snapshot = json.loads((FIXTURES / "snapshot.json").read_text(encoding="utf-8"))
        seen: set[str] = set()

        def within(kind: str, item: dict | None) -> None:
            if item is None:
                return
            seen.add(kind)
            self.assertLessEqual(set(item), set(wb.FIELDS[kind]), f"{kind}: {sorted(set(item) - set(wb.FIELDS[kind]))}")

        for key, meta in snapshot["metas"].items():
            within("meta", meta)
            within("source", meta["source"])
            within("counts", meta["counts"])
            for part in meta["parts"]:
                within("part_ref", part)
            for state in meta["applied"].values():
                within("applied", state)
            for item in meta["withheld"]:
                within("withheld", item)
            core = snapshot["parts"][key]["core"]
            within("core", core)
            for name, kind in (("columns", "column"), ("people", "person"), ("registry", "registry")):
                for item in core[name]:
                    within(kind, item)
            panel = core["panel"]
            within(f"{meta['kind']}_panel", panel)
            for name, kind in (("notes", "note"), ("meetings", "meeting"), ("errata", "erratum"), ("dates", "date")):
                for item in panel.get(name) or []:
                    within(kind, item)
            within("marker", panel.get("ethics"))
            within("marker", panel.get("prereg"))
            for name, doc in snapshot["parts"][key].items():
                if name != "core":
                    within("part", doc)
                    for item in doc.get("cards", []):
                        within("card", item)
                    for item in doc.get("pages", []):
                        within("page", item)
        # the golden levels are not git clones, so no click has landed there: the apply test checks `applied`
        self.assertEqual(seen, set(wb.FIELDS) - {"applied"}, "the golden snapshot should hold every other kind of item")

    def test_the_sources_rows_name_every_allowlisted_field_and_no_other(self) -> None:
        named = {field for row in wb.SOURCES for field in row["fields"]}
        allowed = {f"{kind}.{name}" for kind, names in wb.FIELDS.items() for name in names}
        self.assertEqual(named, allowed)
        self.assertEqual(wb.allow("card", {"slug": "a", "path": "C:/Users/alice/x.md"}), {"slug": "a"})

    def test_names_and_tags_with_personal_data_hold_the_item_back_and_the_page_only_counts_it(self) -> None:
        self.make_flowie()
        token = "ghp_" + "A1b2C3d4" * 5
        self.write(self.flowie / "tasks" / "inbox" / "deploy.md", task("Deploy", "inbox", tags=f"[{token}]"))
        self.write(self.flowie / "meetings" / "2026-10-22-jana@uni.example.org.md", "---\ntitle: Catch-up\n---\n")
        code, result = self.export()
        self.assertEqual(code, 1)
        named = {(item["source"], item["item"]) for item in result["levels"][0]["withheld"]}
        self.assertEqual(named, {("tasks", "inbox/deploy.md"), ("meetings", "2026-10-22-jana@uni.example.org.md")})
        self.assertEqual(self.doc("flowie", "meta")["withheld"],
                         [{"source": "tasks", "reason": "secret-like text"},
                          {"source": "meetings", "reason": "personal data in its file name, tags or links"}])
        everything = "".join(path.read_text(encoding="utf-8") for path in (self.scratch / "up").rglob("*.json"))
        for leak in (token, "jana@", "deploy", "Catch-up"):
            self.assertNotIn(leak, everything, leak)

    def test_every_free_text_field_is_scrubbed_and_an_owner_must_be_on_the_roster(self) -> None:
        hive = "hive+example-lab+hive"
        self.make_hive(policy="allow-names")
        self.write(self.hive / "members.md", "| name | email | github | role |\n|---|---|---|---|\n"
                                             "| Jana Example (jana@uni.example.org) | jana@uni.example.org | jana | postdoc, +420 777 123 456 |\n")
        self.write(self.hive / "projects" / "projects.json", json.dumps({"projects": [
            {"id": "oddball", "status": "waiting on jana@uni.example.org", "current_phase": "call +420 777 123 456"}]}))
        self.write(self.hive / "wiki" / "pages" / "people" / "contact.md",
                   "---\ntitle: Contact\ntype: contact jana@uni.example.org\nstatus: ask bob@uni.example.org\n---\nbody\n")
        self.write(self.hive / "tasks" / "inbox" / "legacy.md", task("Old one", "inbox", assignee="Kristyna"))
        code, result = self.export()
        everything = "".join(path.read_text(encoding="utf-8") for path in (self.scratch / "up").rglob("*.json"))
        for leak in ("jana@", "bob@", "777 123", "Kristyna"):
            self.assertNotIn(leak, everything, leak)
        core = self.doc(hive, "core")
        self.assertEqual(core["people"], [{"handle": "jana", "name": "Jana Example ([email removed])", "role": "postdoc, [phone removed]"}])
        self.assertEqual((core["registry"][0]["status"], core["registry"][0]["current_phase"]),
                         ("waiting on [email removed]", "call [phone removed]"))
        page = self.doc(hive, "wiki-000")["pages"][0]
        self.assertEqual((page["type"], page["status"]), ("contact [email removed]", "ask [email removed]"))
        owners = {card["slug"]: card["owner"] for card in self.doc(hive, "cards-000")["cards"]}
        self.assertEqual((owners["legacy"], owners["fix-map"]), (None, "jana"))  # format alone is not enough: the roster

    def test_machine_local_paths_never_leave_in_free_text_or_wiki_sources(self) -> None:
        self.make_flowie()
        self.write(self.flowie / "tasks" / "inbox" / "raw.md", task("Copy the raw files", "inbox")
                   + "\nThe raw files are in C:\\Users\\jana\\Studies\\oddball\\raw and /home/jana/data.\n")
        self.write(self.flowie / "wiki" / "pages" / "concepts" / "paper.md",
                   "---\ntitle: Paper\nsources: [C:\\Users\\jana\\Documents\\paper.pdf, /home/jana/x/y.pdf]\n---\n\n"
                   "The copy is in `/home/jana/x/y.pdf`; see https://example.org/home/x too.\n")
        code, result = self.export()
        everything = "".join(path.read_text(encoding="utf-8") for path in (self.scratch / "up").rglob("*.json"))
        self.assertNotIn("jana", everything)
        cards = {card["slug"]: card for card in self.doc("flowie", "cards-000")["cards"]}
        self.assertEqual(cards["raw"]["notes"], "The raw files are in [local path removed] and [local path removed].")
        page = next(page for page in self.doc("flowie", "wiki-000")["pages"] if page["id"] == "concepts/paper")
        self.assertEqual(page["sources"], ["paper.pdf", "y.pdf"])
        self.assertIn("`[local path removed]`", page["body"])
        self.assertIn("https://example.org/home/x", page["body"])  # a web address is no local path
        self.assertEqual(result["levels"][0]["withheld"], [])     # replaced, not held back

    def test_registry_urls_leave_without_user_info_and_a_secret_holds_the_entry_back(self) -> None:
        self.make_flowie()
        token = "ghp_" + "A1b2C3d4" * 5
        self.write(self.flowie / "projects" / "projects.json", json.dumps({"projects": [
            {"id": "oddball", "repos": [f"https://jana:{token}@github.com/example-lab/oddball.git",
                                        "git@github.com:example-lab/oddball.git", "ssh://jana@lab.example.org/git/oddball.git",
                                        "https://gitlab.example.org/lab/oddball?private_token=abc123#readme", "C:/Users/jana/oddball"]},
            {"id": "leaky", "repos": [f"https://example.org/{token}/leaky.git"]}]}))
        code, result = self.export()
        registry = {entry["id"]: entry for entry in self.doc("flowie", "core")["registry"]}
        self.assertEqual(registry["oddball"]["repos"], [
            "https://github.com/example-lab/oddball.git", "git@github.com:example-lab/oddball.git",
            "ssh://lab.example.org/git/oddball.git", "https://gitlab.example.org/lab/oddball"])
        self.assertNotIn("leaky", registry)
        self.assertIn({"source": "registry", "item": "leaky", "reason": "secret-like text"}, result["levels"][0]["withheld"])
        everything = "".join(path.read_text(encoding="utf-8") for path in (self.scratch / "up").rglob("*.json"))
        for leak in (token, "jana", "abc123"):
            self.assertNotIn(leak, everything, leak)
        self.assertEqual(wb.public_url("jana@lab-server:repos/x.git"), "lab-server:repos/x.git")

    def test_ids_and_roster_names_follow_the_pii_config_user_yaml_names(self) -> None:
        hive = "hive+example-lab+hive"
        self.make_hive(policy="allow")
        keys = self.base / "keys"  # outside every project, as pii_scan.py wants the roster
        names = self.write(keys / "names.txt", "Jana Novakova\n")
        wb.pii().build_roster(names, keys / "roster.json", self.base / "work")
        self.write(keys / "pii.json", json.dumps({"id_patterns": [{"name": "subject", "regex": r"\bsub-\d{2}\b"}],
                                                  "roster": "roster.json"}))  # relative: read next to the config
        self.write(self.hive / "tasks" / "inbox" / "call.md", task("Call Jana Novakova (sub-07) about session 2", "inbox"))
        self.write(self.hive / "tasks" / "inbox" / "ids.md", task("Re-run sub-07", "inbox"))
        base = 'workbench: on\nworkbench_machine: laptop\nworkbench_levels: ["hive+example-lab+hive"]\n'
        self.user_yaml(base)
        code, result = self.export()  # without pii_config neither is checked — the consent table says so
        titles = {card["slug"]: card["title"] for card in self.doc(hive, "cards-000")["cards"]}
        self.assertEqual(titles["ids"], "Re-run sub-07")
        self.assertIn("call", titles)
        self.assertIn("without it, ID numbers and participant names are not checked", wb.SCRUB)
        self.user_yaml(base + f"pii_config: {(keys / 'pii.json').as_posix()}\n")
        self.assertEqual(self.wb("levels")[1]["pii_config"], (keys / "pii.json").as_posix())
        code, result = self.export()
        titles = {card["slug"]: card["title"] for card in self.doc(hive, "cards-000")["cards"]}
        self.assertEqual(titles["ids"], "Re-run [id removed]")
        self.assertNotIn("call", titles)
        self.assertIn({"source": "tasks", "item": "inbox/call.md", "reason": "a name from your participant roster"},
                      result["levels"][0]["withheld"])
        self.user_yaml(base + f"pii_config: {(keys / 'missing.json').as_posix()}\n")
        code, result = self.export()  # a config that cannot be read stops the export: nothing goes up unchecked
        self.assertEqual(code, 2)
        self.assertIn("pii_scan config", result["error"])

    def test_a_large_export_warns_and_names_index_only(self) -> None:
        self.make_flowie()
        self.write(self.flowie / "wiki" / "pages" / "concepts" / "big.md", "---\ntitle: Big\n---\n" + "word " * 2000)
        with mock.patch.object(wb, "SIZE_WARN", 1000):
            code, result = self.export()
        self.assertEqual(code, 1)
        self.assertEqual(len(result["warnings"]), 1)
        self.assertIn("flowie in workbench_index_only", result["warnings"][0])
        self.assertNotIn("warnings", self.export()[1])

    def test_the_sources_table_in_the_docs_is_the_allowlist(self) -> None:
        page = (REPO / "docs" / "concepts" / "workbench.md").read_text(encoding="utf-8").replace("\r\n", "\n")
        match = re.search(r"<!-- workbench-sources:begin -->\n(.*?)<!-- workbench-sources:end -->", page, re.S)
        self.assertIsNotNone(match, "docs/concepts/workbench.md needs the generated sources table between its markers")
        self.assertEqual(match.group(1).strip(), wb.sources_markdown().strip(),
                         "regenerate it: python skills/neuroflow-core/scripts/workbench.py sources --markdown")


class GoldenTests(unittest.TestCase):
    def test_the_golden_fixtures_are_what_the_exporter_writes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            code, _ = run("fixtures", "--out", tmp, "--json")
            self.assertEqual(code, 0)
            for name in ("snapshot.json", "intents.json", "expected.json"):
                fresh = json.loads(Path(tmp, name).read_text(encoding="utf-8"))
                committed = json.loads((FIXTURES / name).read_text(encoding="utf-8"))
                self.assertEqual(fresh, committed, f"{name} drifted: python skills/neuroflow-core/scripts/workbench.py "
                                                   "fixtures --out tests/fixtures/workbench")

    def test_the_golden_snapshot_shows_the_privacy_rules(self) -> None:
        snapshot = json.loads((FIXTURES / "snapshot.json").read_text(encoding="utf-8"))
        text = json.dumps(snapshot)
        for leak in ("@uni.example.org", "777 123", "correct-horse", "anxiety", "never leaves", "stay on the machine",
                     "private session", "something went wrong", "C:/Users"):
            self.assertNotIn(leak, text, leak)
        self.assertEqual(sorted(snapshot["metas"]), ["flowie", "hive+example-lab+hive", "project+oddball-eeg"])


class GuardTests(Home):
    def setUp(self) -> None:
        super().setUp()
        self.make_hive(git_repo=True)
        self.user_yaml('workbench: on\nworkbench_machine: laptop\nworkbench_levels: ["hive+example-lab+hive"]\n')

    def remote(self, meta: dict | None, parts: dict | None = None) -> Path:
        folder = self.scratch / "remote"
        shutil.rmtree(folder, ignore_errors=True)
        base = folder / "data" / "users" / "u_owner"
        if meta is not None:
            self.write(base / "hive+example-lab+hive.json", json.dumps({"data": meta, "version": 7}))
        for name, body in (parts or {}).items():
            self.write(base / "hive+example-lab+hive" / "parts" / f"{name}.json", json.dumps({"data": body, "version": 3}))
        return folder

    def export(self, remote: Path, *extra: str) -> tuple[int, dict]:
        return self.wb("export", "--out", str(self.scratch / "up"), "--remote", str(remote), *extra)

    def first_meta(self) -> dict:
        code, result = self.export(self.remote(None))
        self.assertEqual(result["guard"]["hive+example-lab+hive"]["verdict"], "write")
        return json.loads(Path(result["batches"][0]["writes"][-1]["file_path"]).read_text(encoding="utf-8"))

    def test_a_new_level_is_written_parts_first_meta_last_without_pins(self) -> None:
        code, result = self.export(self.remote(None))
        writes = result["batches"][0]["writes"]
        self.assertEqual([w["doc_id"] for w in writes][-1], "hive+example-lab+hive")
        self.assertTrue(all("if_version" not in w for w in writes))
        self.assertTrue(all(wb.is_document(f"{w['collection']}/{w['doc_id']}") for w in writes))
        meta = json.loads(Path(writes[-1]["file_path"]).read_text(encoding="utf-8"))
        self.assertEqual(meta["source"]["branch"], "main")
        self.assertEqual(meta["machine"], "laptop")
        self.assertEqual(meta["source"]["upstream_head"], meta["source"]["head"])

    def test_the_same_machine_and_branch_overwrite_pinned_and_skip_unchanged_parts(self) -> None:
        meta = self.first_meta()
        parts = {p.stem: json.loads(p.read_text(encoding="utf-8")) for p in (self.scratch / "up" / "docs" / "hive+example-lab+hive").glob("*.json")
                 if p.stem != "meta"}
        parts["wiki-009"] = {"sha256": "old"}
        code, result = self.export(self.remote(meta, parts))
        writes = result["batches"][0]["writes"]
        self.assertEqual(result["guard"]["hive+example-lab+hive"]["verdict"], "write")
        ops = [(w["op"], w["doc_id"], w.get("if_version")) for w in writes]
        self.assertEqual(ops, [("set", "hive+example-lab+hive", 7), ("delete", "wiki-009", 3)])

    def test_another_machine_asks_and_names_both_and_yes_overwrites(self) -> None:
        meta = self.first_meta()
        meta["machine"] = "desktop"
        code, result = self.export(self.remote(meta))
        verdict = result["guard"]["hive+example-lab+hive"]
        self.assertEqual(verdict["verdict"], "ask")
        self.assertIn("desktop", verdict["question"])
        self.assertIn("laptop", verdict["question"])
        self.assertEqual(result["batches"], [])
        self.assertEqual(code, 1)
        code, result = self.export(self.remote(meta), "--overwrite", "hive+example-lab+hive")
        self.assertEqual(result["guard"]["hive+example-lab+hive"]["verdict"], "write")

    def test_a_clone_whose_upstream_is_behind_the_stored_one_is_skipped(self) -> None:
        meta = self.first_meta()
        other = self.base / "other"
        git(self.base, "clone", "-q", str(self.base / "remotes" / "example-lab-hive.git"), str(other))
        self.write(other / "ideas.md", "new\n")
        git(other, "add", "ideas.md")
        git(other, "commit", "-q", "-m", "more")
        git(other, "push", "-q", "origin", "main")
        newer = git(other, "rev-parse", "HEAD").strip()
        git(self.hive, "fetch", "-q", str(self.base / "remotes" / "example-lab-hive.git"), "main")  # the object is known here
        meta.update({"machine": "desktop"})
        meta["source"]["upstream_head"] = newer
        code, result = self.export(self.remote(meta))
        verdict = result["guard"]["hive+example-lab+hive"]
        self.assertEqual(verdict["verdict"], "skip")
        self.assertIn("behind", verdict["reason"])

    def test_an_unknown_stored_upstream_is_skipped_and_says_why(self) -> None:
        meta = self.first_meta()
        meta.update({"machine": "desktop"})
        meta["source"]["upstream_head"] = "f" * 40
        code, result = self.export(self.remote(meta))
        verdict = result["guard"]["hive+example-lab+hive"]
        self.assertEqual(verdict["verdict"], "skip")
        self.assertIn("not in this clone", verdict["reason"])

    def test_a_newer_snapshot_format_is_never_overwritten(self) -> None:
        meta = self.first_meta()
        meta["snap_schema"] = wb.SNAP_SCHEMA + 1
        code, result = self.export(self.remote(meta), "--overwrite", "hive+example-lab+hive")
        verdict = result["guard"]["hive+example-lab+hive"]
        self.assertEqual(verdict["verdict"], "refuse")
        self.assertIn("newer neuroflow", verdict["reason"])

    def test_a_page_without_settings_gets_them_back_from_the_record(self) -> None:
        prefs = self.write(self.scratch / "prefs-get.json", json.dumps({"data": {"prefs_schema": 1, "theme": "light"}, "version": 4}))
        self.wb("record", "--set", "url=https://claude.ai/artifact/abc", "--set", "account=personal", "--prefs", str(prefs))
        code, result = self.export(self.remote(None))
        first = result["batches"][0]["writes"][0]
        self.assertEqual((first["op"], first["collection"], first["doc_id"]), ("set", "data/users/me", "prefs"))
        self.assertNotIn("if_version", first)
        self.assertEqual(json.loads(Path(first["file_path"]).read_text(encoding="utf-8")), {"prefs_schema": 1, "theme": "light"})
        self.assertEqual(result["prefs"], "restored from the record")
        remote = self.remote(None)
        self.write(remote / "data" / "users" / "u_owner" / "prefs.json", json.dumps({"data": {"theme": "dark"}, "version": 9}))
        code, result = self.export(remote)
        self.assertNotIn("prefs", result)
        self.assertFalse(any(w["doc_id"] == "prefs" for batch in result["batches"] for w in batch["writes"]))

    def test_versions_missing_from_the_listing_are_asked_for(self) -> None:
        meta = self.first_meta()
        folder = self.remote(None)
        self.write(folder / "data" / "users" / "me" / "hive+example-lab+hive.json", json.dumps(meta))
        code, result = self.export(folder)
        self.assertEqual(code, 2)
        self.assertIn("--versions", result["error"])
        versions = self.write(self.scratch / "versions.json", json.dumps({"data/users/me/hive+example-lab+hive": 4}))
        code, result = self.export(folder, "--versions", str(versions))
        self.assertEqual(result["batches"][0]["writes"][-1]["if_version"], 4)

    def test_batches_respect_the_limits(self) -> None:
        entries = [{"op": "set", "collection": "c", "doc_id": f"d{n}", "_bytes": 150_000} for n in range(14)]
        batches = wb.plan_batches(entries)
        self.assertTrue(all(len(batch["writes"]) <= wb.BATCH_WRITES and batch["bytes"] <= wb.BATCH_BYTES for batch in batches))
        self.assertEqual(sum(len(batch["writes"]) for batch in batches), 14)
        many = wb.plan_batches([{"op": "delete", "collection": "c", "doc_id": f"d{n}"} for n in range(120)])
        self.assertEqual([len(batch["writes"]) for batch in many], [50, 50, 20])


class UpstreamPolicyTests(Home):
    """The team's workbench_mirror as the upstream holds it: a clone that is behind follows the stricter value."""

    HIVE = "hive+example-lab+hive"

    def setUp(self) -> None:
        super().setUp()
        self.user_yaml('workbench: on\nworkbench_machine: laptop\nworkbench_levels: ["hive+example-lab+hive"]\n')

    def teammate_sets(self, policy: str) -> None:
        """A teammate pushes hive.md with this workbench_mirror; this member's clone has not pulled it."""
        other = self.base / "teammate"
        git(self.base, "clone", "-q", str(self.base / "remotes" / "example-lab-hive.git"), str(other))
        self.write(other / "hive.md", f"---\nworkbench_mirror: {policy}\n---\n# Example Lab\n")
        git(other, "commit", "-q", "-am", f"hive: workbench_mirror {policy}")
        git(other, "push", "-q", "origin", "main")

    def stored(self) -> Path:
        remote = self.scratch / "remote"
        users = remote / "data" / "users" / "me"
        self.write(users / f"{self.HIVE}.json", json.dumps({"data": {"parts": [{"id": "core"}]}, "version": 3}))
        self.write(users / self.HIVE / "parts" / "core.json", json.dumps({"data": {}, "version": 4}))
        return remote

    def test_a_forbid_the_team_pushed_stops_the_export_and_purges_after_a_fetch(self) -> None:
        self.make_hive(policy="allow", git_repo=True)
        self.teammate_sets("forbid")
        code, result = self.wb("export", "--out", str(self.scratch / "up"))  # nothing fetched yet: as this clone knows
        self.assertEqual([row["level"] for row in result["levels"]], [self.HIVE])
        code, result = self.wb("export", "--out", str(self.scratch / "up"), "--fetch")
        self.assertEqual(result["levels"], [])
        row = next(row for row in result["not_mirrored"] if row["level"] == self.HIVE)
        self.assertEqual(row["reason"], "the team forbids mirroring it — so says the upstream hive.md; pull this clone")
        self.assertEqual([row["level"] for row in result["purge"]], [self.HIVE])
        code, result = self.wb("gc", "--remote", str(self.stored()))
        self.assertEqual([(w["doc_id"], w["if_version"]) for batch in result["batches"] for w in batch["writes"]],
                         [("core", 4), (self.HIVE, 3)])

    def test_an_opt_in_this_clone_has_not_pulled_neither_exports_nor_purges(self) -> None:
        self.make_hive(policy=None, git_repo=True)
        self.teammate_sets("allow")
        code, result = self.wb("export", "--out", str(self.scratch / "up"), "--fetch")
        self.assertEqual(result["levels"], [])  # the stricter value: not until this clone has the team's opt-in
        self.assertIn("the upstream hive.md allows it: pull this clone",
                      next(row for row in result["not_mirrored"] if row["level"] == self.HIVE)["reason"])
        self.assertEqual(result["purge"], [])  # another machine with a current clone may mirror it rightly
        code, result = self.wb("gc", "--remote", str(self.stored()))
        self.assertEqual((code, result["deletes"]), (0, 0))
        git(self.hive, "pull", "-q")
        code, result = self.wb("export", "--out", str(self.scratch / "up"))
        self.assertEqual([row["level"] for row in result["levels"]], [self.HIVE])


def intent(op: str, level: str, created: str, status: str = "claimed", machine: str = "laptop", **fields) -> dict:
    body = {"intent_schema": 1, "op": op, "level": level, "created_at": f"2026-10-21T10:{created}:00.000Z", "status": status, **fields}
    if status == "claimed":
        body["claim"] = {"machine": machine, "claimed_at": "2026-10-21T09:59:00Z"}
    return body


class IntentTests(Home):
    """Pickup, validation (chains, merges, cancels, conflicts) and apply, on real clones."""

    def setUp(self) -> None:
        super().setUp()
        self.make_flowie(git_repo=True)
        self.make_hive(git_repo=True)
        self.make_project()

    def intents(self, docs: dict[str, dict], version: int = 2) -> Path:
        folder = self.scratch / "intents"
        shutil.rmtree(folder, ignore_errors=True)
        for iid, body in docs.items():
            self.write(folder / "data" / "users" / "me" / "inbox" / "intents" / f"{iid}.json", json.dumps({"data": body, "version": version}))
        return folder

    def base_of(self, path: Path) -> str:
        return wb.pj.task_hash(path.read_text(encoding="utf-8"))

    def validate(self, docs: dict[str, dict]) -> tuple[int, dict, dict]:
        plan = self.scratch / "plan.json"
        code, result = self.wb("validate", "--intents", str(self.intents(docs)), "--out", str(plan))
        data = json.loads(plan.read_text(encoding="utf-8"))
        verdicts = {iid: v for level in data["levels"] for iid, v in level["verdicts"].items()}
        verdicts.update(data["rejected"])
        return code, data, verdicts

    def test_pickup_claims_what_this_session_can_apply(self) -> None:
        hive = "hive+example-lab+hive"
        docs = {
            "i-a1-aaaa": intent("move", hive, "01", status="pending", target={"slug": "fix-map"}, **{"from": "inbox"}, to="active", base="0" * 64),
            "i-a2-bbbb": intent("move", "project+other-study", "02", status="pending", target={"slug": "x"}, **{"from": "a"}, to="b", base="0" * 64),
            "i-a3-cccc": intent("move", hive, "03", status="claimed", machine="desktop", target={"slug": "x"}, **{"from": "a"}, to="b", base="0" * 64),
            "i-a4-dddd": dict(intent("move", hive, "04", status="claimed", machine="desktop", target={"slug": "x"}, **{"from": "a"}, to="b", base="0" * 64),
                              claim={"machine": "desktop", "claimed_at": "2026-10-21T09:00:00Z"}),
            "i-a5-eeee": intent("move", "not a key", "05", status="pending"),
            "i-a6-ffff": intent("add", "flowie", "06", status="done", fields={"title": "Done"}),
        }
        code, result = self.wb("pickup", "--intents", str(self.intents(docs)), "--out", str(self.scratch / "claims"))
        claimed = sorted(w["doc_id"] for batch in result["batches"] for w in batch["writes"])
        self.assertEqual(claimed, ["i-a1-aaaa", "i-a4-dddd", "i-a5-eeee"])  # pending here, an expired claim, a malformed one
        reasons = {item["intent"]: item["reason"] for item in result["skipped"]}
        self.assertEqual(reasons["i-a2-bbbb"], "open Claude Code in the project other-study")
        self.assertIn("claimed by desktop", reasons["i-a3-cccc"])
        write = next(w for batch in result["batches"] for w in batch["writes"] if w["doc_id"] == "i-a1-aaaa")
        self.assertEqual((write["op"], write["if_version"]), ("update", 2))
        body = json.loads(Path(write["file_path"]).read_text(encoding="utf-8"))
        self.assertEqual(body, {"status": "claimed", "claim": {"machine": "laptop", "claimed_at": NOW}})

    def test_malformed_or_newer_intents_never_stop_a_run_and_are_rejected_with_a_reason(self) -> None:
        hive = "hive+example-lab+hive"

        def docs(status: str) -> dict[str, dict]:
            return {
                "i-x1-aaaa": intent("move", hive, "01", status=status, target={"slug": "fix-map"}, **{"from": "inbox"}, to="active",
                                    base="0" * 64, intent_schema=2, after=["i-zz-zzzz"]),
                "i-x2-bbbb": intent("move", {"org": "example-lab"}, "02", status=status, target={"slug": "fix-map"}, **{"from": "inbox"}, to="active"),
                "i-x3-cccc": intent("add", hive, "03", status=status, fields={"title": "T", "phase": ["data"]}),
                "i-x4-dddd": intent("move", hive, "04", status=status, target=["fix-map"], **{"from": "inbox"}, to="active"),
                "i-x5-eeee": intent("cancel", hive, "05", status=status, target={"intent": ["i-x1-aaaa"]}),
                "i-x6-ffff": intent("cancel", {"x": 1}, "06", status="pending", target=["i-x1-aaaa"]),
                "i-x7-gggg": dict(intent("add", hive, "07", status="done", fields={"title": "U"}), outcome="applied"),
            }
        code, result = self.wb("pickup", "--intents", str(self.intents(docs("pending"))), "--out", str(self.scratch / "claims"))
        self.assertIn(code, (0, 1), result)
        claimed = sorted(w["doc_id"] for batch in result["batches"] for w in batch["writes"])
        self.assertEqual(claimed, ["i-x1-aaaa", "i-x2-bbbb", "i-x3-cccc", "i-x4-dddd", "i-x5-eeee", "i-x6-ffff"])
        code, result = self.wb("pending", "--intents", str(self.intents(docs("pending"))))
        self.assertEqual(code, 0, result)
        code, plan, verdicts = self.validate(docs("claimed"))
        self.assertEqual(code, 1)
        self.assertIn("intent_schema 2", verdicts["i-x1-aaaa"]["reason"])
        self.assertEqual(verdicts["i-x2-bbbb"]["reason"], "schema: no valid level")
        self.assertEqual(verdicts["i-x3-cccc"]["reason"], "schema: phase must be text")
        self.assertEqual(verdicts["i-x4-dddd"]["reason"], "schema: target must name one slug or one intent")
        self.assertEqual(verdicts["i-x5-eeee"]["reason"], "schema: target must name one slug or one intent")
        self.assertTrue(all(verdict["result"] == "rejected" for verdict in verdicts.values()))

    def test_a_chain_waits_whole_while_its_first_link_is_claimed_elsewhere(self) -> None:
        hive = "hive+example-lab+hive"
        docs = {"i-w1-aaaa": intent("move", hive, "01", status="claimed", machine="desktop", target={"slug": "fix-map"}, **{"from": "inbox"},
                                    to="active", base="0" * 64),
                "i-w2-bbbb": intent("move", hive, "02", status="pending", target={"slug": "fix-map"}, **{"from": "active"}, to="review",
                                    after="i-w1-aaaa", base="0" * 64)}
        code, result = self.wb("pickup", "--intents", str(self.intents(docs)), "--out", str(self.scratch / "claims"))
        self.assertEqual(result["claim"], 0)
        reasons = {item["intent"]: item["reason"] for item in result["skipped"]}
        self.assertEqual(reasons["i-w2-bbbb"], "waits for i-w1-aaaa")
        self.assertIn("claimed by desktop", reasons["i-w1-aaaa"])

    def test_two_moves_of_one_card_merge_into_one(self) -> None:
        hive = "hive+example-lab+hive"
        base = self.base_of(self.hive / "tasks" / "inbox" / "fix-map.md")
        code, plan, verdicts = self.validate({
            "i-b1-aaaa": intent("move", hive, "01", target={"slug": "fix-map"}, **{"from": "inbox"}, to="active", base=base),
            "i-b2-bbbb": intent("move", hive, "02", target={"slug": "fix-map"}, **{"from": "active"}, to="review", after="i-b1-aaaa", base=base),
        })
        self.assertEqual(verdicts["i-b1-aaaa"], {"result": "coalesced", "into": "i-b2-bbbb"})
        self.assertEqual(verdicts["i-b2-bbbb"]["result"], "applied")
        actions = plan["levels"][0]["actions"]
        self.assertEqual([(a["op"], a["from"], a["to"], a["intents"]) for a in actions],
                         [("move", "inbox", "review", ["i-b1-aaaa", "i-b2-bbbb"])])

    def test_a_card_added_on_the_board_is_moved_by_its_add(self) -> None:
        code, plan, verdicts = self.validate({
            "i-c1-aaaa": intent("add", "flowie", "01", fields={"title": "Read paper"}, to="inbox"),
            "i-c2-bbbb": intent("move", "flowie", "02", target={"intent": "i-c1-aaaa"}, **{"from": "inbox"}, to="active", after="i-c1-aaaa"),
        })
        self.assertEqual(verdicts["i-c1-aaaa"]["slug"], "read-paper-2")  # read-paper exists: the slug rules apply
        self.assertEqual(verdicts["i-c1-aaaa"]["column"], "active")
        self.assertEqual(verdicts["i-c2-bbbb"], {"result": "coalesced", "into": "i-c1-aaaa"})
        self.assertEqual([(a["op"], a["to"]) for a in plan["levels"][0]["actions"]], [("add", "active")])

    def test_an_added_cards_slug_is_taken_from_an_earlier_outcome(self) -> None:
        code, plan, verdicts = self.validate({
            "i-d1-aaaa": dict(intent("add", "flowie", "01", status="done", fields={"title": "Read the paper"}),
                              outcome={"result": "applied", "slug": "read-paper"}),
            "i-d2-bbbb": intent("move", "flowie", "02", target={"intent": "i-d1-aaaa"}, **{"from": "inbox"}, to="active", after="i-d1-aaaa"),
        })
        self.assertEqual(plan["levels"][0]["actions"][0]["slug"], "read-paper")
        self.assertEqual(verdicts["i-d2-bbbb"]["result"], "applied")

    def test_a_cancel_cancels_and_what_depended_on_it_is_rejected(self) -> None:
        base = self.base_of(self.flowie / "tasks" / "inbox" / "read-paper.md")
        code, plan, verdicts = self.validate({
            "i-e1-aaaa": intent("move", "flowie", "01", target={"slug": "read-paper"}, **{"from": "inbox"}, to="active", base=base),
            "i-e2-bbbb": intent("move", "flowie", "02", target={"slug": "read-paper"}, **{"from": "active"}, to="done", after="i-e1-aaaa", base=base),
            "i-e3-cccc": intent("cancel", "flowie", "03", target={"intent": "i-e1-aaaa"}),
        })
        self.assertEqual(verdicts["i-e1-aaaa"], {"result": "cancelled", "by": "i-e3-cccc"})
        self.assertEqual(verdicts["i-e2-bbbb"], {"result": "rejected", "reason": "depends on i-e1-aaaa"})
        self.assertEqual(verdicts["i-e3-cccc"]["result"], "applied")
        self.assertEqual(plan["levels"][0]["actions"], [])
        self.assertEqual(code, 1)

    def test_a_release_on_the_page_cancels_a_stuck_claim(self) -> None:
        base = self.base_of(self.flowie / "tasks" / "inbox" / "read-paper.md")
        code, plan, verdicts = self.validate({
            "i-f1-aaaa": intent("move", "flowie", "01", target={"slug": "read-paper"}, **{"from": "inbox"}, to="active", base=base,
                                cancel_requested_at="2026-10-21T10:30:00Z")})
        self.assertEqual(verdicts["i-f1-aaaa"], {"result": "cancelled", "by": "release"})

    def test_cancelling_what_is_applied_is_rejected(self) -> None:
        code, plan, verdicts = self.validate({
            "i-g1-aaaa": dict(intent("move", "flowie", "01", status="done", target={"slug": "read-paper"}, **{"from": "inbox"}, to="active",
                                     base="0" * 64), outcome={"result": "applied"}),
            "i-g2-bbbb": intent("cancel", "flowie", "02", target={"intent": "i-g1-aaaa"}),
        })
        self.assertEqual(verdicts["i-g2-bbbb"]["result"], "rejected")
        self.assertIn("already applied", verdicts["i-g2-bbbb"]["reason"])

    def test_conflicts_rejections_and_the_schema(self) -> None:
        path = self.hive / "tasks" / "inbox" / "fix-map.md"
        base = self.base_of(path)
        path.write_text(path.read_text(encoding="utf-8") + "\nA teammate's note.\n", encoding="utf-8")
        hive = "hive+example-lab+hive"
        code, plan, verdicts = self.validate({
            "i-h1-aaaa": intent("move", hive, "01", target={"slug": "fix-map"}, **{"from": "inbox"}, to="active", base=base),
            "i-h2-bbbb": intent("move", hive, "02", target={"slug": "rerun-ica"}, **{"from": "inbox"}, to="review",
                                base=self.base_of(self.hive / "tasks" / "active" / "rerun-ica.md")),
            "i-h3-cccc": intent("move", hive, "03", target={"slug": "rerun-ica"}, **{"from": "active"}, to="someday",
                                base=self.base_of(self.hive / "tasks" / "active" / "rerun-ica.md")),
            "i-h4-dddd": intent("add", hive, "04", fields={"title": "New", "owner": "stranger"}),
            "i-h5-eeee": dict(intent("add", hive, "05", fields={"title": "New"}), intent_schema=9),
            "i-h6-ffff": intent("move", hive, "06", target={"slug": "gone"}, **{"from": "inbox"}, to="active", base="0" * 64),
            "i-h7-gggg": intent("add", hive, "07", fields={"title": "Fine", "owner": "jana", "due": "2026-11-01"}),
        })
        self.assertEqual(verdicts["i-h1-aaaa"]["result"], "conflict")
        self.assertIn("changed since", verdicts["i-h1-aaaa"]["reason"])
        self.assertEqual((verdicts["i-h2-bbbb"]["result"], verdicts["i-h2-bbbb"]["column"]), ("conflict", "active"))
        self.assertIn("no column someday", verdicts["i-h3-cccc"]["reason"])
        self.assertIn("not on the level's roster", verdicts["i-h4-dddd"]["reason"])
        self.assertTrue(verdicts["i-h5-eeee"]["reason"].startswith("schema:"))
        self.assertEqual(verdicts["i-h6-ffff"]["result"], "conflict")
        self.assertEqual(verdicts["i-h7-gggg"]["result"], "applied")

    def test_a_move_back_where_it_began_changes_nothing(self) -> None:
        base = self.base_of(self.flowie / "tasks" / "inbox" / "read-paper.md")
        code, plan, verdicts = self.validate({
            "i-k1-aaaa": intent("move", "flowie", "01", target={"slug": "read-paper"}, **{"from": "inbox"}, to="active", base=base),
            "i-k2-bbbb": intent("move", "flowie", "02", target={"slug": "read-paper"}, **{"from": "active"}, to="inbox", after="i-k1-aaaa", base=base),
        })
        self.assertEqual(plan["levels"][0]["actions"], [])
        self.assertTrue(verdicts["i-k2-bbbb"]["noop"])

    def test_legacy_and_conflicted_files_offer_no_moves(self) -> None:
        self.write(self.flowie / "tasks" / "T-1-old.md", task("Old", "inbox", assignee="jana"))
        self.write(self.flowie / "tasks" / "inbox" / "broken.md", task("Broken", "inbox") + "<<<<<<< HEAD\nx\n=======\ny\n>>>>>>> b\n")
        code, plan, verdicts = self.validate({
            "i-l1-aaaa": intent("move", "flowie", "01", target={"slug": "old"}, **{"from": "inbox"}, to="active",
                                base=self.base_of(self.flowie / "tasks" / "T-1-old.md")),
            "i-l2-bbbb": intent("move", "flowie", "02", target={"slug": "broken"}, **{"from": "inbox"}, to="active",
                                base=self.base_of(self.flowie / "tasks" / "inbox" / "broken.md")),
        })
        self.assertIn("legacy", verdicts["i-l1-aaaa"]["reason"])
        self.assertIn("conflict markers", verdicts["i-l2-bbbb"]["reason"])

    def apply(self, level: str) -> tuple[int, dict]:
        return self.wb("apply", "--plan", str(self.scratch / "plan.json"), "--level", level, "--today", "2026-10-21")

    def test_apply_moves_stages_and_the_commit_carries_the_trailers(self) -> None:
        hive = "hive+example-lab+hive"
        base = self.base_of(self.hive / "tasks" / "inbox" / "fix-map.md")
        docs = {
            "i-m1-aaaa": intent("move", hive, "01", target={"slug": "fix-map"}, **{"from": "inbox"}, to="active", base=base),
            "i-m2-bbbb": intent("move", hive, "02", target={"slug": "fix-map"}, **{"from": "active"}, to="review", after="i-m1-aaaa", base=base),
            "i-m3-cccc": intent("add", hive, "03", fields={"title": "Check the stats", "owner": "jana", "tags": ["qc"]}),
        }
        self.validate(docs)
        code, result = self.apply(hive)
        self.assertEqual(code, 0, result)
        moved = self.hive / "tasks" / "review" / "fix-map.md"
        self.assertFalse((self.hive / "tasks" / "inbox" / "fix-map.md").exists())
        text = moved.read_text(encoding="utf-8")
        self.assertIn("status: review", text)
        self.assertIn("updated: 2026-10-21", text)
        added = (self.hive / "tasks" / "inbox" / "check-the-stats.md").read_text(encoding="utf-8")
        self.assertIn('title: "Check the stats"\nstatus: inbox\nowner: jana\ntags: [qc]\ncreated: 2026-10-21', added)
        staged = git(self.hive, "diff", "--cached", "--name-status")
        self.assertIn("tasks/review/fix-map.md", staged)
        commit = result["commit"]
        self.assertIn("Neuroflow-Intent: i-m1-aaaa\nNeuroflow-Intent: i-m2-bbbb\nNeuroflow-Intent: i-m3-cccc", commit["message"])
        subprocess.run(commit["argv"], check=True, capture_output=True, env=dict(os.environ, **GIT_ENV))
        self.assertEqual(git(self.hive, "status", "--porcelain").strip(), "")
        self.assertEqual(set(wb.trailer_commits(self.hive)), {"i-m1-aaaa", "i-m2-bbbb", "i-m3-cccc"})
        # outcomes: what landed is applied, with its state from git; the coalesced one points at its lead
        listed = self.intents(docs, version=5)
        code, result = self.wb("export", "--out", str(self.scratch / "up"), "--remote", str(self.scratch / "empty"),
                               "--outcomes", str(self.scratch / "plan.json"), "--intents", str(listed), "--level", hive)
        updates = {w["doc_id"]: (w, json.loads(Path(w["file_path"]).read_text(encoding="utf-8")))
                   for batch in result["batches"] for w in batch["writes"] if w["collection"] == wb.intents_collection()}
        self.assertEqual(updates["i-m2-bbbb"][0]["if_version"], 5)
        self.assertEqual(updates["i-m2-bbbb"][1]["outcome"]["state"], "committed")
        self.assertEqual(updates["i-m1-aaaa"][1]["outcome"]["result"], "coalesced")
        self.assertEqual(updates["i-m3-cccc"][1]["outcome"]["slug"], "check-the-stats")
        meta = json.loads((self.scratch / "up" / "docs" / "hive+example-lab+hive" / "meta.json").read_text(encoding="utf-8"))
        self.assertEqual(meta["applied"]["i-m2-bbbb"]["state"], "committed")
        self.assertLessEqual(set(meta["applied"]["i-m2-bbbb"]), set(wb.FIELDS["applied"]))
        # pushed to a branch (a protected main: the pull request is open) is pushed; on the default branch it is merged
        git(self.hive, "push", "-q", "origin", "HEAD:refs/heads/workbench-changes")
        self.assertEqual(wb.landed_states(self.hive, wb.trailer_commits(self.hive))["i-m2-bbbb"]["state"], "pushed")
        git(self.hive, "push", "-q", "origin", "main")
        git(self.hive, "fetch", "-q", "origin")
        self.assertEqual(wb.landed_states(self.hive, wb.trailer_commits(self.hive))["i-m2-bbbb"]["state"], "merged")

    def ledger(self) -> dict:
        return json.loads((self.home / ".neuroflow" / "workbench" / "ledger.json").read_text(encoding="utf-8"))

    def commit(self, result: dict) -> None:
        subprocess.run(result["commit"]["argv"], check=True, capture_output=True, env=dict(os.environ, **GIT_ENV))

    def test_a_run_that_stopped_before_the_commit_is_finished_not_repeated(self) -> None:
        hive = "hive+example-lab+hive"
        base = self.base_of(self.hive / "tasks" / "inbox" / "fix-map.md")
        docs = {"i-n1-aaaa": intent("move", hive, "01", target={"slug": "fix-map"}, **{"from": "inbox"}, to="active", base=base)}
        self.validate(docs)
        self.apply(hive)  # moved and staged, never committed
        self.assertEqual(self.ledger()["levels"][hive]["i-n1-aaaa"]["to"], "active")  # recorded before any commit
        code, plan, verdicts = self.validate(docs)
        self.assertEqual([(a["op"], a["intents"]) for a in plan["levels"][0]["actions"]], [("commit", ["i-n1-aaaa"])])
        self.assertEqual(verdicts["i-n1-aaaa"], {"result": "applied", "slug": "fix-map", "column": "active"})
        code, result = self.apply(hive)
        self.assertEqual(code, 0, result)
        self.assertEqual(sorted(result["commit"]["paths"]), ["tasks/active/fix-map.md", "tasks/inbox/fix-map.md"])
        self.assertEqual(result["commit"]["message"].splitlines()[0], "tasks: workbench — move fix-map → active")
        self.commit(result)
        code, plan, verdicts = self.validate(docs)
        self.assertEqual(verdicts["i-n1-aaaa"]["note"], "already in git")
        self.assertEqual(plan["levels"][0]["actions"], [])
        self.apply(hive)  # once its commit exists, the entry goes
        self.assertNotIn("i-n1-aaaa", self.ledger()["levels"][hive])

    def test_without_a_ledger_a_move_found_in_its_target_column_is_committed_not_moved_again(self) -> None:
        hive = "hive+example-lab+hive"
        base = self.base_of(self.hive / "tasks" / "inbox" / "fix-map.md")
        docs = {"i-n2-aaaa": intent("move", hive, "01", target={"slug": "fix-map"}, **{"from": "inbox"}, to="active", base=base)}
        self.validate(docs)
        self.apply(hive)
        (self.home / ".neuroflow" / "workbench" / "ledger.json").unlink()  # e.g. applied by an older neuroflow
        code, plan, verdicts = self.validate(docs)
        self.assertTrue(plan["levels"][0]["actions"][0]["half_done"])
        code, result = self.apply(hive)
        self.assertEqual(code, 0, result)
        self.assertEqual(sorted(result["commit"]["paths"]), ["tasks/active/fix-map.md", "tasks/inbox/fix-map.md"])

    def test_an_add_applied_but_not_committed_is_committed_never_added_twice(self) -> None:
        hive = "hive+example-lab+hive"
        docs = {"i-s1-aaaa": intent("add", hive, "01", fields={"title": "Check the stats", "owner": "jana"})}
        self.validate(docs)
        self.apply(hive)  # written and staged; the commit was refused
        code, plan, verdicts = self.validate(docs)
        self.assertEqual(verdicts["i-s1-aaaa"], {"result": "applied", "slug": "check-the-stats", "column": "inbox"})
        self.assertEqual([a["op"] for a in plan["levels"][0]["actions"]], ["commit"])
        code, result = self.apply(hive)
        self.assertEqual(code, 0, result)
        self.assertEqual(result["commit"]["paths"], ["tasks/inbox/check-the-stats.md"])
        self.assertEqual(result["commit"]["message"].splitlines()[0], "tasks: workbench — add check-the-stats")
        self.commit(result)
        self.assertEqual(sorted(path.name for path in (self.hive / "tasks").rglob("check-the-stats*.md")), ["check-the-stats.md"])
        self.assertIn("i-s1-aaaa", wb.trailer_commits(self.hive))
        self.assertEqual(git(self.hive, "status", "--porcelain").strip(), "")

    def test_a_merged_chain_applied_but_not_committed_keeps_its_verdicts(self) -> None:
        hive = "hive+example-lab+hive"
        base = self.base_of(self.hive / "tasks" / "inbox" / "fix-map.md")
        docs = {
            "i-u1-aaaa": intent("move", hive, "01", target={"slug": "fix-map"}, **{"from": "inbox"}, to="active", base=base),
            "i-u2-bbbb": intent("move", hive, "02", target={"slug": "fix-map"}, **{"from": "active"}, to="review", after="i-u1-aaaa", base=base),
        }
        self.validate(docs)
        self.apply(hive)  # inbox → review, staged; the commit never ran
        code, plan, verdicts = self.validate(docs)
        self.assertEqual(code, 0)  # no conflict and no "depends on"
        self.assertEqual(verdicts["i-u1-aaaa"], {"result": "coalesced", "into": "i-u2-bbbb"})
        self.assertEqual(verdicts["i-u2-bbbb"], {"result": "applied", "slug": "fix-map", "column": "review"})
        self.assertEqual([(a["op"], a["intents"]) for a in plan["levels"][0]["actions"]], [("commit", ["i-u1-aaaa", "i-u2-bbbb"])])
        code, result = self.apply(hive)
        self.commit(result)
        self.assertLessEqual({"i-u1-aaaa", "i-u2-bbbb"}, set(wb.trailer_commits(self.hive)))
        self.assertEqual(git(self.hive, "ls-tree", "-r", "--name-only", "HEAD", "tasks").split(),
                         ["tasks/active/rerun-ica.md", "tasks/review/fix-map.md"])

    def test_a_release_or_an_undo_after_the_change_was_made_cannot_undo_it(self) -> None:
        hive = "hive+example-lab+hive"
        base = self.base_of(self.hive / "tasks" / "inbox" / "fix-map.md")
        docs = {"i-v1-aaaa": intent("move", hive, "01", target={"slug": "fix-map"}, **{"from": "inbox"}, to="active", base=base)}
        self.validate(docs)
        self.apply(hive)
        docs["i-v1-aaaa"]["cancel_requested_at"] = "2026-10-21T10:40:00Z"
        docs["i-v2-bbbb"] = intent("cancel", hive, "02", target={"intent": "i-v1-aaaa"})
        code, plan, verdicts = self.validate(docs)
        self.assertEqual(verdicts["i-v1-aaaa"]["result"], "applied")
        self.assertIn("move the card back", verdicts["i-v1-aaaa"]["note"])
        self.assertEqual(verdicts["i-v2-bbbb"]["result"], "rejected")
        self.assertIn("already applied", verdicts["i-v2-bbbb"]["reason"])
        self.assertEqual([a["op"] for a in plan["levels"][0]["actions"]], ["commit"])

    def test_a_ledger_entry_whose_change_is_gone_is_judged_again(self) -> None:
        hive = "hive+example-lab+hive"
        base = self.base_of(self.hive / "tasks" / "inbox" / "fix-map.md")
        docs = {"i-w1-aaaa": intent("move", hive, "01", target={"slug": "fix-map"}, **{"from": "inbox"}, to="active", base=base)}
        self.validate(docs)
        self.apply(hive)
        git(self.hive, "reset", "-q", "--hard")  # the person threw the staged change away
        code, plan, verdicts = self.validate(docs)
        self.assertEqual([(a["op"], a["from"], a["to"]) for a in plan["levels"][0]["actions"]], [("move", "inbox", "active")])

    def test_a_task_moved_after_the_check_is_not_applied_and_is_checked_again(self) -> None:
        hive = "hive+example-lab+hive"
        base = self.base_of(self.hive / "tasks" / "inbox" / "fix-map.md")
        docs = {"i-r1-aaaa": intent("move", hive, "01", target={"slug": "fix-map"}, **{"from": "inbox"}, to="active", base=base)}
        self.validate(docs)
        # a teammate's move to review arrives (a pull) between the check and the apply; status stays out of the hash
        (self.hive / "tasks" / "review").mkdir(parents=True, exist_ok=True)
        git(self.hive, "mv", "tasks/inbox/fix-map.md", "tasks/review/fix-map.md")
        moved = self.hive / "tasks" / "review" / "fix-map.md"
        moved.write_bytes(moved.read_bytes().replace(b"status: inbox", b"status: review"))
        git(self.hive, "commit", "-q", "-am", "a teammate moves fix-map to review")
        self.assertEqual(self.base_of(moved), base)
        code, result = self.apply(hive)
        self.assertEqual(code, 1, result)
        self.assertEqual(result["applied"], [])
        self.assertIn("moved after the check (it is in review now)", result["failed"][0]["reason"])
        self.assertNotIn("commit", result)
        self.assertEqual(git(self.hive, "status", "--porcelain").strip(), "")  # nothing moved, nothing staged
        self.assertFalse((self.hive / "tasks" / "active" / "fix-map.md").exists())
        # no outcome is written for it, so it stays claimed; the next check sees the teammate's move
        listed = self.intents(docs, version=5)
        code, result = self.wb("export", "--out", str(self.scratch / "up"), "--remote", str(self.scratch / "empty"),
                               "--outcomes", str(self.scratch / "plan.json"), "--intents", str(listed), "--level", hive)
        self.assertEqual(result["outcomes"]["written"], 0)
        self.assertEqual([item["intent"] for item in result["outcomes"]["not_yet"]], ["i-r1-aaaa"])
        code, plan, verdicts = self.validate(docs)
        self.assertEqual((verdicts["i-r1-aaaa"]["result"], verdicts["i-r1-aaaa"]["column"]), ("conflict", "review"))

    def test_a_project_move_stays_in_the_working_tree_and_the_ledger_remembers_it(self) -> None:
        self.make_project(git_repo=True)
        key = "project+oddball-eeg"
        base = self.base_of(self.project / ".neuroflow" / "tasks" / "review" / "qc-report.md")
        docs = {"i-p1-aaaa": intent("move", key, "01", target={"slug": "qc-report"}, **{"from": "review"}, to="done", base=base)}
        self.validate(docs)
        code, result = self.apply(key)
        self.assertEqual(code, 0, result)
        self.assertNotIn("commit", result)
        self.assertTrue((self.project / ".neuroflow" / "tasks" / "done" / "qc-report.md").is_file())
        ledger = json.loads((self.home / ".neuroflow" / "workbench" / "ledger.json").read_text(encoding="utf-8"))
        self.assertEqual(ledger["levels"][key]["i-p1-aaaa"]["to"], "done")
        code, result = self.wb("export", "--out", str(self.scratch / "up"), "--level", key)
        meta = json.loads((self.scratch / "up" / "docs" / "project+oddball-eeg" / "meta.json").read_text(encoding="utf-8"))
        self.assertEqual(meta["applied"], {"i-p1-aaaa": {"state": "worktree"}})
        self.assertEqual(meta["source"]["uncommitted_tasks"], 1)  # one staged rename

    def test_pending_names_the_project_root_as_reached_and_as_resolved(self) -> None:
        link = self.base / "jn"
        try:
            if os.name == "nt":
                import _winapi
                _winapi.CreateJunction(str(self.project.parent), str(link))
            else:
                os.symlink(self.project.parent, link, target_is_directory=True)
        except (OSError, AttributeError, ImportError) as error:
            self.skipTest(f"no junction or symlink here: {error}")
        try:
            via = link / "oddball"
            docs = {"i-j1-aaaa": intent("move", "project+oddball-eeg", "01", status="pending", target={"slug": "qc-report"},
                                        **{"from": "review"}, to="done", base="0" * 64)}
            code, result = run("pending", "--intents", str(self.intents(docs)), "--home", str(self.home), "--root", str(via),
                               "--now", NOW, "--json")
            level = next(item for item in result["levels"] if item["level"] == "project+oddball-eeg")
            self.assertEqual(level["root"], via.as_posix())  # the spelling the person opened, which the mod sees
            self.assertEqual(level["roots"], [via.as_posix(), self.project.resolve().as_posix()])
        finally:
            os.rmdir(link) if os.name == "nt" else os.unlink(link)

    def test_pending_json_tells_the_mod_which_cards_wait(self) -> None:
        hive = "hive+example-lab+hive"
        docs = {"i-q1-aaaa": intent("move", hive, "01", status="pending", target={"slug": "fix-map"}, **{"from": "inbox"}, to="active",
                                    base="0" * 64),
                "i-q2-bbbb": intent("add", "flowie", "02", status="pending", fields={"title": "X"}),
                "i-q3-cccc": intent("add", "flowie", "03", status="done", fields={"title": "Y"})}
        code, result = self.wb("pending", "--intents", str(self.intents(docs)))
        data = json.loads((self.home / ".neuroflow" / "workbench" / "pending.json").read_text(encoding="utf-8"))
        self.assertEqual(data["count"], 2)
        levels = {item["level"]: item for item in data["levels"]}
        self.assertEqual(levels[hive]["board"], "hive:lab-folder")
        self.assertEqual(levels[hive]["slugs"], ["fix-map"])
        self.assertEqual(levels["flowie"]["adds"], 1)
        self.assertEqual(data["command"], "/neuroflow:tasks --apply-web")
        self.assertEqual((levels[hive]["oldest"], levels["flowie"]["oldest"]), ("2026-10-21T10:01:00Z", "2026-10-21T10:02:00Z"))
        self.assertEqual(data["oldest"], "2026-10-21T10:01:00Z")


class GcTests(Home):
    def test_old_intents_purged_levels_and_orphans_go_parts_before_their_meta(self) -> None:
        self.make_flowie()
        self.make_hive(policy="forbid")
        intents = self.scratch / "intents" / "data" / "users" / "me" / "inbox" / "intents"
        self.write(intents / "i-old-aaaa.json", json.dumps({"data": {"status": "done", "outcome": {"at": "2026-10-01T00:00:00Z"}}, "version": 2}))
        self.write(intents / "i-new-bbbb.json", json.dumps({"data": {"status": "done", "outcome": {"at": "2026-10-20T00:00:00Z"}}, "version": 2}))
        self.write(intents / "i-wait-cccc.json", json.dumps({"data": {"status": "pending"}, "version": 1}))
        users = self.scratch / "remote" / "data" / "users" / "me"
        self.write(users / "hive+example-lab+hive.json", json.dumps({"data": {"parts": [{"id": "core"}]}, "version": 3}))
        self.write(users / "hive+example-lab+hive" / "parts" / "core.json", json.dumps({"data": {}, "version": 4}))
        self.write(users / "flowie.json", json.dumps({"data": {"parts": [{"id": "core"}]}, "version": 5}))
        self.write(users / "flowie" / "parts" / "core.json", json.dumps({"data": {}, "version": 6}))
        self.write(users / "flowie" / "parts" / "wiki-007.json", json.dumps({"data": {}, "version": 7}))
        self.write(users / "prefs.json", json.dumps({"data": {"theme": "dark"}, "version": 8}))
        code, result = self.wb("gc", "--intents", str(self.scratch / "intents"), "--remote", str(self.scratch / "remote"))
        self.assertEqual(code, 1)
        deletes = [(w["collection"].split("/")[-1], w["doc_id"], w["if_version"]) for batch in result["batches"] for w in batch["writes"]]
        self.assertEqual(deletes, [("intents", "i-old-aaaa", 2), ("parts", "core", 4), ("me", "hive+example-lab+hive", 3),
                                   ("parts", "wiki-007", 7)])
        self.assertIn("forbids", result["purge"][0]["reason"])

    def store(self, levels: dict[str, list[str]], listed: tuple[str, ...] | None = None) -> Path:
        """A saved listing of data/users/me: each level's meta naming its parts, and those parts (for `listed` levels)."""
        remote = self.scratch / "remote"
        shutil.rmtree(remote, ignore_errors=True)
        users = remote / "data" / "users" / "u_0123456789abcdefghijkl"
        for n, (key, parts) in enumerate(levels.items()):
            self.write(users / f"{key}.json", json.dumps({"data": {"parts": [{"id": part} for part in parts]}, "version": 10 + n}))
            for m, part in enumerate(parts if listed is None or key in listed else []):
                self.write(users / key / "parts" / f"{part}.json", json.dumps({"data": {}, "version": 100 + 10 * n + m}))
        return remote

    def test_levels_another_machine_mirrors_are_never_purged_from_here(self) -> None:
        self.make_flowie()
        self.make_project()
        self.user_yaml('workbench: on\nworkbench_machine: laptop\nworkbench_levels: ["flowie", "project+oddball-eeg"]\n')
        remote = self.store({"flowie": ["core"], "project+oddball-eeg": ["core"], "project+other-study": ["core", "cards-000"],
                             "hive+other-lab+hive": ["core"]})
        code, result = self.wb("gc", "--remote", str(remote))
        self.assertEqual((code, result["deletes"], result["purge"], result["unlisted"]), (0, 0, [], []))

    def test_a_level_taken_off_here_is_purged_only_when_named_and_always_with_its_parts(self) -> None:
        self.make_flowie()
        self.make_hive(policy="allow")
        self.user_yaml('workbench: on\nworkbench_machine: laptop\nworkbench_levels: ["flowie"]\n')
        hive = "hive+example-lab+hive"
        remote = self.store({"flowie": ["core"], hive: ["core", "cards-000"]})
        code, result = self.wb("gc", "--remote", str(remote))
        self.assertEqual((code, result["deletes"]), (0, 0))  # only this machine leaves it out: another may mirror it
        code, result = self.wb("gc", "--remote", str(remote), "--purge", hive)
        self.assertEqual(code, 1)
        deletes = [(w["collection"], w["doc_id"], w["if_version"]) for batch in result["batches"] for w in batch["writes"]]
        self.assertEqual(deletes, [(f"data/users/me/{hive}/parts", "cards-000", 111), (f"data/users/me/{hive}/parts", "core", 110),
                                   ("data/users/me", hive, 11)])
        self.assertEqual(result["purge"], [{"level": hive, "reason": "you took it off your workbench"}])
        # the parts were not listed: the meta is not deleted alone, and gc says what to list
        code, result = self.wb("gc", "--remote", str(self.store({"flowie": ["core"], hive: ["core", "cards-000"]}, listed=("flowie",))),
                               "--purge", hive)
        self.assertEqual((code, result["deletes"]), (1, 0))
        self.assertEqual(result["unlisted"], [{"level": hive, "list": f"data/users/me/{hive}/parts"}])
        code, result = self.wb("gc", "--remote", str(remote), "--purge", "flowie")
        self.assertEqual(code, 2)
        self.assertIn("still mirrored on this machine: flowie", result["error"])

    def test_orphans_are_judged_against_the_metas_of_the_listing_given(self) -> None:
        # after an upload cut off before its meta, the next refresh writes a meta naming wiki-000 again: judged against a
        # listing taken before that upload, wiki-000 looks orphaned; against one taken after it (step 8 lists again), not
        self.make_flowie()
        stale = self.store({"flowie": ["core"]})
        self.write(stale / "data" / "users" / "u_0123456789abcdefghijkl" / "flowie" / "parts" / "wiki-000.json",
                   json.dumps({"data": {}, "version": 20}))
        code, result = self.wb("gc", "--remote", str(stale))
        self.assertEqual([w["doc_id"] for batch in result["batches"] for w in batch["writes"]], ["wiki-000"])
        code, result = self.wb("gc", "--remote", str(self.store({"flowie": ["core", "wiki-000"]})))
        self.assertEqual((code, result["deletes"]), (0, 0))

    def test_the_prose_lists_the_store_again_with_every_parts_collection_before_gc(self) -> None:
        text = " ".join((REPO / "commands" / "dashboard.md").read_text(encoding="utf-8").split())
        step = text[text.index("8. **Clean up.**"):text.index("9. **Check and record.**")]
        self.assertIn("List again what the store holds", step)
        self.assertIn("`data/users/me/{level}/parts` for every level that listing shows", step)
        self.assertIn("gc --intents {scratch}/intents --remote {scratch}/remote2", step)
        self.assertIn("--purge {level}", step)
        self.assertIn("and delete {levels} from it", text)

    def test_the_export_names_what_a_refresh_deletes(self) -> None:
        self.make_flowie()
        self.make_hive(policy="forbid")
        self.make_project(policy=None)
        code, result = self.wb("export", "--out", str(self.scratch / "up"))
        self.assertEqual({row["level"]: row["reason"] for row in result["purge"]},
                         {"hive+example-lab+hive": "the team forbids mirroring it",
                          "project+oddball-eeg": "the team has not opted in (workbench_mirror in project_config.md)"})


def prose(*parts: str) -> str:
    """A prose file with its line breaks folded to spaces (the checks below are about words, not wrapping)."""
    return " ".join(REPO.joinpath(*parts).read_bytes().decode("utf-8").split())


class ProseTests(unittest.TestCase):
    """What the commands tell Claude to do around workbench.py (the script cannot enforce these steps itself)."""

    def test_apply_web_pulls_before_the_check_and_never_between_it_and_the_apply(self) -> None:
        text = prose("commands", "tasks.md")
        check = text[text.index("4. **Check.**"):text.index("5. **Apply, level by level.**")]
        apply = text[text.index("5. **Apply, level by level.**"):text.index("6. **Outcomes")]
        self.assertIn("First pull the flowie and each hive clone a claimed intent names", check)
        self.assertIn("nothing is pulled between the check and the apply", check)
        self.assertNotIn("pull", apply.split("- `flowie`")[0].lower())

    def test_a_claim_is_previewed_and_asked_like_every_upload(self) -> None:
        text = prose("commands", "tasks.md")
        claim = text[text.index("<!-- nf-rule: EGRESS-CONFIRM --> 3. **Claim, after your yes.**"):text.index("4. **Check.**")]
        self.assertIn("preview it in one line and ask", claim)
        self.assertIn("Without a yes, claim nothing and stop", claim)
        self.assertIn("every claim of its clicks", prose("skills", "neuroflow-core", "SKILL.md"))

    def test_the_rule_on_intents_carries_the_marker_its_guard_cites(self) -> None:
        lines = REPO.joinpath("skills", "neuroflow-core", "SKILL.md").read_bytes().decode("utf-8").splitlines()
        at = next(n for n, line in enumerate(lines) if line.startswith("**Intents** — the page writes them; Claude Code never creates one"))
        self.assertEqual(lines[at - 1].strip(), "<!-- nf-rule: EGRESS-CONFIRM -->")  # the guard's deny cites this id

    def test_the_docs_give_the_write_limit_per_batch(self) -> None:
        text = prose("docs", "concepts", "workbench.md")
        self.assertIn("50 writes and 1 MiB per batch — an upload is split into as many batches as it needs", text)
        self.assertNotIn("50 writes per upload", text)
        self.assertEqual((wb.BATCH_WRITES, wb.BATCH_BYTES < 1024 * 1024), (50, True))


class RecordTests(Home):
    def test_without_a_flowie_the_record_lives_in_user_yaml_and_other_lines_stay(self) -> None:
        self.write(self.home / ".neuroflow" / "user.yaml", "flowie_handle: alice\r\nworkbench: on\r\nhives: [example-lab/hive]\r\n")
        code, result = self.wb("record", "--set", "url=https://claude.ai/artifact/abc", "--set", "account=personal",
                               "--set", "template_version=1", "--set", "contract=0.2.87")
        self.assertEqual(result["where"], "user.yaml")
        raw = (self.home / ".neuroflow" / "user.yaml").read_bytes().decode("utf-8")
        self.assertIn("hives: [example-lab/hive]\r\n", raw)
        self.assertIn("workbench_account: personal\r\n", raw)
        self.assertEqual(wb.read_user_yaml(self.home)["workbench_records"][0]["url"], "https://claude.ai/artifact/abc")
        code, result = self.wb("record")
        self.assertEqual(result["active"]["template_version"], 1)

    def test_with_a_flowie_the_record_syncs_there_and_prefs_are_copied_once(self) -> None:
        self.make_flowie(git_repo=True)
        prefs = self.write(self.scratch / "prefs.json", json.dumps({"data": {"prefs_schema": 1, "theme": "light"}, "version": 3}))
        code, result = self.wb("record", "--set", "url=https://claude.ai/artifact/abc", "--set", "account=institute", "--prefs", str(prefs))
        self.assertEqual(result["where"], "flowie")
        self.assertTrue(result["changed"])
        self.assertEqual(result["commit"]["argv"][-1], "workbench.json")
        stored = json.loads((self.flowie / "workbench.json").read_text(encoding="utf-8"))
        self.assertEqual(stored["workbenches"][0]["prefs"], {"prefs_schema": 1, "theme": "light"})
        code, result = self.wb("record", "--prefs", str(prefs))
        self.assertFalse(result["changed"])


class UserYamlTests(Home):
    def test_reading_and_merging_keys(self) -> None:
        self.write(self.home / ".neuroflow" / "user.yaml",
                   "name: Alice Example\nworkbench_levels:\n  - flowie\n  - \"hive+example-lab+hive\"\nwiki_auto: ask  # comment\n")
        data = wb.read_user_yaml(self.home)
        self.assertEqual(data["workbench_levels"], ["flowie", "hive+example-lab+hive"])
        self.assertEqual(data["wiki_auto"], "ask")
        wb.set_user_yaml(self.home, "workbench_levels", ["flowie"])
        text = (self.home / ".neuroflow" / "user.yaml").read_text(encoding="utf-8")
        self.assertEqual(text, 'name: Alice Example\nworkbench_levels: ["flowie"]\nwiki_auto: ask  # comment\n')
        self.assertFalse(wb.set_user_yaml(self.home, "workbench_levels", ["flowie"]))


class PageTests(Home):
    def test_stage_inlines_the_logic_and_says_exactly_what_to_publish(self) -> None:
        code, result = run("stage", "--out", str(self.scratch / "page"), "--json")
        self.assertEqual(code, 0, result)
        page = Path(result["file"]).read_text(encoding="utf-8")
        self.assertNotIn(wb.LOGIC_MARK, page)
        self.assertIsNone(re.search(r"(?m)^export ", page))
        self.assertIn("function boardModel(", page)
        self.assertEqual(result["capabilities"], wb.CAPABILITIES)
        self.assertEqual((result["contract"], result["template_version"]), ("0.2.87", 1))
        self.assertEqual((result["title"], result["icon"]), ("neuroflow workbench", "board"))
        self.assertTrue(page.startswith(wb.BEGIN) and page.rstrip().endswith(wb.END))
        self.assertLess(result["bytes"], 160_000, "every publish reads the page in full: keep it small")
        # read back from claude.ai inside the publish skeleton (CRLF, trailing spaces), it hashes the same
        wrapped = "<!doctype html><html><head><meta charset=utf8></head><body>" + page.replace("\n", "  \r\n") + "</body></html>"
        self.assertEqual(wb.page_hash(wrapped), result["page_sha256"])

    def test_page_check_compares_the_live_page_with_the_record(self) -> None:
        code, staged = run("stage", "--out", str(self.scratch / "page"), "--json")
        page = Path(staged["file"])
        self.user_yaml(f'workbench: on\nworkbench_records: [{{"account": "personal", "url": "https://claude.ai/artifact/x", '
                       f'"page_sha256": "{staged["page_sha256"]}", "template_version": 1}}]\n')
        code, result = self.wb("page", "--check", str(page))
        self.assertEqual((code, result["status"], result["upgrade"]), (0, "same", False))
        edited = self.write(self.scratch / "edited.html", page.read_text(encoding="utf-8").replace("Settings</button>", "Prefs</button>"))
        code, result = self.wb("page", "--check", str(edited))
        self.assertEqual((code, result["status"]), (1, "changed"))
        code, result = self.wb("page", "--check", str(self.write(self.scratch / "other.html", "<p>no markers</p>")))
        self.assertEqual(result["status"], "unknown")

    def test_the_template_safety_rules(self) -> None:
        html = wb.TEMPLATE.read_text(encoding="utf-8")
        module = wb.MODULE.read_text(encoding="utf-8")
        self.assertEqual(wb.check_template(html, module), [])
        found = " | ".join(wb.check_template(html.replace("</style>", '</style><script src="https://cdn.example.org/x.js"></script>'),
                                             module + "\nconst a = el.innerHTML\ndocument.write('x')\nfetch('https://example.org')\n"))
        for what in ("innerHTML", "document.write", "a network call", "an external script"):
            self.assertIn(what, found)
        self.assertIn("version tag", " ".join(wb.check_template(html.replace('name="neuroflow:workbench-template"', 'name="x"'), module)))
        self.assertIn("only Google Fonts", " ".join(wb.check_template(html.replace("https://fonts.gstatic.com", "https://example.org"), module)))
        self.assertIn("dependency-free", " ".join(wb.check_template(html, "import x from 'y'\n" + module)))
        code, result = run("check", "--json")
        self.assertEqual((code, result["findings"]), (0, []))


class CliTests(unittest.TestCase):
    def test_help_and_usage_errors(self) -> None:
        out = io.StringIO()
        with contextlib.redirect_stdout(out), self.assertRaises(SystemExit) as stop:
            wb.main(["--help"])
        self.assertEqual(stop.exception.code, 0)
        self.assertIn("exit codes", out.getvalue())
        code, result = run("validate", "--json")
        self.assertEqual(code, 2)
        self.assertIn("--intents", result["error"])

    def test_the_sources_table_names_every_source_once(self) -> None:
        code, text = run("sources")
        self.assertEqual(code, 0)
        rows = [line for line in text.splitlines() if line.startswith("| ") and not line.startswith("| Source")]
        self.assertEqual(len(rows), len(wb.SOURCES))
        self.assertIn("never an email address", text)


if __name__ == "__main__":
    unittest.main()
