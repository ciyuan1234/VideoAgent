#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VideoAgent Quality Gate
确定性的剧本质量评分器：在渲染前拦截模板化、证据不足与节奏单一。

输入 storyboard（dict），输出可追溯的质量报告；不读文件、不调用 LLM。
"""

import re
from typing import Any, Dict, List

DEFAULT_QUALITY_THRESHOLD = 75

VALID_STORY_PROFILES = {"tutorial", "concept", "code_walkthrough", "decision"}

EVIDENCE_REQUIRED_VISUALS = {"chart_benchmark", "benchmark", "chart", "terminal", "terminal_mock", "cli", "git_diff", "diff"}
PLACEHOLDER_VISUALS = {"asset_placeholder", "material_placeholder"}
REAL_ASSET_VISUALS = {"image", "screenshot", "showcase", "diagram_or_image", "video_clip", "video", "clip"}

MAX_SENTENCE_CHARS = 45
MIN_NARRATION_CHARS = 12

DIMENSION_MAX = {
    "visual_diversity": 20,
    "rhythm_variety": 15,
    "evidence_integrity": 25,
    "beat_coverage": 20,
    "narration_quality": 20,
}


def _scenes(spec: Dict[str, Any]) -> List[Dict[str, Any]]:
    scenes = spec.get("scenes", [])
    return [scene for scene in scenes if isinstance(scene, dict)] if isinstance(scenes, list) else []


def _visual_type(scene: Dict[str, Any]) -> str:
    return (scene.get("layout") or (scene.get("visual") or {}).get("type") or "unknown")


def _visual(scene: Dict[str, Any]) -> Dict[str, Any]:
    visual = scene.get("visual")
    return visual if isinstance(visual, dict) else {}


def _narration(scene: Dict[str, Any]) -> str:
    audio = scene.get("audio")
    text = audio.get("text") if isinstance(audio, dict) else None
    return str(text or scene.get("voice_text") or "").strip()


def _score_visual_diversity(scenes: List[Dict[str, Any]]) -> Dict[str, Any]:
    maximum = DIMENSION_MAX["visual_diversity"]
    types = [_visual_type(scene) for scene in scenes]
    distinct = len(set(types))
    ratio = distinct / float(len(types)) if types else 0.0
    diversity_points = int(round(12 * min(1.0, ratio / 0.6)))
    adjacency_points = maximum - 12
    repeated = [current for previous, current in zip(types, types[1:]) if previous == current]
    if repeated:
        adjacency_points = 0
    score = min(maximum, diversity_points + adjacency_points)
    return {
        "score": score, "max": maximum,
        "detail": f"{len(types)} 幕使用 {distinct} 种镜头，相邻重复 {len(repeated)} 处",
        "distinct_types": distinct, "total_scenes": len(types), "adjacent_repeats": repeated,
    }


def _score_rhythm_variety(scenes: List[Dict[str, Any]]) -> Dict[str, Any]:
    maximum = DIMENSION_MAX["rhythm_variety"]
    if not scenes:
        return {"score": 0, "max": maximum, "detail": "无场景"}

    transitions = [str(scene.get("transition") or "slide_left") for scene in scenes]
    dominant_transition = max(set(transitions), key=transitions.count)
    transition_ratio = transitions.count(dominant_transition) / float(len(transitions))
    transition_points = 6 if transition_ratio <= 0.6 else int(round(6 * (1.0 - transition_ratio) / 0.4))

    with_character = [
        scene for scene in scenes
        if scene.get("character_sticker")
        or str(scene.get("character_mode") or "").lower() not in {"", "none"}
    ]
    character_ratio = len(with_character) / float(len(scenes))
    character_points = 5 if character_ratio <= 0.5 else int(round(5 * (1.0 - character_ratio) / 0.5))

    motions = [
        (scene.get("camera") or {}).get("motion")
        for scene in scenes if isinstance(scene.get("camera"), dict) and (scene.get("camera") or {}).get("motion")
    ]
    suggestions: List[str] = []
    if not motions:
        # 全片没有任何虚拟摄像机配置，不应与“有镜头设计”拿同样的分。
        camera_points = 2
        suggestions.append("全片没有虚拟摄像机配置，建议为关键论证场景添加 camera.motion")
    elif len(motions) >= 3 and len(set(motions)) == 1:
        camera_points = 1
        suggestions.append("镜头运动高度单一，建议混合 zoom_in 与 zoom_punch")
    else:
        camera_points = 4

    score = max(0, min(maximum, transition_points + character_points + camera_points))
    return {
        "score": score, "max": maximum,
        "detail": (f"主导转场占比 {round(transition_ratio * 100)}%，"
                   f"角色出镜 {len(with_character)}/{len(scenes)} 幕，"
                   f"镜头运动 {len(motions)} 处 / {len(set(motions))} 种"),
        "suggestions": suggestions,
    }


def _score_evidence_integrity(scenes: List[Dict[str, Any]], spec: Dict[str, Any]) -> Dict[str, Any]:
    maximum = DIMENSION_MAX["evidence_integrity"]
    score = maximum
    blocking: List[str] = []
    warnings: List[str] = []

    unproven = [
        scene.get("id")
        for scene in scenes
        if _visual_type(scene) in EVIDENCE_REQUIRED_VISUALS and not _visual(scene).get("evidence")
    ]
    if unproven:
        score -= 15
        blocking.append("缺少可复核 evidence 的证据型镜头: " + ", ".join(str(item) for item in unproven))

    placeholders = [scene.get("id") for scene in scenes if _visual_type(scene) in PLACEHOLDER_VISUALS]
    if placeholders:
        score -= min(12, 4 * len(placeholders))
        warnings.append("仍有素材占位场景: " + ", ".join(str(item) for item in placeholders))

    real_assets = [scene for scene in scenes if _visual_type(scene) in REAL_ASSET_VISUALS]
    asset_requests = spec.get("asset_requests") or []
    if asset_requests and not real_assets:
        score -= 3
        warnings.append("有素材请求但全片没有真实素材镜头，成片会退化为纯图解")

    score = max(0, min(maximum, score))
    return {
        "score": score, "max": maximum,
        "detail": (f"真实素材镜头 {len(real_assets)} 幕，占位 {len(placeholders)} 幕，"
                   f"素材请求 {len(asset_requests)} 项"),
        "blocking_issues": blocking, "warnings": warnings,
    }


def _score_beat_coverage(scenes: List[Dict[str, Any]], spec: Dict[str, Any]) -> Dict[str, Any]:
    maximum = DIMENSION_MAX["beat_coverage"]
    beats = (spec.get("meta") or {}).get("story_beats") or []
    if not beats:
        return {"score": 0, "max": maximum, "detail": "缺少 meta.story_beats 叙事节拍",
                "blocking_issues": ["缺少 meta.story_beats，无法核对叙事与分镜是否一致"],
                "suggestions": ["重新运行 auto-generate 生成带 story_beats 的剧本"]}

    scene_ids = [scene.get("id") for scene in scenes]
    beat_scene_ids = [beat.get("scene_id") for beat in beats if isinstance(beat, dict)]
    aligned = len(beats) == len(scenes) and set(beat_scene_ids) == set(scene_ids)
    points = 10 if aligned else 0
    intents = [beat.get("id") for beat in beats if isinstance(beat, dict)]
    intent_ratio = len(set(intents)) / float(len(intents)) if intents else 0.0
    points += int(round(6 * intent_ratio))
    points += 4 if {"hook", "takeaway"}.issubset(set(intents)) else 0

    blocking = [] if aligned else ["meta.story_beats 与 scenes 不是一一对应"]
    return {
        "score": max(0, min(maximum, points)), "max": maximum,
        "detail": f"{len(beats)} 个节拍覆盖 {len(set(intents))} 种意图",
        "blocking_issues": blocking,
    }


def _score_narration_quality(scenes: List[Dict[str, Any]]) -> Dict[str, Any]:
    maximum = DIMENSION_MAX["narration_quality"]
    score = maximum
    warnings: List[str] = []
    suggestions: List[str] = []

    texts = [_narration(scene) for scene in scenes]
    non_empty = [text for text in texts if text]

    duplicates = sorted({text for text in non_empty if non_empty.count(text) > 1})
    if duplicates:
        score -= min(10, 5 * len(duplicates))
        warnings.append(f"存在 {len(duplicates)} 条重复台词")
        suggestions.append("为重复台词补充本幕独有的对象或动作，避免逐幕复述")

    long_sentences = 0
    for text in non_empty:
        for sentence in re.split(r"[。！？；;!?]", text):
            if len(sentence.strip()) > MAX_SENTENCE_CHARS:
                long_sentences += 1
    if long_sentences:
        score -= min(9, 3 * long_sentences)
        suggestions.append(f"{long_sentences} 个句子超过 {MAX_SENTENCE_CHARS} 字，建议按呼吸点断句")

    too_short = [text for text in non_empty if len(text) < MIN_NARRATION_CHARS]
    if too_short:
        score -= min(6, 2 * len(too_short))
        suggestions.append(f"{len(too_short)} 条台词少于 {MIN_NARRATION_CHARS} 字，信息量可能不足")

    openings = [text[:4] for text in non_empty if len(text) >= 4]
    if openings:
        dominant = max(set(openings), key=openings.count)
        if openings.count(dominant) >= 3:
            score -= 3
            warnings.append(f"{openings.count(dominant)} 幕以相同句式开头")
            suggestions.append("改变开场句式，避免每幕都是同一句定语从句")

    return {
        "score": max(0, min(maximum, score)), "max": maximum,
        "detail": (f"{len(non_empty)} 条台词，重复 {len(duplicates)} 条，"
                   f"超长句 {long_sentences} 处"),
        "warnings": warnings, "suggestions": suggestions,
    }


def is_enforced(spec: Dict[str, Any]) -> bool:
    """只有新导演生成（带 story_profile）的剧本才强制质量门槛，历史工程保持可复现。"""
    profile = (spec.get("meta") or {}).get("story_profile")
    return profile in VALID_STORY_PROFILES


def evaluate_storyboard(spec: Dict[str, Any], threshold: int = DEFAULT_QUALITY_THRESHOLD) -> Dict[str, Any]:
    """对剧本打分，返回分数、分项、阻断项与修复建议。"""
    scenes = _scenes(spec)
    dimensions = {
        "visual_diversity": _score_visual_diversity(scenes),
        "rhythm_variety": _score_rhythm_variety(scenes),
        "evidence_integrity": _score_evidence_integrity(scenes, spec),
        "beat_coverage": _score_beat_coverage(scenes, spec),
        "narration_quality": _score_narration_quality(scenes),
    }

    blocking: List[str] = []
    warnings: List[str] = []
    suggestions: List[str] = []
    for name, result in dimensions.items():
        blocking.extend(result.get("blocking_issues", []))
        warnings.extend(result.get("warnings", []))
        suggestions.extend(result.get("suggestions", []))

    # 画面层体检：布局遮挡、镜头跳回、callout 越界属于硬缺陷，直接阻断。
    from engine.visual_qa import analyze_storyboard

    visual = analyze_storyboard(spec)
    blocking.extend(visual["blocking_issues"])
    warnings.extend(visual["warnings"])

    if scenes and len(scenes) < 3:
        blocking.append(f"场景数只有 {len(scenes)} 幕，少于最低要求 3 幕")

    score = sum(result["score"] for result in dimensions.values())
    enforced = is_enforced(spec)
    below_threshold = score < threshold
    if below_threshold:
        suggestions.insert(0, f"质量分 {score} 低于门槛 {threshold}：优先修复得分最低的分项")
    weakest = min(dimensions.items(), key=lambda item: item[1]["score"] / float(item[1]["max"]))
    suggestions.append(f"当前最弱分项是 {weakest[0]}（{weakest[1]['score']}/{weakest[1]['max']}）")

    return {
        "score": score,
        "threshold": threshold,
        "enforced": enforced,
        "passed": (not blocking) and (not below_threshold),
        "breakdown": {
            name: {"score": result["score"], "max": result["max"], "detail": result["detail"]}
            for name, result in dimensions.items()
        },
        "blocking_issues": blocking,
        "warnings": warnings,
        "suggestions": suggestions,
    }


def format_report(report: Dict[str, Any]) -> List[str]:
    """把质量报告渲染为 CLI 可打印的文本行。"""
    lines = [f"  • 质量评分: {report['score']}/100 (门槛 {report['threshold']})"
             + ("" if report["enforced"] else " · 历史工程仅供参考")]
    for name, item in report["breakdown"].items():
        lines.append(f"      - {name}: {item['score']}/{item['max']} · {item['detail']}")
    for issue in report["blocking_issues"]:
        lines.append(f"      ❌ {issue}")
    for warning in report["warnings"]:
        lines.append(f"      ⚠️ {warning}")
    for suggestion in report["suggestions"][:3]:
        lines.append(f"      💡 {suggestion}")
    return lines
