#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""发布会竖屏风格回归：画布、原语渲染与字幕安全区。"""

import unittest

from engine import launch_style
from engine.visual_qa import analyze_storyboard


def scene(scene_id, visual, narration="这是一句用于风格回归的讲解台词。"):
    return {
        "id": scene_id,
        "transition": "fade",
        "camera": {"motion": "zoom_in"},
        "audio": {"text": narration, "speed": 1.0, "pause": 0.4, "emotion": "normal"},
        "visual": visual,
    }


class LaunchStyleTest(unittest.TestCase):

    WIDTH, HEIGHT = 1080, 1920

    def render(self, visual, frame=40, total=120, accent="indigo"):
        item = scene("s", visual)
        return launch_style.render(item, frame, total, self.WIDTH, self.HEIGHT, accent)

    def test_all_primitives_render_at_portrait_size(self):
        visuals = {
            "hero": {"type": "hero", "kicker": "GOOGLE DEEPMIND", "title": "Gemini 4.0", "subtitle": "正式发布"},
            "statement": {"type": "statement", "lines": ["又一个版本号", "又一次新的起点"], "highlight": 1},
            "feature_stack": {"type": "feature_stack", "header": "看片提示",
                              "items": [{"title": "发布事实", "sub": "以官方公告为准"}]},
            "closing": {"type": "closing", "title": "Gemini 4.0", "footer": "正式发布"},
        }
        for name, visual in visuals.items():
            with self.subTest(primitive=name):
                frame = self.render(visual)
                self.assertEqual(frame.size, (self.WIDTH, self.HEIGHT))

    def test_frames_animate_over_time(self):
        visual = {"type": "hero", "title": "Gemini 4.0", "subtitle": "正式发布"}
        first = self.render(visual, frame=0)
        later = self.render(visual, frame=60)
        self.assertNotEqual(first.tobytes(), later.tobytes())

    def test_unknown_primitive_is_rejected(self):
        with self.assertRaises(ValueError):
            self.render({"type": "title_card"})

    def test_subtitle_renders_without_pill(self):
        visual = {"type": "closing", "title": "Gemini 4.0", "footer": "正式发布"}
        base = self.render(visual)
        with_sub = launch_style.render_subtitle(base, "这，就是 Gemini 4.0。", 1.0, self.WIDTH, self.HEIGHT)
        self.assertEqual(with_sub.size, base.size)
        self.assertNotEqual(with_sub.tobytes(), base.tobytes())

    def test_long_text_is_fitted_not_overflowed(self):
        visual = {"type": "hero", "title": "Gemini 4.0 " * 8, "subtitle": "正式发布" * 20}
        frame = self.render(visual)
        self.assertEqual(frame.size, (self.WIDTH, self.HEIGHT))

    def test_visual_qa_uses_portrait_width_from_meta(self):
        spec = {
            "meta": {"resolution": [1080, 1920]},
            "scenes": [
                scene("a", {"type": "hero", "title": "Gemini 4.0"}),
                scene("b", {"type": "statement", "lines": ["一"]}),
                scene("c", {"type": "closing", "title": "Gemini 4.0"}),
            ],
        }
        report = analyze_storyboard(spec)
        self.assertTrue(report["passed"], report["blocking_issues"])


if __name__ == "__main__":
    unittest.main()
