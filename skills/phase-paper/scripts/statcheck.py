#!/usr/bin/env python3
"""statcheck.py: recompute p-values from reported test statistics.

Finds APA-style results in manuscript text, for example
    t(23) = 2.45, p = .021      F(1, 38) = 5.21, p = .028      r(48) = .32, p = .023
    chi2(2, N = 120) = 7.31, p = .026      z = 2.10, p = .036
recomputes p from the statistic and its degrees of freedom, and reports whether
the reported p matches. Rounding of the reported statistic and p is taken into
account (a value reported to two decimals stands for a +-0.005 interval).

What it does NOT check: p-values marked as corrected or adjusted (FDR, FWE,
Bonferroni, Holm, permutation, cluster-based, bootstrap). Those cannot be
recomputed from the statistic alone, so they are listed as skipped. A
correction stated in another paragraph is not seen; check flagged items
against the Methods.

Labels name the test, never a virtue: "reported p matches t and df",
"reported p does not match t and df".

Usage:
    python statcheck.py manuscript/results.md
    python statcheck.py manuscript/ --json
    python statcheck.py - < section.md        (text on stdin)

Input: .md .tex .txt .qmd .rmd .docx files or folders, or '-' for stdin.
Exit codes: 0 = no inconsistencies, 1 = at least one inconsistency,
2 = usage or read error.
Stdlib only; uses scipy.special when it is installed (same results within
1e-10), otherwise its own continued-fraction implementations.
"""

import argparse
import json
import math
import re
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _doctext import (  # noqa: E402
    DocumentError,
    configure_utf8_stdio,
    iter_files,
    line_number,
    read_text,
    strip_comments,
)

INPUT_EXTS = frozenset({".md", ".markdown", ".txt", ".tex", ".qmd", ".rmd", ".docx"})

# ---------------------------------------------------------------------------
# Distribution functions (stdlib)
# ---------------------------------------------------------------------------

_FPMIN = 1e-300
_EPS = 3e-16
_MAX_ITER = 20000


def _betacf(a: float, b: float, x: float) -> float:
    """Continued fraction for the incomplete beta function (modified Lentz)."""
    qab, qap, qam = a + b, a + 1.0, a - 1.0
    c = 1.0
    d = 1.0 - qab * x / qap
    if abs(d) < _FPMIN:
        d = _FPMIN
    d = 1.0 / d
    h = d
    for m in range(1, _MAX_ITER + 1):
        m2 = 2 * m
        aa = m * (b - m) * x / ((qam + m2) * (a + m2))
        d = 1.0 + aa * d
        d = _FPMIN if abs(d) < _FPMIN else d
        c = 1.0 + aa / c
        c = _FPMIN if abs(c) < _FPMIN else c
        d = 1.0 / d
        h *= d * c
        aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
        d = 1.0 + aa * d
        d = _FPMIN if abs(d) < _FPMIN else d
        c = 1.0 + aa / c
        c = _FPMIN if abs(c) < _FPMIN else c
        d = 1.0 / d
        delta = d * c
        h *= delta
        if abs(delta - 1.0) < _EPS:
            break
    return h


def betainc_reg(a: float, b: float, x: float) -> float:
    """Regularized incomplete beta function I_x(a, b)."""
    if x <= 0.0:
        return 0.0
    if x >= 1.0:
        return 1.0
    log_bt = (
        math.lgamma(a + b) - math.lgamma(a) - math.lgamma(b) + a * math.log(x) + b * math.log1p(-x)
    )
    bt = math.exp(log_bt)
    if x < (a + 1.0) / (a + b + 2.0):
        return bt * _betacf(a, b, x) / a
    return 1.0 - bt * _betacf(b, a, 1.0 - x) / b


def gammaincc_reg(a: float, x: float) -> float:
    """Regularized upper incomplete gamma function Q(a, x)."""
    if x <= 0.0:
        return 1.0
    log_pre = -x + a * math.log(x) - math.lgamma(a)
    if x < a + 1.0:
        ap, total, term = a, 1.0 / a, 1.0 / a
        for _ in range(_MAX_ITER):
            ap += 1.0
            term *= x / ap
            total += term
            if abs(term) < abs(total) * _EPS:
                break
        return max(0.0, 1.0 - total * math.exp(log_pre))
    b = x + 1.0 - a
    c = 1.0 / _FPMIN
    d = 1.0 / b
    h = d
    for i in range(1, _MAX_ITER):
        an = -i * (i - a)
        b += 2.0
        d = an * d + b
        d = _FPMIN if abs(d) < _FPMIN else d
        c = b + an / c
        c = _FPMIN if abs(c) < _FPMIN else c
        d = 1.0 / d
        delta = d * c
        h *= delta
        if abs(delta - 1.0) < _EPS:
            break
    return math.exp(log_pre) * h


def _special():
    """scipy.special when installed, else None (imported lazily)."""
    try:
        from scipy import special  # type: ignore

        return special
    except Exception:  # noqa: BLE001 - any import problem means "not available"
        return None


class Backend:
    def __init__(self, name: str = "auto"):
        self.special = None
        if name in ("auto", "scipy"):
            self.special = _special()
            if name == "scipy" and self.special is None:
                raise RuntimeError("scipy is not installed (pip install scipy), use --backend stdlib")
        self.name = "scipy" if self.special is not None else "stdlib"

    def betainc(self, a, b, x):
        if self.special is not None:
            return float(self.special.betainc(a, b, x))
        return betainc_reg(a, b, x)

    def gammaincc(self, a, x):
        if self.special is not None:
            return float(self.special.gammaincc(a, x))
        return gammaincc_reg(a, x)

    # Upper-tail / two-tailed p-values -------------------------------------
    def p_t(self, t: float, df: float, tails: int = 2) -> float:
        p2 = self.betainc(df / 2.0, 0.5, df / (df + t * t)) if t != 0 else 1.0
        return p2 if tails == 2 else p2 / 2.0

    def p_z(self, z: float, tails: int = 2) -> float:
        p2 = math.erfc(abs(z) / math.sqrt(2.0))
        return p2 if tails == 2 else p2 / 2.0

    def p_f(self, f: float, df1: float, df2: float) -> float:
        if f <= 0:
            return 1.0
        return self.betainc(df2 / 2.0, df1 / 2.0, df2 / (df2 + df1 * f))

    def p_chi2(self, x: float, df: float) -> float:
        return self.gammaincc(df / 2.0, x / 2.0)

    def p_r(self, r: float, df: float, tails: int = 2) -> float:
        if abs(r) >= 1.0:
            return 0.0
        t = r * math.sqrt(df / (1.0 - r * r))
        return self.p_t(t, df, tails)


# ---------------------------------------------------------------------------
# Text normalization (newline-preserving, so line numbers stay valid)
# ---------------------------------------------------------------------------

_LATEX_WRAPPERS = re.compile(
    r"\\(?:textit|emph|mathit|mathrm|textrm|text|textsf|mathsf|textbf|mathbf|mathnormal)[ \t]*\{([^{}\n]*)\}"
)
_SUBSCRIPT_DF = re.compile(r"(?<![A-Za-z\\])(t|F|r|χ²|chi2)[ \t]*_[ \t]*\{([^{}\n]+)\}")
_SUBSCRIPT_DF_BARE = re.compile(r"(?<![A-Za-z\\])(t|F|r)[ \t]*_[ \t]*(\d+)")
_MD_ITALIC_LETTER = re.compile(r"(?<![A-Za-z0-9])_([A-Za-z])_(?![A-Za-z0-9])")


def normalize(text: str) -> str:
    """Strip LaTeX/Markdown markup around statistics without touching newlines."""
    s = text
    for src, dst in (
        ("\u2212", "-"), ("\u2013", "-"), ("\u00a0", " "), ("\u2009", " "), ("\u202f", " "),
        ("\u2002", " "), ("\u2003", " "), ("\uff1d", "="), ("\u2264", "≤"), ("\u2265", "≥"),
    ):
        s = s.replace(src, dst)
    s = re.sub(r"\\(?:leq|le)(?![A-Za-z])", "≤", s)
    s = re.sub(r"\\(?:geq|ge)(?![A-Za-z])", "≥", s)
    s = re.sub(r"\\textless(?![A-Za-z])", "<", s)
    s = re.sub(r"\\textgreater(?![A-Za-z])", ">", s)
    s = re.sub(r"\\chi[ \t]*\^[ \t]*\{?[ \t]*2[ \t]*\}?", "χ²", s)
    s = re.sub(r"(?<![A-Za-z])(?:χ|chi)[ \t]*\^[ \t]*\{?2\}?", "χ²", s, flags=re.IGNORECASE)
    s = re.sub(r"\\(?:,|;|:|!|quad|qquad)", " ", s)
    s = s.replace("~", " ")
    s = re.sub(r"\\[()\[\]]", " ", s)
    for _ in range(2):
        s = _LATEX_WRAPPERS.sub(r"\1", s)
    s = _SUBSCRIPT_DF.sub(r"\1(\2)", s)
    s = _SUBSCRIPT_DF_BARE.sub(r"\1(\2)", s)
    s = _MD_ITALIC_LETTER.sub(r"\1", s)
    s = re.sub(r"[$*{}]", "", s)
    s = re.sub(r"(?<![A-Za-z])\\?(?:chi-?squared?|chi2|χ2|χ²|X²|X2)(?=[ \t]*\()", "χ²", s, flags=re.IGNORECASE)
    return s


# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------

_NUM = r"-?(?:\d+\.\d+|\.\d+|\d+)"
_DF = r"\d+(?:\.\d+)?"
_STAT_PATTERNS = [
    ("t", re.compile(rf"(?<![A-Za-z])t[ \t]*\([ \t]*(?P<df1>{_DF})[ \t]*\)[ \t]*(?P<op>=|<|>)[ \t]*(?P<val>{_NUM})")),
    ("F", re.compile(
        rf"(?<![A-Za-z])F[ \t]*\([ \t]*(?P<df1>{_DF})[ \t]*,[ \t]*(?P<df2>{_DF})[ \t]*\)[ \t]*(?P<op>=|<|>)[ \t]*(?P<val>{_NUM})"
    )),
    ("r", re.compile(rf"(?<![A-Za-z])r[ \t]*\([ \t]*(?P<df1>{_DF})[ \t]*\)[ \t]*(?P<op>=|<|>)[ \t]*(?P<val>{_NUM})")),
    ("chi2", re.compile(
        rf"χ²[ \t]*\([ \t]*(?P<df1>{_DF})[ \t]*(?:,[ \t]*N[ \t]*=[ \t]*\d+[ \t]*)?\)[ \t]*(?P<op>=|<|>)[ \t]*(?P<val>{_NUM})"
    )),
    ("z", re.compile(rf"(?<![A-Za-z])[zZ][ \t]*(?P<op>=|<|>)[ \t]*(?P<val>{_NUM})")),
]
_P_VALUE = re.compile(
    r"(?<![A-Za-z])p[ \t]*(?P<op><=|>=|=|<|>|≤|≥)[ \t]*"
    r"(?P<val>(?:\d+(?:\.\d+)?|\.\d+)(?:[ \t]*(?:[eE]|[x×·][ \t]*10[ \t]*\^?)[ \t]*\(?[ \t]*-[ \t]*\d+\)?)?"
    r"|n\.?[ \t]*s\.?)",
)
_P_SCI = re.compile(r"(\d+(?:\.\d+)?|\.\d+)[ \t]*(?:[eE]|[x×·][ \t]*10[ \t]*\^?)[ \t]*\(?[ \t]*-[ \t]*(\d+)\)?")

_CORRECTION = re.compile(
    r"correct(?:ed|ion)|adjust(?:ed|ment)|bonferroni|holm|hochberg|benjamini|sidak|šidák|tukey|scheff|"
    r"\bfdr\b|\bfwe\b|false discovery|family-?wise|permut|cluster|bootstrap|monte carlo|"
    r"p[ _-]?(?:fdr|fwe|corr|adj|holm|bonf)\b",
    re.IGNORECASE,
)
_SPHERICITY = re.compile(
    r"(?:greenhouse[- \u2013]?geisser|huynh[- \u2013]?feldt|sphericity)(?:[- ]?(?:corrected|correction))?",
    re.IGNORECASE,
)
_ONE_TAILED = re.compile(r"one[- ]?tailed|one[- ]?sided|directional (?:test|hypothesis)", re.IGNORECASE)
# "x = 12, y = -40, z = 30": a coordinate triplet, not a z statistic.
_COORDINATE_BEFORE = re.compile(r"\by[ \t]*=[ \t]*-?\d[\d.]*[ \t]*,?[ \t]*$")


@dataclass
class Result:
    file: str
    line: int
    unit: str
    text: str
    test: str
    df: list
    statistic: float
    reported_p: dict
    recomputed_p: float | None = None
    recomputed_range: list = field(default_factory=list)
    tails: int = 2
    status: str = "consistent"
    label: str = ""
    note: str = ""


def _decimals(num: str) -> int:
    num = num.lstrip("-")
    return len(num.split(".", 1)[1]) if "." in num else 0


def _parse_p(op: str, raw: str):
    """Return (op, value, decimals). "n.s." is read as p > .05 with unknown decimals."""
    raw = raw.strip()
    if raw.lower().replace(".", "").replace(" ", "") == "ns":
        return ">", 0.05, None
    m = _P_SCI.fullmatch(raw)
    if m:
        mant, exp = m.group(1), int(m.group(2))
        value = float(mant) * 10.0 ** (-exp)
        decimals = _decimals(mant) + exp
        return op, value, decimals
    return op, float(raw), _decimals(raw)


def _test_label(test: str) -> str:
    return {"t": "t and df", "F": "F and df", "r": "r and df", "chi2": "χ² and df", "z": "z"}[test]


def _p_for(backend: Backend, test: str, value: float, df: list, tails: int) -> float:
    if test == "t":
        return backend.p_t(value, df[0], tails)
    if test == "F":
        return backend.p_f(value, df[0], df[1])
    if test == "r":
        return backend.p_r(value, df[0], tails)
    if test == "chi2":
        return backend.p_chi2(value, df[0])
    return backend.p_z(value, tails)


def _p_range(backend: Backend, test: str, value: float, decimals: int, df: list, tails: int):
    """(p_low, p_high) over the rounding interval of the reported statistic."""
    half = 0.5 * 10.0 ** (-decimals)
    mag = abs(value)
    lo_mag, hi_mag = max(mag - half, 0.0), mag + half
    if test == "r":
        hi_mag = min(hi_mag, 0.999999999)
    p_low = _p_for(backend, test, hi_mag, df, tails)
    p_high = _p_for(backend, test, lo_mag, df, tails)
    return min(p_low, p_high), max(p_low, p_high)


def _consistent(op: str, p_rep: float, p_dec, lo: float, hi: float) -> bool:
    if op == "=":
        half = 0.5 * 10.0 ** (-p_dec) if p_dec is not None else 0.0
        return lo <= p_rep + half + 1e-12 and hi >= p_rep - half - 1e-12
    if op in ("<",):
        return lo < p_rep
    if op in ("<=", "≤"):
        return lo <= p_rep
    if op in (">",):
        return hi > p_rep
    if op in (">=", "≥"):
        return hi >= p_rep
    return True


def _claims_significant(op: str, p_rep: float, alpha: float):
    """True / False when the reported p states (non-)significance at alpha, else None."""
    if op == "=":
        return p_rep <= alpha
    if op in ("<", "<=", "≤"):
        return True if p_rep <= alpha else None
    if op in (">", ">=", "≥"):
        return False if p_rep >= alpha else None
    return None


_SENT_END = re.compile(r"[.!?][\"')\]]*\s+(?=[A-Z])|\n[ \t]*\n")
_SENT_END_PARA = re.compile(r"[.!?][\"')\]]*\s+(?=[A-Z])|\n")


def _context(text: str, start: int, end: int, unit: str = "line") -> str:
    """The sentence holding the match plus the sentence before it.

    Corrections and one-tailed tests are usually named there ("FDR-corrected",
    "one-tailed"). In .docx text every newline ends a paragraph; in plain-text
    formats only a blank line does (soft-wrapped lines stay one sentence).
    """
    ends = _SENT_END_PARA if unit == "para" else _SENT_END
    window_start = max(0, start - 1500)
    bounds = [m.end() for m in ends.finditer(text, window_start, start)]
    left = bounds[-2] if len(bounds) >= 2 else window_start
    right_m = ends.search(text, end)
    right = right_m.start() + 1 if right_m else len(text)
    return text[left:right]


def check_text(
    text: str, source: str, backend: Backend, alpha: float = 0.05, unit: str = "line"
) -> list[Result]:
    """Check every reported statistic in `text`. `unit` names what line numbers count."""
    norm = normalize(text)
    hits = []
    taken: list[tuple[int, int]] = []
    for test, pattern in _STAT_PATTERNS:
        for m in pattern.finditer(norm):
            if any(s <= m.start() < e for s, e in taken):
                continue
            if test == "z" and _COORDINATE_BEFORE.search(norm[max(0, m.start() - 30):m.start()]):
                continue
            hits.append((m.start(), m.end(), test, m))
            taken.append((m.start(), m.end()))
    hits.sort(key=lambda h: h[0])
    results: list[Result] = []
    for i, (start, end, test, m) in enumerate(hits):
        next_start = hits[i + 1][0] if i + 1 < len(hits) else len(norm)
        window = norm[end:min(next_start, end + 120)]
        pm = _P_VALUE.search(window)
        if not pm:
            continue
        stat_text = norm[start:end + pm.end()].replace("\n", " ")
        df = [float(m.group(g)) for g in ("df1", "df2") if g in m.groupdict() and m.group(g)]
        raw_val = m.group("val")
        value = float(raw_val)
        p_op, p_val, p_dec = _parse_p(pm.group("op"), pm.group("val"))
        res = Result(
            file=source, line=line_number(norm, start), unit=unit, text=stat_text, test=test, df=df,
            statistic=value, reported_p={"op": p_op, "value": p_val, "text": pm.group(0)},
        )
        results.append(res)
        if m.group("op") != "=":
            res.status, res.label = "skipped", "statistic reported as a bound; not checked"
            continue
        context = _context(norm, start, end + pm.end(), unit)
        if _CORRECTION.search(_SPHERICITY.sub(" ", context)):
            res.status = "skipped"
            res.label = "p marked as corrected or adjusted; cannot be recomputed from the statistic alone"
            continue
        if any(d <= 0 for d in df):
            res.status, res.label = "skipped", "degrees of freedom must be positive; not checked"
            continue
        if test == "r" and abs(value) > 1:
            res.status, res.label = "inconsistent", "r outside [-1, 1]"
            continue
        dec = _decimals(raw_val)
        lo2, hi2 = _p_range(backend, test, value, dec, df, 2)
        res.recomputed_p = _p_for(backend, test, abs(value), df, 2)
        res.recomputed_range = [lo2, hi2]
        if _consistent(p_op, p_val, p_dec, lo2, hi2):
            res.status, res.label = "consistent", f"reported p matches {_test_label(test)}"
        else:
            one_tailed_ok = False
            if test in ("t", "z", "r") and _ONE_TAILED.search(context):
                lo1, hi1 = _p_range(backend, test, value, dec, df, 1)
                if _consistent(p_op, p_val, p_dec, lo1, hi1):
                    one_tailed_ok = True
                    res.tails = 1
                    res.recomputed_p = _p_for(backend, test, abs(value), df, 1)
                    res.recomputed_range = [lo1, hi1]
            if one_tailed_ok:
                res.status = "consistent"
                res.label = f"reported p matches {_test_label(test)} (one-tailed, as stated)"
            else:
                claimed = _claims_significant(p_op, p_val, alpha)
                flips = (claimed is True and lo2 >= alpha) or (claimed is False and hi2 < alpha)
                res.status = "decision-error" if flips else "inconsistent"
                res.label = f"reported p does not match {_test_label(test)}"
                if flips:
                    res.note = f"the difference changes significance at alpha = {alpha:g}"
        if p_op == "=" and p_val == 0:
            res.note = (res.note + "; " if res.note else "") + "report p = 0 as p < .001"
    return results


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _fmt_p(p: float | None) -> str:
    if p is None:
        return "-"
    if p < 0.0001:
        return f"{p:.2e}"
    return f"{p:.4f}"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        description="Recompute p-values from reported t, F, r, chi2 and z statistics and flag mismatches."
    )
    ap.add_argument("paths", nargs="+", help="manuscript files or folders; '-' reads stdin")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    ap.add_argument("--alpha", type=float, default=0.05, help="significance level for decision errors (default 0.05)")
    ap.add_argument("--backend", choices=("auto", "stdlib", "scipy"), default="auto",
                    help="distribution functions: scipy if installed (auto), or the stdlib implementation")
    args = ap.parse_args(argv)
    configure_utf8_stdio()

    try:
        backend = Backend(args.backend)
    except RuntimeError as exc:
        print(f"statcheck: {exc}", file=sys.stderr)
        return 2

    results: list[Result] = []
    try:
        for raw in args.paths:
            if raw == "-":
                results.extend(check_text(sys.stdin.read(), "<stdin>", backend, args.alpha))
                continue
            files = iter_files([raw], INPUT_EXTS)
            if not files:
                print(f"statcheck: no manuscript files under {raw}", file=sys.stderr)
            for f in files:
                if not f.exists():
                    print(f"statcheck: {f} does not exist", file=sys.stderr)
                    return 2
                is_docx = f.suffix.lower() == ".docx"
                text = strip_comments(read_text(f), f.suffix)
                results.extend(check_text(text, str(f), backend, args.alpha, "para" if is_docx else "line"))
    except DocumentError as exc:
        print(f"statcheck: {exc}", file=sys.stderr)
        return 2

    counts = {k: sum(1 for r in results if r.status == k)
              for k in ("consistent", "inconsistent", "decision-error", "skipped")}
    bad = counts["inconsistent"] + counts["decision-error"]

    if args.json:
        print(json.dumps({"backend": backend.name, "alpha": args.alpha, "summary": counts,
                          "results": [asdict(r) for r in results]}, ensure_ascii=False, indent=1))
    else:
        if not results:
            print("statcheck: no reported test statistics with a p-value found.")
        for r in results:
            flag = {"consistent": "ok  ", "skipped": "skip", "inconsistent": "FLAG",
                    "decision-error": "FLAG"}[r.status]
            extra = f" (recomputed p = {_fmt_p(r.recomputed_p)})" if r.recomputed_p is not None else ""
            note = f"; {r.note}" if r.note else ""
            where = f"{r.file}:{r.line}" if r.unit == "line" else f"{r.file} para {r.line}"
            print(f"{flag} {where}  {r.text}  -> {r.label}{extra}{note}")
        if results:
            print(
                f"\nSummary: {counts['consistent']} match, {counts['inconsistent']} do not match, "
                f"{counts['decision-error']} do not match and change significance, "
                f"{counts['skipped']} skipped (backend: {backend.name})."
            )
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
