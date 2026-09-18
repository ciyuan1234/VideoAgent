#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VideoAgent Auto Director
导演编排入口：调用大模型（或内置离线节拍规划器）把主题/文档/URL 变成 storyboard.yaml。

职责边界：
- 本模块只负责 LLM 调度、YAML 清洗校验与对外兼容接口。
- 内容信号分析、叙事节拍规划、镜头映射在 engine/story_planner.py。
- 质量评分在 engine/quality_gate.py。
"""

import os
import re
import json
import yaml
import urllib.request
from typing import Any, Dict, Optional

from engine import story_planner as planner

DIRECTOR_SYSTEM_PROMPT = """你是技术短视频的总导演。将用户材料改编为 60~90 秒、真实素材优先的 VideoAgent storyboard.yaml。

【首要原则】
- 先讲事实与操作证据，再使用图解；不要把每个主题塞进同一套标题、跑分、Diff、终端模板。
- 只能陈述输入材料中存在的数据、命令、性能结论和代码。缺证据时使用 `asset_placeholder` 或 `asset_requests` 标记待补录内容，绝不编造 QPS、日志、API 或压测结论。
- 有界面、录屏、实拍或图表素材时，优先使用 `image`（`presentation: cinematic`）或 `video_clip`，并提供 2~4 个 `beats`。每个 beat 使用 `at`（0~1）、`focus`、`scale`、可选 `callout`、`label`、`accent`。
- 一个视频可有 3~6 幕。场景顺序必须由内容决定，而不是固定原语顺序；角色只在开场、转折或收尾出现。

【素材契约】
- 在顶层输出 `asset_requests` 列表，列出每个未提供但会显著提升视频的素材：`id`、`kind`（screen_recording/screenshot/broll/chart）、`purpose`、`suggested_file`、`capture_notes`。
- `asset_placeholder` 只能用于制作中的预览，不可作为最终发布素材。

【格式】
- 必须且仅输出合法 YAML；每幕必须有 `id`、`audio.text` 与 `visual.type`。
- `chart_benchmark` 仅在材料提供可复核数值时使用，并在 visual 中写入 `evidence`。
"""


class AutoDirector:
    """自动导演类：负责 LLM 调度、剧本生成与语法清洗校验。"""

    VALID_STORY_PROFILES = set(planner.VALID_STORY_PROFILES)
    VALID_STORY_VARIANTS = set(planner.VALID_STORY_VARIANTS)

    def __init__(self, root_dir: Optional[str] = None):
        self.root_dir = root_dir or os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
        self.config = self._load_env_config()

    def _load_env_config(self) -> Dict[str, str]:
        """加载环境变量或本地 .env 配置"""
        cfg = {}
        env_file = os.path.join(self.root_dir, ".env")
        if os.path.exists(env_file):
            with open(env_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        k, v = line.split("=", 1)
                        cfg[k.strip()] = v.strip().strip("'\"")

        # 优先读取 OS 环境变量
        for key in ["OPENAI_API_KEY", "OPENAI_BASE_URL", "OPENAI_MODEL",
                    "DEEPSEEK_API_KEY", "GEMINI_API_KEY", "ANTHROPIC_API_KEY"]:
            if os.getenv(key):
                cfg[key] = os.getenv(key)

        return cfg

    def _call_openai_compatible(self, prompt: str, api_key: str, base_url: str, model: str) -> str:
        """调用 OpenAI / DeepSeek / 本地 vLLM / Qwen 等兼容接口"""
        url = f"{base_url.rstrip('/')}/chat/completions"
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": DIRECTOR_SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.3,
        }
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}",
                "User-Agent": "VideoAgent/2.0"
            }
        )
        with urllib.request.urlopen(req, timeout=45) as resp:
            res_json = json.loads(resp.read().decode("utf-8"))
            return res_json["choices"][0]["message"]["content"]

    def _call_gemini(self, prompt: str, api_key: str, model: str = "gemini-1.5-flash") -> str:
        """调用 Google Gemini 原生 API"""
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
        payload = {
            "contents": [{
                "parts": [
                    {"text": f"{DIRECTOR_SYSTEM_PROMPT}\n\n用户提供的技术资料：\n{prompt}"}
                ]
            }],
            "generationConfig": {"temperature": 0.3}
        }
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data,
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=45) as resp:
            res_json = json.loads(resp.read().decode("utf-8"))
            return res_json["candidates"][0]["content"]["parts"][0]["text"]

    # ----------------- 节拍规划的兼容入口（实现位于 story_planner） -----------------

    def analyze_content_signals(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """兼容入口：内容信号分析。"""
        return planner.analyze_content_signals(content)

    def choose_story_profile(self, signals: Dict[str, Any], requested_profile: str = "auto") -> str:
        """兼容入口：叙事结构选择。"""
        return planner.choose_story_profile(signals, requested_profile)

    def extract_story_beats(self, content: Dict[str, Any], story_profile: str = "auto",
                            story_variant: str = "auto") -> Dict[str, Any]:
        """兼容入口：叙事节拍规划。"""
        return planner.extract_story_beats(content, story_profile, story_variant)

    def generate_offline_storyboard(self, content: Dict[str, Any], story_profile: str = "auto",
                                    story_variant: str = "auto") -> str:
        """确定性离线导演：内容信号 -> 节拍计划 -> 分镜。"""
        storyboard = planner.build_storyboard(content, story_profile, story_variant)
        return yaml.dump(storyboard, allow_unicode=True, sort_keys=False)

    # ----------------- LLM 输出的清洗与校验 -----------------

    def sanitize_yaml(self, raw_yaml: str) -> str:
        """清洗并校验大模型返回的 YAML 内容"""
        # 去除 markdown 代码块
        clean = raw_yaml.strip()
        if clean.startswith("```"):
            clean = re.sub(r"^```[a-zA-Z0-9_\-]*\n", "", clean)
            clean = re.sub(r"\n```$", "", clean)

        # 校验 YAML 格式
        data = yaml.safe_load(clean)
        if not isinstance(data, dict):
            raise ValueError("大模型输出不是有效的 YAML 字典对象")

        # 确保关键元数据完整
        if "meta" not in data:
            data["meta"] = {}
        data["meta"].setdefault("resolution", [1920, 1080])
        data["meta"].setdefault("fps", 30)
        data["meta"].setdefault("theme", "white_grid")
        data["meta"].setdefault("speaker", "erii")
        data["meta"].setdefault("story_profile", "concept")
        data["meta"].setdefault("story_variant", "auto")
        data["meta"].setdefault("story_beats", [])
        data["meta"].setdefault("sfx", {"enabled": True})
        if "bgm" not in data["meta"]:
            data["meta"]["bgm"] = {"file": "bgm.mp3", "volume": 0.10, "fade_in": 1.5, "fade_out": 2.0}

        if "scenes" not in data or not isinstance(data["scenes"], list):
            raise ValueError("剧本中缺失 scenes 场景列表")
        if not data["scenes"]:
            raise ValueError("剧本至少需要一个场景")
        if "asset_requests" not in data:
            data["asset_requests"] = []
        if not isinstance(data["asset_requests"], list):
            raise ValueError("asset_requests 必须为列表")
        profile = data["meta"].get("story_profile")
        if profile not in self.VALID_STORY_PROFILES - {"auto"}:
            raise ValueError(f"meta.story_profile 必须是 {sorted(self.VALID_STORY_PROFILES - {'auto'})} 之一")
        if data["meta"]["story_variant"] not in self.VALID_STORY_VARIANTS:
            raise ValueError(f"meta.story_variant 不支持: {data['meta']['story_variant']}")
        if not isinstance(data["meta"]["story_beats"], list):
            raise ValueError("meta.story_beats 必须为列表")
        visual_types = []

        # 规范化每个场景
        valid_stickers = ["erii_presenter", "erii_chibi_think", "erii_chibi_cheer", "erii_chibi_happy", "erii_avatar"]
        for idx, sc in enumerate(data["scenes"]):
            if not isinstance(sc, dict):
                raise ValueError(f"场景 {idx + 1} 必须是字典")
            if not sc.get("id"):
                sc["id"] = f"scene_{idx + 1}"
            audio = sc.get("audio")
            if not isinstance(audio, dict) or not audio.get("text"):
                raise ValueError(f"场景 {sc['id']} 缺少 audio.text")
            visual = sc.get("visual")
            if not isinstance(visual, dict) or not visual.get("type"):
                raise ValueError(f"场景 {sc['id']} 缺少 visual.type")
            if "character_sticker" not in sc or sc["character_sticker"] not in valid_stickers:
                sc["character_sticker"] = valid_stickers[idx % len(valid_stickers)]
            audio.setdefault("speed", 1.05)
            audio.setdefault("pause", 0.45)
            audio.setdefault("emotion", "normal")

            visual_type = visual["type"]
            visual_types.append(visual_type)
            if visual_type == "chart_benchmark" and not visual.get("evidence"):
                raise ValueError(f"场景 {sc['id']} 的 chart_benchmark 缺少可复核 evidence")
            if visual_type in ["image", "screenshot", "video_clip", "video", "clip"]:
                visual.setdefault("presentation", "cinematic")
                for beat in visual.get("beats", []):
                    if not isinstance(beat, dict):
                        raise ValueError(f"场景 {sc['id']} 的 beats 项必须是字典")
                    at = float(beat.get("at", 0.0))
                    if not 0.0 <= at <= 1.0:
                        raise ValueError(f"场景 {sc['id']} 的 beat.at 必须在 0 到 1 之间")
                    focus = beat.get("focus", [0.5, 0.5])
                    if not isinstance(focus, list) or len(focus) != 2:
                        raise ValueError(f"场景 {sc['id']} 的 beat.focus 必须为 [x, y]")

        for previous, current in zip(visual_types, visual_types[1:]):
            if previous == current and current not in {"asset_placeholder", "material_placeholder"}:
                raise ValueError(f"相邻场景不能重复使用 {current}，请调整镜头结构")

        if data["meta"]["story_beats"]:
            scene_ids = {scene["id"] for scene in data["scenes"]}
            beat_scene_ids = [beat.get("scene_id") for beat in data["meta"]["story_beats"] if isinstance(beat, dict)]
            if len(beat_scene_ids) != len(data["meta"]["story_beats"]) or set(beat_scene_ids) != scene_ids:
                raise ValueError("meta.story_beats 必须与 scenes 一一对应")

        return yaml.dump(data, allow_unicode=True, sort_keys=False)

    # ----------------- 对外主入口 -----------------

    def generate_storyboard(
        self,
        content: Dict[str, Any],
        provider: Optional[str] = None,
        model: Optional[str] = None,
        api_key: Optional[str] = None,
        story_profile: str = "auto",
        story_variant: str = "auto",
    ) -> str:
        """根据输入内容与配置，自动生成 storyboard YAML 文本"""
        if story_profile not in self.VALID_STORY_PROFILES:
            raise ValueError(f"不支持的 story_profile: {story_profile}")
        if story_variant not in self.VALID_STORY_VARIANTS:
            raise ValueError(f"不支持的 story_variant: {story_variant}")
        signals = planner.analyze_content_signals(content)
        resolved_profile = planner.choose_story_profile(signals, story_profile)
        user_prompt = f"""请根据以下提取的技术内容，编写一份 60~90 秒、3~6 幕、素材优先的 VideoAgent 剧本。

先输出 asset_requests，标注缺少但需要补录的真实素材；再输出 scenes。没有材料证据时，不得编造跑分、日志、命令或代码 Diff。真实截图/录屏必须优先使用 image/video_clip + cinematic beats。
本片叙事结构为 `{resolved_profile}`；必须写入 meta.story_profile: `{resolved_profile}`。输入中发现的可复核数值：{signals['metric_evidence'] or '无'}。

【技术资料标题】: {content.get('title')}
【核心要点】:
{chr(10).join(f"- {b}" for b in content.get('bullets', [])[:8])}

【各节概要】:
{chr(10).join(f"• {h}" for h in content.get('headings', [])[:8])}

【参考正文】:
{content.get('raw_text', '')[:2500]}
"""

        # 检查可用的 API
        effective_provider = provider
        effective_key = api_key
        effective_model = model

        if not effective_key:
            if self.config.get("DEEPSEEK_API_KEY"):
                effective_provider = "deepseek"
                effective_key = self.config.get("DEEPSEEK_API_KEY")
                effective_model = effective_model or "deepseek-chat"
            elif self.config.get("OPENAI_API_KEY"):
                effective_provider = "openai"
                effective_key = self.config.get("OPENAI_API_KEY")
                effective_model = effective_model or self.config.get("OPENAI_MODEL", "gpt-4o")
            elif self.config.get("GEMINI_API_KEY"):
                effective_provider = "gemini"
                effective_key = self.config.get("GEMINI_API_KEY")
                effective_model = effective_model or "gemini-1.5-flash"

        # 如果没有配置 API Key，平滑切入离线知识萃取引擎
        if not effective_key or effective_provider == "offline":
            print("ℹ️ 未检测到 LLM API Key，自动启用【内置智能语义萃取引擎】进行剧本编排...")
            return self.generate_offline_storyboard(content, story_profile=story_profile, story_variant=story_variant)

        # 尝试调用 LLM
        try:
            print(f"🤖 正在调用 {effective_provider} ({effective_model}) 导演模型编写分镜剧本...")
            if effective_provider == "deepseek":
                raw_yaml = self._call_openai_compatible(
                    user_prompt,
                    api_key=effective_key,
                    base_url="https://api.deepseek.com/v1",
                    model=effective_model or "deepseek-chat"
                )
            elif effective_provider == "openai":
                base_url = self.config.get("OPENAI_BASE_URL", "https://api.openai.com/v1")
                raw_yaml = self._call_openai_compatible(
                    user_prompt,
                    api_key=effective_key,
                    base_url=base_url,
                    model=effective_model or "gpt-4o"
                )
            elif effective_provider == "gemini":
                raw_yaml = self._call_gemini(
                    user_prompt,
                    api_key=effective_key,
                    model=effective_model or "gemini-1.5-flash"
                )
            else:
                raw_yaml = self._call_openai_compatible(
                    user_prompt,
                    api_key=effective_key,
                    base_url=self.config.get("OPENAI_BASE_URL", "https://api.openai.com/v1"),
                    model=effective_model or "gpt-4o"
                )

            return self.sanitize_yaml(raw_yaml)
        except Exception as e:
            print(f"⚠️ 大模型调用发生异常 ({e})，安全降级至【内置智能语义萃取引擎】...")
            return self.generate_offline_storyboard(content, story_profile=story_profile, story_variant=story_variant)
