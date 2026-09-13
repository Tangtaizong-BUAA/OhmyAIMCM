#!/usr/bin/env python3
"""Real Pandoc/XeLaTeX regressions; raw page setup belongs to fixtures only."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SKILL_DIR / "scripts"))

from _runtime import _page_texts, _render_previews, load_config, render_config_tex  # noqa: E402


SHORT_TABLE = r"""
\noindent BEFORE-SHORT-PAGE

\vspace*{0.80\textheight}

| Identifier | Value |
|:-----------|------:|
| SHORTROW01[^shortnote] | $x_1=1$ |
| SHORTROW02 | 2 |
| SHORTROW03 | 3 |
| SHORTROW04 | 4 |
| SHORTROW05 | 5 |
| SHORTROW06 | 6 |
| SHORTROW07 | 7 |
| SHORTROW08 | 8 |

Table: Short table caption

[^shortnote]: SHORTFOOTNOTE preserved once at the page foot.

AFTER-SHORT-TABLE. Table reference: \ref{tbl-short}.
"""


def run_checked(command: list[str], *, cwd: Path, env: dict | None = None) -> bytes:
    completed = subprocess.run(
        command, cwd=cwd, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT
    )
    if completed.returncode:
        raise AssertionError(completed.stdout.decode("utf-8", errors="replace")[-12000:])
    return completed.stdout


def build_fixture(output: Path, *, guarded: bool, full: bool) -> Path:
    output.mkdir(parents=True)
    source = SHORT_TABLE
    if full:
        source += "\n\\newpage\n\n| Identifier | Value |\n|:---|---:|\n"
        source += "\n".join(f"| LONGROW{index:03} | {index} |" for index in range(1, 91))
        source += "\n\nTable: Long table caption\n\n\\newpage\n\n"
        source += "| Identifier | Wrapped content |\n|:---|:---|\n"
        source += "\n".join(
            f"| LONGCELL{index:02} | {'wrapword ' * 100} CELLEND{index:02} |"
            for index in range(1, 7)
        )
        source += "\n\nTable: Long cell table caption\n\n\\newpage\n\n"
        source += "| Identifier | Value |\n|:---|---:|\n"
        source += "\n".join(f"| STREAMROW{index:03} | {index} |" for index in range(1, 251))
        source += "\n\nTable: Streamed table caption\n\nAFTER-ALL-TABLES\n"
    source_path = output / "fixture.md"
    source_path.write_text(source, encoding="utf-8")
    ast = json.loads(run_checked(["pandoc", str(source_path), "-t", "json"], cwd=output))
    tables = [block for block in ast["blocks"] if block["t"] == "Table"]
    tables[0]["c"][0][0] = "tbl-short"
    if full:
        # Force real paragraph columns for the few-row, many-wrapped-lines case.
        for spec, width in zip(tables[2]["c"][2], (0.20, 0.80)):
            spec[1] = {"t": "ColWidth", "c": width}
    ast_path = output / "fixture.json"
    ast_path.write_text(json.dumps(ast), encoding="utf-8")
    header = render_config_tex(load_config(None))
    if not guarded:
        header += "\n\\makeatletter\\let\\OhmyAIMCM@guardCompletedTable\\relax\\makeatother\n"
    header_path = output / "render-config.tex"
    header_path.write_text(header, encoding="utf-8")
    for name in ("OhmyAIMCM-paper.cls", "OhmyAIMCM-style.sty"):
        shutil.copy2(SKILL_DIR / "assets/latex" / name, output / name)
    run_checked(
        ["pandoc", str(ast_path), "-f", "json", "-t", "latex", "-s",
         "-V", "documentclass:OhmyAIMCM-paper", f"--include-in-header={header_path}",
         "-o", str(output / "paper.tex")],
        cwd=output,
    )
    env = os.environ.copy()
    env["TEXINPUTS"] = str(output) + os.pathsep + env.get("TEXINPUTS", "")
    run_checked(
        ["latexmk", "-xelatex", "-interaction=nonstopmode", "-halt-on-error",
         "-file-line-error", "paper.tex"], cwd=output, env=env,
    )
    return output / "paper.pdf"


@unittest.skipUnless(
    all(shutil.which(tool) for tool in ("pandoc", "xelatex", "latexmk", "pdftotext", "pdftoppm")),
    "requires the real Pandoc/XeLaTeX/Poppler toolchain",
)
class TablePaginationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.tmp = tempfile.TemporaryDirectory(prefix="OhmyAIMCM-table-regression-")
        cls.root = Path(cls.tmp.name)
        cls.pdf = build_fixture(cls.root / "guarded", guarded=True, full=True)
        cls.pages = _page_texts(cls.pdf)
        cls.baseline = _page_texts(build_fixture(cls.root / "baseline", guarded=False, full=False))

    @classmethod
    def tearDownClass(cls) -> None:
        cls.tmp.cleanup()

    def pages_for(self, marker: str, pages: list[str] | None = None) -> list[int]:
        return [index for index, text in enumerate(self.pages if pages is None else pages, 1) if marker in text]

    def test_short_table_moves_intact_after_a_real_split_in_the_baseline(self) -> None:
        baseline_pages = {page for index in range(1, 9) for page in self.pages_for(f"SHORTROW{index:02}", self.baseline)}
        self.assertGreater(len(baseline_pages), 1, "fixture must reproduce a real split without the guard")
        table_pages = {page for index in range(1, 9) for page in self.pages_for(f"SHORTROW{index:02}")}
        self.assertEqual(len(table_pages), 1)
        self.assertGreater(min(table_pages), self.pages_for("BEFORE-SHORT-PAGE")[0])
        self.assertEqual(self.pages_for("Short table caption"), sorted(table_pages))
        self.assertEqual(self.pages_for("SHORTFOOTNOTE"), sorted(table_pages))

    def test_caption_label_number_and_footnote_are_not_duplicated(self) -> None:
        text = "\n".join(self.pages)
        self.assertEqual(text.count("SHORTFOOTNOTE"), 1)
        self.assertEqual(text.count("Short table caption"), 1)
        self.assertRegex(text, r"Table reference:\s*1\.")
        self.assertRegex(text, r"表\s*1\s+Short table caption")
        self.assertRegex(text, r"表\s*2\s+Long table caption")

    def test_default_caption_is_centered_in_actual_pdf(self) -> None:
        root = ET.fromstring(run_checked(["pdftotext", "-bbox-layout", str(self.pdf), "-"], cwd=self.root))
        ns = {"h": "http://www.w3.org/1999/xhtml"}
        found = []
        for page in root.findall(".//h:page", ns):
            for line in page.findall(".//h:line", ns):
                words = " ".join(word.text or "" for word in line.findall("h:word", ns))
                if "Short table caption" in words:
                    center = (float(line.attrib["xMin"]) + float(line.attrib["xMax"])) / 2
                    found.append(center - float(page.attrib["width"]) / 2)
        self.assertEqual(len(found), 1)
        self.assertLess(abs(found[0]), 1.0, f"caption not centered: {found[0]} pt")

    def test_long_and_streamed_tables_remain_breakable_without_losing_rows(self) -> None:
        for prefix, count in (("LONGROW", 90), ("STREAMROW", 250)):
            occupied = set()
            for index in range(1, count + 1):
                found = self.pages_for(f"{prefix}{index:03}")
                self.assertEqual(len(found), 1, f"missing/duplicate row {prefix}{index:03}")
                occupied.update(found)
            self.assertGreater(len(occupied), 1)
        text = "\n".join(self.pages)
        self.assertEqual(text.count("AFTER-ALL-TABLES"), 1)

    def test_few_rows_with_long_cells_use_measured_height_fallback(self) -> None:
        occupied = set()
        for index in range(1, 7):
            found = self.pages_for(f"LONGCELL{index:02}")
            self.assertEqual(len(found), 1)
            self.assertEqual(self.pages_for(f"CELLEND{index:02}"), found)
            occupied.update(found)
        self.assertGreater(len(occupied), 1)
        self.assertEqual("\n".join(self.pages).count("wrapword"), 600)

    def test_no_overflow_or_undefined_references(self) -> None:
        log = (self.pdf.parent / "paper.log").read_text(encoding="utf-8")
        self.assertNotRegex(log, r"Overfull \\[hv]box")
        self.assertNotRegex(log, r"(?:Reference|Citation) `[^']+'[^\n]*undefined")
        self.assertIn("table=1 mode=keep", log)
        self.assertIn("table=2 mode=breakable", log)
        self.assertIn("table=3 mode=breakable", log)
        self.assertIn("table=4 mode=streamed", log)

    def test_previews_cover_the_whole_pdf_and_do_not_count_stale_pages(self) -> None:
        preview_dir = self.root / "previews"
        preview_dir.mkdir()
        (preview_dir / "page-999.png").write_bytes(b"stale generated preview")
        (preview_dir / "keep.png").write_bytes(b"unrelated image")
        previews = _render_previews(self.pdf, preview_dir)
        self.assertEqual(
            [Path(path).name for path in previews],
            [f"page-{index}.png" for index in range(1, len(self.pages) + 1)],
        )
        self.assertGreater(len(previews), 2)
        self.assertFalse((preview_dir / "page-999.png").exists())
        self.assertTrue((preview_dir / "keep.png").exists())
        prefix = _render_previews(self.pdf, preview_dir, pages=2)
        self.assertEqual([Path(path).name for path in prefix], ["page-1.png", "page-2.png"])
        self.assertEqual(len(list(preview_dir.glob("page-*.png"))), 2)


if __name__ == "__main__":
    unittest.main()
