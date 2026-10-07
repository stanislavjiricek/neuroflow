"""Tests for skills/phase-paper/scripts/docx_comments.py (stdlib unittest)."""

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
SCRIPT = ROOT / "skills" / "phase-paper" / "scripts" / "docx_comments.py"


def load():
    spec = importlib.util.spec_from_file_location("docx_comments_under_test", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


dc = load()
W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
W14 = "http://schemas.microsoft.com/office/word/2010/wordml"
W15 = "http://schemas.microsoft.com/office/word/2012/wordml"

DOCUMENT = f"""<w:document xmlns:w="{W}"><w:body>
<w:p><w:r><w:t xml:space="preserve">The P300 was </w:t></w:r><w:commentRangeStart w:id="0"/><w:r><w:t>larger in the noise condition</w:t></w:r><w:commentRangeEnd w:id="0"/><w:r><w:commentReference w:id="0"/></w:r><w:r><w:t>.</w:t></w:r></w:p>
<w:p><w:r><w:t xml:space="preserve">This effect was </w:t></w:r><w:del w:id="5" w:author="Jane Doe" w:date="2026-09-30T10:00:00Z"><w:r><w:delText>significantly</w:delText></w:r></w:del><w:ins w:id="6" w:author="Jane Doe" w:date="2026-09-30T10:00:00Z"><w:r><w:t>reliably</w:t></w:r></w:ins><w:r><w:t xml:space="preserve"> larger</w:t></w:r><w:ins w:id="7" w:author="Alex Roe" w:date="2026-10-01T09:00:00Z"><w:r><w:t xml:space="preserve"> across all 64 </w:t></w:r></w:ins><w:ins w:id="8" w:author="Alex Roe" w:date="2026-10-01T09:00:00Z"><w:r><w:rPr><w:i/></w:rPr><w:t>channels</w:t></w:r></w:ins><w:r><w:rPr><w:rPrChange w:id="9" w:author="Jane Doe"><w:rPr/></w:rPrChange></w:rPr><w:t>.</w:t></w:r></w:p>
<w:p><w:r><w:t xml:space="preserve">Groups | differed </w:t></w:r><w:del w:id="10" w:author="Jane Doe"><w:r><w:delText>a lot</w:delText></w:r></w:del><w:r><w:t xml:space="preserve"> in age and </w:t></w:r><w:ins w:id="11" w:author="Jane Doe"><w:r><w:t>sex</w:t></w:r></w:ins></w:p>
</w:body></w:document>"""

COMMENTS = f"""<w:comments xmlns:w="{W}" xmlns:w14="{W14}">
<w:comment w:id="0" w:author="Jane Doe" w:date="2026-09-30T10:00:00Z" w:initials="JD"><w:p w14:paraId="1A2B3C4D"><w:r><w:t>Is this corrected for multiple comparisons?</w:t></w:r></w:p></w:comment>
<w:comment w:id="1" w:author="Alex Roe" w:date="2026-10-01T09:00:00Z" w:initials="AR"><w:p w14:paraId="5E6F7A8B"><w:r><w:t>Yes, cluster-based.</w:t></w:r></w:p></w:comment>
</w:comments>"""

EXTENDED = f"""<w15:commentsEx xmlns:w15="{W15}"><w15:commentEx w15:paraId="1A2B3C4D" w15:done="1"/>
<w15:commentEx w15:paraId="5E6F7A8B" w15:paraIdParent="1A2B3C4D" w15:done="0"/></w15:commentsEx>"""


def make_docx(path, document=DOCUMENT, comments=COMMENTS, extended=EXTENDED):
    with zipfile.ZipFile(path, "w") as zf:
        zf.writestr("word/document.xml", document)
        if comments:
            zf.writestr("word/comments.xml", comments)
        if extended:
            zf.writestr("word/commentsExtended.xml", extended)


def run_main(args):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = dc.main(args)
    return code, out.getvalue(), err.getvalue()


class ExtractTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name, "main-JD.docx")
        make_docx(self.path)
        self.data = dc.extract(self.path)

    def tearDown(self):
        self.tmp.cleanup()

    def test_comments_anchor_threads_and_resolved(self):
        first, reply = self.data["comments"]
        self.assertEqual(first["anchor"], "larger in the noise condition")
        self.assertEqual(first["para"], 1)
        self.assertTrue(first["done"])
        self.assertEqual(reply["parent"], first["id"])
        self.assertEqual(reply["para"], 1)
        self.assertFalse(reply["done"])

    def test_tracked_changes_are_merged_only_when_touching(self):
        changes = [(c["kind"], c["author"], c["para"], c["text"]) for c in self.data["changes"]]
        self.assertEqual(changes, [
            ("replacement", "Jane Doe", 2, '"significantly" -> "reliably"'),
            ("insertion", "Alex Roe", 2, '+ " across all 64 channels"'),
            ("deletion", "Jane Doe", 3, '- "a lot"'),
            ("insertion", "Jane Doe", 3, '+ "sex"'),
        ])
        self.assertEqual(self.data["formatting_changes"], 1)
        self.assertEqual(self.data["changes"][0]["context"], "This effect was reliably larger across all 64 channels.")

    def test_markdown_table(self):
        md = dc.to_markdown(self.data, 2, "2026-10-07")
        self.assertIn("# Coauthor round 2: main-JD.docx", md)
        self.assertIn("| C2 | reply to C1 | Alex Roe |", md)
        self.assertIn("| C1 | comment (resolved) |", md)
        self.assertIn("| T1 | replacement |", md)
        self.assertIn("Groups \\| differed", md, "pipes inside cells are escaped")
        rows = [line for line in md.splitlines() if line.startswith("| C") or line.startswith("| T")]
        self.assertEqual(len(rows), 6)
        self.assertTrue(all(line.endswith("|  |  |") for line in rows), "Disposition and Note start empty")


class CliTests(unittest.TestCase):
    def test_exit_codes_out_file_and_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            busy, clean = Path(tmp, "busy.docx"), Path(tmp, "clean.docx")
            make_docx(busy)
            make_docx(clean, document=f'<w:document xmlns:w="{W}"><w:body><w:p><w:r><w:t>Fine.</w:t></w:r></w:p>'
                                      "</w:body></w:document>", comments=None, extended=None)
            out_file = Path(tmp, "paper", "coauthor-round-1.md")
            code, out, _ = run_main([str(busy), "--round", "1", "--out", str(out_file)])
            self.assertEqual(code, 1)
            self.assertTrue(out_file.exists())
            self.assertIn("2 comment(s), 4 tracked change(s)", out)
            code, _, err = run_main([str(busy), "--out", str(out_file)])
            self.assertEqual(code, 2, "never overwrite an existing round file")
            self.assertIn("exists", err)
            code, out, _ = run_main([str(clean), "--json"])
            self.assertEqual(code, 0)
            self.assertEqual(json.loads(out)["comments"], [])
            notes = Path(tmp, "notes.txt")
            notes.write_text("x", encoding="utf-8")
            self.assertEqual(run_main([str(notes)])[0], 2)
            Path(tmp, "broken.docx").write_bytes(b"not a zip")
            self.assertEqual(run_main([str(Path(tmp, "broken.docx"))])[0], 2)


if __name__ == "__main__":
    unittest.main()
