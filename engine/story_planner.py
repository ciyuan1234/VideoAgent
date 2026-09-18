#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VideoAgent Story Planner
确定性内容节拍规划器：内容信号 -> 叙事节拍 -> 分镜。

该模块不调用 LLM，不触碰文件系统；给定相同输入必须产出相同剧本，
便于快照回归与人工审阅。
"""

import re
from typing import Any, Dict, List, Optional

from engine.text_metrics import fit_text_to_width

VALID_STORY_PROFILES = ("auto", "tutorial", "concept", "code_walkthrough", "decision")
VALID_STORY_VARIANTS = ("auto", "evidence_first", "mechanism_first")

ASSET_TAG_HINTS = {
    "operation": ("demo", "record", "terminal", "install", "run", "screen", "tutorial"),
    "code": ("code", "source", "diff", "editor"),
    "architecture": ("arch", "diagram", "flow", "node"),
    "metrics": ("metric", "chart", "benchmark", "monitor"),
}

# 每个节拍期望哪一类素材；未命中的节拍会退化为素材占位。
BEAT_ASSET_TAG = {
    "operation": "operation",
    "runtime_evidence": "operation",
    "decision_evidence": "metrics",
    "source": "code",
    "mechanism": "architecture",
}

PROFILE_TAG = {
    "tutorial": "跟着操作",
    "concept": "机制拆解",
    "code_walkthrough": "源码走读",
    "decision": "方案决策",
}

# 只有这些单位能独立证明“这是一个可复核的量化指标”。
STRONG_METRIC_UNITS = {"QPS", "TPS", "RPS", "ms", "MB", "GB", "KB", "%"}
# 这些单位本身有歧义（变焦倍率、分辨率、循环次数都会用到），必须邻近性能语境才算指标。
AMBIGUOUS_METRIC_UNITS = {"x", "倍"}
METRIC_UNIT_CANONICAL = {
    "qps": "QPS", "tps": "TPS", "rps": "RPS",
    "ms": "ms", "mb": "MB", "gb": "GB", "kb": "KB",
    "%": "%", "x": "x", "倍": "倍",
}
# 「放大到 1.08x」「1920x1080」等非性能用法需要被排除。
RESOLUTION_PATTERN = re.compile(r"\d+(?:\.\d+)?\s*[x×]\s*\d+", re.IGNORECASE)
METRIC_CONTEXT_WORDS = (
    "性能", "提升", "降低", "吞吐", "延迟", "压测", "基准", "优化",
    "提速", "倍速", "更快", "更慢", "响应", "耗时", "下降", "增长",
)
METRIC_PATTERN = re.compile(
    r"(?<![\w.])(\d+(?:\.\d+)?)\s*(QPS|TPS|RPS|ms|MB|GB|KB|%|倍|x)(?!\w)",
    re.IGNORECASE,
)

# 来源文档常用 emoji 做标题装饰，但 CJK 字体没有对应字形，渲染出来是豆腐块。
UNSUPPORTED_GLYPH_PATTERN = re.compile(
    "["
    "\U0001F000-\U0001FAFF"  # 表情与象形符号
    "\U00002600-\U000027BF"  # 杂项符号、装饰符号、箭头
    "\U00002B00-\U00002BFF"  # 杂项符号与箭头
    "\U00002190-\U000021FF"  # 箭头
    "\uFE0F\u200D\u20E3"      # 变体选择符、零宽连接符、键帽
    "]+"
)


def strip_unsupported_glyphs(text: str) -> str:
    """移除当前字体无法绘制、会渲染成豆腐块的符号。"""
    cleaned = UNSUPPORTED_GLYPH_PATTERN.sub(" ", str(text))
    return re.sub(r"\s{2,}", " ", cleaned).strip()


def extract_metrics(raw_text: str) -> List[Dict[str, Any]]:
    """只提取可复核的量化指标，排除变焦倍率、分辨率等无关数字。

    返回 `[{"value": float, "unit": str, "raw": str}]`，保持首次出现顺序并去重。
    """
    text = RESOLUTION_PATTERN.sub(" ", str(raw_text))
    collected: List[Dict[str, Any]] = []
    seen = set()
    for match in METRIC_PATTERN.finditer(text):
        raw_value, raw_unit = match.group(1), match.group(2)
        unit = METRIC_UNIT_CANONICAL.get(raw_unit.lower(), raw_unit)
        if unit in AMBIGUOUS_METRIC_UNITS:
            window = text[max(0, match.start() - 24):match.end() + 24]
            if not any(word in window for word in METRIC_CONTEXT_WORDS):
                continue
        raw = f"{raw_value} {unit}"
        if raw in seen:
            continue
        seen.add(raw)
        collected.append({"value": float(raw_value), "unit": unit, "raw": raw})
    return collected


def analyze_content_signals(content: Dict[str, Any]) -> Dict[str, Any]:
    """只提取可观测信号；绝不把缺失证据变成技术结论。"""
    title = strip_unsupported_glyphs(content.get("title", "技术主题")) or "技术主题"
    raw_text = str(content.get("raw_text", ""))
    headings = [strip_unsupported_glyphs(item) for item in content.get("headings", [])]
    bullets = [strip_unsupported_glyphs(item) for item in content.get("bullets", [])]
    corpus = "\n".join([title, raw_text, *headings, *bullets]).lower()
    code_snippets = [item for item in content.get("code_snippets", []) if item.get("code")]
    keywords = {
        "tutorial": ("教程", "安装", "配置", "步骤", "使用", "实战", "操作", "命令", "deploy", "install", "quickstart"),
        "decision": ("对比", "选型", "vs", "方案", "优缺点", "tradeoff", "比较", "替代"),
        "concept": ("原理", "机制", "架构", "模型", "调度", "内核", "协议", "工作原理"),
    }
    scores = {name: sum(token in corpus for token in tokens) for name, tokens in keywords.items()}
    scores["code_walkthrough"] = len(code_snippets) * 4 + sum(
        token in corpus for token in ("源码", "代码", "函数", "实现", "api", "class")
    )
    metrics = extract_metrics(raw_text)
    has_strong_metric = any(metric["unit"] in STRONG_METRIC_UNITS for metric in metrics)
    # 至少两个指标、且其中一个是无歧义单位，才允许生成图表。
    has_explicit_metrics = len(metrics) >= 2 and has_strong_metric
    facts = [item for item in [*headings, *bullets] if item.strip()][:6]
    return {
        "title": title,
        "raw_text": raw_text,
        "facts": facts,
        "code_snippets": code_snippets,
        "scores": scores,
        "metrics": metrics,
        "metric_evidence": [metric["raw"] for metric in metrics[:4]],
        "has_explicit_metrics": has_explicit_metrics,
        "source_type": content.get("source_type", "topic"),
        "assets": list(content.get("available_assets", []) or []),
    }


def choose_story_profile(signals: Dict[str, Any], requested_profile: str = "auto") -> str:
    requested_profile = requested_profile or "auto"
    if requested_profile not in VALID_STORY_PROFILES:
        raise ValueError(f"不支持的 story_profile: {requested_profile}")
    if requested_profile != "auto":
        return requested_profile
    scores = signals["scores"]
    # 只有材料里确实存在源码时才可能走源码走读，再与其它内容意图比较。
    if signals["code_snippets"] and scores["code_walkthrough"] >= max(
        scores["tutorial"], scores["decision"], scores["concept"]
    ):
        return "code_walkthrough"
    return max(("tutorial", "decision", "concept"), key=lambda profile: scores[profile])


def _beat(beat_id: str, intent: str, evidence_level: str, visuals: List[str],
          source_refs: List[str], requires_asset: bool = False) -> Dict[str, Any]:
    return {
        "id": beat_id,
        "intent": intent,
        "evidence_level": evidence_level,
        "source_refs": source_refs,
        "preferred_visuals": visuals,
        "requires_asset": requires_asset,
    }


def extract_story_beats(content: Dict[str, Any], story_profile: str = "auto",
                        story_variant: str = "auto") -> Dict[str, Any]:
    """在挑选任何视觉原语之前，先生成可审阅的确定性叙事计划。"""
    if story_variant not in VALID_STORY_VARIANTS:
        raise ValueError(f"不支持的 story_variant: {story_variant}")
    signals = analyze_content_signals(content)
    profile = choose_story_profile(signals, story_profile)
    facts = signals["facts"] or [f"{signals['title']} 的背景", "关键机制", "实际取舍"]
    source_refs = facts[:4]

    candidates = [_beat("hook", "提出材料中的核心问题", "derived", ["title_card"], source_refs)]
    if profile == "tutorial":
        candidates += [
            _beat("operation", "展示关键操作和结果", "required", ["video_clip", "image"], source_refs, True),
            _beat("workflow", "解释操作步骤之间的关系", "derived", ["custom_nodes"], source_refs),
        ]
    elif profile == "decision":
        candidates += [
            _beat("comparison", "对比方案的适用边界", "derived", ["split_compare"], source_refs),
            _beat("decision_evidence", "展示目标环境的约束或结果", "required", ["image", "video_clip"], source_refs, True),
        ]
    else:
        if signals["code_snippets"]:
            candidates.append(_beat("source", "定位输入材料中的关键实现", "source", ["code"], source_refs))
        candidates.append(_beat("mechanism", "解释材料中已给出的对象关系", "derived", ["custom_nodes"], source_refs))
        candidates.append(_beat("runtime_evidence", "验证运行时状态或结果", "required", ["video_clip", "image"], source_refs, True))
    if signals["has_explicit_metrics"]:
        candidates.append(_beat("metrics", "展示材料提供的可复核数据", "source", ["chart_benchmark"], source_refs))
    candidates.append(_beat("takeaway", "回到真实项目中的验证动作", "derived", ["title_card"], source_refs))

    middle = candidates[1:-1]
    if story_variant == "auto":
        story_variant = "evidence_first" if sum(ord(c) for c in signals["title"]) % 2 else "mechanism_first"
    if story_variant == "evidence_first":
        middle.sort(key=lambda item: 0 if item["requires_asset"] else 1)
    else:
        middle.sort(key=lambda item: 1 if item["requires_asset"] else 0)
    # 短视频保留 hook 与 takeaway，中间只取最相关的 1~4 个节拍。
    beats = [candidates[0], *middle[:4], candidates[-1]]
    return {"profile": profile, "variant": story_variant, "signals": signals, "facts": facts, "beats": beats}


def asset_tags(asset: Dict[str, Any]) -> set:
    """素材标签：显式 tags 优先，其次从文件名推断。"""
    tags = {str(tag).lower() for tag in asset.get("tags", []) or []}
    name = str(asset.get("file", "")).lower()
    for tag, hints in ASSET_TAG_HINTS.items():
        if any(hint in name for hint in hints):
            tags.add(tag)
    return tags


def match_asset_for_beat(beat: Dict[str, Any], assets: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """按节拍语义匹配素材，而不是直接取目录里的第一个文件。"""
    wanted = BEAT_ASSET_TAG.get(beat["id"])
    best, best_score = None, 0
    for asset in assets:
        score = 0
        if wanted and wanted in asset_tags(asset):
            score += 10
        if beat.get("requires_asset") and asset.get("kind") == "video":
            score += 3
        if asset.get("kind") == "video":
            score += 1
        if score > best_score:
            best, best_score = asset, score
    return best


def asset_request(request_id: str, purpose: str, kind: str = "screen_recording") -> Dict[str, str]:
    extension = "mp4" if kind == "screen_recording" else "png"
    return {
        "id": request_id,
        "kind": kind,
        "purpose": purpose,
        "suggested_file": f"extra_assets/{request_id}.{extension}",
        "capture_notes": "8~15 秒，仅保留关键动作与结果；录制前遮蔽账号、令牌和私密数据。",
    }


def placeholder_scene(request: Dict[str, str], narration: str) -> Dict[str, Any]:
    return {
        "id": request["id"],
        "character_mode": "none",
        "transition": "cut",
        "audio": {"text": narration, "speed": 1.0, "pause": 0.35, "emotion": "normal"},
        "visual": {
            "type": "asset_placeholder",
            "header_title": "等待真实操作证据",
            "required_asset": request["suggested_file"],
            "purpose": request["purpose"],
            "capture_notes": request["capture_notes"],
        },
    }


def _cinematic_scene(scene_id: str, narration: str, visual_type: str, asset: Dict[str, Any],
                     purpose: str) -> Dict[str, Any]:
    # label 画在左下角、与居中字幕同一横带，必须是短语，否则会遮挡字幕（见 engine/visual_qa.py）。
    short_label = purpose if len(purpose) <= 16 else "查看关键操作与结果"
    visual = {
        "type": visual_type,
        "presentation": "cinematic",
        "file": asset["file"],
        "beats": [
            {"at": 0.0, "focus": [0.5, 0.45], "scale": 1.04, "label": "建立全局上下文", "accent": "indigo"},
            {"at": 0.55, "focus": [0.5, 0.70], "scale": 1.28, "label": short_label, "accent": "emerald"},
        ],
    }
    if visual_type == "video_clip":
        visual["clip_fps"] = 12
    return {
        "id": scene_id,
        "character_mode": "none",
        "transition": "cut",
        "audio": {"text": narration, "speed": 1.0, "pause": 0.35, "emotion": "normal"},
        "visual": visual,
    }


def scene_from_beat(beat: Dict[str, Any], plan: Dict[str, Any]) -> Dict[str, Any]:
    """把单个节拍映射为分镜；需要真实证据但缺素材时保留可见的占位。"""
    signals, facts = plan["signals"], plan["facts"]
    title = signals["title"]
    beat_id = beat["id"]
    node_themes = ["blue", "amber", "green", "white"]
    # 节点卡是固定 320x150，标题按可用宽度预裁，避免渲染期截断。
    nodes = [
        {"title": fit_text_to_width(f"{i + 1}. {fact}", 272, 24),
         "sub": "来自输入材料", "theme": node_themes[i]}
        for i, fact in enumerate(facts[:4])
    ]
    base = {
        "id": beat_id,
        "character_mode": "none",
        "transition": "slide_left",
        "audio": {"text": "", "speed": 1.0, "pause": 0.35, "emotion": "calm"},
    }
    # 运镜按节拍意图分配：开场冲击、解释推进、收束安静；真实素材镜头由 cinematic beats 自行运动。
    if beat_id == "hook":
        base["camera"] = {"motion": "zoom_punch"}
    elif beat_id in {"source", "mechanism", "workflow", "metrics", "comparison"}:
        base["camera"] = {"motion": "zoom_in"}

    if beat_id == "hook":
        base.update({
            "character_sticker": "erii_presenter",
            "audio": {"text": f"Sakura，今天从 {title} 的真实材料出发，只讲可以验证的部分。",
                      "speed": 1.03, "pause": 0.35, "emotion": "normal"},
            "visual": {"type": "title_card", "tag": "从证据出发", "title": title,
                       "subtitle": "先看问题，再看证据", "bullets": facts[:3]},
        })
    elif beat_id == "takeaway":
        base.update({
            "character_sticker": "erii_chibi_happy",
            "transition": "cut",
            "audio": {"text": "最后，把这条线索带回自己的项目验证；结论应该来自真实素材，而不是套用模板。",
                      "speed": 1.03, "pause": 0.35, "emotion": "normal"},
            "visual": {"type": "title_card", "tag": "下一步", "title": "回到真实项目验证",
                       "subtitle": "补齐证据后再发布", "bullets": facts[:3]},
        })
    elif beat_id in {"mechanism", "workflow"}:
        base["audio"]["text"] = "把材料中的关系展开，只解释已经给出的对象与步骤。"
        base["visual"] = {"type": "custom_nodes", "header_title": "关键关系",
                          "header_sub": "由输入材料提炼", "nodes": nodes}
    elif beat_id == "source":
        snippet = signals["code_snippets"][0]
        base["audio"]["text"] = "这段源码是机制落点；关注状态与控制流，不外推没有证据支持的结论。"
        base["visual"] = {"type": "code", "header_title": "关键源码片段", "header_sub": "来自输入材料",
                          "lang": snippet.get("lang", "text"), "theme": "OneHalfLight",
                          "spotlight_line": 1, "code": snippet["code"][:700]}
    elif beat_id == "comparison":
        left, right = (facts + ["方案 A", "方案 B"])[:2]
        base["audio"]["text"] = "把选择条件摆在台面上；差异来自适用边界，而不是一句绝对的谁更快。"
        base["visual"] = {
            "type": "split_compare", "header_title": "方案取舍", "header_sub": "仅依据输入材料描述",
            "left": {"badge": "方案 A", "title": left, "bullets": facts[:2],
                     "metrics": {"label": "关注点", "value": "适用边界"}},
            "right": {"badge": "方案 B", "title": right, "bullets": facts[2:4] or facts[:2],
                      "metrics": {"label": "决策依据", "value": "真实约束"}},
        }
    elif beat_id == "metrics":
        values = [
            {"label": f"材料指标 {i + 1}", "value": metric["value"], "unit": metric["unit"], "theme": theme}
            for i, (metric, theme) in enumerate(zip(signals.get("metrics", [])[:3], ["blue", "amber", "green"]))
        ]
        base["audio"]["text"] = "这组数据直接来自输入材料；解读前仍需核对测试条件。"
        base["visual"] = {"type": "chart_benchmark", "header_title": "材料提供的数据",
                          "header_sub": "未补充输入材料之外的数值", "data": values,
                          "champion_tag": "结合条件解读", "evidence": signals["metric_evidence"]}
    else:
        asset = match_asset_for_beat(beat, signals["assets"])
        purpose = f"展示 {title} 的关键操作、状态变化或运行结果"
        if asset:
            visual_type = "video_clip" if asset.get("kind") == "video" else "image"
            base = _cinematic_scene(beat_id, "现在切到真实素材，观察刚才的关键动作或结果。",
                                    visual_type, asset, purpose)
        else:
            request = asset_request(
                beat_id, purpose,
                "screen_recording" if beat_id != "decision_evidence" else "screenshot",
            )
            base = placeholder_scene(request, "这里需要真实操作或运行结果；补录素材后再输出发布版。")
            base["asset_request"] = request
    return base


def build_storyboard(content: Dict[str, Any], story_profile: str = "auto",
                     story_variant: str = "auto") -> Dict[str, Any]:
    """完整离线导演流程：内容信号 -> 节拍计划 -> 分镜。"""
    plan = extract_story_beats(content, story_profile, story_variant)
    scenes: List[Dict[str, Any]] = []
    requests: List[Dict[str, Any]] = []
    for beat in plan["beats"]:
        scene = scene_from_beat(beat, plan)
        request = scene.pop("asset_request", None)
        if request:
            requests.append(request)
        scenes.append(scene)

    summary = [
        {"id": beat["id"], "intent": beat["intent"],
         "evidence_level": beat["evidence_level"], "scene_id": scene["id"]}
        for beat, scene in zip(plan["beats"], scenes)
    ]
    signals = plan["signals"]
    return {
        "meta": {
            "title": f"{signals['title']}：从证据理解技术",
            "resolution": [1920, 1080],
            "fps": 30,
            "theme": "white_grid",
            "speaker": "erii",
            "story_profile": plan["profile"],
            "story_variant": plan["variant"],
            "story_beats": summary,
            "production_style": "material_first",
            "content_evidence": {
                "facts": plan["facts"],
                "metrics": signals["metric_evidence"],
                "source_type": signals["source_type"],
            },
            "bgm": {"file": "bgm.mp3", "volume": 0.10, "fade_in": 1.5, "fade_out": 2.0},
            "sfx": {"enabled": True},
        },
        "asset_requests": requests,
        "scenes": scenes,
    }


def collect_available_assets(assets_dir: str) -> List[Dict[str, Any]]:
    """扫描工程的 extra_assets/，为导演提供可编排的真实素材清单。"""
    import os

    if not os.path.isdir(assets_dir):
        return []
    video_suffixes = {".mp4", ".mov", ".webm"}
    image_suffixes = {".png", ".jpg", ".jpeg", ".webp"}
    collected = []
    for filename in sorted(os.listdir(assets_dir)):
        suffix = os.path.splitext(filename)[1].lower()
        if suffix not in video_suffixes | image_suffixes:
            continue
        asset = {"file": filename, "kind": "video" if suffix in video_suffixes else "image"}
        asset["tags"] = sorted(asset_tags(asset))
        collected.append(asset)
    return collected
