#!/usr/bin/env python3

from __future__ import annotations

import copy
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SKILL_DIR / "scripts"))

from _runtime import (  # noqa: E402
    _audit_report,
    TypesetterError,
    load_config,
    normalize_for_compare,
    pandoc_ast,
    prepare_ai_declaration,
    render_config_tex,
    stringify_pandoc,
    verify_output,
)


class ConfigTests(unittest.TestCase):
    def test_owner_default_is_journal_projection_without_claiming_v2(self):
        config = load_config(None)
        explicit = load_config(None, semantic_policy_path=SKILL_DIR / "assets/models/semantic-layout-policy-v1.json")
        self.assertEqual(config, explicit)
        self.assertEqual(config["style_tokens"]["line_height_ratio"], 1.25)
        self.assertEqual(config["style_tokens"]["section_numbering_style"], "arabic")
        self.assertEqual(config["style_tokens"]["h1_alignment"], "left_aligned")
        self.assertIn("legacy_unverified_v1", json.dumps(config["model_policy"]))
        self.assertEqual(config["style_tokens"]["table_caption_alignment"], "centered")
        self.assertEqual(config["owner_style_overrides"][0]["base_value"], "left_aligned")
        self.assertEqual(config["owner_style_overrides"][0]["evidence_class"], "explicit_preference_not_learned")
        original = json.loads((SKILL_DIR / "assets/models/semantic-layout-policy-v1.json").read_text())
        self.assertEqual(original["runtime_projection"]["style_tokens"]["captions"]["table_alignment"], "left_aligned")

    def test_explicit_custom_caption_choice_is_not_overridden(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "config.json"
            path.write_text(json.dumps({"style_tokens": {"table_caption_alignment": "left_aligned"}}))
            config = load_config(path)
        self.assertEqual(config["style_tokens"]["table_caption_alignment"], "left_aligned")
        self.assertNotIn("owner_style_overrides", config)

    def test_explicit_balanced_style_still_available(self):
        config = load_config(None, style_tokens_path=SKILL_DIR / "assets/latex/balanced-cn.json")
        self.assertEqual(config["style_tokens"]["line_height_ratio"], 1.44)
        self.assertNotIn("model_policy", config)

    def test_missing_explicit_policy_does_not_fall_back(self):
        with self.assertRaises(TypesetterError):
            load_config(None, semantic_policy_path=SKILL_DIR / "assets/models/missing-policy.json")

    @staticmethod
    def _canonical_hash(value: object) -> str:
        raw = json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
        return hashlib.sha256(raw).hexdigest()

    def _compiled_v2_policy(self) -> dict:
        legacy = json.loads(
            (
                SKILL_DIR
                / "assets"
                / "models"
                / "semantic-layout-policy-v1.json"
            ).read_text(encoding="utf-8")
        )
        source_hash = "a" * 64
        payload = {
            "schema_version": "2.0.0",
            "policy_type": "journal_semantic_layout_projection_v2",
            "compiler": {
                "name": "layout_lab.runtime_policy_compiler",
                "version": "1.0.0",
            },
            "policy_id": "journal-consensus-cn-test",
            "source_model_id": "e" * 64,
            "source_artifact": {
                "sha256": source_hash,
                "canonical_sha256": "b" * 64,
            },
            "source_admission": {
                "status": "validated_consensus_robust",
                "runtime_export_eligible": True,
                "consensus_transferable": True,
            },
            "status": "compiled_validated_consensus",
            "runtime_export_eligible": True,
            "fallback_profile": "balanced-cn",
            "semantic_scope": "structure_and_relational_semantics",
            "selected_factor_ids": ["numeric:body_paragraph:leading_ratio"],
            "rule_provenance": [
                {
                    "rule_id": "test-rule",
                    "provenance_class": "learned_factor",
                    "factor_id": "numeric:body_paragraph:leading_ratio",
                    "token_paths": ["body.leading_ratio"],
                },
                {
                    "rule_id": "test-hard-boundaries",
                    "provenance_class": "hard_constraint",
                    "constraint_id": "test-fixture-only",
                    "token_paths": [
                        "page.*",
                        "body.font_size_pt",
                        "body.cjk_font",
                        "body.latin_font",
                        "body.math_font",
                        "title.*",
                        "abstract.*",
                        "headings.*",
                        "captions.*",
                        "math.*",
                        "paragraphs.*",
                        "flow.*",
                    ],
                },
            ],
            "runtime_projection": copy.deepcopy(legacy["runtime_projection"]),
        }
        payload["runtime_projection"]["profile_id"] = "journal-consensus-cn-test"
        payload["runtime_projection"]["style_tokens"][
            "profile_id"
        ] = "journal-consensus-cn-test"
        style_hash = self._canonical_hash(
            payload["runtime_projection"]["style_tokens"]
        )
        quality_hash = self._canonical_hash(
            payload["runtime_projection"]["quality_targets"]
        )
        payload_hash = self._canonical_hash(payload)
        veto = {
            "status": "accepted",
            "training_eligible": False,
            "pair_id": "test-pair",
            "accepted_policy_id": payload["policy_id"],
            "accepted_runtime_profile_id": payload["runtime_projection"]["profile_id"],
            "accepted_policy_payload_sha256": payload_hash,
            "accepted_style_tokens_sha256": style_hash,
            "accepted_quality_targets_sha256": quality_hash,
            "accepted_source_artifact_sha256": source_hash,
        }
        return {
            **payload,
            "human_veto": veto,
            "integrity": {
                "algorithm": "sha256-canonical-json-v1",
                "compiler_name": "layout_lab.runtime_policy_compiler",
                "compiler_version": "1.0.0",
                "accepted_policy_payload_sha256": payload_hash,
                "accepted_style_tokens_sha256": style_hash,
                "accepted_quality_targets_sha256": quality_hash,
                "accepted_source_artifact_sha256": source_hash,
                "human_veto_sha256": self._canonical_hash(veto),
            },
        }

    def _load_temp_semantic_policy(self, policy: dict) -> dict:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "policy.json"
            path.write_text(json.dumps(policy), encoding="utf-8")
            return load_config(None, semantic_policy_path=path)

    def test_default_config_is_valid(self) -> None:
        config = load_config(None)
        self.assertEqual(config["rules"]["paper_size"], "a4")
        self.assertGreaterEqual(config["style_tokens"]["margin_left_mm"], 25)

    def test_official_rules_adapter(self) -> None:
        rules = SKILL_DIR / "references" / "compliance-2026.json"
        config = load_config(None, rules_path=rules)
        self.assertEqual(config["rules"]["pdf_max_bytes"], 20 * 1024 * 1024)
        self.assertFalse(config["rules"]["allow_toc"])

    def test_canonical_style_tokens_drive_advanced_controls(self) -> None:
        profile = SKILL_DIR / "assets" / "latex" / "balanced-cn.json"
        config = load_config(None, style_tokens_path=profile)
        rendered = render_config_tex(config)
        self.assertIn("\\cumcmApplyHeadingStyle", rendered)
        self.assertIn("\\cumcmApplyMathStyle", rendered)
        self.assertIn("texgyretermes-math.otf", rendered)

    def test_hybrid_profile_drives_the_complete_visual_system(self) -> None:
        profile = SKILL_DIR / "assets" / "latex" / "hybrid-cn.json"
        config = load_config(None, style_tokens_path=profile)
        style = config["style_tokens"]
        rendered = render_config_tex(config)

        self.assertEqual(style["title_font_role"], "sans")
        self.assertEqual(style["h1_alignment"], "left_aligned")
        self.assertEqual(style["section_numbering_style"], "arabic")
        self.assertEqual(style["table_caption_alignment"], "left_aligned")
        self.assertIn("\\cumcmApplyRoleStyle{sans}{centered}{1.4500}", rendered)
        self.assertIn("\\cumcmApplyNumbering{arabic}", rendered)
        self.assertIn("\\cumcmApplyCaptionStyle{0.8400}{centering}{raggedright}", rendered)

    def test_validated_semantic_policy_drives_bounded_projection(self) -> None:
        policy = (
            SKILL_DIR
            / "assets"
            / "models"
            / "semantic-layout-policy-v1.json"
        )
        config = load_config(None, semantic_policy_path=policy)
        style = config["style_tokens"]
        binding = config["model_policy"]

        self.assertEqual(binding["status"], "validated_core_robust")
        self.assertEqual(binding["semantic_scope"], "structure_role_only")
        self.assertEqual(binding["human_veto_status"], "accepted")
        self.assertEqual(binding["human_veto_pair_id"], "frb-calibration-06")
        self.assertEqual(binding["human_veto_decision"], "left_better")
        self.assertEqual(binding["integrity_status"], "legacy_unverified_v1")
        self.assertFalse(binding["automatic_promotion_eligible"])
        self.assertEqual(style["line_height_ratio"], 1.25)
        self.assertEqual(style["title_size_ratio"], 1.6)
        self.assertEqual(style["caption_font_ratio"], 0.8)

    def test_content_addressed_v2_policy_is_verified_before_use(self) -> None:
        config = self._load_temp_semantic_policy(self._compiled_v2_policy())
        binding = config["model_policy"]
        self.assertEqual(binding["integrity_status"], "verified_content_addressed_v2")
        self.assertTrue(binding["automatic_promotion_eligible"])
        self.assertEqual(
            binding["quality_targets"]["text_occupied_bbox_area_ratio"],
            0.69654188,
        )
        self.assertEqual(binding["rule_provenance"][0]["rule_id"], "test-rule")
        self.assertEqual(
            binding["selected_factor_ids"],
            ["numeric:body_paragraph:leading_ratio"],
        )
        self.assertEqual(binding["compiler"]["version"], "1.0.0")
        self.assertEqual(len(binding["quality_targets_sha256"]), 64)

    def test_v2_policy_rejects_style_token_tampering(self) -> None:
        policy = self._compiled_v2_policy()
        policy["runtime_projection"]["style_tokens"]["body"]["leading_ratio"] = 1.3
        with self.assertRaisesRegex(TypesetterError, "payload integrity mismatch"):
            self._load_temp_semantic_policy(policy)

    def test_v2_policy_rejects_source_binding_tampering(self) -> None:
        policy = self._compiled_v2_policy()
        policy["source_artifact"]["sha256"] = "c" * 64
        with self.assertRaisesRegex(TypesetterError, "payload integrity mismatch"):
            self._load_temp_semantic_policy(policy)

    def test_v2_policy_rejects_non_hash_source_model_identity(self) -> None:
        policy = self._compiled_v2_policy()
        policy["source_model_id"] = "forged-model-id"
        with self.assertRaisesRegex(TypesetterError, "source research model identity"):
            self._load_temp_semantic_policy(policy)

    def test_v2_policy_rejects_human_veto_binding_tampering(self) -> None:
        policy = self._compiled_v2_policy()
        policy["human_veto"]["accepted_style_tokens_sha256"] = "d" * 64
        with self.assertRaisesRegex(TypesetterError, "human veto integrity mismatch"):
            self._load_temp_semantic_policy(policy)

    def test_v2_policy_rejects_independently_unaccepted_quality_target(self) -> None:
        policy = self._compiled_v2_policy()
        policy["runtime_projection"]["quality_targets"][
            "text_occupied_bbox_area_ratio"
        ] = 0.75
        payload = {
            key: value
            for key, value in policy.items()
            if key not in {"human_veto", "integrity"}
        }
        payload_hash = self._canonical_hash(payload)
        policy["integrity"]["accepted_policy_payload_sha256"] = payload_hash
        policy["human_veto"]["accepted_policy_payload_sha256"] = payload_hash
        policy["integrity"]["human_veto_sha256"] = self._canonical_hash(
            policy["human_veto"]
        )
        with self.assertRaisesRegex(TypesetterError, "quality target integrity mismatch"):
            self._load_temp_semantic_policy(policy)

    def test_v2_policy_rejects_style_token_without_provenance_owner(self) -> None:
        policy = self._compiled_v2_policy()
        policy["rule_provenance"][1]["token_paths"].remove("flow.*")
        with self.assertRaisesRegex(TypesetterError, "lack provenance ownership"):
            self._load_temp_semantic_policy(policy)

    def test_v2_policy_rejects_overlapping_provenance_owners(self) -> None:
        policy = self._compiled_v2_policy()
        policy["rule_provenance"][1]["token_paths"].append("body.leading_ratio")
        with self.assertRaisesRegex(TypesetterError, "overlapping provenance ownership"):
            self._load_temp_semantic_policy(policy)

    def test_semantic_policy_fails_closed_on_unvalidated_status(self) -> None:
        import tempfile

        policy_path = (
            SKILL_DIR
            / "assets"
            / "models"
            / "semantic-layout-policy-v1.json"
        )
        policy = json.loads(policy_path.read_text(encoding="utf-8"))
        policy["status"] = "research_candidate"
        with tempfile.TemporaryDirectory() as tmp:
            invalid = Path(tmp) / "invalid-policy.json"
            invalid.write_text(json.dumps(policy), encoding="utf-8")
            with self.assertRaisesRegex(TypesetterError, "repeated-split"):
                load_config(None, semantic_policy_path=invalid)

    def test_semantic_policy_fails_closed_without_accepted_human_veto(self) -> None:
        import tempfile

        policy_path = (
            SKILL_DIR
            / "assets"
            / "models"
            / "semantic-layout-policy-v1.json"
        )
        policy = json.loads(policy_path.read_text(encoding="utf-8"))
        policy["human_veto"]["status"] = "pending"
        with tempfile.TemporaryDirectory() as tmp:
            invalid = Path(tmp) / "invalid-policy.json"
            invalid.write_text(json.dumps(policy), encoding="utf-8")
            with self.assertRaisesRegex(TypesetterError, "human aesthetic veto"):
                load_config(None, semantic_policy_path=invalid)

    def test_semantic_policy_fails_closed_on_veto_evidence_hash_drift(self) -> None:
        import tempfile

        policy_path = (
            SKILL_DIR
            / "assets"
            / "models"
            / "semantic-layout-policy-v1.json"
        )
        policy = json.loads(policy_path.read_text(encoding="utf-8"))
        policy["human_veto"]["preference_record_sha256"] = "not-a-hash"
        with tempfile.TemporaryDirectory() as tmp:
            invalid = Path(tmp) / "invalid-policy.json"
            invalid.write_text(json.dumps(policy), encoding="utf-8")
            with self.assertRaisesRegex(TypesetterError, "evidence hashes"):
                load_config(None, semantic_policy_path=invalid)

    def test_semantic_policy_and_manual_style_are_mutually_exclusive(self) -> None:
        policy = (
            SKILL_DIR
            / "assets"
            / "models"
            / "semantic-layout-policy-v1.json"
        )
        profile = SKILL_DIR / "assets" / "latex" / "hybrid-cn.json"
        with self.assertRaisesRegex(TypesetterError, "either"):
            load_config(
                None,
                style_tokens_path=profile,
                semantic_policy_path=policy,
            )

    def test_unindented_paragraphs_require_visible_separation(self) -> None:
        import tempfile

        profile = json.loads(
            (SKILL_DIR / "assets" / "latex" / "hybrid-cn.json").read_text(
                encoding="utf-8"
            )
        )
        profile["paragraphs"]["indent_em"] = 0
        profile["paragraphs"]["paragraph_skip_em"] = 0
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "invalid.json"
            path.write_text(json.dumps(profile), encoding="utf-8")
            with self.assertRaisesRegex(TypesetterError, "PARAGRAPH_SEPARATION"):
                load_config(None, style_tokens_path=path)

    def test_paragraph_indent_token_survives_ctex_initialization(self) -> None:
        style = (SKILL_DIR / "assets" / "latex" / "cumcm-style.sty").read_text(
            encoding="utf-8"
        )
        self.assertIn("\\renewcommand{\\cumcmParagraphIndent}{#7}", style)
        self.assertIn(
            "\\AtBeginDocument{%\n  \\color{cumcmInk}%\n"
            "  \\fontsize{\\cumcmBodyFontSize pt}{\\cumcmBodyLeading pt}\\selectfont\n"
            "  % ctexart initializes its paragraph layout at begin-document time.",
            style,
        )
        self.assertGreaterEqual(
            style.count("\\setlength{\\parindent}{\\cumcmParagraphIndent em}"),
            2,
        )


class AstTests(unittest.TestCase):
    def test_stringifier_does_not_leak_alignment_types(self) -> None:
        fixture = SKILL_DIR / "tests" / "fixtures" / "smoke-paper.md"
        text = stringify_pandoc(pandoc_ast(fixture)["blocks"])
        self.assertNotIn("AlignDefault", text)
        self.assertIn("单位收益", text)

    def test_normalize_compare_ignores_punctuation(self) -> None:
        self.assertEqual(normalize_for_compare("内容，锁！"), "内容锁")


class DeclarationTests(unittest.TestCase):
    def test_not_used_rejects_summary(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(TypesetterError):
                prepare_ai_declaration(
                    state="not_used",
                    summary="cannot be present",
                    support_pdf=None,
                    output_dir=Path(tmp),
                )

    def test_used_requires_support(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(TypesetterError):
                prepare_ai_declaration(
                    state="used",
                    summary="这是一个足够长的用途阶段说明文本",
                    support_pdf=None,
                    output_dir=Path(tmp),
                )


class AuditScopeTests(unittest.TestCase):
    def make_report(self, *, requested: bool, preview_pages: list[int]) -> dict:
        return _audit_report(
            Path("/test-output"), [], {"page_count": 3, "pdf_sha256": "a" * 64},
            [{"page": index} for index in range(1, 4)],
            [f"/test-output/previews/page-{index}.png" for index in preview_pages],
            {}, previews_requested=requested,
        )

    def test_mechanical_pass_never_claims_visual_or_semantic_review(self) -> None:
        report = self.make_report(requested=True, preview_pages=[1, 2, 3])
        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["status_scope"], "mechanical_checks_only")
        self.assertEqual(report["review_status"], "pending_visual_and_semantic_review")
        scope = report["review_scope"]
        self.assertEqual(scope["mechanical"]["pdf_pages_checked"], [1, 2, 3])
        self.assertEqual(scope["previews"]["status"], "complete")
        self.assertEqual(scope["previews"]["coverage_ratio"], 1.0)
        self.assertFalse(scope["previews"]["rendering_is_visual_review"])
        self.assertEqual(scope["visual"], {"status": "not_performed", "reviewed_pages": []})
        self.assertEqual(scope["semantic"]["status"], "not_performed")

    def test_disabled_and_incomplete_previews_are_explicit(self) -> None:
        disabled = self.make_report(requested=False, preview_pages=[])["review_scope"]["previews"]
        self.assertEqual(disabled["status"], "not_generated")
        self.assertEqual(disabled["missing_pages"], [1, 2, 3])
        self.assertIsNone(disabled["pdf_sha256"])
        incomplete = self.make_report(requested=True, preview_pages=[1, 2])["review_scope"]["previews"]
        self.assertEqual(incomplete["status"], "incomplete")
        self.assertEqual(incomplete["missing_pages"], [3])

    def test_missing_outputs_do_not_claim_pdf_pages_were_checked(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report = verify_output(Path(tmp))
        self.assertEqual(report["status"], "fail")
        scope = report["review_scope"]
        self.assertEqual(scope["mechanical"]["checks"], ["required_output_files"])
        self.assertEqual(scope["mechanical"]["pdf_pages_checked"], [])
        self.assertEqual(scope["previews"]["status"], "unavailable")


if __name__ == "__main__":
    unittest.main()
