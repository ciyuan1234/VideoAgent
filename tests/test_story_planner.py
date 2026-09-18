#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""节拍规划器回归：结构差异、证据纪律与快照稳定性。"""

import json
import os
import unittest

from engine import story_planner as planner

from tests.support import (
    SNAPSHOTS_DIR,
    dumps_fingerprint,
    list_fixtures,
    load_fixture,
    storyboard_fingerprint,
)

UPDATE_HINT = (
    "快照缺失或不匹配。确认输出确实是期望结果后，"
    "运行 python -m tests.update_snapshots 更新基线。"
)


class StoryPlannerTest(unittest.TestCase):

    def build(self, fixture_name):
        fixture = load_fixture(fixture_name)
        return planner.build_storyboard(
            fixture["content"],
            story_profile=fixture.get("story_profile", "auto"),
            story_variant=fixture.get("story_variant", "auto"),
        )

    def test_all_fixtures_match_snapshot(self):
        for name in list_fixtures():
            with self.subTest(fixture=name):
                spec = self.build(name)
                snapshot_path = os.path.join(SNAPSHOTS_DIR, name)
                self.assertTrue(os.path.exists(snapshot_path), f"{name}: {UPDATE_HINT}")
                with open(snapshot_path, "r", encoding="utf-8") as handle:
                    expected = json.load(handle)
                self.assertEqual(
                    json.loads(dumps_fingerprint(storyboard_fingerprint(spec))),
                    expected,
                    f"{name}: {UPDATE_HINT}",
                )

    def test_profiles_are_auto_detected(self):
        expectations = {
            "tutorial.json": "tutorial",
            "concept.json": "concept",
            "code_walkthrough.json": "code_walkthrough",
            "decision.json": "decision",
        }
        for name, profile in expectations.items():
            with self.subTest(fixture=name):
                fixture = load_fixture(name)
                spec = planner.build_storyboard(fixture["content"], "auto")
                self.assertEqual(spec["meta"]["story_profile"], profile)

    def test_profiles_produce_different_visual_sequences(self):
        names = ("tutorial.json", "concept.json", "code_walkthrough.json", "decision.json")
        fingerprints = {name: storyboard_fingerprint(self.build(name)) for name in names}

        # 四种 profile 的叙事结构（节拍与分镜身份）必须各不相同。
        structures = {name: tuple(data["scene_ids"]) for name, data in fingerprints.items()}
        self.assertEqual(len(set(structures.values())), len(structures), structures)

        # 视觉原语序列允许在缺乏区分性材料时重叠，但四种 profile 不应退化成同一种镜头形状。
        visuals = {name: tuple(data["visuals"]) for name, data in fingerprints.items()}
        self.assertGreaterEqual(len(set(visuals.values())), 3, visuals)

    def test_no_adjacent_duplicate_visuals(self):
        for name in list_fixtures():
            with self.subTest(fixture=name):
                visuals = storyboard_fingerprint(self.build(name))["visuals"]
                duplicates = [
                    current for previous, current in zip(visuals, visuals[1:]) if previous == current
                ]
                self.assertEqual(duplicates, [], f"{name}: 相邻场景重复镜头 {duplicates}")

    def test_chart_only_when_metrics_exist(self):
        for name in list_fixtures():
            with self.subTest(fixture=name):
                fixture = load_fixture(name)
                signals = planner.analyze_content_signals(fixture["content"])
                visuals = storyboard_fingerprint(self.build(name))["visuals"]
                if signals["has_explicit_metrics"]:
                    self.assertIn("chart_benchmark", visuals)
                else:
                    self.assertNotIn("chart_benchmark", visuals)

    def test_no_fabricated_terminal_or_diff(self):
        for name in list_fixtures():
            with self.subTest(fixture=name):
                visuals = storyboard_fingerprint(self.build(name))["visuals"]
                self.assertNotIn("terminal", visuals)
                self.assertNotIn("git_diff", visuals)

    def test_story_variant_reorders_without_changing_facts(self):
        fixture = load_fixture("concept.json")
        mechanism_first = planner.build_storyboard(fixture["content"], "concept", "mechanism_first")
        evidence_first = planner.build_storyboard(fixture["content"], "concept", "evidence_first")

        self.assertNotEqual(
            storyboard_fingerprint(mechanism_first)["scene_ids"],
            storyboard_fingerprint(evidence_first)["scene_ids"],
        )
        self.assertEqual(
            mechanism_first["meta"]["content_evidence"],
            evidence_first["meta"]["content_evidence"],
        )
        self.assertEqual(
            set(storyboard_fingerprint(mechanism_first)["scene_ids"]),
            set(storyboard_fingerprint(evidence_first)["scene_ids"]),
        )

    def test_tagged_asset_matches_operation_beat(self):
        spec = self.build("tutorial_with_assets.json")
        operation = next(scene for scene in spec["scenes"] if scene["id"] == "operation")
        self.assertEqual(operation["visual"]["type"], "video_clip")
        self.assertEqual(operation["visual"]["file"], "terminal_demo.mp4")
        self.assertEqual(spec["asset_requests"], [])

    def test_asset_request_preserved_when_nothing_matches(self):
        spec = self.build("tutorial.json")
        self.assertTrue(spec["asset_requests"])
        visuals = storyboard_fingerprint(spec)["visuals"]
        self.assertIn("asset_placeholder", visuals)

    def test_unknown_profile_is_rejected(self):
        fixture = load_fixture("concept.json")
        with self.assertRaises(ValueError):
            planner.build_storyboard(fixture["content"], "not_a_profile")
        with self.assertRaises(ValueError):
            planner.build_storyboard(fixture["content"], "concept", "not_a_variant")

    def test_collect_available_assets_tags_files(self):
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            open(os.path.join(tmp, "terminal_demo.mp4"), "w").close()
            open(os.path.join(tmp, "code_diff.png"), "w").close()
            open(os.path.join(tmp, "notes.txt"), "w").close()
            assets = planner.collect_available_assets(tmp)

        by_file = {asset["file"]: asset for asset in assets}
        self.assertEqual(len(assets), 2)
        self.assertIn("operation", by_file["terminal_demo.mp4"]["tags"])
        self.assertIn("code", by_file["code_diff.png"]["tags"])
        self.assertEqual(by_file["terminal_demo.mp4"]["kind"], "video")


if __name__ == "__main__":
    unittest.main()
