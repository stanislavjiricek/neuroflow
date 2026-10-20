"""Tests for scripts/automation/brand_assets.py: the committed ring images match the generator and keep
the rules (no <text>, external url(...), @import or external href in an SVG; the PNG sizes; each image
under 512 KB and all of them under 1 MB). No browser and no network: --png is never run here."""

from __future__ import annotations

import contextlib
import io
import json
import re
import shutil
import struct
import tempfile
import unittest
import zlib
from pathlib import Path

from .helpers import REPO, load

ba = load("brand_assets")
BRAND = REPO / ba.BRAND_DIR


def png(width: int, height: int, padding: int = 0) -> bytes:
    """A small valid grey PNG of the given size; `padding` bytes of trailing data make it heavier."""
    def chunk(kind: bytes, data: bytes) -> bytes:
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
    rows = b"".join(b"\x00" + b"\x80" * width for _ in range(height))
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 0, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(rows)) + chunk(b"IEND", b"") + b"\x00" * padding)


def run(*args: str) -> tuple[int, str]:
    out = io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(out):
        code = ba.main(list(args))
    return code, out.getvalue()


class RepoImagesTests(unittest.TestCase):
    """The images committed in docs/assets/brand/."""

    def test_check_passes_on_the_repo(self):
        code, out = run("--check")
        self.assertEqual(code, 0, out)
        code, out = run()  # --check is the default
        self.assertEqual(code, 0, out)

    def test_json_report(self):
        code, out = run("--json")
        report = json.loads(out)
        self.assertEqual((code, report["exit_code"], report["findings"]), (0, 0, []))

    def test_the_folder_holds_exactly_the_asset_table(self):
        self.assertEqual(sorted(p.name for p in BRAND.iterdir()), sorted([*ba.SVGS, *ba.PNGS]))

    def test_svgs_draw_without_text_or_outside_references(self):
        for name in ba.SVGS:
            text = (BRAND / name).read_text(encoding="utf-8")
            with self.subTest(name):
                self.assertNotRegex(text, r"<text\b")
                self.assertNotRegex(text, r"url\(\s*['\"]?https?:")
                self.assertNotIn("@import", text)
                self.assertNotRegex(text, r"href\s*=\s*['\"](?:https?:)?//")

    def test_png_dimensions(self):
        expected = {"favicon-32.png": (32, 32), "apple-touch-icon.png": (180, 180), "icon-512.png": (512, 512),
                    "social-card.png": (1280, 640)}
        for name, size in expected.items():
            self.assertEqual(ba.PNGS[name], size)
        for name, size in ba.PNGS.items():
            with self.subTest(name):
                self.assertEqual(ba.png_size((BRAND / name).read_bytes()), size)

    def test_weight(self):
        sizes = {p.name: p.stat().st_size for p in BRAND.iterdir()}
        for name, size in sizes.items():
            with self.subTest(name):
                self.assertLess(size, 512 * 1024)
        self.assertLess(sum(sizes.values()), 1024 * 1024)

    def test_the_mark_is_the_landing_dial(self):
        """The ticks and phase dots are the landing page's (overrides/home.html): 76 ticks, the long ones
        on the dots, and 19 dots of radius 4 on a ring of radius 176, the first at (220, 44)."""
        home = (REPO / "overrides" / "home.html").read_text(encoding="utf-8")
        mark = (BRAND / "neuroflow-mark.svg").read_text(encoding="utf-8")
        segment = r"M(-?[\d.]+) (-?[\d.]+)L(-?[\d.]+) (-?[\d.]+)"
        dial_ticks = re.search(r'<path d="(M[^"]+)" stroke="#2C2F37"', home)
        mark_ticks = re.search(r'<path class="t" d="([^"]+)"', mark)
        self.assertIsNotNone(dial_ticks)
        self.assertIsNotNone(mark_ticks)
        dial = [tuple(map(float, s)) for s in re.findall(segment, dial_ticks.group(1))]
        ours = [tuple(map(float, s)) for s in re.findall(segment, mark_ticks.group(1))]
        self.assertEqual(len(dial), 76)
        self.assertEqual(len(ours), 76)
        for a, b in zip(dial, ours):
            self.assertTrue(all(abs(x - y) < .051 for x, y in zip(a, b)), f"{a} != {b}")
        dial_dots = sorted(tuple(map(float, d)) for d in re.findall(
            r'<circle data-dot="" cx="([\d.]+)" cy="([\d.]+)" r="4"', home))
        ours_dots = sorted(tuple(map(float, d)) for d in re.findall(r'<circle[^>]* cx="([\d.]+)" cy="([\d.]+)" r="4"', mark))
        self.assertEqual(len(dial_dots), 19)
        self.assertEqual(dial_dots, ours_dots)
        self.assertIn('<circle class="s" cx="220" cy="44" r="4"', mark)

    def test_fonts_load_as_on_the_landing_page(self):
        href = re.search(r'href="(https://fonts\.googleapis\.com/css2\?[^"]+)"', ba.FONT_LINK).group(1)
        self.assertIn(href, (REPO / "overrides" / "home.html").read_text(encoding="utf-8"))


class RulesTests(unittest.TestCase):
    def test_svg_rules(self):
        self.assertEqual(ba.svg_problems('<svg><circle r="4"/></svg>'), [])
        self.assertEqual(len(ba.svg_problems('<svg><text x="0">neuroflow</text></svg>')), 1)
        self.assertEqual(len(ba.svg_problems("<svg><style>@import 'a.css';</style></svg>")), 1)
        self.assertEqual(len(ba.svg_problems("<svg><rect fill=\"url('https://example.org/p.svg#g')\"/></svg>")), 1)
        self.assertEqual(len(ba.svg_problems('<svg><image href="https://example.org/a.png"/></svg>')), 1)
        self.assertEqual(ba.svg_problems('<svg><use href="#ring"/><title>x</title></svg>'), [])

    def test_png_size(self):
        self.assertEqual(ba.png_size(png(32, 16)), (32, 16))
        self.assertIsNone(ba.png_size(b"GIF89a" + b"\x00" * 30))
        self.assertIsNone(ba.png_size(b""))

    def test_tokens(self):
        css = """/* --nf-bg: #123456; in a comment */
:root { --nf-bg: #06070A; --nf-fg: #E9E9E4; --nf-mark: rgba(1, 2, 3, .1); }
[data-x] { --nf-bg: #FFFFFF; }
@media (prefers-color-scheme: light) { :root { --nf-bg: #F4F3EF; } }
@media (min-width: 10px) { :root { --nf-fg: #000000; } }"""
        tokens = ba.read_tokens(css)
        self.assertEqual(tokens["dark"], {"bg": "#06070A", "fg": "#E9E9E4", "mark": "rgba(1, 2, 3, .1)"})
        self.assertEqual(tokens["light"]["bg"], "#F4F3EF")
        self.assertEqual(tokens["light"]["fg"], "#E9E9E4")

    def test_numbers(self):
        self.assertEqual([ba.num(220.0), ba.num(236.24), ba.num(-0.04), ba.num(1.25, 2)], ["220", "236.2", "0", "1.25"])
        self.assertEqual([ba.alpha(.18), ba.alpha(1)], [".18", "1"])


class FixtureTests(unittest.TestCase):
    """--check, --write and the errors on a copy of the repo's stylesheet and images."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        (self.root / "docs" / "stylesheets").mkdir(parents=True)
        shutil.copy(REPO / ba.NF_CSS, self.root / ba.NF_CSS)
        shutil.copytree(BRAND, self.root / ba.BRAND_DIR)
        self.brand = self.root / ba.BRAND_DIR

    def tearDown(self):
        self._tmp.cleanup()

    def check(self) -> tuple[int, str]:
        return run("--root", str(self.root))

    def test_a_copy_is_clean(self):
        self.assertEqual(self.check()[0], 0)

    def test_crlf_checkout_is_not_drift(self):
        path = self.brand / "favicon.svg"
        path.write_bytes(path.read_bytes().replace(b"\n", b"\r\n"))
        self.assertEqual(self.check()[0], 0)

    def test_an_edited_svg_is_drift_and_write_repairs_it(self):
        path = self.brand / "favicon.svg"
        path.write_bytes(path.read_bytes().replace(b'r="6"', b'r="7"'))
        code, out = self.check()
        self.assertEqual(code, 1)
        self.assertIn("favicon.svg: differs from the generator's output", out)
        code, out = run("--write", "--root", str(self.root))
        self.assertEqual(code, 0)
        self.assertIn("favicon.svg", out)
        self.assertEqual(self.check()[0], 0)

    def test_a_palette_change_reaches_the_svgs(self):
        css = self.root / ba.NF_CSS
        css.write_text(css.read_text(encoding="utf-8").replace("--nf-bg: #06070A", "--nf-bg: #000000", 1),
                       encoding="utf-8")
        code, out = self.check()
        self.assertEqual(code, 1)
        self.assertIn("favicon.svg", out)
        run("--write", "--root", str(self.root))
        self.assertIn('fill="#000000"', (self.brand / "favicon.svg").read_text(encoding="utf-8"))

    def test_png_problems(self):
        (self.brand / "favicon-32.png").write_bytes(png(16, 16))
        (self.brand / "icon-512.png").unlink()
        (self.brand / "apple-touch-icon.png").write_bytes(b"not a png")
        (self.brand / "logo-old.png").write_bytes(png(8, 8))
        code, out = self.check()
        self.assertEqual(code, 1)
        self.assertIn("favicon-32.png: 16x16, expected 32x32", out)
        self.assertIn("icon-512.png: missing", out)
        self.assertIn("apple-touch-icon.png: not a PNG file", out)
        self.assertIn("logo-old.png: not made by this generator", out)

    def test_weight_limits(self):
        (self.brand / "social-card.png").write_bytes(png(1280, 640, padding=600 * 1024))
        code, out = self.check()
        self.assertEqual(code, 1)
        self.assertRegex(out, r"social-card\.png: 60\d KB, over the 512 KB limit")
        (self.brand / "social-card.png").write_bytes(png(1280, 640, padding=400 * 1024))
        for name in ("neuroflow-lockup-dark.png", "neuroflow-lockup-light.png"):
            (self.brand / name).write_bytes(png(880, 880, padding=400 * 1024))
        code, out = self.check()
        self.assertEqual(code, 1)
        self.assertNotIn("over the 512 KB limit", out)
        self.assertIn("in all, over the 1024 KB limit", out)

    def test_an_svg_with_text_fails(self):
        (self.brand / "neuroflow-mark.svg").write_text('<svg><text>neuroflow</text></svg>\n', encoding="utf-8")
        code, out = self.check()
        self.assertEqual(code, 1)
        self.assertIn("neuroflow-mark.svg: contains a <text> element", out)

    def test_a_missing_token_is_an_error(self):
        css = self.root / ba.NF_CSS
        css.write_text(css.read_text(encoding="utf-8").replace("--nf-strong: #FFFFFF;", "", 1), encoding="utf-8")
        code, out = self.check()
        self.assertEqual(code, 2)
        self.assertIn("--nf-strong", out)

    def test_render_needs_a_browser(self):
        code, out = run("--png", "--browser", str(self.root / "no-such-browser"), "--root", str(self.root))
        self.assertEqual(code, 2)
        self.assertIn("no such program", out)

    def test_browser_goes_with_png(self):
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as raised:
            ba.main(["--browser", "chrome"])
        self.assertEqual(raised.exception.code, 2)


if __name__ == "__main__":
    unittest.main()
