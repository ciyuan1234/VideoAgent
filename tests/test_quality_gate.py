#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""质量门禁回归：评分维度、阻断项与历史工程兼容。"""

import unittest

from engine import story_planner as planner
from engine.quality_gate import DEFAULT_QUALITY_THRESHOLD, evaluate_storyboard

from tests.support import load_fixture


def scene(scene_id, visual, narration="这是一段用于质量评估的普通讲解台词内容。", **extra):
    payload = {
        "id": scene_id,
        "transition": "cut",
        "camera": {"motion": "zoom_in"},
        "audio": {"text": narration, "speed": 1.0, "pause": 0.3, "emotion": "normal"},
        "visual": visual,
    }
    payload.update(extra)
    return payload


class QualityGateTest(unittest.TestCase):

    def generated_spec(self, fixture_name):
        fixture = load_fixture(fixture_name)
        return planner.build_storyboard(
            fixture["content"],
            story_profile=fixture.get("story_profile", "auto"),
            story_variant=fixture.get("story_variant", "auto"),
        )

    def test_generated_storyboards_pass_threshold(self):
        for name in ("tutorial.json", "concept.json", "code_walkthrough.json", "decision.json"):
            with self.subTest(fixture=name):
                report = evaluate_storyboard(self.generated_spec(name))
                self.assertTrue(report["enforced"])
                self.assertGreaterEqual(report["score"], DEFAULT_QUALITY_THRESHOLD, report)
                self.assertTrue(report["passed"], report)

    def test_report_shape_is_stable(self):
        report = evaluate_storyboard(self.generated_spec("concept.json"))
        self.assertEqual(
            set(report["breakdown"]),
            {"visual_diversity", "rhythm_variety", "evidence_integrity",
             "beat_coverage", "narration_quality"},
        )
        self.assertEqual(sum(item["max"] for item in report["breakdown"].values()), 100)
        for key in ("score", "threshold", "enforced", "passed",
                    "blocking_issues", "warnings", "suggestions"):
            self.assertIn(key, report)

    def test_template_storyboard_scores_below_threshold(self):
        spec = {
            "meta": {"title": "模板剧本", "story_profile": "concept"},
            "scenes": [
                scene("s1", {"type": "title_card", "title": "一"}),
                scene("s2", {"type": "title_card", "title": "二"}),
                scene("s3", {"type": "title_card", "title": "三"}),
                scene("s4", {"type": "title_card", "title": "四"}),
            ],
        }
        report = evaluate_storyboard(spec)
        self.assertLess(report["score"], DEFAULT_QUALITY_THRESHOLD)
        self.assertFalse(report["passed"])
        self.assertTrue(report["blocking_issues"])
        self.assertLessEqual(report["breakdown"]["visual_diversity"]["score"], 8)
        self.assertEqual(report["breakdown"]["beat_coverage"]["score"], 0)

    def test_evidence_primitive_without_evidence_is_blocking(self):
        spec = {
            "meta": {"title": "证据缺失", "story_profile": "concept",
                     "story_beats": [
                         {"id": "hook", "intent": "x", "evidence_level": "derived", "scene_id": "s1"},
                         {"id": "metrics", "intent": "y", "evidence_level": "source", "scene_id": "s2"},
                         {"id": "takeaway", "intent": "z", "evidence_level": "derived", "scene_id": "s3"},
                     ]},
            "scenes": [
                scene("s1", {"type": "title_card", "title": "一"}),
                scene("s2", {"type": "chart_benchmark", "data": [{"label": "a", "value": 1}]}),
                scene("s3", {"type": "custom_nodes", "nodes": [{"title": "n"}]}),
            ],
        }
        report = evaluate_storyboard(spec)
        self.assertTrue(report["blocking_issues"])
        self.assertEqual(report["breakdown"]["evidence_integrity"]["score"], 10)

    def test_evidence_primitive_with_evidence_scores_higher(self):
        spec = {
            "meta": {"title": "证据完整", "story_profile": "concept",
                     "story_beats": [
                         {"id": "hook", "intent": "x", "evidence_level": "derived", "scene_id": "s1"},
                         {"id": "metrics", "intent": "y", "evidence_level": "source", "scene_id": "s2"},
                         {"id": "takeaway", "intent": "z", "evidence_level": "derived", "scene_id": "s3"},
                     ]},
            "scenes": [
                scene("s1", {"type": "title_card", "title": "一"}),
                scene("s2", {"type": "chart_benchmark", "data": [{"label": "a", "value": 1}],
                             "evidence": ["1200 QPS"]}),
                scene("s3", {"type": "custom_nodes", "nodes": [{"title": "n"}]}),
            ],
        }
        report = evaluate_storyboard(spec)
        self.assertEqual(report["blocking_issues"], [])
        self.assertEqual(report["breakdown"]["evidence_integrity"]["score"], 25)

    def test_placeholder_lowers_evidence_score(self):
        spec = self.generated_spec("tutorial.json")
        report = evaluate_storyboard(spec)
        self.assertEqual(report["breakdown"]["evidence_integrity"]["score"], 18)
        self.assertTrue(any("素材占位" in warning for warning in report["warnings"]))

    def test_matched_real_asset_scores_higher_than_placeholder(self):
        placeholder = evaluate_storyboard(self.generated_spec("tutorial.json"))
        with_asset = evaluate_storyboard(self.generated_spec("tutorial_with_assets.json"))
        self.assertGreater(
            with_asset["breakdown"]["evidence_integrity"]["score"],
            placeholder["breakdown"]["evidence_integrity"]["score"],
        )
        self.assertGreater(with_asset["score"], placeholder["score"])

    def test_duplicate_and_overlong_narration_are_penalised(self):
        long_text = "这是一句刻意写得很长很长的讲解台词" * 5
        spec = {
            "meta": {"title": "台词问题", "story_profile": "concept",
                     "story_beats": [
                         {"id": "hook", "intent": "a", "evidence_level": "derived", "scene_id": "s1"},
                         {"id": "mechanism", "intent": "b", "evidence_level": "derived", "scene_id": "s2"},
                         {"id": "takeaway", "intent": "c", "evidence_level": "derived", "scene_id": "s3"},
                     ]},
            "scenes": [
                scene("s1", {"type": "title_card", "title": "一"}, narration=long_text),
                scene("s2", {"type": "custom_nodes", "nodes": [{"title": "n"}]}, narration=long_text),
                scene("s3", {"type": "title_card", "title": "二"}, narration=long_text),
            ],
        }
        report = evaluate_storyboard(spec)
        self.assertLess(report["breakdown"]["narration_quality"]["score"], 20)
        self.assertTrue(any("重复台词" in warning for warning in report["warnings"]))

    def test_legacy_storyboard_is_not_enforced(self):
        spec = {
            "meta": {"title": "历史工程"},
            "scenes": [
                scene("s1", {"type": "title_card", "title": "一"}),
                scene("s2", {"type": "custom_nodes", "nodes": [{"title": "n"}]}),
                scene("s3", {"type": "title_card", "title": "二"}),
            ],
        }
        report = evaluate_storyboard(spec)
        self.assertFalse(report["enforced"])
        self.assertFalse(report["passed"])


if __name__ == "__main__":
    unittest.main()
