"""Tests for scripts/automation/repo_checks.py and validate_pr.py on fixture repos."""

from __future__ import annotations

import contextlib
import io
import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from .helpers import FILES, load, make_repo, write

rc = load("repo_checks")
validate_pr = load("validate_pr")


class RepoCase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = make_repo(Path(self._tmp.name))

    def tearDown(self):
        self._tmp.cleanup()

    def run_checks(self, *ids):
        return rc.run(self.root, only=set(ids) if ids else None)

    def text(self, *ids):
        return "\n".join(f"{f.check} {f.severity} {f.message}" for f in self.run_checks(*ids))


class BaselineTests(RepoCase):
    def test_fixture_repo_is_clean(self):
        self.assertEqual(self.run_checks(), [])

    def test_ids_are_stable_and_unique(self):
        self.assertEqual(rc.CHECK_IDS, tuple(f"V{i}" for i in range(1, 16)))

    def test_validate_pr_exit_codes(self):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            self.assertEqual(validate_pr.main(["--root", str(self.root)]), 0)
            write(self.root, {"commands/alpha.md": FILES["commands/alpha.md"].replace("lifecycle: full\n", "")})
            self.assertEqual(validate_pr.main(["--root", str(self.root), "--json"]), 1)
        data = json.loads(out.getvalue().split("\n", 1)[1])
        self.assertEqual(data["summary"]["fail"], 1)
        with contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(validate_pr.main(["--root", str(self.root), "--only", "V99"]), 2)


class VersionTests(RepoCase):
    def test_drift_is_reported_and_synced_without_reformatting(self):
        mkt = self.root / ".claude-plugin/marketplace.json"
        mkt.write_bytes(mkt.read_bytes().replace(b'"version": "1.2.3"', b'"version": "1.2.2"'))
        write(self.root, {".neuroflow/project_config.md": "**Plugin version:** 1.0.0\n"})
        found = self.run_checks("V2")
        self.assertEqual(len(found), 2)
        self.assertTrue(all(f.fix == rc.FIX_VERSION_SYNC for f in found))
        changed = rc.sync_versions(self.root)
        self.assertEqual(changed, [rc.MARKETPLACE_JSON, rc.REPO_CONFIG])
        self.assertEqual(self.run_checks("V2"), [])
        self.assertIn(b'"keywords": ["a", "b"]', mkt.read_bytes())  # formatting kept
        self.assertNotIn(b"\r\n", mkt.read_bytes())  # line endings kept

    def test_mkdocs_only_extra_version_counts(self):
        self.assertEqual(rc.site_versions(self.root, rc.MKDOCS_YML), ["1.2.3"])
        rc.set_site_version(self.root, rc.MKDOCS_YML, "2.0.0")
        text = (self.root / "mkdocs.yml").read_text(encoding="utf-8")
        self.assertIn('version: "9.9.9"', text)
        self.assertIn('version: "2.0.0"', text)

    def test_frontmatter_config_version(self):
        write(self.root, {".neuroflow/project_config.md": "---\nnf_schema: 1\nplugin_version: 1.2.3\n---\n# x\n"})
        self.assertEqual(rc.site_versions(self.root, rc.REPO_CONFIG), ["1.2.3"])
        rc.set_site_version(self.root, rc.REPO_CONFIG, "1.2.4")
        self.assertIn("plugin_version: 1.2.4", (self.root / rc.REPO_CONFIG).read_text(encoding="utf-8"))

    def test_substantive_changes_share_one_exempt_list(self):
        paths = ["README.md", ".github/workflows/x.yml", "tests/automation/t.py", "skills/x/SKILL.md", "docs/index.md"]
        self.assertEqual(rc.substantive_changes(paths), ["skills/x/SKILL.md", "docs/index.md"])


class CommandFrontmatterTests(RepoCase):
    def set_command(self, old, new):
        write(self.root, {"commands/alpha.md": FILES["commands/alpha.md"].replace(old, new)})

    def test_lifecycle_required_and_enum(self):
        self.set_command("lifecycle: full\n", "")
        self.assertIn("missing `lifecycle:`", self.text("V3"))
        self.set_command("lifecycle: full", "lifecycle: sometimes")
        self.assertIn("must be one of full, light, quiet", self.text("V3"))

    def test_next_and_lists(self):
        self.set_command("next:\n  - alpha", "next:\n  - ghost\n  - /alpha")
        text = self.text("V3")
        self.assertIn("names `ghost`, which is not a command", text)
        self.assertIn("use bare command names", text)
        self.set_command("requires:\n  - .neuroflow/alpha/plan.md", "requires: .neuroflow/alpha/plan.md")
        self.assertIn("`requires:` must be a list", self.text("V3"))

    def test_phase_must_be_canonical(self):
        self.set_command("phase: alpha", "phase: beta")
        self.assertIn("not in the canonical taxonomy", self.text("V3"))


class NamesAndHooksTests(RepoCase):
    def test_skill_flags_must_be_boolean(self):
        write(self.root, {"skills/phase-alpha/SKILL.md": "---\nname: phase-alpha\nuser-invocable: maybe\n---\n"})
        self.assertIn("must be true or false", self.text("V5"))

    def test_agent_name_mismatch(self):
        write(self.root, {"agents/helper.md": "---\nname: aide\n---\n"})
        self.assertIn("!= filename `helper`", self.text("V5"))

    def test_hook_must_fail_silently(self):
        data = json.loads(FILES["hooks/hooks.json"])
        data["hooks"]["PostToolUse"][0]["hooks"][0]["command"] = "ruff format x 2>/dev/null"
        write(self.root, {"hooks/hooks.json": json.dumps(data)})
        self.assertIn("does not end with `; true`", self.text("V6"))

    def test_modules_key(self):
        data = json.loads(FILES["hooks/hooks.json"])
        data["modules"] = ["./mod/neuroflow.ts"]
        write(self.root, {"hooks/hooks.json": json.dumps(data)})
        self.assertIn("does not resolve to a file", self.text("V6"))
        write(self.root, {"hooks/mod/neuroflow.ts": "export const register = () => {}\n"})
        self.assertEqual(self.run_checks("V6"), [])
        data["modules"] = ["./mod/neuroflow.ts", "./mod/other.ts"]
        write(self.root, {"hooks/hooks.json": json.dumps(data)})
        self.assertIn("exactly one module path", self.text("V6"))


class RuleMarkerTests(RepoCase):
    def test_guard_needs_a_marker(self):
        write(self.root, {"hooks/mod/features/guards.ts": "// nf-rule: PREREG-FROZEN\nexport const g = 1\n"})
        self.assertEqual(self.run_checks("V8"), [])
        write(self.root, {"hooks/mod/features/raw.ts": "const reason = 'denied (nf-rule: RAW-READONLY)'\n"})
        self.assertIn("cites unknown rule id `RAW-READONLY`", self.text("V8"))

    def test_marker_ids_must_be_known(self):
        write(self.root, {"commands/alpha.md": FILES["commands/alpha.md"] + "\n<!-- nf-rule: MADE-UP -->\nA rule.\n"})
        self.assertIn("unknown rule id `MADE-UP`", self.text("V8"))

    def test_examples_and_tests_are_not_markers_or_guards(self):
        write(self.root, {
            "skills/phase-alpha/SKILL.md": FILES["skills/phase-alpha/SKILL.md"] + "\n```\n<!-- nf-rule: NOPE-NOPE -->\n```\n",
            "hooks/mod/tests/guards.test.ts": "// nf-rule: FAKE-RULE\n",
            "hooks/mod/neuroflow.ts": "// every guard states an <!-- nf-rule: ID --> marker\n",
        })
        self.assertEqual(self.run_checks("V8"), [])

    def test_unmarked_rule_is_a_warning(self):
        write(self.root, {"skills/phase-alpha/SKILL.md": "---\nname: phase-alpha\n---\nNo markers here.\n"})
        found = self.run_checks("V8")
        self.assertEqual([(f.severity, "PREREG-FROZEN" in f.message) for f in found], [(rc.WARN, True)])


class CollisionAndPropagationTests(RepoCase):
    def test_skill_shadowed_by_command(self):
        write(self.root, {"skills/alpha/SKILL.md": "---\nname: alpha\n---\n"})
        found = self.run_checks("V9")
        self.assertEqual(found[0].severity, rc.FAIL)
        self.assertIn("the command shadows the skill", found[0].message)

    def test_new_command_needs_every_site(self):
        write(self.root, {"commands/beta.md": FILES["commands/alpha.md"].replace("name: alpha", "name: beta"),
                          "docs/commands/beta.md": "# beta\n"})
        text = self.text("V10")
        self.assertIn("commands/beta.md has no link in README.md", text)
        self.assertIn("commands/beta.md is not in the mkdocs.yml nav", text)

    def test_dead_links(self):
        write(self.root, {"README.md": FILES["README.md"] + "| [`gone`](agents/gone.md) | x |\n",
                          "mkdocs.yml": FILES["mkdocs.yml"] + "  - Old: old-page.md\n"})
        text = self.text("V10")
        self.assertIn("links to non-existent file `agents/gone.md`", text)
        self.assertIn("non-existent file `old-page.md`", text)
        self.assertNotIn("removed-long-ago", text)  # the What's new history is not checked

    def test_a_page_listed_twice_in_the_nav(self):
        self.assertNotIn("times - the sidebar repeats", self.text("V10"))
        write(self.root, {"mkdocs.yml": FILES["mkdocs.yml"] + "  - Again: commands/alpha.md\n"})
        self.assertIn("mkdocs.yml nav lists `commands/alpha.md` 2 times", self.text("V10"))

    def test_dead_skill_reference(self):
        write(self.root, {"skills/phase-alpha/SKILL.md": FILES["skills/phase-alpha/SKILL.md"] + "Read neuroflow:ghost.\n"})
        self.assertIn("`neuroflow:ghost`", self.text("V11"))


class HygieneTests(RepoCase):
    def test_release_notes_are_warnings(self):
        write(self.root, {"docs/changelog.md": "# Changelog\n\n## 1.2.2\n\n- x\n"})
        found = self.run_checks("V12")
        self.assertEqual([f.severity for f in found], [rc.WARN])

    def test_private_key_material_not_mentions(self):
        write(self.root, {"skills/phase-alpha/scan.py": 'PEM = r"-----BEGIN (?:RSA )*PRIVATE KEY-----"\n'})
        self.assertEqual(self.run_checks("V14"), [])
        write(self.root, {"scripts/key.md": "-----BEGIN RSA PRIVATE KEY-----\n" + "A" * 64 + "\n-----END RSA PRIVATE KEY-----\n"})
        self.assertEqual([f.severity for f in self.run_checks("V14")], [rc.FAIL])

    def test_stale_paths(self):
        write(self.root, {"commands/alpha.md": FILES["commands/alpha.md"] + "Save it to .neuroflow/flowie/profile.md\n"
                                                                            "Ignored: .neuroflow/flowie/\n"})
        found = self.run_checks("V15")
        self.assertEqual(len(found), 1)
        self.assertIn("project-level `.neuroflow/flowie/`", found[0].message)

    def test_repo_memory_folders(self):
        write(self.root, {".neuroflow/phase-alpha/x.md": "x"})
        self.assertIn("matches a skill name", self.text("V13"))


@unittest.skipUnless(shutil.which("git"), "git not installed")
class VersionBumpGitTests(RepoCase):
    def git(self, *args):
        subprocess.run(["git", *args], cwd=self.root, check=True, capture_output=True)

    def test_substantive_change_without_bump(self):
        self.git("init", "-q", "-b", "main")
        self.git("-c", "user.name=t", "-c", "user.email=t@example.com", "add", "-A")
        self.git("-c", "user.name=t", "-c", "user.email=t@example.com", "commit", "-q", "-m", "base")
        self.git("checkout", "-q", "-b", "feature")
        write(self.root, {"skills/phase-alpha/SKILL.md": FILES["skills/phase-alpha/SKILL.md"] + "More.\n"})
        self.git("-c", "user.name=t", "-c", "user.email=t@example.com", "commit", "-qam", "change")
        found = rc.run(self.root, base="main", only={"V7"})
        self.assertEqual(len(found), 1)
        self.assertIn("bump the patch version", found[0].message)
        rc.sync_versions(self.root, "1.2.4")
        self.assertEqual(rc.run(self.root, base="main", only={"V7"}), [])


if __name__ == "__main__":
    unittest.main()
