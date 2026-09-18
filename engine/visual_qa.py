#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VideoAgent Visual QA
确定性画面体检：只依据 storyboard 与渲染器已知布局常量做检查，不引入图像模型。

阈值直接来自 engine/compositor.py 的实际绘制逻辑：
- _render_cinematic_asset 把 label 画在 (42, height-91)、字号 30
- render_subtitle_pill 字号 28、左右各 32 内边距、超过 24 字折行、默认水平居中
因此「label 右边界」与「居中字幕胶囊左边界」发生重叠即为真实遮挡风险。
"""

from typing import Any, Dict, List, Tuple

from engine.text_metrics import estimate_text_width, fit_text_to_width, max_chars_for_width
from engine.tts_engine import split_sentences

# 与 compositor.py 保持一致的布局常量。
LABEL_X = 42
LABEL_FONT_SIZE = 30
SUBTITLE_FONT_SIZE = 28
SUBTITLE_MAX_CHARS = 24
SUBTITLE_PAD_X = 32
CALLOUT_MIN_SIZE = 0.04
LABEL_SAFE_MARGIN = 16

CINEMATIC_VISUALS = {"image", "screenshot", "showcase", "diagram_or_image", "video_clip", "video", "clip"}


def estimate_subtitle_pill_width(narration: str) -> float:
    """复现 render_subtitle_pill 的折行与宽度计算。"""
    text = str(narration or "")
    if not text:
        return 0.0
    if len(text) > SUBTITLE_MAX_CHARS:
        half = len(text) // 2
        split = half
        for index in range(max(0, half - 6), min(len(text), half + 6)):
            if text[index] in "，、；： ":
                split = index + 1
                break
        lines = [text[:split].strip(), text[split:].strip()]
    else:
        lines = [text]
    widest = max(estimate_text_width(line, SUBTITLE_FONT_SIZE) for line in lines)
    return widest + SUBTITLE_PAD_X * 2


def estimate_scene_max_pill_width(narration: str) -> float:
    """字幕逐句显示，因此取该幕所有断句中最宽的胶囊宽度作为最坏情况。"""
    sentences = split_sentences(str(narration or "")) or [""]
    return max(estimate_subtitle_pill_width(sentence) for sentence in sentences)


def label_safe_width(narration: str, frame_width: int = 1920) -> float:
    """左下角标签可用的最大像素宽度（不侵入居中字幕胶囊）。"""
    pill_width = estimate_scene_max_pill_width(narration)
    return max(120.0, (frame_width - pill_width) / 2.0 - LABEL_SAFE_MARGIN - LABEL_X)


def fit_label_to_width(label: str, max_width: float) -> str:
    """按估算宽度截断标签并追加省略号，保证渲染时不会压到字幕。"""
    return fit_text_to_width(label, max_width, LABEL_FONT_SIZE)


# 节点卡固定 320x150，标题字号 24、副标题字号 20，左右各留 24px 内边距。
NODE_WIDTH = 320
NODE_TITLE_FONT_SIZE = 24
NODE_SUB_FONT_SIZE = 20
NODE_PADDING = 24
NODE_TEXT_BUDGET = NODE_WIDTH - NODE_PADDING * 2


def _check_beats(scene_id: str, visual: Dict[str, Any], narration: str,
                 frame_width: int) -> Tuple[List[str], List[str]]:
    issues: List[str] = []
    warnings: List[str] = []
    beats = visual.get("beats") or []
    if not beats:
        return issues, warnings

    previous_at = -1.0
    pill_width = estimate_scene_max_pill_width(narration)
    safe_right = (frame_width - pill_width) / 2.0 - LABEL_SAFE_MARGIN

    for index, beat in enumerate(beats):
        if not isinstance(beat, dict):
            issues.append(f"{scene_id}.beats[{index}]: 必须是对象")
            continue

        at = float(beat.get("at", 0.0))
        if at < previous_at:
            issues.append(f"{scene_id}.beats[{index}]: at={at} 未按时间递增，镜头会跳回")
        if index == 0 and abs(at) > 1e-6:
            warnings.append(f"{scene_id}.beats[0]: 首个节拍 at={at} 不为 0，开场存在空镜")
        previous_at = at

        focus = beat.get("focus", [0.5, 0.5])
        if not isinstance(focus, (list, tuple)) or len(focus) != 2:
            issues.append(f"{scene_id}.beats[{index}]: focus 必须是 [x, y]")
        elif not all(0.0 <= float(value) <= 1.0 for value in focus):
            issues.append(f"{scene_id}.beats[{index}]: focus 超出素材归一化范围 {focus}")

        callout = beat.get("callout")
        if callout is not None:
            if not isinstance(callout, (list, tuple)) or len(callout) != 4:
                issues.append(f"{scene_id}.beats[{index}]: callout 必须是 [x, y, w, h]")
            else:
                x, y, w, h = (float(value) for value in callout)
                if x < 0 or y < 0 or x + w > 1.0 or y + h > 1.0:
                    issues.append(f"{scene_id}.beats[{index}]: callout 越界 {callout}")
                if w < CALLOUT_MIN_SIZE or h < CALLOUT_MIN_SIZE:
                    warnings.append(f"{scene_id}.beats[{index}]: callout 过小，观众难以识别")

        label = str(beat.get("label") or "")
        if label and pill_width:
            label_right = LABEL_X + estimate_text_width(label, LABEL_FONT_SIZE)
            if label_right > safe_right:
                issues.append(
                    f"{scene_id}.beats[{index}]: label 宽约 {int(label_right)}px，超过左下角安全宽度 "
                    f"{int(safe_right)}px（再长就会被居中字幕遮挡，渲染时已强制截断），"
                    f"请缩短为 “{label[:8]}…” 这类短语"
                )
    return issues, warnings


def analyze_storyboard(spec: Dict[str, Any], frame_width: int = None) -> Dict[str, Any]:
    """对剧本做画面层体检，返回阻断项与提示。"""
    if frame_width is None:
        # 竖屏成片必须按实际画布宽度判断安全线，不能写死 1920。
        resolution = (spec.get("meta") or {}).get("resolution") or [1920, 1080]
        frame_width = int(resolution[0])
    scenes = [scene for scene in (spec.get("scenes") or []) if isinstance(scene, dict)]
    issues: List[str] = []
    warnings: List[str] = []
    static_scenes: List[str] = []
    labels: List[str] = []

    for scene in scenes:
        scene_id = str(scene.get("id") or "scene")
        visual = scene.get("visual") if isinstance(scene.get("visual"), dict) else {}
        visual_type = scene.get("layout") or visual.get("type") or "unknown"
        narration = str(((scene.get("audio") or {}).get("text")) or scene.get("voice_text") or "")

        beat_issues, beat_warnings = _check_beats(scene_id, visual, narration, frame_width)
        issues.extend(beat_issues)
        warnings.extend(beat_warnings)

        pill_width = estimate_scene_max_pill_width(narration)
        if pill_width > frame_width - 80:
            issues.append(
                f"{scene_id}: 最长字幕胶囊约 {int(pill_width)}px，已接近或超出画面宽度 {frame_width}px，"
                "请缩短该句或增加折行数"
            )

        for beat in visual.get("beats") or []:
            if isinstance(beat, dict) and beat.get("label"):
                labels.append(str(beat["label"]))

        has_camera = bool((scene.get("camera") or {}).get("motion"))
        has_beats = bool(visual.get("beats"))
        # 真实素材镜头靠 beats 运动，不算静止；其余场景既无运镜也无位移即为静态。
        if not has_camera and not has_beats and visual_type not in CINEMATIC_VISUALS:
            static_scenes.append(scene_id)

        for index, node in enumerate(visual.get("nodes") or []):
            if not isinstance(node, dict):
                continue
            budget = NODE_TEXT_BUDGET
            title = str(node.get("title") or "")
            sub = str(node.get("sub") or "")
            if estimate_text_width(title, NODE_TITLE_FONT_SIZE) > budget:
                warnings.append(
                    f"{scene_id}.nodes[{index}]: 标题超宽（{title!r}），渲染时会被截断，建议压到 "
                    f"{max_chars_for_width(budget, NODE_TITLE_FONT_SIZE)} 个汉字以内"
                )
            if estimate_text_width(sub, NODE_SUB_FONT_SIZE) > budget:
                warnings.append(f"{scene_id}.nodes[{index}]: 副标题超宽，渲染时会被截断")

    if len(scenes) >= 3 and len(static_scenes) == len(scenes):
        issues.append(f"全片 {len(scenes)} 幕均为静态画面（既无 camera 也无 beats），观感等同幻灯片")
    elif static_scenes:
        warnings.append("以下场景没有任何位移，建议补 camera.motion: " + ", ".join(static_scenes))

    duplicated = sorted({label for label in labels if labels.count(label) > 1})
    if duplicated:
        warnings.append("以下镜头标签重复使用，无法体现节拍差异: " + ", ".join(duplicated))

    return {
        "checked_scenes": len(scenes),
        "static_scenes": static_scenes,
        "blocking_issues": issues,
        "warnings": warnings,
        "passed": not issues,
    }


def estimate_scene_seconds(scene: Dict[str, Any]) -> float:
    """无 TTS 时按字数估算幕时长，仅用于抽帧定位，不参与成片时间轴。"""
    audio = scene.get("audio") if isinstance(scene.get("audio"), dict) else {}
    text = str(audio.get("text") or scene.get("voice_text") or "")
    speed = float(audio.get("speed") or 1.05)
    pause = float(audio.get("pause") or 0.35)
    # 中文配音在 speed=1.0 时约 4.5 字/秒，按句间停顿叠加。
    spoken = len(text) / (4.5 * max(0.5, speed))
    return max(2.0, spoken + pause)
