#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""发布门禁回归：结构预检、质量门槛与历史工程兼容。"""

import os
import tempfile
import unittest

import yaml

from engine import story_planner as planner
from engine.compositor import VideoCompositor

from tests.support import load_fixture

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def write_project(directory, spec):
    os.makedirs(os.path.join(directory, "extra_assets"), exist_ok=True)
    with open(os.path.join(directory, "storyboard.yaml"), "w", encoding="utf-8") as handle:
        yaml.dump(spec, handle, allow_unicode=True, sort_keys=False)


class ReleaseGateTest(unittest.TestCase):

    def compositor_for(self, spec, directory):
        write_project(directory, spec)
        return VideoCompositor(directory, root_dir=REPO_ROOT)

    def test_placeholder_scene_blocks_release_but_allows_preview(self):
        fixture = load_fixture("tutorial.json")
        spec = planner.build_storyboard(fixture["content"], "tutorial", "mechanism_first")
        with tempfile.TemporaryDirectory() as tmp:
            compositor = self.compositor_for(spec, tmp)
            errors, _ = compositor.validate_storyboard()
            self.assertTrue(any("素材占位" in error for error in errors), errors)
            preview_errors, _ = compositor.validate_storyboard(allow_placeholders=True)
            self.assertEqual(preview_errors, [])

    def test_build_refuses_placeholder(self):
        fixture = load_fixture("tutorial.json")
        spec = planner.build_storyboard(fixture["content"], "tutorial", "mechanism_first")
        with tempfile.TemporaryDirectory() as tmp:
            compositor = self.compositor_for(spec, tmp)
            with self.assertRaises(ValueError) as ctx:
                compositor.build()
            self.assertIn("预检未通过", str(ctx.exception))

    def test_build_refuses_low_quality_storyboard(self):
        # 该剧本能通过结构预检（无相邻重复、至少两种镜头），但缺少 story_beats
        # 且台词高度重复，质量分必然低于门槛。
        repeated = "这是一段刻意重复并且明显过长的讲解台词，用来触发台词质量扣分" * 2
        spec = {
            "meta": {"title": "模板剧本", "story_profile": "concept", "story_variant": "auto",
                     "story_beats": []},
            "scenes": [
                {"id": "s1", "transition": "slide_left", "audio": {"text": repeated},
                 "visual": {"type": "title_card", "title": "第一幕"}},
                {"id": "s2", "transition": "slide_left", "audio": {"text": repeated},
                 "visual": {"type": "custom_nodes", "nodes": [{"title": "节点"}]}},
                {"id": "s3", "transition": "slide_left", "audio": {"text": repeated},
                 "visual": {"type": "title_card", "title": "第三幕"}},
            ],
        }
        with tempfile.TemporaryDirectory() as tmp:
            compositor = self.compositor_for(spec, tmp)
            errors, _ = compositor.validate_storyboard()
            self.assertEqual(errors, [])
            with self.assertRaises(ValueError) as ctx:
                compositor.build()
            self.assertIn("质量分", str(ctx.exception))

    def test_legacy_project_is_not_blocked_by_quality(self):
        legacy_dir = os.path.join(REPO_ROOT, "projects", "codex_tutorial")
        if not os.path.exists(os.path.join(legacy_dir, "storyboard.yaml")):
            self.skipTest("缺少 codex_tutorial 回归工程")
        compositor = VideoCompositor(legacy_dir, root_dir=REPO_ROOT)
        errors, _ = compositor.validate_storyboard()
        self.assertEqual(errors, [])
        report = compositor.quality_report()
        self.assertFalse(report["enforced"])

    def test_quality_report_is_serialisable(self):
        fixture = load_fixture("concept.json")
        spec = planner.build_storyboard(fixture["content"], "concept", "mechanism_first")
        with tempfile.TemporaryDirectory() as tmp:
            compositor = self.compositor_for(spec, tmp)
            report = compositor.quality_report()
        reloaded = yaml.safe_load(yaml.dump(report, allow_unicode=True))
        self.assertEqual(reloaded["score"], report["score"])
        self.assertEqual(reloaded["passed"], report["passed"])


if __name__ == "__main__":
    unittest.main()
