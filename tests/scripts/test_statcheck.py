"""Tests for skills/phase-paper/scripts/statcheck.py (stdlib unittest, no network)."""

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
SCRIPT = ROOT / "skills" / "phase-paper" / "scripts" / "statcheck.py"


def load():
    spec = importlib.util.spec_from_file_location("statcheck_under_test", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


sc = load()
W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"


def run_main(args):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = sc.main(args)
    return code, out.getvalue(), err.getvalue()


class DistributionTests(unittest.TestCase):
    """Reference values computed with scipy.stats (two-tailed unless noted)."""

    def setUp(self):
        self.b = sc.Backend("stdlib")

    def test_t(self):
        self.assertAlmostEqual(self.b.p_t(2.45, 23), 0.022315728160948567, places=10)
        self.assertAlmostEqual(self.b.p_t(3.1, 1.5), 0.12776977657068014, places=10)
        self.assertAlmostEqual(self.b.p_t(0.0, 10), 1.0, places=12)

    def test_f(self):
        self.assertAlmostEqual(self.b.p_f(5.21, 1, 38), 0.028142238861382854, places=10)
        self.assertAlmostEqual(self.b.p_f(2.1, 3, 57.3), 0.11023408479935919, places=10)

    def test_chi2(self):
        self.assertAlmostEqual(self.b.p_chi2(7.31, 2), 0.02586149748316563, places=10)
        self.assertAlmostEqual(self.b.p_chi2(100.2, 80), 0.06286922405920889, places=10)

    def test_r_and_z(self):
        self.assertAlmostEqual(self.b.p_r(0.32, 48), 0.023485526327821395, places=10)
        self.assertAlmostEqual(self.b.p_z(2.1), 0.035728841125633085, places=10)
        self.assertAlmostEqual(self.b.p_z(2.1, tails=1), 0.035728841125633085 / 2, places=10)


class CheckTextTests(unittest.TestCase):
    def setUp(self):
        self.b = sc.Backend("stdlib")

    def check(self, text, **kw):
        return sc.check_text(text, "test.md", self.b, **kw)

    def test_consistent_values(self):
        text = ("An effect, t(23) = 2.45, p = .022. ANOVA: F(1, 38) = 5.21, p = .028. "
                "A correlation, r(48) = .32, p = .023. Counts: χ²(2, N = 120) = 7.31, p = .026. "
                "Wald z = 2.10, p = .036.")
        results = self.check(text)
        self.assertEqual([r.test for r in results], ["t", "F", "r", "chi2", "z"])
        self.assertTrue(all(r.status == "consistent" for r in results), [r.label for r in results])
        self.assertEqual(results[0].label, "reported p matches t and df")

    def test_inconsistent_and_decision_error(self):
        results = self.check("Small difference, t(23) = 2.45, p = .002. Null effect, t(30) = 1.20, p = .03.")
        self.assertEqual(results[0].status, "inconsistent")
        self.assertEqual(results[0].label, "reported p does not match t and df")
        self.assertEqual(results[1].status, "decision-error")
        self.assertIn("changes significance", results[1].note)

    def test_rounding_of_statistic_is_allowed(self):
        # t(10) = 2.23 is p = .0499 to .0506 over the rounding interval of 2.225-2.235
        self.assertEqual(self.check("Effect, t(10) = 2.23, p = .05.")[0].status, "consistent")

    def test_inequalities(self):
        results = self.check("Strong, t(40) = 6.10, p < .001. Weak, t(18) = 0.90, p > .05. Also t(18) = 0.90, p = n.s.")
        self.assertEqual([r.status for r in results], ["consistent", "consistent", "consistent"])
        bad = self.check("Strong, t(40) = 1.10, p < .001.")
        self.assertEqual(bad[0].status, "decision-error")

    def test_corrected_p_is_skipped(self):
        results = self.check("After Bonferroni correction, t(10) = 2.0, p = .30. "
                             "FDR-corrected: F(2, 40) = 3.1, p = .2.")
        self.assertEqual([r.status for r in results], ["skipped", "skipped"])
        self.assertIn("corrected", results[0].label)

    def test_sphericity_correction_is_still_checked(self):
        results = self.check("Greenhouse-Geisser corrected, F(1.45, 33.2) = 5.0, p = .022.")
        self.assertNotEqual(results[0].status, "skipped")

    def test_one_tailed_when_stated(self):
        result = self.check("A one-tailed test showed t(20) = 1.80, p = .044.")[0]
        self.assertEqual(result.status, "consistent")
        self.assertEqual(result.tails, 1)
        # without the statement the two-tailed p (.087) is used, which flips significance
        self.assertEqual(self.check("A test showed t(20) = 1.80, p = .044.")[0].status, "decision-error")

    def test_latex_and_markdown_markup(self):
        text = (r"LaTeX \textit{t}(15)~=~3.10, \textit{p}~$<$~.01 and $\chi^2(1) = 3.84$, $p = .05$; "
                r"subscript $F_{2,57} = 3.2$, $p = .048$; markdown *t*(12) = −2.20, *p* = .048.")
        results = self.check(text)
        self.assertEqual([r.test for r in results], ["t", "chi2", "F", "t"])
        self.assertTrue(all(r.status == "consistent" for r in results), [r.label for r in results])

    def test_coordinates_are_not_z_statistics(self):
        self.assertEqual(self.check("Peak at x = 12, y = -40, z = 30, p < .001."), [])

    def test_scientific_p(self):
        result = self.check("Huge effect, t(40) = 6.1, p = 3.2 × 10^-7.")[0]
        self.assertEqual(result.status, "consistent")
        self.assertAlmostEqual(result.reported_p["value"], 3.2e-7)

    def test_line_numbers(self):
        results = self.check("Intro.\n\nResult t(23) = 2.45,\np = .022.\n")
        self.assertEqual(results[0].line, 3)


class CliTests(unittest.TestCase):
    def test_exit_codes_and_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            good = Path(tmp, "good.md")
            good.write_text("Effect, t(23) = 2.45, p = .022.\n", encoding="utf-8")
            bad = Path(tmp, "bad.tex")
            bad.write_text("% old value t(23) = 2.45, p = .5\nEffect, $t(23) = 2.45$, $p = .002$.\n", encoding="utf-8")
            code, out, _ = run_main([str(good)])
            self.assertEqual(code, 0)
            self.assertIn("reported p matches t and df", out)
            code, out, _ = run_main([str(bad), "--json"])
            self.assertEqual(code, 1)
            data = json.loads(out)
            self.assertEqual(len(data["results"]), 1, "LaTeX comments must be ignored")
            self.assertEqual(data["results"][0]["line"], 2)
            self.assertEqual(data["summary"]["inconsistent"], 1)
            code, _, err = run_main([str(Path(tmp, "missing.md"))])
            self.assertEqual(code, 2)
            self.assertIn("does not exist", err)

    def test_folder_and_docx(self):
        with tempfile.TemporaryDirectory() as tmp:
            doc = (f'<w:document xmlns:w="{W_NS}"><w:body>'
                   '<w:p><w:r><w:t>Methods.</w:t></w:r></w:p>'
                   '<w:p><w:r><w:t xml:space="preserve">Effect, t(23) = 2.45, </w:t></w:r>'
                   '<w:del w:id="1" w:author="A"><w:r><w:delText>p = .9</w:delText></w:r></w:del>'
                   '<w:ins w:id="2" w:author="A"><w:r><w:t>p = .002</w:t></w:r></w:ins></w:p>'
                   '</w:body></w:document>')
            with zipfile.ZipFile(Path(tmp, "paper.docx"), "w") as zf:
                zf.writestr("word/document.xml", doc)
            Path(tmp, "notes.csv").write_text("t(23) = 2.45, p = .9", encoding="utf-8")
            code, out, _ = run_main([tmp])
            self.assertEqual(code, 1)
            self.assertIn("para 2", out)
            self.assertIn("recomputed p", out)
            self.assertNotIn("notes.csv", out)


if __name__ == "__main__":
    unittest.main()
