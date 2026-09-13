#!/usr/bin/env python3
"""End-to-end compile smoke test for the runtime skill."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


TEST_DIR = Path(__file__).resolve().parent
SKILL_DIR = TEST_DIR.parent
FIXTURE_DIR = TEST_DIR / "fixtures"


def main() -> int:
    for tool in ("pandoc", "latexmk", "xelatex", "pdftotext", "pdftoppm"):
        if not shutil.which(tool):
            print(f"missing required smoke-test tool: {tool}", file=sys.stderr)
            return 2
    with tempfile.TemporaryDirectory(prefix="OhmyAIMCM-runtime-smoke-") as raw_tmp:
        tmp = Path(raw_tmp)
        support_work = tmp / "support"
        support_work.mkdir()
        subprocess.run(
            [
                "xelatex",
                "-interaction=nonstopmode",
                "-halt-on-error",
                f"-output-directory={support_work}",
                str(FIXTURE_DIR / "ai-support.tex"),
            ],
            cwd=FIXTURE_DIR,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        support_pdf = tmp / "AI工具使用详情.pdf"
        shutil.copy2(support_work / "ai-support.pdf", support_pdf)
        output = tmp / "delivery"
        command = [
            sys.executable,
            str(SKILL_DIR / "scripts" / "render.py"),
            str(FIXTURE_DIR / "smoke-paper.md"),
            "--output-dir",
            str(output),
            "--rules",
            str(SKILL_DIR / "references" / "compliance-2026.json"),
            "--style-tokens",
            str(SKILL_DIR / "assets" / "latex" / "balanced-cn.json"),
            "--ai-usage",
            "used",
            "--ai-summary",
            "使用确定性排版工具生成 LaTeX 并核验 PDF，全部学术内容由测试样例提供",
            "--ai-support-pdf",
            str(support_pdf),
        ]
        completed = subprocess.run(command, check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if completed.returncode:
            sys.stderr.write(completed.stderr.decode("utf-8", errors="replace"))
            sys.stderr.write(completed.stdout.decode("utf-8", errors="replace"))
            return completed.returncode
        report = json.loads((output / "build-report.json").read_text(encoding="utf-8"))
        assert report["status"] == "pass", report
        assert (output / "paper.tex").is_file()
        assert (output / "paper.pdf").is_file()
        assert (output / "layout-audit.json").is_file()
        assert (output / "previews" / "page-1.png").is_file()
        audit = json.loads((output / "layout-audit.json").read_text(encoding="utf-8"))
        assert report["status_scope"] == "mechanical_checks_only"
        assert report["audit_summary"]["review_scope"] == audit["review_scope"]
        assert audit["review_scope"]["previews"]["rendered_pages"] == list(range(1, audit["metrics"]["page_count"] + 1))
        assert audit["review_scope"]["visual"]["status"] == "not_performed"
        assert audit["review_scope"]["semantic"]["status"] == "not_performed"
        print(json.dumps(report["audit_summary"], ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
