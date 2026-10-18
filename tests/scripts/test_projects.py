"""Tests for skills/neuroflow-core/scripts/projects.py (one project across the flowie, hives and repositories)."""
import importlib.util
import io
import json
import os
import shutil
import subprocess
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest import mock

SCRIPT = Path(__file__).resolve().parents[2] / "skills" / "neuroflow-core" / "scripts" / "projects.py"
spec = importlib.util.spec_from_file_location("projects", SCRIPT)
pj = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pj)

GIT_ENV = {"GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@example.com", "GIT_COMMITTER_NAME": "t",
           "GIT_COMMITTER_EMAIL": "t@example.com"}


def run(*args: str) -> tuple[int, str, str]:
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        code = pj.main(list(args))
    return code, out.getvalue(), err.getvalue()


def task(title: str, project: str, **keys: str) -> str:
    lines = ["---", f"title: {title}", f"project: {project}", *[f"{key}: {value}" for key, value in keys.items()], "---", ""]
    return "\n".join(lines)


class RegistryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.home = Path(tempfile.mkdtemp())
        self.addCleanup(lambda: pj.remove_tree(self.home) if self.home.exists() else None)
        self.flowie = self.home / ".neuroflow" / "flowie"
        self.hive = self.home / ".neuroflow" / "hives" / "example-lab-hive"
        self.write(self.hive / ".git" / "config", '[remote "origin"]\n\turl = https://github.com/example-lab/hive.git\n')
        self.write(self.hive / ".git" / "HEAD", "ref: refs/heads/main\n")

    def write(self, path: Path, text: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    def registry(self, root: Path, *entries: dict) -> None:
        self.write(root / "projects" / "projects.json", json.dumps({"projects": list(entries)}, indent=2) + "\n")

    def h(self, *args: str) -> tuple[int, str, str]:
        return run(*args, "--home", str(self.home))

    def test_two_cards_pointers_and_dangling_references_are_found(self) -> None:
        self.registry(self.flowie,
                      {"id": "Oddball", "description": "P300", "status": "paused", "current_phase": "data"},
                      {"id": "Alpha", "ref": "hive:example-lab/hive", "status": "active"},
                      {"id": "Gone", "ref": "hive:example-lab/other"})
        self.registry(self.hive,
                      {"id": "Oddball", "description": "P300", "status": "active", "current_phase": "data"},
                      {"id": "Alpha", "description": "alpha", "status": "active"})
        self.write(self.flowie / "tasks" / "inbox" / "write-intro.md", task("Write intro", "Oddball", blocked_by="[get-data]"))
        self.write(self.flowie / "tasks" / "inbox" / "coffee.md", task("Coffee", "personal"))
        self.write(self.flowie / "tasks" / "active" / "x.md", task("X", "Unknown"))
        code, out, _ = self.h("check", "--json")
        self.assertEqual(code, 1)
        kinds = sorted((f["kind"], f.get("project", "")) for f in json.loads(out)["findings"])
        self.assertEqual(kinds, [("blocked-by", ""), ("pointer-copies", "Alpha"), ("pointer-target", "Gone"),
                                 ("two-cards", "Oddball"), ("unknown-project", "")])
        two = next(f for f in json.loads(out)["findings"] if f["kind"] == "two-cards")
        self.assertEqual(two["differ"], ["status"])

    def test_a_clean_registry_has_no_findings(self) -> None:
        self.registry(self.flowie, {"id": "Alpha", "ref": "hive:example-lab/hive"}, {"id": "Solo", "status": "active"})
        self.registry(self.hive, {"id": "Alpha", "description": "alpha", "status": "active"})
        self.write(self.flowie / "tasks" / "ready" / "a.md", task("A", "Solo"))
        self.write(self.flowie / "tasks" / "ready" / "b.md", task("B", "Solo", blocked_by="[a]"))
        self.assertEqual(self.h("check")[0], 0)
        code, out, _ = self.h("list", "--json")
        rows = json.loads(out)["projects"]
        self.assertIn({"project": "Alpha", "where": "flowie", "kind": "pointer", "ref": "hive:example-lab/hive"}, rows)
        self.assertIn({"project": "Alpha", "where": "hive example-lab/hive", "kind": "card"}, rows)

    def test_fold_turns_the_flowie_copy_into_a_pointer_and_keeps_personal_notes(self) -> None:
        self.registry(self.flowie, {"id": "Oddball", "description": "new scope", "status": "paused"}, {"id": "Solo"})
        self.write(self.flowie / "projects" / "Oddball.md", "# Oddball\n\n## Phase timeline\n\n| x |\n\n## Notes\n\nMy own note.\n")
        self.registry(self.hive, {"id": "Oddball", "description": "old scope", "status": "active", "current_phase": "data"})
        code, out, _ = self.h("fold", "--json")
        self.assertEqual(code, 1)
        plan = json.loads(out)["plan"]
        self.assertEqual([(c["field"], c["keep"]) for c in plan[0]["differ"]], [("description", "hive"), ("status", "hive")])
        self.assertIn("new scope", (self.flowie / "projects" / "projects.json").read_text(encoding="utf-8"), "a dry run writes nothing")
        code, out, _ = self.h("fold", "--apply", "--keep", "Oddball.description=flowie", "--json")
        result = json.loads(out)
        self.assertTrue(result["applied"])
        self.assertEqual(sorted(result["changed"]["flowie"]), ["projects/Oddball.md", "projects/projects.json"])
        self.assertEqual(result["changed"]["example-lab-hive"], ["projects/projects.json"])
        flowie = json.loads((self.flowie / "projects" / "projects.json").read_text(encoding="utf-8"))["projects"]
        self.assertEqual(flowie, [{"id": "Oddball", "ref": "hive:example-lab/hive"}, {"id": "Solo"}])
        hive = json.loads((self.hive / "projects" / "projects.json").read_text(encoding="utf-8"))["projects"][0]
        self.assertEqual((hive["description"], hive["status"]), ("new scope", "active"))
        note = (self.flowie / "projects" / "Oddball.md").read_text(encoding="utf-8")
        self.assertIn("Card: hive example-lab/hive", note)
        self.assertIn("My own note.", note)
        self.assertNotIn("Phase timeline", note)
        self.assertEqual(self.h("fold")[0], 0, "nothing left to fold")
        self.assertEqual(self.h("check")[0], 0)

    def test_fold_never_writes_into_a_copied_hive(self) -> None:
        (self.hive / ".git" / "HEAD").unlink()
        self.registry(self.flowie, {"id": "Oddball", "status": "paused"})
        self.registry(self.hive, {"id": "Oddball", "status": "active"})
        code, out, _ = self.h("fold", "--apply", "--json")
        result = json.loads(out)
        self.assertIn("not a git clone", result["plan"][0]["blocked"])
        self.assertEqual(result["changed"], {"flowie": []})
        self.assertIn("paused", (self.flowie / "projects" / "projects.json").read_text(encoding="utf-8"))

    def test_usage_errors(self) -> None:
        self.assertEqual(self.h("view")[0], 2)
        self.assertEqual(self.h("fold", "--keep", "Oddball.colour=flowie")[0], 2)

    def test_repo_keys(self) -> None:
        for url in ("https://github.com/Example-Lab/Oddball.git", "git@github.com:example-lab/oddball.git",
                    "github.com/example-lab/oddball", "ssh://git@github.com/example-lab/oddball/"):
            self.assertEqual(pj.repo_key(url), "github.com/example-lab/oddball")
        self.assertIsNone(pj.repo_key("C:/Users/alice/oddball"))
        self.assertIsNone(pj.repo_key("oddball"))


@unittest.skipUnless(shutil.which("git"), "needs git")
class ViewTests(RegistryTests):
    def git(self, cwd: Path, *args: str) -> None:
        subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, env=dict(os.environ, **GIT_ENV))

    def remote_board(self) -> Path:
        """A bare repository standing in for https://example.org/lab/oddball, with two tasks on its board."""
        work = self.home / "work"
        self.write(work / ".neuroflow" / "project_config.md", "---\nnf_schema: 1\n---\n")
        self.write(work / ".neuroflow" / "tasks" / "active" / "rerun-ica.md", task("Rerun ICA", "Oddball", owner="li"))
        self.write(work / ".neuroflow" / "tasks" / "done" / "old.md", task("Old", "Oddball"))
        self.write(work / "analysis.py", "print(1)\n")
        self.git(work, "init", "-q", "-b", "main")
        self.git(work, "add", "-A")
        self.git(work, "commit", "-q", "-m", "init")
        bare = self.home / "remote.git"
        self.git(self.home, "clone", "-q", "--bare", str(work), str(bare))
        return bare

    def test_view_reads_every_level_and_the_boards_of_the_cards_repositories(self) -> None:
        bare = self.remote_board()
        self.registry(self.flowie, {"id": "Oddball", "ref": "hive:example-lab/hive"})
        self.registry(self.hive, {"id": "Oddball", "status": "active", "current_phase": "data",
                                  "repos": [{"url": "https://example.org/lab/oddball"}]})
        self.write(self.flowie / "tasks" / "inbox" / "read.md", task("Read the review", "Oddball"))
        self.write(self.flowie / "tasks" / "inbox" / "other.md", task("Other", "Solo"))
        self.write(self.hive / "tasks" / "meeting" / "figures.md", task("Figure plan", "Oddball", owner="jana"))
        rewrite = {"GIT_CONFIG_COUNT": "1", "GIT_CONFIG_KEY_0": f"url.{bare.as_uri()}.insteadOf",
                   "GIT_CONFIG_VALUE_0": "https://example.org/lab/oddball"}
        with mock.patch.dict(os.environ, rewrite):
            code, out, _ = self.h("view", "--project", "Oddball", "--root", str(self.home), "--json")
        self.assertEqual(code, 0, out)
        result = json.loads(out)
        self.assertEqual(result["card"]["where"], "hive example-lab/hive")
        open_by_level = {level["name"]: [t["title"] for t in level["tasks"] if t["open"]] for level in result["levels"]}
        self.assertEqual(open_by_level, {"flowie": ["Read the review"], "hive example-lab/hive": ["Figure plan"],
                                         "example.org/lab/oddball": ["Rerun ICA"]})
        cache = self.home / ".neuroflow" / "boards" / "example.org" / "lab" / "oddball"
        self.assertTrue((cache / ".neuroflow" / "tasks" / "active" / "rerun-ica.md").is_file())
        self.assertFalse((cache / "analysis.py").exists(), "only the task board is checked out")
        # Offline: the cache is read as it is, with the time it was fetched.
        code, out, _ = self.h("view", "--project", "Oddball", "--root", str(self.home), "--no-remote", "--json")
        remote = next(level for level in json.loads(out)["levels"] if level["source"] == "remote")
        self.assertTrue(remote["fetched"])
        self.assertEqual([t["title"] for t in remote["tasks"] if t["open"]], ["Rerun ICA"])
        # A repository that cannot be reached is named, never fatal.
        self.registry(self.hive, {"id": "Oddball", "repos": ["https://example.invalid/lab/none"]})
        code, out, _ = self.h("view", "--project", "Oddball", "--root", str(self.home), "--json")
        self.assertEqual(code, 1)
        self.assertTrue(json.loads(out)["levels"][-1]["error"])

    def test_this_repositorys_board_when_it_is_the_project(self) -> None:
        repo = self.home / "code" / "oddball"
        self.write(repo / ".neuroflow" / "project_config.md", "---\nnf_schema: 1\n---\n")
        self.write(repo / ".neuroflow" / "tasks" / "inbox" / "fix-montage.md", task("Fix montage", "Oddball"))
        self.write(self.home / ".neuroflow" / "local-projects.json",
                   json.dumps({"projects": [{"name": "Oddball", "path": repo.as_posix()}]}))
        self.registry(self.flowie, {"id": "Oddball", "status": "active"})
        code, out, _ = self.h("view", "--project", "Oddball", "--root", str(repo / ".neuroflow"), "--json")
        levels = json.loads(out)["levels"]
        self.assertEqual([level["name"] for level in levels], ["flowie", "this repository"])
        self.assertEqual(levels[1]["tasks"][0]["title"], "Fix montage")


class SafetyAndShapesTests(RegistryTests):
    def test_repository_urls_that_could_leave_the_cache_are_refused(self) -> None:
        for url in ("https://nohost.invalid/../../../victim", "https://nohost.invalid/../../flowie", "-oProxyCommand=x",
                    "https://github.com/org", "https://github.com/a/b/c", "file:///C:/repo", "C:/Users/alice/repo",
                    "https://github.com/org/re po", "https://c:/x/y"):
            self.assertIsNone(pj.parse_repo(url), url)
        self.assertEqual(pj.parse_repo("git@github.com:Example-Lab/Oddball.git"),
                         ("github.com/example-lab/oddball", "git@github.com:Example-Lab/Oddball.git"))
        self.assertEqual(pj.parse_repo("github.com/example-lab/oddball")[1], "https://github.com/example-lab/oddball")
        with self.assertRaises(pj.UsageError):
            pj.cache_dir(self.home, "nohost.invalid/../victim")
        inside = pj.cache_dir(self.home, "github.com/example-lab/oddball")
        self.assertIn(self.home.resolve() / ".neuroflow" / "boards", inside.resolve().parents)

    def test_a_folder_the_script_did_not_make_is_never_replaced(self) -> None:
        target = pj.cache_dir(self.home, "example.org/lab/oddball")
        self.write(target / "precious.txt", "keep me\n")
        ok, reason = pj.refresh_cache(self.home, "https://example.org/lab/oddball", "example.org/lab/oddball")
        self.assertFalse(ok)
        self.assertIn("left alone", reason)
        self.assertEqual((target / "precious.txt").read_text(encoding="utf-8"), "keep me\n")

    def test_older_registry_shapes(self) -> None:
        self.write(self.flowie / "projects" / "projects.json", "\ufeff" + json.dumps([{"name": "Solo", "status": "active"}]))
        self.write(self.hive / "projects" / "projects.json", json.dumps({"projects": None}))
        code, out, _ = self.h("list", "--json")
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(out)["projects"], [{"project": "Solo", "where": "flowie", "kind": "card"}])
        self.assertEqual(self.h("check")[0], 0)
        self.write(self.hive / "projects" / "projects.json", "{not json")
        code, out, _ = self.h("check", "--json")
        self.assertEqual([f["kind"] for f in json.loads(out)["findings"]], ["registry"])

    def test_a_local_folder_in_a_cards_repos_is_reported(self) -> None:
        self.registry(self.flowie, {"id": "Solo", "repos": ["C:/Users/alice/solo", "https://github.com/example-lab/solo"]})
        code, out, _ = self.h("check", "--json")
        self.assertEqual([f["kind"] for f in json.loads(out)["findings"]], ["local-repo"])

    def test_fold_loses_nothing(self) -> None:
        self.registry(self.flowie, {"id": "Oddball", "status": "paused", "tags": ["eeg"], "deadline": "2026-12-01",
                                    "repos": ["https://github.com/example-lab/oddball-analysis"],
                                    "visited_phases": [{"phase": "data", "entered": "2026-09-01"}]})
        note = ("# Oddball\r\n\r\nP300 study\r\n\r\n## Repos\r\n\r\n| url |\r\n|---|\r\n| https://github.com/example-lab/oddball-analysis |\r\n\r\n"
                "## Linked repos\r\n\r\n- https://github.com/example-lab/oddball-eeg\r\n\r\n## Phase timeline\r\n\r\n| data | 2026-09-01 |\r\n\r\n"
                "## Reading list\r\n\r\n- the N2pc review\r\n")
        (self.flowie / "projects").mkdir(parents=True, exist_ok=True)
        (self.flowie / "projects" / "Oddball.md").write_bytes(note.encode("utf-8"))
        self.registry(self.hive, {"id": "Oddball", "status": "active", "description": "P300 study",
                                  "repos": [{"url": "https://github.com/example-lab/oddball-eeg"}]})
        code, out, _ = self.h("fold", "--json")
        plan = json.loads(out)["plan"][0]
        self.assertEqual({c["field"]: c["keep"] for c in plan["differ"]},
                         {"repos": "both", "visited_phases": "flowie", "status": "hive"})
        self.assertEqual(plan["extra"], {"tags": ["eeg"], "deadline": "2026-12-01"})
        code, out, _ = self.h("fold", "--apply", "--json")
        hive = json.loads((self.hive / "projects" / "projects.json").read_text(encoding="utf-8"))["projects"][0]
        self.assertEqual(hive["status"], "active")
        self.assertEqual(sorted(str(r) for r in hive["repos"]),
                         sorted(["https://github.com/example-lab/oddball-analysis", "https://github.com/example-lab/oddball-eeg",
                                 str({"url": "https://github.com/example-lab/oddball-eeg"})]))
        self.assertEqual(hive["visited_phases"], [{"phase": "data", "entered": "2026-09-01"}])
        pointer = json.loads((self.flowie / "projects" / "projects.json").read_text(encoding="utf-8"))["projects"][0]
        self.assertEqual(pointer, {"id": "Oddball", "ref": "hive:example-lab/hive", "tags": ["eeg"], "deadline": "2026-12-01"})
        kept = (self.flowie / "projects" / "Oddball.md").read_bytes().decode("utf-8")
        self.assertIn("\r\n", kept, "the note keeps its line endings")
        self.assertIn("## Reading list", kept)
        self.assertIn("the N2pc review", kept)
        self.assertNotIn("## Phase timeline", kept)

    def test_fold_filters(self) -> None:
        self.registry(self.flowie, {"id": "A", "status": "paused"}, {"id": "B"})
        self.registry(self.hive, {"id": "A"}, {"id": "B", "status": "active"})
        code, out, _ = self.h("fold", "--no-hive", "--json")
        plan = {item["project"]: item for item in json.loads(out)["plan"]}
        self.assertIn("would change", plan["A"]["blocked"], "A's status exists only in the flowie: the hive card changes")
        self.assertNotIn("blocked", plan["B"])
        code, out, _ = self.h("fold", "--project", "B", "--json")
        self.assertEqual([item["project"] for item in json.loads(out)["plan"]], ["B"])
        code, out, _ = self.h("fold", "--hive", "other-hive", "--json")
        self.assertTrue(all("not part of this run" in item["blocked"] for item in json.loads(out)["plan"]))
        code, out, _ = self.h("fold", "--no-hive", "--apply", "--json")
        flowie = json.loads((self.flowie / "projects" / "projects.json").read_text(encoding="utf-8"))["projects"]
        self.assertEqual(flowie, [{"id": "A", "status": "paused"}, {"id": "B", "ref": "hive:example-lab/hive"}])

    def test_a_project_with_cards_in_two_hives_is_not_folded(self) -> None:
        other = self.home / ".neuroflow" / "hives" / "other-hive"
        self.write(other / ".git" / "HEAD", "ref: refs/heads/main\n")
        self.registry(self.flowie, {"id": "A"})
        self.registry(self.hive, {"id": "A"})
        self.registry(other, {"id": "A"})
        self.assertEqual(json.loads(self.h("fold", "--json")[1])["plan"], [])
        two = [f for f in json.loads(self.h("check", "--json")[1])["findings"] if f["kind"] == "two-cards"]
        self.assertIn("keep one", two[0]["message"])

    def test_an_unforeseen_shape_is_an_error_not_a_finding(self) -> None:
        self.registry(self.flowie, {"id": "A", "repos": 5})
        self.assertEqual(self.h("check")[0], 0, "a repos value that is no text is no repository")
        with mock.patch.object(pj, "check", side_effect=TypeError("a shape nobody foresaw")):
            code, _, err = self.h("check")
        self.assertEqual(code, 2)
        self.assertIn("TypeError", err)


@unittest.skipUnless(shutil.which("git"), "needs git")
class DirtyFoldTests(RegistryTests):
    def test_uncommitted_registry_changes_block_the_fold(self) -> None:
        self.registry(self.flowie, {"id": "A", "status": "paused"})
        self.registry(self.hive, {"id": "A", "status": "active"})
        env = dict(os.environ, **GIT_ENV)
        for args in (["init", "-q", "-b", "main"], ["add", "-A"], ["commit", "-q", "-m", "init"]):
            subprocess.run(["git", *args], cwd=self.flowie, check=True, capture_output=True, env=env)
        self.registry(self.flowie, {"id": "A", "status": "paused", "description": "edited, not committed"})
        plan = json.loads(self.h("fold", "--apply", "--json")[1])["plan"]
        self.assertIn("uncommitted changes", plan[0]["blocked"])
        self.assertIn("edited, not committed", (self.flowie / "projects" / "projects.json").read_text(encoding="utf-8"))

    def test_refresh_skips_this_repository_and_rebuilds_a_broken_cache(self) -> None:
        view = ViewTests(methodName="test_view_reads_every_level_and_the_boards_of_the_cards_repositories")
        view.home, view.flowie, view.hive = self.home, self.flowie, self.hive
        bare = view.remote_board()
        self.registry(self.hive, {"id": "Oddball", "repos": ["https://example.org/lab/oddball", "https://example.org/lab/here"]})
        here = self.home / "here"
        self.write(here / ".neuroflow" / "project_config.md", "---\n---\n")
        self.write(here / ".git" / "config", '[remote "origin"]\n\turl = https://example.org/lab/here\n')
        rewrite = {"GIT_CONFIG_COUNT": "1", "GIT_CONFIG_KEY_0": f"url.{bare.as_uri()}.insteadOf",
                   "GIT_CONFIG_VALUE_0": "https://example.org/lab/oddball"}
        with mock.patch.dict(os.environ, rewrite):
            code, out, _ = self.h("refresh", "--project", "Oddball", "--root", str(here), "--json")
            self.assertEqual((code, [r["repo"] for r in json.loads(out)["repos"]]), (0, ["example.org/lab/oddball"]))
            cache = pj.cache_dir(self.home, "example.org/lab/oddball")
            pj.remove_tree(cache / ".git")  # an interrupted or broken cache of ours
            code, out, _ = self.h("refresh", "--project", "Oddball", "--root", str(here), "--json")
        self.assertEqual(code, 0, out)
        self.assertTrue((cache / ".neuroflow" / "tasks" / "active" / "rerun-ica.md").is_file())

class ThirdReviewTests(RegistryTests):
    def test_fold_with_a_repos_string_and_a_name_key(self) -> None:
        self.registry(self.flowie, {"name": "Oddball", "repos": "https://github.com/example-lab/oddball-analysis", "tags": ["eeg"]})
        self.registry(self.hive, {"id": "Oddball", "repos": ["https://github.com/example-lab/oddball-eeg"]})
        self.h("fold", "--apply", "--json")
        hive = json.loads((self.hive / "projects" / "projects.json").read_text(encoding="utf-8"))["projects"][0]
        self.assertEqual(hive["repos"], ["https://github.com/example-lab/oddball-eeg", "https://github.com/example-lab/oddball-analysis"])
        pointer = json.loads((self.flowie / "projects" / "projects.json").read_text(encoding="utf-8"))["projects"][0]
        self.assertEqual(pointer, {"id": "Oddball", "ref": "hive:example-lab/hive", "name": "Oddball", "tags": ["eeg"]})

    @unittest.skipUnless(shutil.which("git"), "needs git")
    def test_a_clone_cut_off_half_way_is_cleaned_up_by_the_next_refresh(self) -> None:
        target = pj.cache_dir(self.home, "example.invalid/lab/oddball")
        partial = target.with_name(target.name + ".neuroflow-partial")
        self.write(partial / "leftover.txt", "a killed clone\n")
        ok, reason = pj.refresh_cache(self.home, "https://example.invalid/lab/oddball", "example.invalid/lab/oddball")
        self.assertFalse(ok)
        self.assertFalse(partial.exists(), "the half-made clone of an earlier run is removed")
        self.assertFalse(target.exists())

class FinalReviewTests(RegistryTests):
    def test_fold_never_puts_a_local_folder_on_the_team_card(self) -> None:
        self.registry(self.flowie, {"id": "Oddball", "repos": ["https://github.com/example-lab/oddball", "C:/Users/alice/projects/oddball"]})
        self.registry(self.hive, {"id": "Oddball", "repos": ["https://github.com/example-lab/oddball"]})
        plan = json.loads(self.h("fold", "--json")[1])["plan"][0]
        self.assertEqual(plan["local_repos"], ["C:/Users/alice/projects/oddball"])
        self.assertEqual(plan["differ"], [], "the remote URL is already on the card")
        self.h("fold", "--apply", "--json")
        hive = json.loads((self.hive / "projects" / "projects.json").read_text(encoding="utf-8"))["projects"][0]
        self.assertEqual(hive["repos"], ["https://github.com/example-lab/oddball"])
        self.assertEqual([f["kind"] for f in json.loads(self.h("check", "--json")[1])["findings"]], [])

    def test_a_repos_string_is_one_repository_everywhere(self) -> None:
        self.registry(self.flowie, {"id": "Solo", "repos": "https://github.com/example-lab/solo"})
        self.assertEqual(self.h("check")[0], 0)
        self.assertEqual(pj.card_repos({"repos": "https://github.com/example-lab/solo"}), ["https://github.com/example-lab/solo"])

    def test_a_task_may_name_a_card_of_another_level(self) -> None:
        self.registry(self.flowie, {"id": "Solo"})
        self.registry(self.hive, {"id": "Team"})
        self.write(self.flowie / "tasks" / "inbox" / "a.md", task("A", "Team"))
        self.assertEqual(self.h("check")[0], 0)

    def test_a_key_part_never_ends_in_a_dot(self) -> None:
        self.assertIsNone(pj.parse_repo("https://github.com/example-lab/oddball."))
        self.assertEqual(pj.repo_key("https://github.com/example-lab/odd.ball"), "github.com/example-lab/odd.ball")


if __name__ == "__main__":
    unittest.main()
