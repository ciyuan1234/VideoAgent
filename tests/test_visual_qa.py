#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""画面层体检回归：布局遮挡、镜头顺序与静态镜头。"""

import unittest

import yaml

from engine import story_planner as planner
from engine.quality_gate import evaluate_storyboard
from engine.visual_qa import analyze_storyboard, estimate_subtitle_pill_width, estimate_text_width

from tests.support import load_fixture


def yaml_dump_text(spec):
    return yaml.dump(spec, allow_unicode=True, sort_keys=False)


def scene(scene_id, visual, narration="这是用于画面体检的普通讲解台词。", **extra):
    payload = {
        "id": scene_id,
        "transition": "cut",
        "camera": {"motion": "zoom_in"},
        "audio": {"text": narration, "speed": 1.0, "pause": 0.3, "emotion": "normal"},
        "visual": visual,
    }
    payload.update(extra)
    return payload


class VisualQaTest(unittest.TestCase):

    def test_subtitle_pill_width_is_reproducible(self):
        # 复现 render_subtitle_pill：短句单行、长句折行后取最宽行。
        short = estimate_subtitle_pill_width("短句")
        long_text = "这是一段明显超过二十四个字的讲解台词用于触发字幕胶囊自动折行逻辑"
        self.assertGreater(estimate_subtitle_pill_width(long_text), short)

    def test_clean_storyboard_passes(self):
        spec = {
            "scenes": [
                scene("s1", {"type": "title_card", "title": "一"}),
                scene("s2", {"type": "image", "file": "a.png", "beats": [
                    {"at": 0.0, "focus": [0.5, 0.4], "label": "先看整体"},
                    {"at": 0.6, "focus": [0.5, 0.7], "scale": 1.2, "label": "再看细节"},
                ]}, narration="这一段讲解配合截图说明。"),
                scene("s3", {"type": "custom_nodes", "nodes": [{"title": "n"}]}),
            ]
        }
        report = analyze_storyboard(spec)
        self.assertTrue(report["passed"], report["blocking_issues"])
        self.assertEqual(report["blocking_issues"], [])

    def test_long_label_overlaps_subtitle(self):
        long_label = "展示 Redis 安装与配置教程 的关键操作、状态变化或运行结果"
        spec = {"scenes": [
            scene("s1", {"type": "title_card", "title": "一"}),
            scene("s2", {"type": "image", "file": "a.png", "beats": [
                {"at": 0.0, "focus": [0.5, 0.4], "label": long_label},
            ]}),
            scene("s3", {"type": "custom_nodes", "nodes": [{"title": "n"}]}),
        ]}
        report = analyze_storyboard(spec)
        self.assertFalse(report["passed"])
        self.assertTrue(any("居中字幕" in issue for issue in report["blocking_issues"]))

    def test_label_is_truncated_to_stay_clear_of_subtitles(self):
        from engine.visual_qa import fit_label_to_width, label_safe_width

        narration = "按 Tab 键还能自动补全文件名和命令，操作体验非常顺畅。"
        budget = label_safe_width(narration, 1920)
        fitted = fit_label_to_width("跟随高亮条浏览命令，再用 Tab 完成下一步操作", budget)
        self.assertLessEqual(estimate_text_width(fitted, 30), budget)
        self.assertTrue(fitted.endswith("…"), fitted)
        # 未超宽的标签保持原样
        self.assertEqual(fit_label_to_width("查看关键操作", budget), "查看关键操作")

    def test_node_text_never_overflows_card(self):
        from engine.text_metrics import estimate_text_width, fit_text_to_width

        fixture = load_fixture("concept.json")
        spec = planner.build_storyboard(fixture["content"], "concept", "mechanism_first")
        for item in spec["scenes"]:
            for node in item.get("visual", {}).get("nodes") or []:
                self.assertLessEqual(estimate_text_width(node["title"], 24), 272, node)
                self.assertLessEqual(estimate_text_width(node["sub"], 20), 272, node)

        # 渲染器兜底：任何超长输入都不会溢出卡片
        self.assertLessEqual(estimate_text_width(fit_text_to_width("超长标题" * 10, 272, 24), 24), 272)

    def test_emoji_from_source_does_not_reach_storyboard(self):
        spec = planner.build_storyboard(
            {
                "title": "🎯 核心机制",
                "raw_text": "机制说明",
                "headings": ["⚡ 标准生产工作流", "🚀 端到端模式"],
                "bullets": ["🎨 视觉资产"],
                "code_snippets": [],
            },
            "concept",
            "mechanism_first",
        )
        blob = yaml_dump_text(spec)
        for glyph in ("🎯", "⚡", "🚀", "🎨"):
            self.assertNotIn(glyph, blob)
        self.assertIn("核心机制", blob)

    def test_callout_out_of_bounds_is_blocking(self):
        spec = {"scenes": [
            scene("s1", {"type": "title_card", "title": "一"}),
            scene("s2", {"type": "image", "file": "a.png", "beats": [
                {"at": 0.0, "focus": [0.5, 0.4], "callout": [0.6, 0.5, 0.6, 0.3]},
            ]}),
            scene("s3", {"type": "custom_nodes", "nodes": [{"title": "n"}]}),
        ]}
        report = analyze_storyboard(spec)
        self.assertFalse(report["passed"])
        self.assertTrue(any("越界" in issue for issue in report["blocking_issues"]))

    def test_beat_order_regression_is_blocking(self):
        spec = {"scenes": [
            scene("s1", {"type": "title_card", "title": "一"}),
            scene("s2", {"type": "image", "file": "a.png", "beats": [
                {"at": 0.0, "focus": [0.5, 0.4], "label": "先看整体"},
                {"at": 0.2, "focus": [0.5, 0.6], "label": "再看细节"},
                {"at": 0.1, "focus": [0.5, 0.8], "label": "跳回镜头"},
            ]}),
            scene("s3", {"type": "custom_nodes", "nodes": [{"title": "n"}]}),
        ]}
        report = analyze_storyboard(spec)
        self.assertFalse(report["passed"])
        self.assertTrue(any("递增" in issue for issue in report["blocking_issues"]))

    def test_all_static_scenes_is_blocking(self):
        spec = {"scenes": [
            scene(f"s{i}", {"type": "title_card" if i % 2 else "custom_nodes", "title": f"{i}"},
                  camera={})
            for i in range(1, 4)
        ]}
        report = analyze_storyboard(spec)
        self.assertFalse(report["passed"])
        self.assertTrue(any("静态画面" in issue for issue in report["blocking_issues"]))

    def test_quality_gate_surfaces_visual_issues(self):
        spec = self.generated_with_asset(fixture_name="tutorial_with_assets.json")
        # 规划器生成的标签必须是短语，不能压到居中字幕。
        labels = [
            beat.get("label")
            for item in spec["scenes"]
            for beat in (item.get("visual", {}).get("beats") or [])
        ]
        self.assertTrue(labels)
        self.assertTrue(all(len(label) <= 16 for label in labels), labels)
        self.assertEqual(evaluate_storyboard(spec)["blocking_issues"], [])

    def generated_with_asset(self, fixture_name):
        fixture = load_fixture(fixture_name)
        return planner.build_storyboard(
            fixture["content"],
            story_profile=fixture.get("story_profile", "auto"),
            story_variant=fixture.get("story_variant", "auto"),
        )


if __name__ == "__main__":
    unittest.main()
