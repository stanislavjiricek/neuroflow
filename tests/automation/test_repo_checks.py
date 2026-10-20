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
        readme = FILES["README.md"].replace("- [Alpha](commands/alpha.md) got better",
                                            "- [old thing](agents/removed-long-ago.md)")
        write(self.root, {"README.md": readme + "| [`gone`](agents/gone.md) | x |\n",
                          "mkdocs.yml": FILES["mkdocs.yml"] + "  - Old: old-page.md\n"})
        text = self.text("V10")
        self.assertIn("links to non-existent file `agents/gone.md`", text)
        self.assertIn("non-existent file `old-page.md`", text)
        self.assertIn("links to non-existent file `agents/removed-long-ago.md`", text)  # What's new is checked too

    def test_a_page_listed_twice_in_the_nav(self):
        self.assertNotIn("times - the sidebar repeats", self.text("V10"))
        write(self.root, {"mkdocs.yml": FILES["mkdocs.yml"] + "  - Again: commands/alpha.md\n"})
        self.assertIn("mkdocs.yml nav lists `commands/alpha.md` 2 times", self.text("V10"))

    def test_dead_skill_reference(self):
        write(self.root, {"skills/phase-alpha/SKILL.md": FILES["skills/phase-alpha/SKILL.md"] + "Read neuroflow:ghost.\n"})
        self.assertIn("`neuroflow:ghost`", self.text("V11"))


class ReadmeLinkTests(RepoCase):
    """V10 reads the whole README: Markdown links and images, HTML src/href/srcset, in-page anchors."""

    def readme(self, old="", new="", extra=""):
        write(self.root, {"README.md": FILES["README.md"].replace(old, new) + extra})
        return self.run_checks("V10")

    def test_dead_image_src_fails(self):
        found = self.readme('src="docs/assets/logo.svg"', 'src="docs/assets/gone.svg"')
        self.assertEqual([(f.severity, f.message) for f in found],
                         [(rc.FAIL, "README.md links to non-existent file `docs/assets/gone.svg`")])

    def test_dead_srcset_candidate_fails(self):
        found = self.readme('srcset="docs/assets/logo-dark.svg"',
                            'srcset="docs/assets/logo-dark.svg 1x, docs/assets/logo-dark@2x.svg 2x"')
        self.assertEqual([f.message for f in found], ["README.md links to non-existent file `docs/assets/logo-dark@2x.svg`"])
        self.assertEqual(found[0].severity, rc.FAIL)

    def test_dead_markdown_image_fails(self):
        found = self.readme(extra="\n![diagram](docs/assets/diagram.png)\n")
        self.assertIn("non-existent file `docs/assets/diagram.png`", found[0].message)

    def test_dead_anchor_warns(self):
        found = self.readme(extra='\n<a href="#nowhere">x</a> and [y](#whats-new-in-999)\n')
        self.assertEqual(sorted((f.severity, f.message) for f in found), [
            (rc.WARN, "README.md links to `#nowhere`, which no heading or id in it defines"),
            (rc.WARN, "README.md links to `#whats-new-in-999`, which no heading or id in it defines"),
        ])

    def test_anchors_from_ids_and_heading_slugs(self):
        self.assertEqual(self.run_checks("V10"), [])  # #whats-new is an id, #installation a heading
        found = self.readme(extra="\n## Notes\n\n## Notes\n\n[a](#whats-new-in-123) [b](#notes) [c](#notes-1) "
                                  "[d](#user-content-whats-new) [e](#notes-2)\n")
        self.assertEqual([f.message for f in found], ["README.md links to `#notes-2`, which no heading or id in it defines"])

    def test_code_and_comments_are_not_links(self):
        extra = ("\n```html\n<img src=\"gone.png\">\n[x](gone.md)\n```\n\n"
                 "Inline `[y](gone2.md)` and ``<a href=\"gone3.md\">``.\n\n<!-- [z](gone4.md) -->\n")
        self.assertEqual(self.readme(extra=extra), [])

    def test_urls_are_not_fetched(self):
        extra = "\n[site](https://example.org/x) <a href=\"mailto:team@example.org\">mail</a> [cdn](//example.org/a.png)\n"
        self.assertEqual(self.readme(extra=extra), [])

    def test_links_into_the_docs_site_name_a_page(self):
        # site_url in mkdocs.yml maps a site link to its source, offline: docs/<page>.md, a static
        # file in docs/, or a skills/ or agents/ page that docs/hooks.py copies in at build time
        pages = ("https://example.org/neuroflow", "https://example.org/neuroflow/commands/alpha/#usage",
                 "https://example.org/neuroflow/skills/phase-alpha/SKILL/", "https://example.org/neuroflow/assets/logo.svg",
                 "https://example.org/neuroflow-other/gone/")
        self.assertEqual(self.readme(extra="\n" + " ".join(f"[x]({u})" for u in pages) + "\n"), [])
        found = self.readme(extra="\n[gone](https://example.org/neuroflow/concepts/gone/)\n")
        self.assertEqual([(f.severity, f.message) for f in found], [(
            rc.FAIL, "README.md links to `https://example.org/neuroflow/concepts/gone/`, a site page with no source in docs/")])

    def test_link_outside_the_repository_fails(self):
        found = self.readme(extra="\n[up](../outside.md)\n")
        self.assertEqual([f.message for f in found], ["README.md links to `../outside.md`, outside the repository"])

    def test_paths_with_fragments_and_root_slashes(self):
        self.assertEqual(self.readme(extra="\n[a](commands/alpha.md#usage) [b](/commands/alpha.md) [c](<docs/assets/logo.svg>)\n"), [])

    def test_reference_definitions_but_not_footnotes(self):
        found = self.readme(extra="\nSee [the guide][g].[^1]\n\n[g]: docs/guide.md\n[^1]: a footnote, not a path\n")
        self.assertEqual([f.message for f in found], ["README.md links to non-existent file `docs/guide.md`"])

    def test_mkdocs_theme_images(self):
        mk = FILES["mkdocs.yml"]
        write(self.root, {"mkdocs.yml": mk.replace("logo: assets/logo.svg", "logo: assets/brand/mark.svg")})
        self.assertEqual(self.text("V10"), "V10 fail mkdocs.yml theme logo `assets/brand/mark.svg` does not exist in docs/")
        write(self.root, {"mkdocs.yml": mk.replace("favicon: assets/logo.svg", "favicon: https://example.org/f.svg")})
        self.assertEqual(self.run_checks("V10"), [])
        # a deeper key of the same name (theme: icon: logo:) is not the theme logo
        write(self.root, {"mkdocs.yml": mk.replace("  logo: assets/logo.svg\n", "")
                          .replace("    repo: fontawesome/brands/github", "    logo: material/brain")})
        self.assertEqual(self.run_checks("V10"), [])
        # the theme's custom_dir counts too
        write(self.root, {"mkdocs.yml": mk.replace("logo: assets/logo.svg", "logo: assets/own.svg\n  custom_dir: overrides"),
                          "overrides/assets/own.svg": "<svg/>\n"})
        self.assertEqual(self.run_checks("V10"), [])

    def test_plugin_icon(self):
        plugin = json.loads(FILES[".claude-plugin/plugin.json"])
        for icon, ok in (("./docs/assets/logo.svg", True), ("docs/assets/logo.svg", True),
                         ("https://example.org/icon.png", True), ("./docs/assets/brand/icon-512.png", False)):
            write(self.root, {".claude-plugin/plugin.json": json.dumps({**plugin, "icon": icon}, indent=2) + "\n"})
            found = self.run_checks("V10")
            self.assertEqual(found == [], ok, (icon, found))
        self.assertEqual(self.text("V10"),
                         "V10 fail .claude-plugin/plugin.json icon `./docs/assets/brand/icon-512.png` does not exist")


class ReleaseNotesTests(RepoCase):
    """V12: one What's new section, for the plugin.json version; docs/changelog.md lists that version first."""

    def readme(self, old, new):
        write(self.root, {"README.md": FILES["README.md"].replace(old, new)})
        return self.run_checks("V12")

    def test_two_sections_fail_once(self):
        found = self.readme("## Installation", "## What's new in 1.2.2\n\n- older\n\n## Installation")
        self.assertEqual(len(found), 1)
        self.assertEqual(found[0].severity, rc.FAIL)
        self.assertIn("2 What's new sections (1.2.3, 1.2.2)", found[0].message)
        self.assertIn("docs/changelog.md", found[0].message)

    def test_a_curly_apostrophe_counts(self):
        found = self.readme("## Installation", "<details><summary>What’s new in 1.2.2</summary>\n\n- older\n\n"
                                               "</details>\n\n## Installation")
        self.assertEqual([f.severity for f in found], [rc.FAIL])

    def test_a_stale_section_warns(self):
        found = self.readme("## What's new in 1.2.3", "## What's new in 1.2.2")
        self.assertEqual([(f.severity, f.message) for f in found], [
            (rc.WARN, "README.md What's new is for 1.2.2, plugin.json is 1.2.3 - replace the section with "
                      "`## What's new in 1.2.3`")])

    def test_the_version_must_match_exactly(self):
        found = self.readme("## What's new in 1.2.3", "## What's new in 1.2.30")
        self.assertEqual([f.severity for f in found], [rc.WARN])
        self.assertIn("is for 1.2.30", found[0].message)

    def test_no_section_warns(self):
        found = self.readme("## What's new in 1.2.3", "## Recent changes")
        self.assertEqual([(f.severity, f.message) for f in found],
                         [(rc.WARN, "README.md has no `## What's new in 1.2.3` section")])

    def test_mentions_in_code_do_not_count(self):
        found = self.readme("## Installation", "```\n## What's new in 1.0.0\n```\n\n`What's new in 1.1.0`\n\n## Installation")
        self.assertEqual(found, [])

    def test_the_changelog_lists_the_version_first(self):
        write(self.root, {"docs/changelog.md": "# Changelog\n\n## 1.2.2\n\n- older\n\n## 1.2.3\n\n- x\n"})
        self.assertEqual([(f.severity, f.message) for f in self.run_checks("V12")], [
            (rc.WARN, "docs/changelog.md lists 1.2.2 first - the newest entry (`## 1.2.3`) goes on top")])

    def test_a_missing_changelog_entry_warns(self):
        write(self.root, {"docs/changelog.md": "# Changelog\n\n## 1.2.2\n\n- x\n"})
        found = self.run_checks("V12")
        self.assertEqual([(f.severity, f.message) for f in found], [(rc.WARN, "docs/changelog.md has no `## 1.2.3` entry")])


class HygieneTests(RepoCase):

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

    def test_stale_paths_in_the_readme(self):
        # README.md keeps only the newest release notes now, so V15 reads it like any other page.
        write(self.root, {"README.md": FILES["README.md"] + "Notes go to .neuroflow/flowie/notes/\n"})
        line = len(FILES["README.md"].splitlines()) + 1
        self.assertEqual([f.message.split(" uses ")[0] for f in self.run_checks("V15")], [f"README.md:{line}"])

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
