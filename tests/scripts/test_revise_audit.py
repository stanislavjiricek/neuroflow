"""Tests for skills/phase-paper/scripts/revise_audit.py (stdlib unittest)."""

import contextlib
import importlib.util
import io
import json
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "skills" / "phase-paper" / "scripts" / "revise_audit.py"


def load():
    spec = importlib.util.spec_from_file_location("revise_audit_under_test", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


ra = load()
W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"

ORIGINAL = """# Methods

We recorded EEG from 64 channels. Data were filtered between 0.1 and 40 Hz.
We computed connectivity between all channel pairs.

Statistics used paired t-tests. The significance level was 0.05.
Trials with artefacts were removed by visual inspection.
"""

REVISED = """# Methods

We recorded EEG from 64 channels. Data were filtered between 0.1 and 40 Hz.
We computed connectivity between all channel pairs. We used the weighted phase-lag index because it is insensitive to volume conduction.

Statistics used paired t-tests with FDR correction across channel pairs. The significance level was 0.05.
"""

RESPONSE = """# Response to reviewers

## R1.1 Justify connectivity
> The choice of connectivity measure is not justified.

We added a justification.

Changed (Methods, line 4):
> We used the weighted phase-lag index because it is insensitive to volume conduction.

## R2.1 Multiple comparisons
> Please correct for multiple comparisons.

Revised (Methods, line 6):
> Statistics used paired t-tests with FDR correction ... across channel pairs.

## R2.2 Artefacts
> Visual inspection is not reproducible.

Deleted (Methods, line 7):
> Trials with artefacts were removed by visual inspection.
"""


def run_main(args):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = ra.main(args)
    return code, out.getvalue(), err.getvalue()


class ReviseAuditTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def write(self, name, text):
        path = self.dir / name
        path.write_text(text, encoding="utf-8")
        return path

    def test_clean_revision_passes(self):
        orig, rev = self.write("methods.md", ORIGINAL), self.write("methods-r1.md", REVISED)
        resp = self.write("response.md", RESPONSE)
        code, out, _ = run_main(["--response", str(resp), "--pair", str(orig), str(rev)])
        self.assertEqual(code, 0, out)
        self.assertIn("3 change(s) trace to a comment, 0 untraceable", out)

    def test_untraceable_and_missing(self):
        orig = self.write("methods.md", ORIGINAL)
        rev = self.write("methods-r1.md", REVISED + "Participants were paid.\n")
        resp = self.write("response.md", RESPONSE + "\n## R3.1 Sample\n> Report N.\n\nAdded:\n> We tested 24 participants.\n")
        code, out, _ = run_main(["--response", str(resp), "--pair", str(orig), str(rev), "--json"])
        self.assertEqual(code, 1)
        data = json.loads(out)
        untraced = [c for c in data["changes"] if not c["comments"]]
        self.assertEqual([c["text"] for c in untraced], ["Participants were paid."])
        self.assertEqual(untraced[0]["line"], 7)
        self.assertEqual([m["comment"] for m in data["claimed_but_missing"]], ["R3.1"])

    def test_unclaimed_deletion_is_flagged(self):
        orig, rev = self.write("methods.md", ORIGINAL), self.write("methods-r1.md", REVISED)
        resp = self.write("response.md", RESPONSE.split("## R2.2")[0])
        code, out, _ = run_main(["--response", str(resp), "--pair", str(orig), str(rev)])
        self.assertEqual(code, 1)
        self.assertIn('deleted: "Trials with artefacts were removed by visual inspection."', out)

    def test_latex_comments_are_ignored(self):
        orig = self.write("intro.tex", "We study attention. % TODO cite more\nIt matters.\n")
        rev = self.write("intro-r1.tex", "We study attention. % cite Smith 2020 here\nIt matters.\n")
        resp = self.write("response.md", "## R1.1 Typo\n> Fix the typo.\n\nNo change needed.\n")
        code, out, _ = run_main(["--response", str(resp), "--pair", str(orig), str(rev)])
        self.assertEqual(code, 0, out)

    def test_docx_pair_with_tracked_changes(self):
        def docx(name, body):
            path = self.dir / name
            with zipfile.ZipFile(path, "w") as zf:
                zf.writestr("word/document.xml", f'<w:document xmlns:w="{W_NS}"><w:body>{body}</w:body></w:document>')
            return path

        orig = docx("main.docx", "<w:p><w:r><w:t>The effect was significant.</w:t></w:r></w:p>")
        rev = docx("main-r1.docx",
                   '<w:p><w:r><w:t xml:space="preserve">The effect was </w:t></w:r>'
                   '<w:del w:id="1" w:author="A"><w:r><w:delText>significant</w:delText></w:r></w:del>'
                   '<w:ins w:id="2" w:author="A"><w:r><w:t>significant after FDR correction</w:t></w:r></w:ins>'
                   "<w:r><w:t>.</w:t></w:r></w:p>")
        resp = self.write("response.md", "## R1.1\n> Correct.\n\nNow reads:\n> The effect was significant after FDR correction.\n")
        code, out, _ = run_main(["--response", str(resp), "--pair", str(orig), str(rev)])
        self.assertEqual(code, 0, out)
        self.assertIn("-> R1.1", out)

    def test_response_without_ids_is_a_usage_error(self):
        orig, rev = self.write("a.md", ORIGINAL), self.write("a-r1.md", REVISED)
        resp = self.write("response.md", "# Response\nThanks for the comments.\n")
        code, _, err = run_main(["--response", str(resp), "--pair", str(orig), str(rev)])
        self.assertEqual(code, 2)
        self.assertIn("no comment headings", err)

    def test_parse_response_kinds(self):
        comments, passages = ra.parse_response(RESPONSE)
        self.assertEqual(list(comments), ["R1.1", "R2.1", "R2.2"])
        self.assertEqual([p.kind for p in passages],
                         ["context", "change", "context", "change", "context", "deletion"])

    def test_other_id_families(self):
        text = "## Results\nintro\n## C4 coauthor row\n## T2\n## S3.2-1 X-ray finding\n## E.1 Editor\n"
        comments, _ = ra.parse_response(text)
        self.assertEqual(list(comments), ["C4", "T2", "S3.2-1", "E.1"])


if __name__ == "__main__":
    unittest.main()
