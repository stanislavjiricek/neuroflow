"""Tests for skills/phase-paper/scripts/cite_check.py (stdlib unittest, network mocked)."""

import contextlib
import importlib.util
import io
import json
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "skills" / "phase-paper" / "scripts" / "cite_check.py"


def load():
    spec = importlib.util.spec_from_file_location("cite_check_under_test", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


cc = load()
W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"

GOOD = "10.1038/nature14539"
RETRACTED = "10.1016/S0140-6736(97)11096-0"
DATACITE = "10.18112/openneuro.ds000001.v1.0.0"
MISSING = "10.9999/does-not-exist"
PREPRINT = "10.1101/2020.01.01.123456"


def fake_fetch(url, timeout, user_agent=None):
    """Canned Crossref / doi.org answers keyed on the DOI in the URL."""
    def work(doi, **extra):
        msg = {"DOI": doi, "type": "journal-article", "title": [f"Title of {doi}"],
               "container-title": ["Journal"], "issued": {"date-parts": [[2015, 5, 27]]}}
        msg.update(extra)
        return 200, {"status": "ok", "message": msg}

    if "filter=updates:" in url:
        if "11096-0" in url:
            return 200, {"message": {"items": [
                {"DOI": "10.1016/S0140-6736(04)15715-2",
                 "update-to": [{"DOI": RETRACTED, "type": "correction", "updated": {"date-parts": [[2004, 3, 6]]}}]},
                {"DOI": "10.1016/x-unrelated", "update-to": [{"DOI": "10.1/other", "type": "retraction"}]},
            ]}}
        return 200, {"message": {"items": []}}
    if url.startswith("https://api.crossref.org/works/"):
        if "nature14539" in url:
            return work(GOOD)
        if "11096-0" in url:
            return work(RETRACTED, **{"updated-by": [
                {"DOI": "10.1016/S0140-6736(10)60175-4", "type": "retraction", "source": "retraction-watch",
                 "updated": {"date-parts": [[2010, 2, 6]]}}]})
        if "2020.01.01.123456" in url:
            return work(PREPRINT, type="posted-content",
                        relation={"is-preprint-of": [{"id-type": "doi", "id": "10.7554/eLife.99999"}]})
        return 404, {"status": "error"}
    if url.startswith("https://doi.org/api/handles/"):
        if "openneuro" in url:
            return 200, {"responseCode": 1}
        return 404, {"responseCode": 100}
    raise AssertionError(f"unexpected URL {url}")


def offline_fetch(url, timeout, user_agent=None):
    raise cc.NetworkError("no route to host")


def run_main(args, fetch=fake_fetch):
    out, err = io.StringIO(), io.StringIO()
    with mock.patch.object(cc, "fetch_json", fetch), mock.patch.object(cc, "_sleep", lambda s: None), \
            contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = cc.main(args)
    return code, out.getvalue(), err.getvalue()


class ExtractionTests(unittest.TestCase):
    def test_clean_doi(self):
        self.assertEqual(cc.clean_doi("10.1000/xyz)."), "10.1000/xyz")
        self.assertEqual(cc.clean_doi("10.1016/S0140-6736(97)11096-0"), "10.1016/S0140-6736(97)11096-0")
        self.assertEqual(cc.clean_doi("10.1000/a%2Fb,"), "10.1000/a/b")

    def test_text_formats(self):
        with tempfile.TemporaryDirectory() as tmp:
            bib = Path(tmp, "refs.bib")
            bib.write_text("@article{a2015,\n  title={A},\n  doi = {10.1038/nature14539},\n}\n"
                           "@book{nodoi2001,\n  title={No DOI here},\n}\n", encoding="utf-8")
            md = Path(tmp, "paper.md")
            md.write_text("See [x](https://doi.org/10.1000/abc) and doi:10.1016/S0140-6736(97)11096-0.\n",
                          encoding="utf-8")
            self.assertEqual([d for d, _ in cc.extract_dois(bib)], ["10.1038/nature14539"])
            found = list(cc.extract_dois(md))
            self.assertEqual([d for d, _ in found], ["10.1000/abc", "10.1016/S0140-6736(97)11096-0"])
            self.assertTrue(found[0][1].endswith("paper.md:1"))
            missing = cc.bib_entries_without_doi(bib)
            self.assertEqual(len(missing), 1)
            self.assertTrue(missing[0].startswith("nodoi2001"))

    def test_docx_text_links_and_field_codes(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp, "m.docx")
            doc = (f'<w:document xmlns:w="{W_NS}"><w:body>'
                   '<w:p><w:r><w:t>Body cites 10.1000/inbody.</w:t></w:r></w:p>'
                   '<w:p><w:r><w:instrText xml:space="preserve"> ADDIN ZOTERO_ITEM {"DOI":"10.1000/zotero"} </w:instrText>'
                   '</w:r></w:p></w:body></w:document>')
            rels = ('<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                    '<Relationship Id="rId9" Type="hyperlink" Target="https://doi.org/10.1000%2Flinked" '
                    'TargetMode="External"/></Relationships>')
            with zipfile.ZipFile(path, "w") as zf:
                zf.writestr("word/document.xml", doc)
                zf.writestr("word/_rels/document.xml.rels", rels)
            dois = sorted(d for d, _ in cc.extract_dois(path))
            self.assertEqual(dois, ["10.1000/inbody", "10.1000/linked", "10.1000/zotero"])


class LookupTests(unittest.TestCase):
    def test_resolves_with_notices(self):
        entry = cc.lookup(RETRACTED, fetch=fake_fetch, today="2026-10-07")
        self.assertTrue(entry["resolves"])
        types = [n["type"] for n in entry["notices"]]
        self.assertEqual(types, ["correction", "retraction"])
        finding = cc.judge(RETRACTED, entry, ["x:1"], None)
        self.assertEqual(finding.status, "flag")
        self.assertIn("retraction notice 10.1016/S0140-6736(10)60175-4", finding.label)
        self.assertNotIn("no retraction notice found", finding.label)

    def test_clean_record_wording(self):
        entry = cc.lookup(GOOD, fetch=fake_fetch, today="2026-10-07")
        finding = cc.judge(GOOD, entry, ["x:1"], None)
        self.assertEqual(finding.status, "ok")
        self.assertEqual(finding.label,
                         "DOI resolves (crossref); no retraction notice found in Crossref as of 2026-10-07")

    def test_datacite_missing_and_preprint(self):
        datacite = cc.lookup(DATACITE, fetch=fake_fetch)
        self.assertEqual((datacite["resolves"], datacite["source"]), (True, "doi.org"))
        self.assertIn("notices were not checked", cc.judge(DATACITE, datacite, [], None).label)
        missing = cc.lookup(MISSING, fetch=fake_fetch)
        self.assertIs(missing["resolves"], False)
        self.assertEqual(cc.judge(MISSING, missing, [], None).label, "does not resolve")
        pre = cc.lookup(PREPRINT, fetch=fake_fetch)
        self.assertEqual(pre["vor"], ["10.7554/eLife.99999"])
        self.assertEqual(cc.judge(PREPRINT, pre, [], None).status, "note")

    def test_server_error_is_unchecked(self):
        entry = cc.lookup(GOOD, fetch=lambda url, t, ua=None: (500, None))
        self.assertIsNone(entry["resolves"])
        self.assertEqual(cc.judge(GOOD, entry, [], None).status, "unchecked")


class CliTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)
        self.paper = self.dir / "paper.md"
        self.paper.write_text(f"Good {GOOD}. Bad {MISSING}.\n", encoding="utf-8")

    def tearDown(self):
        self.tmp.cleanup()

    def test_findings_cache_and_offline(self):
        cache = self.dir / "cache.json"
        code, out, _ = run_main([str(self.paper), "--cache", str(cache), "--delay", "0"])
        self.assertEqual(code, 1)
        self.assertIn("does not resolve", out)
        self.assertIn("DOI resolves", out)
        self.assertNotIn("verified", out.lower())
        self.assertTrue(cache.exists())
        cached = json.loads(cache.read_text(encoding="utf-8"))["entries"]
        self.assertEqual(set(cached), {GOOD.lower(), MISSING.lower()})
        code, out, _ = run_main([str(self.paper), "--offline", "--cache", str(cache), "--json"], fetch=offline_fetch)
        self.assertEqual(code, 1)
        data = json.loads(out)
        self.assertEqual(data["mode"], "offline")
        self.assertEqual(data["summary"]["do_not_resolve"], 1)

    def test_clean_run_and_library(self):
        clean = self.dir / "clean.md"
        clean.write_text(f"Only {GOOD}.\n", encoding="utf-8")
        self.assertEqual(run_main([str(clean), "--delay", "0"])[0], 0)
        library = self.dir / "papers" / "lecun-2015-deep-learning"
        library.mkdir(parents=True)
        (library / "lecun-2015-deep-learning.md").write_text('---\ndoi: "unverified: 10.1000/other"\n---\n',
                                                             encoding="utf-8")
        code, out, _ = run_main([str(clean), "--library", str(self.dir / "papers"), "--delay", "0"])
        self.assertEqual(code, 1)
        self.assertIn("not in the project library", out)
        export = self.dir / "library.bib"
        export.write_text("@article{x,\n  doi = {10.1038/NATURE14539},\n}\n", encoding="utf-8")
        self.assertEqual(run_main([str(clean), "--library", str(export), "--delay", "0"])[0], 0,
                         "a .bib export works as the library; DOIs match case-insensitively")

    def test_max_age_looks_up_only_new_or_stale_dois(self):
        cache = self.dir / "cache.json"
        self.assertEqual(run_main([str(self.paper), "--cache", str(cache), "--delay", "0"])[0], 1)
        # Fresh entries are reused: no lookup at all (a lookup would fail with no network).
        code, out, _ = run_main([str(self.paper), "--cache", str(cache), "--max-age", "7", "--json"], fetch=offline_fetch)
        self.assertEqual(code, 1)
        data = json.loads(out)
        self.assertEqual(data["reused_from_cache"], 2)
        self.assertEqual(data["summary"]["do_not_resolve"], 1)
        # An entry older than the limit is looked up again; the fresh one is not.
        stored = json.loads(cache.read_text(encoding="utf-8"))
        stored["entries"][GOOD.lower()]["checked_at"] = "2000-01-01"
        cache.write_text(json.dumps(stored), encoding="utf-8")
        asked = []

        def counting_fetch(url, timeout, user_agent=None):
            asked.append(url)
            return fake_fetch(url, timeout, user_agent)

        code, out, _ = run_main([str(self.paper), "--cache", str(cache), "--max-age", "7", "--json"], fetch=counting_fetch)
        self.assertEqual(json.loads(out)["reused_from_cache"], 1)
        self.assertTrue(asked and all("nature14539" in url for url in asked))
        self.assertNotEqual(json.loads(cache.read_text(encoding="utf-8"))["entries"][GOOD.lower()]["checked_at"], "2000-01-01")
        self.assertEqual(run_main([str(self.paper), "--max-age", "7"])[0], 2, "--max-age needs --cache")

    def test_offline_without_cache_and_no_network(self):
        self.assertEqual(run_main([str(self.paper), "--offline"])[0], 2)
        code, _, err = run_main([str(self.paper), "--delay", "0"], fetch=offline_fetch)
        self.assertEqual(code, 2)
        self.assertIn("no network", err)

    def test_no_dois(self):
        empty = self.dir / "empty.md"
        empty.write_text("Smith et al. (2019) showed this.\n", encoding="utf-8")
        code, out, _ = run_main([str(empty)])
        self.assertEqual(code, 0)
        self.assertIn("no DOIs found", out)


if __name__ == "__main__":
    unittest.main()
