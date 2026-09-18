#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""测试辅助：加载固定输入并生成稳定的剧本指纹。"""

import json
import os
from typing import Any, Dict, List

TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
FIXTURES_DIR = os.path.join(TESTS_DIR, "fixtures")
SNAPSHOTS_DIR = os.path.join(TESTS_DIR, "snapshots")


def load_fixture(name: str) -> Dict[str, Any]:
    with open(os.path.join(FIXTURES_DIR, name), "r", encoding="utf-8") as handle:
        return json.load(handle)


def list_fixtures() -> List[str]:
    return sorted(name for name in os.listdir(FIXTURES_DIR) if name.endswith(".json"))


def storyboard_fingerprint(spec: Dict[str, Any]) -> Dict[str, Any]:
    """把剧本压缩成可对比的稳定指纹，不含时间戳或二进制产物。"""
    meta = spec.get("meta", {}) or {}
    scenes = [scene for scene in spec.get("scenes", []) if isinstance(scene, dict)]
    beats = [beat for beat in (meta.get("story_beats") or []) if isinstance(beat, dict)]
    visuals = [(scene.get("visual") or {}).get("type") for scene in scenes]
    return {
        "profile": meta.get("story_profile"),
        "variant": meta.get("story_variant"),
        "beats": [beat.get("id") for beat in beats],
        "scene_ids": [scene.get("id") for scene in scenes],
        "visuals": visuals,
        "asset_requests": [request.get("id") for request in (spec.get("asset_requests") or [])],
        "evidence_scenes": [
            scene.get("id") for scene in scenes if (scene.get("visual") or {}).get("evidence")
        ],
        "has_placeholders": any(
            visual in {"asset_placeholder", "material_placeholder"} for visual in visuals
        ),
    }


def dumps_fingerprint(fingerprint: Dict[str, Any]) -> str:
    return json.dumps(fingerprint, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
