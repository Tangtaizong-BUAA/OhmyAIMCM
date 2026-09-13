#!/usr/bin/env python3
"""Render completed Markdown to editable LaTeX and an audited CUMCM PDF."""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

from _runtime import (
    TypesetterError,
    add_content_lock_markers,
    analyze_source,
    canonical_json_bytes,
    compile_tex,
    copy_runtime_assets,
    load_config,
    materialize_images,
    prepare_output_dir,
    prepare_ai_declaration,
    print_json,
    render_ast_with_declaration,
    render_config_tex,
    render_tex,
    sha256_bytes,
    sha256_file,
    tool_version,
    verify_output,
    write_json,
)


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("input", type=Path, help="completed Markdown paper")
    result.add_argument("--output-dir", type=Path, required=True, help="standalone delivery directory")
    result.add_argument("--config", type=Path, help="JSON override merged over the safe defaults")
    result.add_argument("--rules", type=Path, help="official compliance JSON or a rules object")
    result.add_argument("--style-tokens", type=Path, help="controlled style-token JSON or profile")
    result.add_argument(
        "--semantic-policy",
        type=Path,
        help="validated corpus-model policy containing a bounded runtime projection",
    )
    result.add_argument(
        "--ai-usage",
        required=True,
        choices=("used", "not_used"),
        help="explicit declaration; the runtime never infers this state",
    )
    result.add_argument("--ai-summary", help="required purpose/stage summary when AI was used")
    result.add_argument("--ai-support-pdf", type=Path, help="required AI工具使用详情.pdf when AI was used")
    result.add_argument("--no-compile", action="store_true", help="emit editable TeX without building PDF")
    result.add_argument("--force", action="store_true", help="replace only known generated files")
    result.add_argument("--no-previews", action="store_true", help="skip full-PDF PNG previews; the audit records missing preview coverage")
    return result


def main() -> int:
    args = parser().parse_args()
    started = time.monotonic()
    try:
        source = args.input.resolve()
        config = load_config(
            args.config,
            rules_path=args.rules,
            style_tokens_path=args.style_tokens,
            semantic_policy_path=args.semantic_policy,
        )
        source_ast, analysis = analyze_source(source, config)
        if not analysis["ready_to_render"]:
            print_json(analysis)
            return 2
        # Validate the explicit declaration before writing any output.  The
        # support PDF is staged after all policy checks succeed.
        if args.ai_usage == "used":
            if not args.ai_summary or len(" ".join(args.ai_summary.split())) < 10:
                raise TypesetterError("--ai-summary must explain the AI purpose/stage when --ai-usage=used")
            if args.ai_support_pdf is None:
                raise TypesetterError("--ai-support-pdf is required when --ai-usage=used")
        elif args.ai_summary or args.ai_support_pdf is not None:
            raise TypesetterError("AI summary/support PDF must be omitted when --ai-usage=not_used")
        output_dir = prepare_output_dir(args.output_dir, args.force)
        copy_runtime_assets(output_dir)
        write_json(output_dir / "effective-config.json", config)
        write_json(output_dir / "input.ast.json", source_ast)
        render_input_ast, assets_manifest = materialize_images(source_ast, source, output_dir)
        write_json(output_dir / "render-input.ast.json", render_input_ast)
        write_json(output_dir / "assets-manifest.json", assets_manifest)
        (output_dir / "render-config.tex").write_text(render_config_tex(config), encoding="utf-8")
        ai_declaration = prepare_ai_declaration(
            state=args.ai_usage,
            summary=args.ai_summary,
            support_pdf=args.ai_support_pdf,
            output_dir=output_dir,
        )

        render_ast_with_declaration(
            output_dir / "render-input.ast.json",
            output_dir / "rendered.ast.json",
            output_dir / "semantic.lua",
            source.parent,
            ai_usage=args.ai_usage,
            ai_summary=ai_declaration["summary"],
        )
        rendered_ast = json.loads((output_dir / "rendered.ast.json").read_text(encoding="utf-8"))
        source_ast_hash = sha256_bytes(canonical_json_bytes(source_ast))
        rendered_ast_hash = sha256_bytes(canonical_json_bytes(rendered_ast))
        tex_path = output_dir / "paper.tex"
        render_tex(
            output_dir / "rendered.ast.json",
            tex_path,
            output_dir / "render-config.tex",
            source.parent,
            number_sections=(
                config["style_tokens"]["section_numbering_style"] != "none"
            ),
        )
        add_content_lock_markers(tex_path, source_ast_hash, rendered_ast_hash)
        content_lock = {
            "schema_version": 1,
            "source_path": str(source),
            "source_sha256": sha256_file(source),
            "source_ast_sha256": source_ast_hash,
            "render_input_ast_sha256": sha256_bytes(canonical_json_bytes(render_input_ast)),
            "rendered_ast_sha256": rendered_ast_hash,
            "assets_manifest_sha256": sha256_file(output_dir / "assets-manifest.json"),
            "ai_declaration_sha256": sha256_file(output_dir / "ai-declaration.json"),
            "tex_sha256_at_build": sha256_file(tex_path),
            "contract": "paper.tex was generated only from input.ast.json through semantic.lua; raw TeX is disabled by default",
        }
        write_json(output_dir / "content-lock.json", content_lock)

        compile_report = None
        audit = None
        if not args.no_compile:
            compile_report = compile_tex(tex_path, output_dir, source.parent)
            audit = verify_output(output_dir, render_previews=not args.no_previews)
            write_json(output_dir / "layout-audit.json", audit)

        report = {
            "schema_version": 1,
            "status": "tex-only" if args.no_compile else audit["status"],
            "status_scope": "tex_generation_only" if args.no_compile else audit["status_scope"],
            "review_status": "pending_visual_and_semantic_review",
            "source": str(source),
            "output_dir": str(output_dir),
            "analysis": analysis,
            "content_lock": content_lock,
            "ai_declaration": ai_declaration,
            "compile": compile_report,
            "audit_summary": None
            if audit is None
            else {
                "status": audit["status"],
                "status_scope": audit["status_scope"],
                "review_status": audit["review_status"],
                "review_scope": audit["review_scope"],
                "finding_counts": audit["finding_counts"],
                "metrics": audit["metrics"],
            },
            "tools": {
                "pandoc": tool_version("pandoc"),
                "latexmk": tool_version("latexmk"),
                "xelatex": tool_version("xelatex"),
                "pdftotext": tool_version("pdftotext"),
            },
            "duration_seconds": round(time.monotonic() - started, 3),
        }
        write_json(output_dir / "build-report.json", report)
        print_json(report)
        return 0 if args.no_compile or audit["status"] == "pass" else 3
    except TypesetterError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
