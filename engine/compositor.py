#!/Users/a1-6/GPT-SoVITS/venv/bin/python
# -*- coding: utf-8 -*-
"""
VideoAgent Core Engine - Compositor Module (V2 - 动态视听设计系统)
声明式剧本 (storyboard.yaml) 驱动的多图层动效合成引擎。

支持特性：
1. 丰富布局原语：
   - title_card: 封面大卡片与主讲人立绘
   - split_compare: 左右分屏 PK 对决 (痛点 vs 突破 / 传统 vs 现代)
   - chart_benchmark: 动态生长跑分柱状图与数字翻牌器
   - terminal: 拟真 macOS 黑客终端打字机
   - custom_nodes: 动态拓扑流向图与数据粒子
   - code: Silicon 语法高亮代码卡片 + 呼吸聚光灯
   - diagram: Mermaid 架构与时序图
   - image: 高清特写与配图
2. 虚拟摄像机 (Virtual Camera)：
   - zoom_in: 镜头平滑微距推入，打破幻灯片感
   - zoom_punch: 弹性冲击放大回弹
3. 多形态角色系统 (Erii Persona)：
   - position: right / left / center / pip (画中画微缩视窗) / hidden
   - 待机浮动呼吸与情绪贴纸交互
4. 剪辑节奏与转场：
   - cut / hard_cut (硬切，极简有力)
   - slide_left (平滑滑动推镜)
   - zoom_fade (缩放淡入)
"""

import os
import sys
import yaml
import math
import wave
import json
import shutil
import subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from engine.tts_engine import synthesize_speech
from engine.code_card_engine import render_code_card
from engine.diagram_engine import render_diagram

# CJK 字体的跨平台候选：macOS 优先，其次常见 Linux 发行版路径。
FONT_HEITI_CANDIDATES = (
    "/System/Library/Fonts/STHeiti Medium.ttc",
    "/System/Library/Fonts/Hiragino Sans GB.ttc",
    "/System/Library/Fonts/PingFang.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJKsc-Bold.otf",
    "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
    "/usr/share/fonts/truetype/arphic/uming.ttc",
)
FONT_LIGHT_CANDIDATES = (
    "/System/Library/Fonts/STHeiti Light.ttc",
    "/System/Library/Fonts/Hiragino Sans GB.ttc",
    "/System/Library/Fonts/PingFang.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJKsc-Regular.otf",
    "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
)


def _resolve_font(candidates, label):
    """返回首个存在的字体文件；全部缺失时给出可操作的安装提示。"""
    for candidate in candidates:
        if os.path.isfile(candidate):
            return candidate
    print(
        f"⚠️ 未找到可用{label}字体，中文可能无法渲染。\n"
        f"   macOS: 系统自带 STHeiti/PingFang，通常无需处理。\n"
        f"   Linux: sudo apt-get install fonts-noto-cjk 或 fonts-wqy-microhei\n"
        f"   候选路径: {', '.join(candidates)}"
    )
    return candidates[0]


FONT_HEITI = _resolve_font(FONT_HEITI_CANDIDATES, "标题")
FONT_LIGHT = _resolve_font(FONT_LIGHT_CANDIDATES, "正文")

# ----------------- EASING FUNCTIONS -----------------
def ease_out_cubic(t):
    t = max(0.0, min(1.0, float(t)))
    return 1.0 - (1.0 - t) ** 3

def ease_out_back(t, s=1.6):
    t = max(0.0, min(1.0, float(t)))
    t -= 1.0
    return t * t * ((s + 1.0) * t + s) + 1.0

def ease_in_out_quad(t):
    t = max(0.0, min(1.0, float(t)))
    if t < 0.5:
        return 2.0 * t * t
    return 1.0 - ((-2.0 * t + 2.0) ** 2) / 2.0

# ----------------- ASSET RESOLVER -----------------
class AssetResolver:
    def __init__(self, project_dir, root_assets_dir):
        self.project_dir = project_dir
        self.extra_assets = os.path.join(project_dir, "extra_assets")
        self.root_assets = root_assets_dir

    def resolve_image(self, name):
        """寻找图片素材路径"""
        if not name:
            return None
        if os.path.isabs(name) and os.path.isfile(name):
            return name
        proj_p = os.path.join(self.project_dir, name)
        if os.path.isfile(proj_p):
            return proj_p
        candidates = [
            os.path.join(self.extra_assets, name),
            os.path.join(self.extra_assets, f"{name}.png"),
            os.path.join(self.extra_assets, f"{name}.jpg"),
            os.path.join(self.root_assets, "character", name),
            os.path.join(self.root_assets, "character", f"{name}.png"),
            os.path.join(self.root_assets, "character", f"{name}.jpg"),
            os.path.join(self.root_assets, name),
            os.path.join(self.root_assets, f"{name}.png")
        ]
        for c in candidates:
            if os.path.isfile(c):
                return c
        return None

    def resolve_audio(self, name):
        """寻找音频素材路径"""
        if not name:
            return None
        candidates = [
            os.path.join(self.extra_assets, name),
            os.path.join(self.root_assets, "sfx", name),
            os.path.join(self.root_assets, "audio", "sfx", name),
            os.path.join(self.root_assets, name),
            os.path.join(self.root_assets, f"{name}.wav"),
            os.path.join(self.root_assets, f"{name}.mp3")
        ]
        for c in candidates:
            if os.path.isfile(c):
                return c
        return None

# ----------------- COMPOSITOR CLASS -----------------
class VideoCompositor:
    def __init__(self, project_dir, root_dir=None):
        self.project_dir = os.path.abspath(project_dir)
        if root_dir is None:
            self.root_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
        else:
            self.root_dir = os.path.abspath(root_dir)

        self.assets_dir = os.path.join(self.root_dir, "assets")
        self.cache_dir = os.path.join(self.project_dir, ".cache")
        self.dist_dir = os.path.join(self.project_dir, "dist")
        self.resolver = AssetResolver(self.project_dir, self.assets_dir)

        os.makedirs(self.cache_dir, exist_ok=True)
        os.makedirs(self.dist_dir, exist_ok=True)

        self.storyboard_path = os.path.join(self.project_dir, "storyboard.yaml")
        if not os.path.exists(self.storyboard_path):
            raise FileNotFoundError(f"未找到剧本文件: {self.storyboard_path}")

        with open(self.storyboard_path, "r", encoding="utf-8") as f:
            self.spec = yaml.safe_load(f)

        meta = self.spec.get("meta", {})
        self.title = meta.get("title", "科技视频")
        self.width, self.height = meta.get("resolution", [1920, 1080])
        self.fps = meta.get("fps", 30)
        self.theme = meta.get("theme", "white_grid")
        self.bgm_conf = meta.get("bgm", {"file": "bgm.mp3", "volume": 0.10, "fade_in": 1.5, "fade_out": 2.0})
        self.sfx_conf = meta.get("sfx", {"enabled": True})

        self.sprites = {}
        self._label_budget_cache = {}
        # 视频素材只保留抽帧路径；按需读取，避免长素材将内存撑满。
        self.video_clips = {}
        self._video_frame_cache = {}
        self.grid_bg_light = self._create_grid_background(dark=False)
        self.grid_bg_dark = self._create_grid_background(dark=True)
        self.grid_bg = self.grid_bg_light

    def validate_storyboard(self, allow_placeholders=False):
        """在启动昂贵的 TTS/逐帧渲染前，检查素材契约与镜头配置。"""
        errors, warnings = [], []
        scenes = self.spec.get("scenes", [])
        profile = self.spec.get("meta", {}).get("story_profile")
        story_beats = self.spec.get("meta", {}).get("story_beats", [])
        valid_profiles = {"tutorial", "concept", "code_walkthrough", "decision"}
        if profile is not None and profile not in valid_profiles:
            errors.append(f"meta.story_profile 不支持: {profile}")
        if story_beats and not isinstance(story_beats, list):
            errors.append("meta.story_beats 必须是列表")
        if not isinstance(scenes, list) or not scenes:
            return ["scenes 必须是非空列表"], warnings

        valid_types = {
            "title_card", "split_compare", "compare", "chart_benchmark", "benchmark", "chart",
            "terminal", "terminal_mock", "cli", "git_diff", "diff", "custom_nodes", "code",
            "diagram", "image", "screenshot", "showcase", "diagram_or_image",
            "video_clip", "video", "clip", "asset_placeholder", "material_placeholder"
        }
        visual_types = []
        for index, scene in enumerate(scenes, 1):
            scene_id = scene.get("id", f"scene_{index}") if isinstance(scene, dict) else f"scene_{index}"
            if not isinstance(scene, dict):
                errors.append(f"{scene_id}: 场景必须是对象")
                continue
            if not (scene.get("audio", {}).get("text") or scene.get("voice_text")):
                errors.append(f"{scene_id}: 缺少 audio.text")
            visual = scene.get("visual", {})
            visual_type = scene.get("layout") or visual.get("type")
            if visual_type not in valid_types:
                errors.append(f"{scene_id}: 不支持的 visual.type: {visual_type}")
                continue
            visual_types.append(visual_type)
            if visual_type in ["asset_placeholder", "material_placeholder"] and not allow_placeholders:
                errors.append(f"{scene_id}: 仍是素材占位场景，补录素材后才能发布")
            if visual_type in ["image", "screenshot", "showcase", "diagram_or_image", "video_clip", "video", "clip"]:
                asset_name = visual.get("file")
                if not asset_name:
                    errors.append(f"{scene_id}: {visual_type} 缺少 file")
                elif not self.resolver.resolve_image(asset_name):
                    errors.append(f"{scene_id}: 未找到素材文件: {asset_name}")
                if visual.get("presentation") == "cinematic" and not visual.get("beats"):
                    warnings.append(f"{scene_id}: cinematic 素材未设置 beats，将只使用默认全景镜头")
            for beat in visual.get("beats", []):
                if not isinstance(beat, dict):
                    errors.append(f"{scene_id}: beats 项必须是对象")
                    continue
                try:
                    at = float(beat.get("at", 0.0))
                    focus = beat.get("focus", [0.5, 0.5])
                    if not 0.0 <= at <= 1.0 or len(focus) != 2:
                        raise ValueError
                except (TypeError, ValueError):
                    errors.append(f"{scene_id}: beat 需包含 0~1 的 at 与 [x, y] focus")

            if visual_type in ["chart_benchmark", "benchmark", "chart"] and not visual.get("evidence"):
                errors.append(f"{scene_id}: 图表缺少可复核 evidence")

        # 仅对新导演生成的剧本施加去模板化约束，保持历史工程可复现。
        if profile:
            for previous, current in zip(visual_types, visual_types[1:]):
                if previous == current and current not in ["asset_placeholder", "material_placeholder"]:
                    errors.append(f"相邻场景重复使用 {current}，请改为不同镜头或合并场景")
            if len(scenes) >= 3 and len(set(visual_types)) < 2:
                errors.append("剧本缺少镜头多样性：至少使用两种 visual.type")
            if story_beats:
                scene_ids = {scene.get("id") for scene in scenes if isinstance(scene, dict)}
                beat_scene_ids = {beat.get("scene_id") for beat in story_beats if isinstance(beat, dict)}
                if scene_ids != beat_scene_ids or len(story_beats) != len(scenes):
                    errors.append("meta.story_beats 必须与 scenes 一一对应")
                for beat in story_beats:
                    if not isinstance(beat, dict) or not all(beat.get(key) for key in ["id", "intent", "evidence_level", "scene_id"]):
                        errors.append("meta.story_beats 每项必须包含 id、intent、evidence_level、scene_id")
                        break
            for scene in scenes:
                visual = scene.get("visual", {}) if isinstance(scene, dict) else {}
                visual_type = visual.get("type")
                if visual_type in ["terminal", "terminal_mock", "cli", "git_diff", "diff"] and not visual.get("evidence"):
                    errors.append(f"{scene.get('id')}: {visual_type} 缺少可复核 evidence")

        for request in self.spec.get("asset_requests", []):
            if not isinstance(request, dict):
                warnings.append("asset_requests 中存在非对象条目")
                continue
            suggested = request.get("suggested_file")
            if suggested and not self.resolver.resolve_image(suggested):
                warnings.append(f"待补录素材: {suggested}（{request.get('purpose', '未说明用途')}）")
        return errors, warnings

    def _create_grid_background(self, dark=False):
        if dark:
            bg_col = (15, 23, 42)
            line_col = (30, 41, 59)
            img = Image.new("RGB", (self.width, self.height), bg_col)
            draw = ImageDraw.Draw(img)
            step = 48
            for x in range(0, self.width, step):
                draw.line([(x, 0), (x, self.height)], fill=line_col, width=1)
            for y in range(0, self.height, step):
                draw.line([(0, y), (self.width, y)], fill=line_col, width=1)
            return img
        else:
            # 现代极简设计工作室风格 (Modern Studio Canvas) - 告别机械 AI 网格感
            bg_col = (248, 250, 252)  # Slate-50
            dot_col = (226, 232, 240) # 微弱精致点阵
            img = Image.new("RGB", (self.width, self.height), bg_col)
            draw = ImageDraw.Draw(img)
            step = 48
            for x in range(24, self.width, step):
                for y in range(24, self.height, step):
                    draw.ellipse([x - 1, y - 1, x + 1, y + 1], fill=dot_col)
            return img

    def _get_background(self, scene):
        theme = scene.get("theme") or self.theme
        if theme in ["dark", "midnight", "hacker"]:
            return self.grid_bg_dark
        return self.grid_bg_light

    def _render_pip_avatar(self, frame, scene, local_f, global_f):
        """右下角画中画悬浮小头像，释放全宽画布给高密度内容"""
        stk_name = scene.get("character_sticker", "erii_avatar")
        stk = self.sprites.get(stk_name) or self.sprites.get("erii_avatar")
        if not stk:
            p = self.resolver.resolve_image(stk_name) or self.resolver.resolve_image("erii_avatar")
            if p:
                stk = Image.open(p)
        if not stk:
            return frame

        size = 160
        av = stk.resize((size, size), Image.Resampling.LANCZOS)
        mask = Image.new("L", (size, size), 0)
        ImageDraw.Draw(mask).ellipse((0, 0, size, size), fill=255)

        hover_y = math.sin(global_f / 12.0) * 5.0
        pip_x = self.width - size - 40
        pip_y = int(self.height - size - 40 + hover_y)

        glow_size = size + 14
        glow = Image.new("RGBA", (glow_size, glow_size), (0, 0, 0, 0))
        d_glow = ImageDraw.Draw(glow)
        is_dark = (scene.get("theme") or self.theme) in ["dark", "midnight", "hacker"]
        if is_dark:
            d_glow.ellipse((0, 0, glow_size, glow_size), fill=(15, 23, 42, 230), outline=(56, 189, 248, 255), width=3)
        else:
            d_glow.ellipse((0, 0, glow_size, glow_size), fill=(255, 255, 255, 250), outline=(203, 213, 225, 255), width=2)

        frame.paste(glow, (pip_x - 7, pip_y - 7), glow)
        frame.paste(av, (pip_x, pip_y), mask)
        return frame

    def prepare_audio_and_timings(self):
        """编译各场景语音并计算全局时间线与字幕"""
        print("🎙️ 正在编译各幕配音与精确时间线...")
        audio_cache_dir = os.path.join(self.cache_dir, "audio")
        os.makedirs(audio_cache_dir, exist_ok=True)

        scene_timelines = []
        global_subtitles = []
        current_frame = 0

        scenes = self.spec.get("scenes", [])
        for idx, scene in enumerate(scenes):
            scene_id = scene.get("id", f"scene_{idx}")
            audio_conf = scene.get("audio", {})
            text = audio_conf.get("text") or scene.get("voice_text", "")
            speed = audio_conf.get("speed", 1.05)
            pause_sec = audio_conf.get("pause", 0.45)
            emotion = audio_conf.get("emotion", "normal")
            
            # 转场模式: cut / hard_cut (0帧) 或 slide_left (12帧)
            trans_mode = scene.get("transition", "slide_left")
            trans_frames = 0 if trans_mode in ["cut", "hard_cut"] else 12

            scene_wav = os.path.join(audio_cache_dir, f"{scene_id}.wav")
            meta = synthesize_speech(
                text,
                output_file=scene_wav,
                speed=speed,
                pause_sec=pause_sec,
                cache_dir=audio_cache_dir,
                emotion=emotion
            )
            dur_sec = meta["total_duration"]
            dur_frames = int(math.ceil(dur_sec * self.fps))
            start_frame = current_frame
            end_frame = current_frame + dur_frames

            # 映射字幕时间戳
            for s_info in meta["sentences"]:
                s_start_f = start_frame + int(s_info["start_time"] * self.fps)
                s_end_f = start_frame + int(s_info["end_time"] * self.fps)
                global_subtitles.append((s_start_f, s_end_f, s_info["text"]))

            # 提取 punch_words 关键词冲击时间戳
            p_words = scene.get("punch_words", [])
            scene_punch_cues = []
            for pw in p_words:
                if isinstance(pw, str):
                    pw_text = pw
                    pw_style = "emerald"
                else:
                    pw_text = pw.get("text", "")
                    pw_style = pw.get("style", "emerald")

                matched = False
                for s_info in meta["sentences"]:
                    if pw_text in s_info["text"] or any(char in s_info["text"] for char in pw_text[:3]):
                        s_f = start_frame + int(s_info["start_time"] * self.fps)
                        cue_len = min(36, max(24, int(s_info["duration"] * self.fps)))
                        scene_punch_cues.append({
                            "text": pw_text,
                            "start_frame": s_f,
                            "duration_frames": cue_len,
                            "style": pw_style
                        })
                        matched = True
                        break
                if not matched and meta["sentences"]:
                    mid_f = start_frame + dur_frames // 3
                    scene_punch_cues.append({
                        "text": pw_text,
                        "start_frame": mid_f,
                        "duration_frames": 32,
                        "style": pw_style
                    })

            scene_timelines.append({
                "index": idx,
                "id": scene_id,
                "scene": scene,
                "start_frame": start_frame,
                "end_frame": end_frame,
                "duration_frames": dur_frames,
                "audio_path": scene_wav,
                "transition": trans_mode,
                "transition_frames": trans_frames,
                "punch_cues": scene_punch_cues
            })

            current_frame = end_frame
            if idx < len(scenes) - 1:
                current_frame += trans_frames

        total_frames = current_frame
        total_duration = total_frames / float(self.fps)

        self._export_srt(global_subtitles)
        master_voice_wav = os.path.join(self.cache_dir, "master_voice.wav")
        self._stitch_audio_tracks(scene_timelines, total_duration, master_voice_wav)

        return scene_timelines, global_subtitles, total_frames, total_duration, master_voice_wav

    def _overlay_sfx(self, master_buffer, sfx_name, start_sample, framerate=32000, volume=0.45):
        sfx_path = self.resolver.resolve_audio(sfx_name)
        if not sfx_path or not os.path.exists(sfx_path):
            return master_buffer
        try:
            with wave.open(sfx_path, "rb") as wf:
                s_rate = wf.getframerate()
                s_raw = wf.readframes(wf.getnframes())
                s_data = np.frombuffer(s_raw, dtype=np.int16)
                if wf.getnchannels() > 1:
                    s_data = s_data.reshape(-1, wf.getnchannels())[:, 0]
            
            if s_rate != framerate:
                num_new_samples = int(len(s_data) * (framerate / float(s_rate)))
                indices = np.linspace(0, len(s_data) - 1, num_new_samples)
                s_data = np.interp(indices, np.arange(len(s_data)), s_data).astype(np.int16)

            start_sample = max(0, start_sample)
            end_sample = min(len(master_buffer), start_sample + len(s_data))
            chunk_len = end_sample - start_sample
            if chunk_len > 0:
                mixed = master_buffer[start_sample:end_sample].astype(np.int32) + (s_data[:chunk_len] * volume).astype(np.int32)
                master_buffer[start_sample:end_sample] = np.clip(mixed, -32768, 32767).astype(np.int16)
        except Exception:
            pass
        return master_buffer

    def _stitch_audio_tracks(self, scene_timelines, total_duration, output_wav):
        framerate = 32000
        n_channels = 1
        sampwidth = 2
        total_samples = int(total_duration * framerate)
        master_buffer = np.zeros(total_samples, dtype=np.int16)

        for item in scene_timelines:
            wav_path = item["audio_path"]
            with wave.open(wav_path, "rb") as wf:
                framerate = wf.getframerate()
                n_channels = wf.getnchannels()
                sampwidth = wf.getsampwidth()
                raw = wf.readframes(wf.getnframes())
                data = np.frombuffer(raw, dtype=np.int16)

            start_sample = int((item["start_frame"] / float(self.fps)) * framerate)
            end_sample = start_sample + len(data)
            if end_sample > total_samples:
                master_buffer = np.pad(master_buffer, (0, end_sample - total_samples))
                total_samples = end_sample
            master_buffer[start_sample:end_sample] = data

        # 叠加智能微音效 (SFX)
        if self.sfx_conf.get("enabled", True):
            for item in scene_timelines:
                pop_sample = int(((item["start_frame"] + 8) / float(self.fps)) * framerate)
                master_buffer = self._overlay_sfx(master_buffer, "pop.wav", pop_sample, framerate=framerate, volume=0.30)

                if item.get("transition_frames", 0) > 0:
                    trans_sample = int((item["end_frame"] / float(self.fps)) * framerate)
                    master_buffer = self._overlay_sfx(master_buffer, "whoosh.wav", trans_sample, framerate=framerate, volume=0.35)

                for cue in item.get("punch_cues", []):
                    punch_sample = int((cue["start_frame"] / float(self.fps)) * framerate)
                    master_buffer = self._overlay_sfx(master_buffer, "punch.wav", punch_sample, framerate=framerate, volume=0.55)

        with wave.open(output_wav, "wb") as wf:
            wf.setnchannels(n_channels)
            wf.setsampwidth(sampwidth)
            wf.setframerate(framerate)
            wf.writeframes(master_buffer.tobytes())

    def _export_srt(self, subtitles):
        srt_path = os.path.join(self.dist_dir, "subtitles.srt")
        def format_time(seconds):
            hrs = int(seconds // 3600)
            mins = int((seconds % 3600) // 60)
            secs = int(seconds % 60)
            millis = int((seconds - int(seconds)) * 1000)
            return f"{hrs:02d}:{mins:02d}:{secs:02d},{millis:03d}"

        with open(srt_path, "w", encoding="utf-8") as f:
            for idx, (sf, ef, text) in enumerate(subtitles):
                t1 = format_time(sf / float(self.fps))
                t2 = format_time(ef / float(self.fps))
                f.write(f"{idx + 1}\n{t1} --> {t2}\n{text}\n\n")

    def prepare_visual_assets(self):
        """预加载和编译静态素材"""
        print("🎨 预加载视觉组件与代码/架构图卡片...")
        cards_cache = os.path.join(self.cache_dir, "visual")
        os.makedirs(cards_cache, exist_ok=True)

        for idx, scene in enumerate(self.spec.get("scenes", [])):
            scene_id = scene.get("id", f"scene_{idx}")
            v_conf = scene.get("visual", {})
            v_type = scene.get("layout") or v_conf.get("type", "title_card")

            if v_type == "code":
                code_content = v_conf.get("code")
                code_file = v_conf.get("code_file")
                if not code_content and code_file:
                    target_file = os.path.join(self.project_dir, code_file)
                    if not os.path.exists(target_file):
                        target_file = os.path.join(self.project_dir, "extra_assets", code_file)
                    with open(target_file, "r", encoding="utf-8") as f:
                        code_content = f.read()

                lang = v_conf.get("lang", "python")
                theme = v_conf.get("theme", "OneHalfLight")
                out_png = os.path.join(cards_cache, f"{scene_id}_code.png")
                render_code_card(code_content, out_png, lang=lang, theme=theme)
                img = Image.open(out_png)
                cw, ch = int(img.width * 1.3), int(img.height * 1.3)
                self.sprites[f"{scene_id}_visual"] = img.resize((cw, ch), Image.Resampling.LANCZOS)

            elif v_type == "diagram":
                diag_content = v_conf.get("source")
                diag_file = v_conf.get("source_file")
                if not diag_content and diag_file:
                    target_file = os.path.join(self.project_dir, diag_file)
                    if not os.path.exists(target_file):
                        target_file = os.path.join(self.project_dir, "extra_assets", diag_file)
                    with open(target_file, "r", encoding="utf-8") as f:
                        diag_content = f.read()

                out_png = os.path.join(cards_cache, f"{scene_id}_diag.png")
                render_diagram(diag_content, out_png, bg="transparent", scale=2)
                self.sprites[f"{scene_id}_visual"] = Image.open(out_png)

            elif v_type in ["video_clip", "video", "clip"]:
                video_path = self.resolver.resolve_image(v_conf.get("file"))
                if not video_path:
                    raise FileNotFoundError(f"未找到视频素材: {v_conf.get('file')}")
                clip_fps = max(1, min(int(v_conf.get("clip_fps", 12)), self.fps))
                frames_dir = os.path.join(cards_cache, f"{scene_id}_clip")
                os.makedirs(frames_dir, exist_ok=True)
                frame_pattern = os.path.join(frames_dir, "%06d.jpg")
                if not any(name.endswith(".jpg") for name in os.listdir(frames_dir)):
                    subprocess.run([
                        "ffmpeg", "-y", "-i", video_path,
                        "-vf", f"fps={clip_fps},scale=1280:-2",
                        "-q:v", "3", frame_pattern
                    ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
                frame_paths = sorted(
                    os.path.join(frames_dir, name)
                    for name in os.listdir(frames_dir)
                    if name.endswith(".jpg")
                )
                if not frame_paths:
                    raise RuntimeError(f"视频素材抽帧失败: {video_path}")
                self.video_clips[scene_id] = {"fps": clip_fps, "frames": frame_paths}

            elif v_type in ["image", "screenshot", "showcase", "diagram_or_image"] or v_conf.get("file"):
                img_path = self.resolver.resolve_image(v_conf.get("file"))
                if img_path:
                    self.sprites[f"{scene_id}_visual"] = Image.open(img_path)

        # 加载角色立绘与贴纸
        char_presenter = self.resolver.resolve_image("erii_presenter")
        if char_presenter:
            p_img = Image.open(char_presenter)
            ph = 960
            pw = int(p_img.width * (ph / float(p_img.height)))
            self.sprites["erii_presenter"] = p_img.resize((pw, ph), Image.Resampling.LANCZOS)

        for stk_name in ["erii_chibi_think", "erii_chibi_happy", "erii_chibi_cheer"]:
            p = self.resolver.resolve_image(stk_name)
            if p:
                img = Image.open(p)
                self.sprites[stk_name] = img.resize((390, 390), Image.Resampling.LANCZOS)

    # ----------------- 布局组件 1: 封面大卡片 (Title Card) -----------------
    def _render_title_card(self, scene, local_f, global_f):
        frame = self._get_background(scene).copy()
        draw = ImageDraw.Draw(frame)
        v_conf = scene.get("visual", {})

        is_dark = (scene.get("theme") or self.theme) in ["dark", "midnight", "hacker"]
        char_mode = scene.get("character_mode", "side")

        card_p = ease_out_back(local_f / 18.0)
        card_y = int(95 + (1.0 - card_p) * 60)
        
        card_w = 1600 if char_mode in ["pip", "none"] else 1040
        card_x = (self.width - card_w) // 2 if char_mode in ["pip", "none"] else 120

        card_bg_col = (30, 41, 59, 252) if is_dark else (255, 255, 255, 255)
        card_border_col = (51, 65, 85) if is_dark else (226, 232, 240)
        card = Image.new("RGBA", (card_w, 850), (0, 0, 0, 0))
        ImageDraw.Draw(card).rounded_rectangle([0, 0, card_w, 850], radius=24, fill=card_bg_col, outline=card_border_col, width=2)
        if not is_dark:
            draw.rounded_rectangle([card_x + 6, card_y + 8, card_x + card_w + 6, card_y + 858], radius=24, fill=(226, 232, 240, 160))
        frame.paste(card, (card_x, card_y), card)

        tag = v_conf.get("tag", "实战教程 · 零基础特训")
        if local_f >= 8:
            font_tag = ImageFont.truetype(FONT_HEITI, 20)
            tb = draw.textbbox((0, 0), tag, font=font_tag)
            tw = tb[2] - tb[0]
            tag_w = tw + 56
            tag_bg = (49, 46, 129) if is_dark else (238, 242, 255)
            tag_border = (99, 102, 241) if is_dark else (199, 210, 254)
            tag_text_col = (199, 210, 254) if is_dark else (67, 56, 202)
            draw.rounded_rectangle([card_x + 60, card_y + 55, card_x + 60 + tag_w, card_y + 100], radius=10, fill=tag_bg, outline=tag_border, width=1)
            draw.ellipse([card_x + 78, card_y + 72, card_x + 90, card_y + 84], fill=(129, 140, 248) if is_dark else (79, 70, 229))
            draw.text((card_x + 100, card_y + 67), tag, font=font_tag, fill=tag_text_col)

        if local_f >= 6:
            tp = ease_out_cubic((local_f - 6) / 16.0)
            ty = int(card_y + 135 - (1.0 - tp) * 20)
            font_t = ImageFont.truetype(FONT_HEITI, 56)
            t_col = (248, 250, 252) if is_dark else (15, 23, 42)
            draw.text((card_x + 60, ty), v_conf.get("title", self.title), font=font_t, fill=t_col)

        if local_f >= 14:
            font_sub = ImageFont.truetype(FONT_HEITI, 28)
            sub_col = (148, 163, 184) if is_dark else (71, 85, 105)
            draw.text((card_x + 60, card_y + 225), v_conf.get("subtitle", ""), font=font_sub, fill=sub_col)

        bullets = v_conf.get("bullets", [])
        font_bullet = ImageFont.truetype(FONT_LIGHT, 24)
        b_col = (226, 232, 240) if is_dark else (51, 65, 85)
        for b_idx, b_text in enumerate(bullets):
            appear_f = 20 + b_idx * 15
            if local_f >= appear_f:
                bp = ease_out_cubic((local_f - appear_f) / 14.0)
                bx = int(card_x + 60 - (1.0 - bp) * 35)
                by = card_y + 295 + b_idx * 54
                dot_col = (59, 130, 246) if b_idx % 2 == 0 else (16, 185, 129)
                draw.ellipse([bx, by + 6, bx + 14, by + 20], fill=dot_col)
                draw.text((bx + 26, by), str(b_text), font=font_bullet, fill=b_col)

        if local_f >= 20:
            badge_info = scene.get("host_badge") or self.spec.get("meta", {}).get("host_badge") or {}
            b_name = badge_info.get("name", "上杉绘梨衣")
            b_sub = badge_info.get("sub", "Codex CLI 实战精讲")
            badge = self._render_host_badge(name=b_name, sub=b_sub)
            hp = ease_out_back((local_f - 20) / 16.0)
            hx = int(card_x + 60 - (1.0 - hp) * 40)
            frame.paste(badge, (hx, card_y + 640), badge)

        # 角色展示
        if char_mode == "pip":
            frame = self._render_pip_avatar(frame, scene, local_f, global_f)
        elif char_mode != "none":
            pres = self.sprites.get("erii_presenter")
            if pres:
                pres_p = ease_out_back(local_f / 24.0)
                px = int(self.width - pres.width - 40 + (1.0 - pres_p) * 200)
                py = int(self.height - pres.height + math.sin(global_f / 16.0) * 8.0)
                frame.paste(pres, (px, py), pres)

        return frame

    # ----------------- 布局组件 2: 左右分屏 PK 对决 (Split Compare) -----------------
    def _render_split_compare(self, scene, local_f, global_f):
        """左右分屏高能对抗组件：左侧劣势/传统 vs 右侧突破/现代"""
        frame = self._get_background(scene).copy()
        draw = ImageDraw.Draw(frame)
        v_conf = scene.get("visual", {})

        is_dark = (scene.get("theme") or self.theme) in ["dark", "midnight", "hacker"]

        # 顶部标题栏
        ht = v_conf.get("header_title", "技术方案对比与选型")
        hs = v_conf.get("header_sub", "性能瓶颈 vs 架构突破")
        font_ht = ImageFont.truetype(FONT_HEITI, 46)
        font_hs = ImageFont.truetype(FONT_LIGHT, 26)
        draw.text((120, 60), ht, font=font_ht, fill=(248, 250, 252) if is_dark else (15, 23, 42))
        draw.text((120, 122), hs, font=font_hs, fill=(148, 163, 184) if is_dark else (100, 116, 139))

        left_data = v_conf.get("left", {})
        right_data = v_conf.get("right", {})

        card_w = 780
        card_h = 720
        card_y = 200

        # 1. 左侧卡片
        left_theme = left_data.get("theme", "rose")
        if local_f >= 4:
            lp = ease_out_back((local_f - 4) / 16.0)
            lx = int(120 - (1.0 - lp) * 60)
            card_left = Image.new("RGBA", (card_w, card_h), (0, 0, 0, 0))
            d_l = ImageDraw.Draw(card_left)
            
            if is_dark:
                if left_theme in ["blue", "indigo"]:
                    bg_l = (30, 41, 59, 245)
                    border_l = (59, 130, 246)
                    badge_bg = (30, 58, 138)
                    badge_border = (96, 165, 250)
                    badge_fg = (147, 197, 253)
                    title_fg = (248, 250, 252)
                    bullet_fg = (226, 232, 240)
                    met_bg = (15, 23, 42)
                    met_border = (51, 65, 85)
                    met_lbl = (148, 163, 184)
                    met_val = (96, 165, 250)
                else:
                    bg_l = (30, 41, 59, 245)
                    border_l = (225, 29, 72)
                    badge_bg = (76, 5, 25)
                    badge_border = (244, 63, 94)
                    badge_fg = (254, 205, 211)
                    title_fg = (248, 250, 252)
                    bullet_fg = (226, 232, 240)
                    met_bg = (15, 23, 42)
                    met_border = (51, 65, 85)
                    met_lbl = (251, 113, 133)
                    met_val = (244, 63, 94)
            else:
                if left_theme in ["blue", "indigo"]:
                    bg_l = (239, 246, 255, 245)
                    border_l = (191, 219, 254)
                    badge_bg = (219, 234, 254)
                    badge_border = (147, 197, 253)
                    badge_fg = (29, 78, 216)
                    title_fg = (30, 58, 138)
                    bullet_fg = (30, 41, 59)
                    met_bg = (255, 255, 255)
                    met_border = (191, 219, 254)
                    met_lbl = (30, 58, 138)
                    met_val = (37, 99, 235)
                else:
                    bg_l = (255, 241, 242, 245)
                    border_l = (254, 205, 211)
                    badge_bg = (255, 228, 230)
                    badge_border = (253, 164, 175)
                    badge_fg = (225, 29, 72)
                    title_fg = (159, 18, 57)
                    bullet_fg = (76, 5, 25)
                    met_bg = (255, 255, 255)
                    met_border = (254, 205, 211)
                    met_lbl = (159, 18, 57)
                    met_val = (225, 29, 72)

            d_l.rounded_rectangle([0, 0, card_w, card_h], radius=24, fill=bg_l, outline=border_l, width=2)
            d_l.rounded_rectangle([40, 40, 380, 92], radius=12, fill=badge_bg, outline=badge_border, width=1)
            font_badge = ImageFont.truetype(FONT_HEITI, 22)
            l_badge_txt = left_data.get("badge", "传统方式").lstrip("✦●■◆★[] 🔒🖥️⚡❌✅ ")
            l_tb = d_l.textbbox((0, 0), l_badge_txt, font=font_badge)
            l_badge_w = max(200, (l_tb[2] - l_tb[0]) + 48)
            d_l.rounded_rectangle([40, 40, 40 + l_badge_w, 90], radius=12, fill=badge_bg, outline=badge_border, width=1)
            d_l.text((64, 52), l_badge_txt, font=font_badge, fill=badge_fg)

            font_ct = ImageFont.truetype(FONT_HEITI, 36)
            d_l.text((40, 118), left_data.get("title", "性能痛点"), font=font_ct, fill=title_fg)

            font_cb = ImageFont.truetype(FONT_LIGHT, 24)
            by_l = 185
            for b_text in left_data.get("bullets", []):
                s = str(b_text)
                w_lines = []
                while len(s) > 23:
                    sp = 23
                    for i in range(18, 23):
                        if s[i] in "，、：； ":
                            sp = i + 1
                            break
                    w_lines.append(s[:sp].strip())
                    s = s[sp:].strip()
                if s:
                    w_lines.append(s)
                for l_idx, l in enumerate(w_lines):
                    prefix = "• " if l_idx == 0 else "  "
                    d_l.text((40, by_l), f"{prefix}{l}", font=font_cb, fill=bullet_fg)
                    by_l += 36
                by_l += 14

            metric = left_data.get("metrics", {})
            if metric:
                d_l.rounded_rectangle([40, card_h - 140, card_w - 40, card_h - 35], radius=16, fill=met_bg, outline=met_border, width=1)
                font_ml = ImageFont.truetype(FONT_LIGHT, 22)
                font_mv = ImageFont.truetype(FONT_HEITI, 32)
                d_l.text((65, card_h - 128), metric.get("label", "核心开销"), font=font_ml, fill=met_lbl)
                d_l.text((65, card_h - 85), metric.get("value", "严重瓶颈"), font=font_mv, fill=met_val)

            frame.paste(card_left, (lx, card_y), card_left)

        # 2. 右侧卡片 (现代/突破 - 柔和翡翠绿 Emerald / 靛蓝 Indigo 调)
        if local_f >= 14:
            rp = ease_out_back((local_f - 14) / 16.0)
            rx = int(1020 + (1.0 - rp) * 60)
            card_right = Image.new("RGBA", (card_w, card_h), (0, 0, 0, 0))
            d_r = ImageDraw.Draw(card_right)

            if is_dark:
                bg_r = (30, 41, 59, 245)
                border_r = (16, 185, 129)
                badge_bg = (6, 78, 59)
                badge_border = (52, 211, 153)
                badge_fg = (167, 243, 208)
                title_fg = (248, 250, 252)
                bullet_fg = (226, 232, 240)
                met_bg = (15, 23, 42)
                met_border = (51, 65, 85)
                met_lbl = (110, 231, 183)
                met_val = (52, 211, 153)
            else:
                bg_r = (236, 253, 245, 245)
                border_r = (167, 243, 208)
                badge_bg = (209, 250, 229)
                badge_border = (110, 231, 183)
                badge_fg = (5, 150, 105)
                title_fg = (6, 95, 70)
                bullet_fg = (2, 44, 34)
                met_bg = (255, 255, 255)
                met_border = (167, 243, 208)
                met_lbl = (6, 95, 70)
                met_val = (5, 150, 105)

            d_r.rounded_rectangle([0, 0, card_w, card_h], radius=24, fill=bg_r, outline=border_r, width=2)
            font_badge = ImageFont.truetype(FONT_HEITI, 22)
            r_badge_txt = right_data.get("badge", "现代方案").lstrip("✦●■◆★[] 🔒🖥️⚡❌✅ ")
            r_tb = d_r.textbbox((0, 0), r_badge_txt, font=font_badge)
            r_badge_w = max(200, (r_tb[2] - r_tb[0]) + 48)
            d_r.rounded_rectangle([40, 40, 40 + r_badge_w, 90], radius=12, fill=badge_bg, outline=badge_border, width=1)
            d_r.text((64, 52), r_badge_txt, font=font_badge, fill=badge_fg)

            font_ct = ImageFont.truetype(FONT_HEITI, 36)
            d_r.text((40, 118), right_data.get("title", "架构突破"), font=font_ct, fill=title_fg)

            font_cb = ImageFont.truetype(FONT_LIGHT, 24)
            by_r = 185
            for b_text in right_data.get("bullets", []):
                s = str(b_text)
                w_lines = []
                while len(s) > 23:
                    sp = 23
                    for i in range(18, 23):
                        if s[i] in "，、：； ":
                            sp = i + 1
                            break
                    w_lines.append(s[:sp].strip())
                    s = s[sp:].strip()
                if s:
                    w_lines.append(s)
                for l_idx, l in enumerate(w_lines):
                    prefix = "• " if l_idx == 0 else "  "
                    d_r.text((40, by_r), f"{prefix}{l}", font=font_cb, fill=bullet_fg)
                    by_r += 36
                by_r += 14

            metric = right_data.get("metrics", {})
            if metric:
                d_r.rounded_rectangle([40, card_h - 140, card_w - 40, card_h - 35], radius=16, fill=met_bg, outline=met_border, width=1)
                font_ml = ImageFont.truetype(FONT_LIGHT, 22)
                font_mv = ImageFont.truetype(FONT_HEITI, 32)
                d_r.text((65, card_h - 128), metric.get("label", "核心开销"), font=font_ml, fill=met_lbl)
                d_r.text((65, card_h - 85), metric.get("value", "极致性能"), font=font_mv, fill=met_val)

            frame.paste(card_right, (rx, card_y), card_right)

        # 3. 中间高光 VS 徽标
        if local_f >= 22:
            vs_p = ease_out_back((local_f - 22) / 14.0)
            vs_r = max(1, int(48 * vs_p))
            cx, cy = 960, 560
            draw.ellipse([cx - vs_r, cy - vs_r, cx + vs_r, cy + vs_r], fill=(15, 23, 42), outline=(255, 255, 255), width=3)
            if vs_r >= 12:
                font_vs = ImageFont.truetype(FONT_HEITI, max(12, int(36 * vs_p)))
                bbox = draw.textbbox((0, 0), "VS", font=font_vs)
                vw, vh = bbox[2] - bbox[0], bbox[3] - bbox[1]
                draw.text((cx - vw // 2, cy - vh // 2 - 4), "VS", font=font_vs, fill=(255, 255, 255))

        # 角色展示
        char_mode = scene.get("character_mode", "side")
        if char_mode == "pip":
            frame = self._render_pip_avatar(frame, scene, local_f, global_f)
        elif char_mode != "none":
            stk = self.sprites.get(scene.get("character_sticker", "erii_chibi_think"))
            if stk and local_f >= 12:
                hover_y = math.sin(local_f / 16.0) * 6.0
                frame.paste(stk, (self.width - 360, int(self.height - 380 + hover_y)), stk)

        return frame

    # ----------------- 布局组件 3: 动态生长跑分柱状图 (Chart Benchmark) -----------------
    def _render_chart_benchmark(self, scene, local_f, global_f):
        """动态生长柱状图与数字计数翻牌器"""
        frame = self._get_background(scene).copy()
        draw = ImageDraw.Draw(frame)
        v_conf = scene.get("visual", {})

        is_dark = (scene.get("theme") or self.theme) in ["dark", "midnight", "hacker"]
        char_mode = scene.get("character_mode", "side")

        ht = v_conf.get("header_title", "核心性能实测对比 (Benchmark)")
        hs = v_conf.get("header_sub", "吞吐量 QPS 压测")
        font_ht = ImageFont.truetype(FONT_HEITI, 46)
        font_hs = ImageFont.truetype(FONT_LIGHT, 26)
        draw.text((120, 60), ht, font=font_ht, fill=(248, 250, 252) if is_dark else (15, 23, 42))
        draw.text((120, 122), hs, font=font_hs, fill=(148, 163, 184) if is_dark else (100, 116, 139))

        if char_mode in ["pip", "none"]:
            card_w = 1680
            bar_max_w = 1040
            card_x = (self.width - card_w) // 2
        else:
            card_w = 1400
            bar_max_w = 760
            card_x = 120

        # 主容器卡片
        card_fill = (30, 41, 59, 252) if is_dark else (255, 255, 255, 250)
        card_border = (51, 65, 85) if is_dark else (226, 232, 240)
        card = Image.new("RGBA", (card_w, 750), (0, 0, 0, 0))
        ImageDraw.Draw(card).rounded_rectangle([0, 0, card_w, 750], radius=24, fill=card_fill, outline=card_border, width=2)
        frame.paste(card, (card_x, 190), card)

        items = v_conf.get("data", [])
        if not items:
            return frame

        max_val = max(it.get("value", 1) for it in items)
        start_y = 280
        row_h = 130

        font_lbl = ImageFont.truetype(FONT_HEITI, 28)
        font_num = ImageFont.truetype(FONT_HEITI, 32)

        for idx, it in enumerate(items):
            delay = 8 + idx * 16
            it_val = it.get("value", 0)
            theme = it.get("theme", "emerald" if idx == len(items)-1 else "slate")
            
            # 颜色方案
            if theme == "emerald":
                bar_col = (16, 185, 129)
                num_col = (52, 211, 153) if is_dark else (5, 150, 105)
            elif theme == "rose":
                bar_col = (244, 63, 94)
                num_col = (251, 113, 133) if is_dark else (225, 29, 72)
            elif theme == "indigo":
                bar_col = (99, 102, 241)
                num_col = (129, 140, 248) if is_dark else (79, 70, 229)
            else:
                bar_col = (148, 163, 184)
                num_col = (203, 213, 225) if is_dark else (71, 85, 105)

            y = start_y + idx * row_h

            # 1. 标题标签
            draw.text((card_x + 60, y), it.get("label", f"方案 {idx+1}"), font=font_lbl, fill=(241, 245, 249) if is_dark else (15, 23, 42))

            # 2. 动态生长进度
            if local_f >= delay:
                prog = ease_out_cubic((local_f - delay) / 28.0)
                curr_w = max(20, int((it_val / float(max_val)) * bar_max_w * prog))
                
                # 槽位底色
                track_col = (51, 65, 85) if is_dark else (241, 245, 249)
                draw.rounded_rectangle([card_x + 60, y + 42, card_x + 60 + bar_max_w, y + 80], radius=10, fill=track_col)
                # 填充彩色条
                draw.rounded_rectangle([card_x + 60, y + 42, card_x + 60 + curr_w, y + 80], radius=10, fill=bar_col)

                # 3. 动态数字翻牌器
                curr_val = int(it_val * prog)
                disp = f"{curr_val:,} {it.get('unit', 'QPS')}"
                draw.text((card_x + 60 + curr_w + 20, y + 42), disp, font=font_num, fill=num_col)

        # 冠军高亮气泡标签 (Champ badge)
        champ = v_conf.get("champion_tag")
        if champ and local_f >= 45:
            cp = ease_out_back((local_f - 45) / 14.0)
            bx, by = card_x + 60, start_y + len(items) * row_h + 30
            champ_bg = (6, 78, 59) if is_dark else (236, 253, 245)
            champ_border = (52, 211, 153) if is_dark else (110, 231, 183)
            champ_text = (209, 250, 229) if is_dark else (5, 150, 105)
            draw.rounded_rectangle([bx, by, bx + 440, by + 60], radius=16, fill=champ_bg, outline=champ_border, width=2)
            font_champ = ImageFont.truetype(FONT_HEITI, 24)
            draw.text((bx + 25, by + 16), champ, font=font_champ, fill=champ_text)

        # 角色展示
        if char_mode == "pip":
            frame = self._render_pip_avatar(frame, scene, local_f, global_f)
        elif char_mode != "none":
            stk = self.sprites.get(scene.get("character_sticker", "erii_chibi_cheer"))
            if stk:
                hop_y = -abs(math.sin(local_f / 6.0)) * 14.0
                frame.paste(stk, (self.width - 400, int(self.height - 440 + hop_y)), stk)

        return frame

    # ----------------- 布局组件 4: 拟真 macOS 终端打字机 (Terminal Mock) -----------------
    def _render_terminal_mock(self, scene, local_f, global_f):
        """黑客科技感打字机终端"""
        frame = self._get_background(scene).copy()
        draw = ImageDraw.Draw(frame)
        v_conf = scene.get("visual", {})

        is_dark = (scene.get("theme") or self.theme) in ["dark", "midnight", "hacker"]
        char_mode = scene.get("character_mode", "side")

        tag = v_conf.get("tag", "")
        title_y = 60
        if tag:
            font_tag = ImageFont.truetype(FONT_HEITI, 16)
            tb = draw.textbbox((0, 0), tag, font=font_tag)
            tw = tb[2] - tb[0]
            tag_bg = (30, 58, 138, 220) if is_dark else (219, 234, 254, 230)
            tag_border = (96, 165, 250) if is_dark else (59, 130, 246)
            tag_fg = (147, 197, 253) if is_dark else (30, 64, 175)
            draw.rounded_rectangle((120, 28, 120 + tw + 28, 58), radius=15, fill=tag_bg, outline=tag_border, width=1)
            draw.text((134, 35), tag, font=font_tag, fill=tag_fg)
            title_y = 72

        ht = v_conf.get("header_title", "实操验证：生产环境极限调优")
        hs = v_conf.get("header_sub", "Linux 命令行实机演示")
        font_ht = ImageFont.truetype(FONT_HEITI, 44)
        font_hs = ImageFont.truetype(FONT_LIGHT, 24)
        draw.text((120, title_y), ht, font=font_ht, fill=(248, 250, 252) if is_dark else (15, 23, 42))
        draw.text((120, title_y + 56), hs, font=font_hs, fill=(148, 163, 184) if is_dark else (100, 116, 139))

        if char_mode in ["pip", "none"]:
            term_w = 1680
            term_h = 780
            tx, ty = (self.width - term_w) // 2, 190
        else:
            term_w = 1380
            term_h = 760
            tx, ty = 120, 190

        # 终端窗口主体 (macOS 极客暗黑风)
        term = Image.new("RGBA", (term_w, term_h), (0, 0, 0, 0))
        d_t = ImageDraw.Draw(term)
        d_t.rounded_rectangle([0, 0, term_w, term_h], radius=20, fill=(30, 41, 59, 255), outline=(51, 65, 85), width=2)
        
        # 顶部标题栏
        d_t.rounded_rectangle([0, 0, term_w, 55], radius=20, fill=(15, 23, 42, 255))
        d_t.rectangle([0, 35, term_w, 55], fill=(15, 23, 42, 255))
        # 红黄绿三颗交通灯
        d_t.ellipse([20, 20, 34, 34], fill=(239, 68, 68))
        d_t.ellipse([42, 20, 56, 34], fill=(245, 158, 11))
        d_t.ellipse([64, 20, 78, 34], fill=(34, 197, 94))
        
        font_tt = ImageFont.truetype(FONT_LIGHT, 20)
        d_t.text((term_w // 2 - 80, 18), "zsh — 1920x1080", font=font_tt, fill=(148, 163, 184))

        # 命令行打字机效果
        cmd_text = v_conf.get("command", "redis-benchmark -q -n 100000 -c 50 -P 16")
        chars_typed = min(len(cmd_text), max(0, int(local_f * 2.2)))
        typed_cmd = cmd_text[:chars_typed]

        font_code = ImageFont.truetype(FONT_HEITI, 26)
        prompt = v_conf.get("prompt", "dev@mac:~/repo$ ")
        d_t.text((30, 85), prompt, font=font_code, fill=(56, 189, 248))
        
        # 测距
        bbox = d_t.textbbox((0, 0), prompt, font=font_code)
        pw = bbox[2] - bbox[0]
        d_t.text((30 + pw, 85), typed_cmd, font=font_code, fill=(241, 245, 249))

        # 闪烁光标
        if chars_typed < len(cmd_text) or math.sin(local_f / 3.0) > 0:
            c_bbox = d_t.textbbox((0, 0), typed_cmd, font=font_code)
            cw = c_bbox[2] - c_bbox[0]
            d_t.rectangle([30 + pw + cw + 4, 85, 30 + pw + cw + 18, 115], fill=(56, 189, 248))

        # 输出日志逐行淡入（带智能语法高亮）
        out_lines = v_conf.get("output_lines", [])
        type_finished_f = int(len(cmd_text) / 2.2)
        if local_f > type_finished_f:
            for idx, line in enumerate(out_lines):
                line_f = type_finished_f + 8 + idx * 10
                if local_f >= line_f:
                    line_str = str(line)
                    if any(k in line_str for k in ["[Auth]", "[Success]", "[Done]", "[Verify]", "✓", "✔"]):
                        fg = (52, 211, 153)
                    elif any(k in line_str for k in ["[Sandbox]", "[Security]", "[Warn]", "⚠", "Mode:", "blocked", "disabled"]):
                        fg = (251, 191, 36)
                    elif any(k in line_str for k in ["[Install]", "[Inspect]", "[Analysis]", "[Token]", "[Ready]"]):
                        fg = (56, 189, 248)
                    else:
                        fg = (226, 232, 240)
                    d_t.text((30, 140 + idx * 42), f"> {line_str}", font=font_code, fill=fg)

        if not is_dark:
            draw.rounded_rectangle([tx + 8, ty + 10, tx + term_w + 8, ty + term_h + 10], radius=24, fill=(226, 232, 240, 160))
        frame.paste(term, (tx, ty), term)

        # 角色展示
        if char_mode == "pip":
            frame = self._render_pip_avatar(frame, scene, local_f, global_f)
        elif char_mode != "none":
            stk = self.sprites.get(scene.get("character_sticker", "erii_chibi_think"))
            if stk:
                hover_y = math.sin(local_f / 16.0) * 6.0
                frame.paste(stk, (self.width - 400, int(self.height - 440 + hover_y)), stk)

        return frame

    # ----------------- 布局组件 5: 动态节点拓扑 (Custom Nodes) -----------------
    def _render_custom_nodes(self, scene, local_f, global_f):
        frame = self._get_background(scene).copy()
        draw = ImageDraw.Draw(frame)
        v_conf = scene.get("visual", {})

        is_dark = (scene.get("theme") or self.theme) in ["dark", "midnight", "hacker"]
        char_mode = scene.get("character_mode", "side")

        tag = v_conf.get("tag", "")
        title_y = 60
        if tag:
            font_tag = ImageFont.truetype(FONT_HEITI, 16)
            tb = draw.textbbox((0, 0), tag, font=font_tag)
            tw = tb[2] - tb[0]
            tag_bg = (30, 58, 138, 220) if is_dark else (219, 234, 254, 230)
            tag_border = (96, 165, 250) if is_dark else (59, 130, 246)
            tag_fg = (147, 197, 253) if is_dark else (30, 64, 175)
            draw.rounded_rectangle((120, 28, 120 + tw + 28, 58), radius=15, fill=tag_bg, outline=tag_border, width=1)
            draw.text((134, 35), tag, font=font_tag, fill=tag_fg)
            title_y = 72

        ht = v_conf.get("header_title", "")
        hs = v_conf.get("header_sub", "")
        font_ht = ImageFont.truetype(FONT_HEITI, 44)
        font_hs = ImageFont.truetype(FONT_LIGHT, 24)
        draw.text((120, title_y), ht, font=font_ht, fill=(248, 250, 252) if is_dark else (15, 23, 42))
        draw.text((120, title_y + 56), hs, font=font_hs, fill=(148, 163, 184) if is_dark else (100, 116, 139))

        node_items = v_conf.get("nodes", [])
        positions = [(100, 460), (480, 460), (860, 460), (1240, 460)]
        node_frames = [4, 30, 80, 130]

        line_col = (71, 85, 105) if is_dark else (148, 163, 184)
        for i in range(min(len(node_items) - 1, 3)):
            if local_f >= node_frames[i + 1]:
                x1 = positions[i][0] + 320
                x2 = positions[i + 1][0]
                y = positions[i][1] + 75
                draw.line([(x1 + 10, y), (x2 - 10, y)], fill=line_col, width=3)
                draw.polygon([(x2 - 10, y), (x2 - 20, y - 6), (x2 - 20, y + 6)], fill=line_col)

        for i, item in enumerate(node_items[:4]):
            if local_f >= node_frames[i]:
                node_sprite = self._make_flow_node(item.get("title", ""), item.get("sub", ""), item.get("theme", "white"), is_dark=is_dark)
                scale = ease_out_back((local_f - node_frames[i]) / 14.0)
                bx, by = positions[i]
                if not is_dark:
                    draw.rounded_rectangle([bx + 4, by + 6, bx + 324, by + 156], radius=16, fill=(226, 232, 240, 180))
                if abs(scale - 1.0) > 0.02:
                    nw, nh = max(1, int(320 * scale)), max(1, int(150 * scale))
                    sc_node = node_sprite.resize((nw, nh), Image.Resampling.BILINEAR)
                    frame.paste(sc_node, (bx - (nw - 320) // 2, by - (nh - 150) // 2), sc_node)
                else:
                    frame.paste(node_sprite, (bx, by), node_sprite)

        # 循环粒子
        if local_f >= node_frames[1]:
            cycle = local_f % 75
            prog = cycle / 75.0
            start_x = positions[0][0] + 320
            end_x = positions[min(len(node_items)-1, 3)][0]
            curr_x = start_x + (end_x - start_x) * prog
            cy = positions[0][1] + 75
            draw.ellipse([curr_x - 8, cy - 8, curr_x + 8, cy + 8], fill=(59, 130, 246, 200))
            draw.ellipse([curr_x - 4, cy - 4, curr_x + 4, cy + 4], fill=(255, 255, 255, 255))

        # 角色展示
        if char_mode == "pip":
            frame = self._render_pip_avatar(frame, scene, local_f, global_f)
        elif char_mode != "none":
            stk = self.sprites.get(scene.get("character_sticker", "erii_chibi_think"))
            if stk and local_f >= 10:
                stk_p = ease_out_back((local_f - 10) / 16.0)
                angle = math.sin(local_f / 12.0) * 3.5
                hover_y = math.sin(local_f / 16.0) * 6.0
                rot = stk.rotate(angle, resample=Image.Resampling.BILINEAR, expand=True)
                rx = int(self.width - 430 + (1.0 - stk_p) * 80)
                ry = int(self.height - 460 + hover_y)
                frame.paste(rot, (rx, ry), rot)

        return frame

    # ----------------- 布局组件 6: 语法高亮代码卡片 (Code) -----------------
    def _render_code_card(self, scene, local_f, global_f):
        frame = self._get_background(scene).copy()
        draw = ImageDraw.Draw(frame)
        v_conf = scene.get("visual", {})

        is_dark = (scene.get("theme") or self.theme) in ["dark", "midnight", "hacker"]
        char_mode = scene.get("character_mode", "side")

        ht = v_conf.get("header_title", "")
        hs = v_conf.get("header_sub", "")
        font_ht = ImageFont.truetype(FONT_HEITI, 46)
        font_hs = ImageFont.truetype(FONT_LIGHT, 26)
        draw.text((120, 65), ht, font=font_ht, fill=(248, 250, 252) if is_dark else (15, 23, 42))
        draw.text((120, 128), hs, font=font_hs, fill=(148, 163, 184) if is_dark else (100, 116, 139))

        code_sprite = self.sprites.get(f"{scene.get('id')}_visual")
        if code_sprite:
            if char_mode in ["pip", "none"]:
                cx = (self.width - code_sprite.width) // 2
            else:
                cx = 120
            cy = (self.height - code_sprite.height) // 2 + 25
            frame.paste(code_sprite, (cx, cy), code_sprite)

            if "spotlight_line" in v_conf:
                pulse_alpha = int(120 + 40 * math.sin(local_f / 5.0))
                hl_y1 = cy + int(code_sprite.height * 0.82)
                hl_y2 = hl_y1 + 42
                hl_x1 = cx + 50
                hl_x2 = cx + code_sprite.width - 60
                overlay = Image.new("RGBA", (self.width, self.height), (0, 0, 0, 0))
                ImageDraw.Draw(overlay).rounded_rectangle(
                    [hl_x1, hl_y1, hl_x2, hl_y2], radius=8,
                    fill=(254, 240, 138, pulse_alpha), outline=(234, 179, 8, pulse_alpha), width=2
                )
                frame = Image.alpha_composite(frame.convert("RGBA"), overlay).convert("RGB")

        # 角色展示
        if char_mode == "pip":
            frame = self._render_pip_avatar(frame, scene, local_f, global_f)
        elif char_mode != "none":
            stk = self.sprites.get(scene.get("character_sticker", "erii_chibi_happy"))
            if stk:
                hp = ease_out_back(local_f / 14.0)
                hop_y = -abs(math.sin(local_f / 6.0)) * 14.0
                hx = int(self.width - 450 + (1.0 - hp) * 80)
                hy = int(self.height - 470 + hop_y)
                frame.paste(stk, (hx, hy), stk)

        return frame

    # ----------------- 镜头节拍：真实截图 / 视频素材的动态聚焦 -----------------
    def _cinematic_beat(self, visual, local_f, total_scene_frames):
        """返回当前镜头节拍，并在相邻节拍间平滑移动焦点。"""
        """返回当前镜头节拍，并在相邻节拍间平滑移动焦点。"""
        beats = visual.get("beats") or [{"at": 0.0, "focus": [0.5, 0.5], "scale": 1.0}]
        beats = sorted(beats, key=lambda beat: float(beat.get("at", 0.0)))
        progress = min(1.0, max(0.0, local_f / float(max(1, total_scene_frames - 1))))
        current_index = max((i for i, beat in enumerate(beats) if float(beat.get("at", 0.0)) <= progress), default=0)
        current = beats[current_index]
        next_beat = beats[current_index + 1] if current_index + 1 < len(beats) else current
        current_at = float(current.get("at", 0.0))
        next_at = float(next_beat.get("at", 1.0))
        travel = 0.0 if next_at <= current_at else ease_in_out_quad((progress - current_at) / (next_at - current_at))

        current_focus = current.get("focus", [0.5, 0.5])
        next_focus = next_beat.get("focus", current_focus)
        focus = [
            float(current_focus[0]) + (float(next_focus[0]) - float(current_focus[0])) * travel,
            float(current_focus[1]) + (float(next_focus[1]) - float(current_focus[1])) * travel,
        ]
        current_scale = float(current.get("scale", 1.0))
        next_scale = float(next_beat.get("scale", current_scale))
        scale = current_scale + (next_scale - current_scale) * travel
        return current_index, current, focus, max(1.0, scale)

    def _fit_cinematic_label(self, scene, label):
        """把左下角标签限制在字幕胶囊之外；超长时截断并加省略号。

        预算按幕缓存，避免逐帧重算字幕宽度影响渲染速度。
        """
        scene_id = scene.get("id", "scene")
        if scene_id not in self._label_budget_cache:
            from engine.visual_qa import label_safe_width

            narration = (scene.get("audio") or {}).get("text") or scene.get("voice_text") or ""
            self._label_budget_cache[scene_id] = label_safe_width(narration, self.width)
        from engine.visual_qa import fit_label_to_width

        return fit_label_to_width(label, self._label_budget_cache[scene_id])

    def _render_cinematic_asset(self, scene, local_f, global_f, total_scene_frames, asset):
        """将截图或视频帧作为主画面，并按 beats 完成推镜、平移和标注。"""
        visual = scene.get("visual", {})
        if asset is None:
            return self._get_background(scene).copy()

        source = asset.convert("RGB")
        beat_index, beat, focus, scale = self._cinematic_beat(visual, local_f, total_scene_frames)
        iw, ih = source.size
        base_scale = max(self.width / float(iw), self.height / float(ih))
        render_scale = base_scale * scale
        rw, rh = max(1, int(iw * render_scale)), max(1, int(ih * render_scale))
        rendered = source.resize((rw, rh), Image.Resampling.LANCZOS)

        # 将素材焦点移到略高于画面中心的位置，同时始终约束在素材边缘内。
        target_x, target_y = self.width * 0.5, self.height * 0.47
        raw_x = int(target_x - focus[0] * rw)
        raw_y = int(target_y - focus[1] * rh)
        x = min(0, max(self.width - rw, raw_x))
        y = min(0, max(self.height - rh, raw_y))
        frame = Image.new("RGB", (self.width, self.height), (8, 12, 20))
        frame.paste(rendered, (x, y))

        overlay = Image.new("RGBA", (self.width, self.height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        # 顶部信息带和底部暗角让真实素材保持主角，但仍保留清晰的讲解上下文。
        draw.rectangle((0, 0, self.width, 100), fill=(2, 6, 16, 184))
        draw.rectangle((0, self.height - 128, self.width, self.height), fill=(2, 6, 16, 145))
        accent_palette = {
            "emerald": (52, 211, 153), "gold": (251, 191, 36),
            "rose": (251, 113, 133), "indigo": (129, 140, 248),
        }
        accent = accent_palette.get(beat.get("accent", "indigo"), accent_palette["indigo"])
        draw.rectangle((0, 0, 10, 100), fill=accent + (255,))
        font_meta = ImageFont.truetype(FONT_HEITI, 18)
        font_label = ImageFont.truetype(FONT_HEITI, 30)
        draw.text((42, 22), f"SCREEN WALKTHROUGH  ·  {beat_index + 1:02d}", font=font_meta, fill=(203, 213, 225, 255))
        label = beat.get("label") or visual.get("header_title", "")
        if label:
            label = self._fit_cinematic_label(scene, label)
            draw.text((42, self.height - 91), label, font=font_label, fill=(248, 250, 252, 255))

        # callout 使用原始素材的归一化坐标，镜头移动时会和被讲解的 UI 元素一起移动。
        callout = beat.get("callout")
        if callout and len(callout) == 4:
            cx, cy, cw, ch = [float(value) for value in callout]
            left, top = int(x + cx * rw), int(y + cy * rh)
            right, bottom = int(left + cw * rw), int(top + ch * rh)
            pulse = int(2 + abs(math.sin(global_f / 7.0)) * 3)
            draw.rounded_rectangle((left, top, right, bottom), radius=14, outline=accent + (255,), width=pulse)
            draw.rounded_rectangle((left - 6, top - 6, right + 6, bottom + 6), radius=18, outline=accent + (115,), width=2)

        return Image.alpha_composite(frame.convert("RGBA"), overlay).convert("RGB")

    def _video_frame_for_scene(self, scene_id, local_f):
        clip = self.video_clips.get(scene_id)
        if not clip:
            return None
        frame_index = min(len(clip["frames"]) - 1, int(local_f / float(self.fps) * clip["fps"]))
        cache_key = (scene_id, frame_index)
        if cache_key not in self._video_frame_cache:
            # 视频镜头通常顺序播放；仅保留当前帧，避免长片段占用大量 RAM。
            self._video_frame_cache.clear()
            with Image.open(clip["frames"][frame_index]) as image:
                self._video_frame_cache[cache_key] = image.convert("RGB")
        return self._video_frame_cache[cache_key]

    def _render_video_clip(self, scene, local_f, global_f, total_scene_frames):
        frame = self._video_frame_for_scene(scene.get("id"), local_f)
        return self._render_cinematic_asset(scene, local_f, global_f, total_scene_frames, frame)

    def _render_asset_placeholder(self, scene, local_f, global_f):
        """制作期素材占位画面：明确告知缺口，避免用虚构终端或跑分掩盖它。"""
        frame = self._get_background(scene).copy()
        draw = ImageDraw.Draw(frame)
        visual = scene.get("visual", {})
        is_dark = (scene.get("theme") or self.theme) in ["dark", "midnight", "hacker"]
        bg = (15, 23, 42) if is_dark else (239, 246, 255)
        border = (59, 130, 246) if is_dark else (147, 197, 253)
        title_fg = (248, 250, 252) if is_dark else (30, 58, 138)
        body_fg = (203, 213, 225) if is_dark else (71, 85, 105)
        p = ease_out_back(min(1.0, local_f / 18.0))
        card_w, card_h = 1280, 610
        card_x = (self.width - card_w) // 2
        card_y = int(220 + (1.0 - p) * 60)
        draw.rounded_rectangle((card_x, card_y, card_x + card_w, card_y + card_h), radius=28, fill=bg, outline=border, width=3)
        font_tag = ImageFont.truetype(FONT_HEITI, 20)
        font_title = ImageFont.truetype(FONT_HEITI, 48)
        font_body = ImageFont.truetype(FONT_LIGHT, 28)
        draw.rounded_rectangle((card_x + 56, card_y + 54, card_x + 310, card_y + 96), radius=20, fill=(30, 64, 175), outline=border, width=1)
        draw.text((card_x + 78, card_y + 64), "素材待补录", font=font_tag, fill=(219, 234, 254))
        draw.text((card_x + 56, card_y + 138), visual.get("header_title", "需要真实证据"), font=font_title, fill=title_fg)
        required = visual.get("required_asset", "screen_recording_demo.mp4")
        purpose = visual.get("purpose", "展示关键操作或状态变化")
        notes = visual.get("capture_notes", "录制关键动作与结果")
        for idx, line in enumerate((f"需要文件：{required}", f"用途：{purpose}", f"录制提示：{notes}")):
            draw.ellipse((card_x + 65, card_y + 245 + idx * 94, card_x + 77, card_y + 257 + idx * 94), fill=(96, 165, 250))
            draw.text((card_x + 98, card_y + 235 + idx * 94), line, font=font_body, fill=body_fg)
        return frame

    # ----------------- 布局组件 7: 架构图 / 真实截图展台 (Diagram / Screenshot Showcase) -----------------
    def _render_diagram_or_image(self, scene, local_f, global_f, total_scene_frames=300):
        frame = self._get_background(scene).copy()
        draw = ImageDraw.Draw(frame)
        v_conf = scene.get("visual", {})

        is_dark = (scene.get("theme") or self.theme) in ["dark", "midnight", "hacker"]
        char_mode = scene.get("character_mode", "side")

        # 顶部标题栏与分类标签
        ht = v_conf.get("header_title", "")
        hs = v_conf.get("header_sub", "")
        tag = v_conf.get("tag", "")

        title_y = 60
        if tag:
            font_tag = ImageFont.truetype(FONT_HEITI, 16)
            tb = draw.textbbox((0, 0), tag, font=font_tag)
            tw = tb[2] - tb[0]
            tag_bg = (30, 58, 138, 220) if is_dark else (219, 234, 254, 230)
            tag_border = (96, 165, 250) if is_dark else (59, 130, 246)
            tag_fg = (147, 197, 253) if is_dark else (30, 64, 175)
            draw.rounded_rectangle((120, 28, 120 + tw + 28, 58), radius=15, fill=tag_bg, outline=tag_border, width=1)
            draw.text((134, 35), tag, font=font_tag, fill=tag_fg)
            title_y = 72

        if ht:
            font_ht = ImageFont.truetype(FONT_HEITI, 44)
            draw.text((120, title_y), ht, font=font_ht, fill=(248, 250, 252) if is_dark else (15, 23, 42))
        if hs:
            font_hs = ImageFont.truetype(FONT_LIGHT, 24)
            draw.text((120, title_y + 56), hs, font=font_hs, fill=(148, 163, 184) if is_dark else (100, 116, 139))

        img_sprite = self.sprites.get(f"{scene.get('id')}_visual")
        bullets = v_conf.get("bullets", [])
        window_title = v_conf.get("window_title", "OpenAI Codex - Workspace")

        if v_conf.get("presentation") == "cinematic":
            return self._render_cinematic_asset(scene, local_f, global_f, total_scene_frames, img_sprite)

        # 动效缓动
        p_in = ease_out_back(min(1.0, max(0.0, local_f / 14.0)))

        # 布局分支：如果存在 bullets，则采用 [左侧重点提炼卡 + 右侧真实软件窗口]；如果无 bullets，采用全宽居中 macOS 展台
        if bullets and len(bullets) > 0:
            left_w = 600
            right_w = 1040
            card_h = 750
            card_y = 195 + int((1.0 - p_in) * 35)

            # 1. 左侧要点提炼卡片
            card_left = Image.new("RGBA", (left_w, card_h), (0, 0, 0, 0))
            d_l = ImageDraw.Draw(card_left)
            bg_l = (30, 41, 59, 240) if is_dark else (255, 255, 255, 245)
            bdr_l = (51, 65, 85) if is_dark else (226, 232, 240)
            d_l.rounded_rectangle((0, 0, left_w, card_h), radius=18, fill=bg_l, outline=bdr_l, width=2)

            card_badge = v_conf.get("badge", "核心要点解析").lstrip("✦●■◆★[] 🔒🖥️⚡ ")
            font_bd = ImageFont.truetype(FONT_HEITI, 22)
            badge_fg = (96, 165, 250) if is_dark else (37, 99, 235)
            d_l.rounded_rectangle((36, 32, 42, 54), radius=3, fill=badge_fg)
            d_l.text((54, 30), card_badge, font=font_bd, fill=badge_fg)

            card_title = v_conf.get("title", "")
            if card_title:
                font_ct = ImageFont.truetype(FONT_HEITI, 28)
                d_l.text((36, 80), card_title, font=font_ct, fill=(248, 250, 252) if is_dark else (15, 23, 42))

            by = 135 if card_title else 88
            font_bt = ImageFont.truetype(FONT_LIGHT, 23)
            for b_idx, bullet in enumerate(bullets):
                dot_color = (59, 130, 246) if b_idx % 2 == 0 else (16, 185, 129)
                d_l.ellipse((36, by + 10, 48, by + 22), fill=dot_color)

                # 文本折行
                b_text = str(bullet)
                w_lines = []
                while len(b_text) > 21:
                    sp = 21
                    for i in range(16, 21):
                        if b_text[i] in "，、：； ":
                            sp = i + 1
                            break
                    w_lines.append(b_text[:sp].strip())
                    b_text = b_text[sp:].strip()
                if b_text:
                    w_lines.append(b_text)

                for wl in w_lines:
                    d_l.text((60, by + 4), wl, font=font_bt, fill=(226, 232, 240) if is_dark else (51, 65, 85))
                    by += 38
                by += 16

            frame.paste(card_left, (120, card_y), card_left)

            # 2. 右侧图片 macOS 容器
            right_x = 120 + left_w + 30
            card_right = Image.new("RGBA", (right_w, card_h), (0, 0, 0, 0))
            d_r = ImageDraw.Draw(card_right)
            img_bg_opt = v_conf.get("img_bg", "dark" if is_dark else "light")
            if img_bg_opt == "white":
                bg_r = (255, 255, 255, 255)
                top_bg_r = (241, 245, 249)
                top_fg_r = (100, 116, 139)
                bdr_r = (226, 232, 240)
            else:
                bg_r = (15, 23, 42, 255) if is_dark else (248, 250, 252, 255)
                top_bg_r = (30, 41, 59) if is_dark else (241, 245, 249)
                top_fg_r = (148, 163, 184) if is_dark else (100, 116, 139)
                bdr_r = (51, 65, 85) if is_dark else (203, 213, 225)
            d_r.rounded_rectangle((0, 0, right_w, card_h), radius=18, fill=bg_r, outline=bdr_r, width=2)

            # 顶部操作栏
            d_r.rounded_rectangle((0, 0, right_w, 42), radius=18, fill=top_bg_r)
            d_r.rectangle((0, 26, right_w, 42), fill=top_bg_r)
            d_r.ellipse((20, 15, 32, 27), fill=(239, 68, 68))
            d_r.ellipse((40, 15, 52, 27), fill=(245, 158, 11))
            d_r.ellipse((60, 15, 72, 27), fill=(16, 185, 129))
            font_wt = ImageFont.truetype(FONT_LIGHT, 17)
            d_r.text((90, 12), window_title, font=font_wt, fill=top_fg_r)

            if img_sprite:
                avail_w = right_w - 20
                avail_h = card_h - 42 - 16
                iw, ih = img_sprite.size
                scale = min(float(avail_w) / iw, float(avail_h) / ih)
                target_w, target_h = max(1, int(iw * scale)), max(1, int(ih * scale))
                resized = img_sprite.resize((target_w, target_h), Image.Resampling.LANCZOS)
                px = (right_w - target_w) // 2
                py = 42 + (avail_h - target_h) // 2
                if resized.mode == "RGBA":
                    card_right.paste(resized, (px, py), resized)
                else:
                    card_right.paste(resized, (px, py))

            frame.paste(card_right, (right_x, card_y), card_right)

        else:
            # 全屏宽居中 macOS 窗口展台模式
            card_w = 1680 if char_mode in ["pip", "none"] else 1380
            card_h = 760
            card_x = (self.width - card_w) // 2 if char_mode in ["pip", "none"] else 120
            card_y = 190 + int((1.0 - p_in) * 35)

            card_win = Image.new("RGBA", (card_w, card_h), (0, 0, 0, 0))
            d_w = ImageDraw.Draw(card_win)
            img_bg_opt = v_conf.get("img_bg", "dark" if is_dark else "light")
            if img_bg_opt == "white":
                bg_w = (255, 255, 255, 255)
                top_bg_w = (241, 245, 249)
                top_fg_w = (100, 116, 139)
                bdr_w = (226, 232, 240)
            else:
                bg_w = (15, 23, 42, 255) if is_dark else (255, 255, 255, 255)
                top_bg_w = (30, 41, 59) if is_dark else (241, 245, 249)
                top_fg_w = (148, 163, 184) if is_dark else (100, 116, 139)
                bdr_w = (51, 65, 85) if is_dark else (203, 213, 225)
            d_w.rounded_rectangle((0, 0, card_w, card_h), radius=18, fill=bg_w, outline=bdr_w, width=2)

            # 顶部操作栏
            d_w.rounded_rectangle((0, 0, card_w, 42), radius=18, fill=top_bg_w)
            d_w.rectangle((0, 26, card_w, 42), fill=top_bg_w)
            d_w.ellipse((22, 15, 34, 27), fill=(239, 68, 68))
            d_w.ellipse((42, 15, 54, 27), fill=(245, 158, 11))
            d_w.ellipse((62, 15, 74, 27), fill=(16, 185, 129))
            font_wt = ImageFont.truetype(FONT_LIGHT, 18)
            d_w.text((94, 12), window_title, font=font_wt, fill=top_fg_w)

            if img_sprite:
                avail_w = card_w - 24
                avail_h = card_h - 42 - 16
                iw, ih = img_sprite.size
                scale = min(float(avail_w) / iw, float(avail_h) / ih)
                target_w, target_h = max(1, int(iw * scale)), max(1, int(ih * scale))
                resized = img_sprite.resize((target_w, target_h), Image.Resampling.LANCZOS)
                px = (card_w - target_w) // 2
                py = 42 + (avail_h - target_h) // 2
                if resized.mode == "RGBA":
                    card_win.paste(resized, (px, py), resized)
                else:
                    card_win.paste(resized, (px, py))

            frame.paste(card_win, (card_x, card_y), card_win)

        # 贴纸动效（仅在 side 模式下渲染）
        if char_mode == "side":
            stk = self.sprites.get(scene.get("character_sticker", "erii_chibi_think"))
            if stk:
                hover_y = math.sin(local_f / 16.0) * 6.0
                frame.paste(stk, (self.width - 430, int(self.height - 460 + hover_y)), stk)

        return frame

    # ----------------- 布局组件 8: Git Diff 源码重构对比 (Git Diff) -----------------
    def _render_git_diff(self, scene, local_f, global_f):
        frame = self._get_background(scene).copy()
        draw = ImageDraw.Draw(frame)
        v_conf = scene.get("visual", {})

        is_dark = (scene.get("theme") or self.theme) in ["dark", "midnight", "hacker"]
        char_mode = scene.get("character_mode", "side")

        ht = v_conf.get("header_title", "核心源码重构对比")
        hs = v_conf.get("header_sub", "从旧逻辑到新架构的代码演进")
        font_ht = ImageFont.truetype(FONT_HEITI, 46)
        font_hs = ImageFont.truetype(FONT_LIGHT, 26)
        draw.text((120, 60), ht, font=font_ht, fill=(248, 250, 252) if is_dark else (15, 23, 42))
        draw.text((120, 122), hs, font=font_hs, fill=(148, 163, 184) if is_dark else (100, 116, 139))

        if char_mode in ["pip", "none"]:
            diff_w = 1680
            diff_h = 780
            dx, dy = (self.width - diff_w) // 2, 190
        else:
            diff_w = 1380
            diff_h = 760
            dx, dy = 120, 190

        card_bg = (30, 41, 59, 255) if is_dark else (255, 255, 255, 252)
        card_border = (51, 65, 85) if is_dark else (203, 213, 225)
        diff_card = Image.new("RGBA", (diff_w, diff_h), (0, 0, 0, 0))
        d_draw = ImageDraw.Draw(diff_card)
        d_draw.rounded_rectangle([0, 0, diff_w, diff_h], radius=20, fill=card_bg, outline=card_border, width=2)
        
        # Header bar
        header_bg = (15, 23, 42, 255) if is_dark else (241, 245, 249, 255)
        d_draw.rounded_rectangle([0, 0, diff_w, 55], radius=20, fill=header_bg)
        d_draw.rectangle([0, 35, diff_w, 55], fill=header_bg)
        d_draw.line([(0, 55), (diff_w, 55)], fill=(51, 65, 85) if is_dark else (226, 232, 240), width=1)
        d_draw.ellipse([20, 20, 34, 34], fill=(239, 68, 68))
        d_draw.ellipse([42, 20, 56, 34], fill=(245, 158, 11))
        d_draw.ellipse([64, 20, 78, 34], fill=(34, 197, 94))
        
        file_name = v_conf.get("file_name", "src/event_loop.c (Git Diff 优化)")
        font_fn = ImageFont.truetype(FONT_LIGHT, 20)
        d_draw.text((100, 18), file_name, font=font_fn, fill=(203, 213, 225) if is_dark else (71, 85, 105))

        diff_text = v_conf.get("diff", "")
        lines = [l for l in diff_text.strip().split("\n") if l.strip()]
        font_code = ImageFont.truetype(FONT_HEITI, 22)
        font_num = ImageFont.truetype(FONT_LIGHT, 18)
        
        line_y = 70
        line_height = 46

        for idx, line in enumerate(lines[:12]):
            line_f = 6 + idx * 4
            if local_f < line_f:
                continue

            slide_p = ease_out_cubic((local_f - line_f) / 10.0)
            off_x = int((1.0 - slide_p) * 25)

            is_add = line.startswith("+")
            is_del = line.startswith("-")

            if is_add:
                bg_col = (6, 78, 59, 220) if is_dark else (236, 253, 245, 255)
                border_col = (52, 211, 153) if is_dark else (167, 243, 208)
                text_col = (209, 250, 229) if is_dark else (6, 95, 70)
                sign_col = (52, 211, 153) if is_dark else (5, 150, 105)
            elif is_del:
                bg_col = (136, 19, 55, 220) if is_dark else (255, 241, 242, 255)
                border_col = (251, 113, 133) if is_dark else (254, 205, 211)
                text_col = (255, 228, 230) if is_dark else (159, 18, 57)
                sign_col = (251, 113, 133) if is_dark else (225, 29, 72)
            else:
                bg_col = (255, 255, 255, 0)
                border_col = None
                text_col = (226, 232, 240) if is_dark else (51, 65, 85)
                sign_col = (148, 163, 184)

            d_draw.rectangle([20, line_y, diff_w - 20, line_y + line_height], fill=bg_col)
            if border_col:
                d_draw.line([(20, line_y), (20, line_y + line_height)], fill=border_col, width=4)

            d_draw.text((35, line_y + 12), f"{idx+1:2d}", font=font_num, fill=(148, 163, 184))
            sign = line[0] if (is_add or is_del) else " "
            d_draw.text((70, line_y + 10), sign, font=font_code, fill=sign_col)
            content = line[1:].strip() if (is_add or is_del) else line.strip()
            d_draw.text((95 + off_x, line_y + 10), content, font=font_code, fill=text_col)

            line_y += line_height

        summary_tag = v_conf.get("summary_tag", "⚡ 消除 100% CPU 空转，重构后仅在事件就绪时唤醒")
        if summary_tag and local_f >= 28:
            tag_fill = (49, 46, 129) if is_dark else (238, 242, 255)
            tag_border = (99, 102, 241) if is_dark else (199, 210, 254)
            tag_text = (199, 210, 254) if is_dark else (79, 70, 229)
            d_draw.rounded_rectangle([25, diff_h - 65, diff_w - 25, diff_h - 18], radius=12, fill=tag_fill, outline=tag_border, width=1)
            font_st = ImageFont.truetype(FONT_HEITI, 20)
            d_draw.text((45, diff_h - 52), summary_tag, font=font_st, fill=tag_text)

        frame.paste(diff_card, (dx, dy), diff_card)

        # 角色展示
        if char_mode == "pip":
            frame = self._render_pip_avatar(frame, scene, local_f, global_f)
        elif char_mode != "none":
            stk = self.sprites.get(scene.get("character_sticker", "erii_chibi_happy"))
            if stk:
                hop_y = -abs(math.sin(local_f / 6.0)) * 12.0
                frame.paste(stk, (self.width - 400, int(self.height - 440 + hop_y)), stk)

        return frame

    # ----------------- 视听爆点: 关键词高能冲击大字报 (Kinetic Punch) -----------------
    def _render_kinetic_punch(self, frame, text, local_f, start_f, length=36, style="emerald"):
        rel_f = local_f - start_f
        if rel_f < 0 or rel_f >= length:
            return frame

        prog = rel_f / float(length)
        if prog < 0.22:
            scale = ease_out_back(prog / 0.22, s=2.0)
            alpha = min(1.0, prog / 0.1)
        elif prog < 0.80:
            scale = 1.0 + 0.03 * math.sin(prog * 12.0)
            alpha = 1.0
        else:
            scale = 1.0 - 0.15 * ((prog - 0.80) / 0.20)
            alpha = max(0.0, (1.0 - prog) / 0.20)

        if scale <= 0.05 or alpha <= 0.01:
            return frame

        palettes = {
            "emerald": {
                "fill": (6, 78, 59, int(245 * alpha)),
                "border": (52, 211, 153, int(255 * alpha)),
                "text": (255, 255, 255, int(255 * alpha)),
                "icon": "⚡"
            },
            "rose": {
                "fill": (136, 19, 55, int(245 * alpha)),
                "border": (251, 113, 133, int(255 * alpha)),
                "text": (255, 255, 255, int(255 * alpha)),
                "icon": "💥"
            },
            "gold": {
                "fill": (120, 53, 15, int(245 * alpha)),
                "border": (251, 191, 36, int(255 * alpha)),
                "text": (255, 255, 255, int(255 * alpha)),
                "icon": "🔥"
            },
            "indigo": {
                "fill": (30, 27, 75, int(245 * alpha)),
                "border": (129, 140, 248, int(255 * alpha)),
                "text": (255, 255, 255, int(255 * alpha)),
                "icon": "🚀"
            }
        }
        pal = palettes.get(style, palettes["emerald"])
        full_text = text

        font_punch = ImageFont.truetype(FONT_HEITI, max(14, int(52 * scale)))
        dummy = ImageDraw.Draw(frame)
        bbox = dummy.textbbox((0, 0), full_text, font=font_punch)
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]

        pad_x = int(48 * scale)
        pad_y = int(22 * scale)
        box_w = tw + pad_x * 2
        box_h = th + pad_y * 2

        cx = self.width // 2
        shake_x = int(math.sin(rel_f * 2.5) * 5.0 * (1.0 - prog)) if prog < 0.25 else 0
        cy = 340 + int(math.sin(rel_f / 8.0) * 4.0)

        bx1 = cx - box_w // 2 + shake_x
        by1 = cy - box_h // 2
        bx2 = bx1 + box_w
        by2 = by1 + box_h

        overlay = Image.new("RGBA", (self.width, self.height), (0, 0, 0, 0))
        d_ov = ImageDraw.Draw(overlay)
        d_ov.rounded_rectangle([bx1 - 4, by1 - 4, bx2 + 4, by2 + 4], radius=box_h // 2, outline=pal["border"], width=3)
        d_ov.rounded_rectangle([bx1, by1, bx2, by2], radius=box_h // 2, fill=pal["fill"], outline=pal["border"], width=3)
        d_ov.text((bx1 + pad_x, by1 + pad_y - int(4 * scale)), full_text, font=font_punch, fill=pal["text"])

        return Image.alpha_composite(frame.convert("RGBA"), overlay).convert("RGB")

    # ----------------- 调度总入口与虚拟摄像机 -----------------
    def render_scene_frame(self, scene, local_f, global_f, total_scene_frames=300):
        v_conf = scene.get("visual", {})
        v_type = scene.get("layout") or v_conf.get("type", "title_card")

        if v_type == "title_card":
            frame = self._render_title_card(scene, local_f, global_f)
        elif v_type in ["split_compare", "compare"]:
            frame = self._render_split_compare(scene, local_f, global_f)
        elif v_type in ["chart_benchmark", "benchmark", "chart"]:
            frame = self._render_chart_benchmark(scene, local_f, global_f)
        elif v_type in ["terminal", "terminal_mock", "cli"]:
            frame = self._render_terminal_mock(scene, local_f, global_f)
        elif v_type in ["git_diff", "diff"]:
            frame = self._render_git_diff(scene, local_f, global_f)
        elif v_type == "custom_nodes":
            frame = self._render_custom_nodes(scene, local_f, global_f)
        elif v_type == "code":
            frame = self._render_code_card(scene, local_f, global_f)
        elif v_type in ["video_clip", "video", "clip"]:
            frame = self._render_video_clip(scene, local_f, global_f, total_scene_frames)
        elif v_type in ["asset_placeholder", "material_placeholder"]:
            frame = self._render_asset_placeholder(scene, local_f, global_f)
        else:
            frame = self._render_diagram_or_image(scene, local_f, global_f, total_scene_frames)

        # 虚拟摄像机平滑微动效 (Virtual Camera)
        cam = scene.get("camera", {})
        c_motion = cam.get("motion")
        if c_motion == "zoom_in":
            prog = min(1.0, local_f / float(max(1, total_scene_frames)))
            scale = 1.0 + 0.08 * prog
            nw, nh = int(self.width * scale), int(self.height * scale)
            zoomed = frame.resize((nw, nh), Image.Resampling.BILINEAR)
            ox = (nw - self.width) // 2
            oy = (nh - self.height) // 2
            frame = zoomed.crop((ox, oy, ox + self.width, oy + self.height))
        elif c_motion == "zoom_punch":
            prog = ease_out_back(min(1.0, local_f / 16.0))
            scale = 1.12 - 0.12 * prog
            nw, nh = int(self.width * scale), int(self.height * scale)
            zoomed = frame.resize((nw, nh), Image.Resampling.BILINEAR)
            ox = (nw - self.width) // 2
            oy = (nh - self.height) // 2
            frame = zoomed.crop((ox, oy, ox + self.width, oy + self.height))

        return frame

    def _render_host_badge(self, name="上杉绘梨衣", sub="Sakura 的计算机小课堂"):
        badge = Image.new("RGBA", (540, 130), (0, 0, 0, 0))
        draw = ImageDraw.Draw(badge)
        draw.rounded_rectangle([0, 0, 540, 130], radius=20, fill=(248, 250, 252, 255), outline=(226, 232, 240, 255), width=1)
        
        avatar_path = self.resolver.resolve_image("erii_avatar")
        if avatar_path:
            av = Image.open(avatar_path).resize((100, 100), Image.Resampling.LANCZOS)
            mask = Image.new("L", (100, 100), 0)
            ImageDraw.Draw(mask).ellipse((0, 0, 100, 100), fill=255)
            badge.paste(av, (15, 15), mask)
            
        font_name = ImageFont.truetype(FONT_HEITI, 28)
        font_sub_name = ImageFont.truetype(FONT_LIGHT, 22)
        draw.text((130, 25), f"主讲：{name}", font=font_name, fill=(15, 23, 42))
        draw.ellipse((132, 77, 142, 87), fill=(244, 114, 182))
        draw.text((152, 70), sub, font=font_sub_name, fill=(225, 29, 72))
        return badge

    def _make_flow_node(self, title, sub, theme="white", is_dark=False):
        if is_dark:
            palette = {
                "white": ((30, 41, 59, 240), (71, 85, 105), (248, 250, 252), (148, 163, 184)),
                "slate": ((30, 41, 59, 240), (71, 85, 105), (248, 250, 252), (148, 163, 184)),
                "blue": ((30, 58, 138, 240), (96, 165, 250), (239, 246, 255), (191, 219, 254)),
                "amber": ((120, 53, 15, 240), (245, 158, 11), (254, 243, 199), (253, 230, 138)),
                "green": ((20, 83, 45, 240), (74, 222, 128), (240, 253, 244), (187, 247, 208))
            }
        else:
            palette = {
                "white": ((255, 255, 255), (203, 213, 225), (15, 23, 42), (100, 116, 139)),
                "slate": ((241, 245, 249), (203, 213, 225), (15, 23, 42), (100, 116, 139)),
                "blue": ((239, 246, 255), (96, 165, 250), (30, 58, 138), (37, 99, 235)),
                "amber": ((254, 243, 199), (245, 158, 11), (120, 53, 15), (180, 83, 9)),
                "green": ((240, 253, 244), (74, 222, 128), (20, 83, 45), (22, 101, 52))
            }
        bg, border, tc, sc = palette.get(theme, palette["white"])
        w, h = 320, 150
        node = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        draw = ImageDraw.Draw(node)
        draw.rounded_rectangle([0, 0, w, h], radius=16, fill=bg, outline=border, width=2)
        
        font_t = ImageFont.truetype(FONT_HEITI, 24)
        font_s = ImageFont.truetype(FONT_LIGHT, 20)
        
        bbox_t = draw.textbbox((0, 0), title, font=font_t)
        tw = bbox_t[2] - bbox_t[0]
        draw.text(((w - tw) // 2, 35), title, font=font_t, fill=tc)
        
        bbox_s = draw.textbbox((0, 0), sub, font=font_s)
        sw = bbox_s[2] - bbox_s[0]
        draw.text(((w - sw) // 2, 80), sub, font=font_s, fill=sc)
        return node

    def render_subtitle_pill(self, frame, text, alpha, pop_progress=1.0, center_x=None):
        if not text or alpha <= 0:
            return frame
        font = ImageFont.truetype(FONT_HEITI, 28)
        dummy = ImageDraw.Draw(frame)
        
        # 智能折行：如果单句超过 24 字，在合适标点或居中位置折行
        max_chars = 24
        if len(text) > max_chars:
            mid = len(text) // 2
            best_split = mid
            for i in range(max(0, mid - 6), min(len(text), mid + 6)):
                if text[i] in "，、；： ":
                    best_split = i + 1
                    break
            lines = [text[:best_split].strip(), text[best_split:].strip()]
        else:
            lines = [text]

        pad_x, pad_y = 32, 12
        line_height = 36
        
        line_widths = []
        for l in lines:
            bbox = dummy.textbbox((0, 0), l, font=font)
            line_widths.append(bbox[2] - bbox[0])
            
        max_lw = max(line_widths) if line_widths else 200
        pill_w = max_lw + pad_x * 2
        pill_h = len(lines) * line_height + pad_y * 2
        
        # 严格避让右下角画中画头像 (头像位于 x=1700, y=860, r=80, 避让边界 250px)
        max_right = self.width - 250
        if center_x is None:
            x = (self.width - pill_w) // 2
        else:
            x = int(center_x - pill_w // 2)
            
        x = max(60, min(x, max_right - pill_w))
        y_offset = (1.0 - pop_progress) * 10.0
        y = int(self.height - 110 + y_offset - (len(lines) - 1) * 20)
        
        overlay = Image.new("RGBA", (self.width, self.height), (0, 0, 0, 0))
        draw_ov = ImageDraw.Draw(overlay)
        
        # 暗黑极客毛玻璃胶囊（高对比度白字 + 精致深色投影）
        draw_ov.rounded_rectangle([x, y + 4, x + pill_w, y + pill_h + 4], radius=16, fill=(0, 0, 0, int(70 * alpha)))
        draw_ov.rounded_rectangle([x, y, x + pill_w, y + pill_h], radius=16, fill=(15, 23, 42, int(235 * alpha)), outline=(51, 65, 85, int(220 * alpha)), width=2)
        
        for idx, l in enumerate(lines):
            cur_bbox = dummy.textbbox((0, 0), l, font=font)
            cur_tw = cur_bbox[2] - cur_bbox[0]
            cur_x = x + (pill_w - cur_tw) // 2
            cur_y = y + pad_y + idx * line_height
            draw_ov.text((cur_x, cur_y), l, font=font, fill=(248, 250, 252, int(255 * alpha)))
            
        return Image.alpha_composite(frame.convert("RGBA"), overlay).convert("RGB")

    def quality_report(self, threshold=None):
        """返回当前剧本的质量报告（不写文件、不渲染）。"""
        from engine.quality_gate import DEFAULT_QUALITY_THRESHOLD, evaluate_storyboard
        return evaluate_storyboard(self.spec, threshold or DEFAULT_QUALITY_THRESHOLD)

    def sample_scene_frames(self, output_dir=None, fractions=(0.0, 0.5, 1.0)):
        """按幕抽取首/中/末帧用于目视质检；时长与字幕按逐句估算，不调用 TTS。

        字幕在 build() 的时间轴循环里叠加，因此这里必须补画，否则检查帧与成片不一致。
        """
        from engine.tts_engine import split_sentences
        from engine.visual_qa import estimate_scene_seconds

        # QA 抽帧与人工策展的展示图分开存放，避免互相覆盖。
        out_dir = output_dir or os.path.join(self.dist_dir, "inspect", "qa")
        os.makedirs(out_dir, exist_ok=True)
        self.prepare_visual_assets()

        def sentence_timeline(scene):
            audio_conf = scene.get("audio", {}) or {}
            text = str(audio_conf.get("text") or scene.get("voice_text") or "")
            speed = float(audio_conf.get("speed") or 1.05)
            pause = float(audio_conf.get("pause") or 0.35)
            timeline = []
            cursor = 0.0
            for sentence in split_sentences(text):
                duration = len(sentence) / (4.5 * max(0.5, speed))
                timeline.append((cursor, cursor + duration, sentence))
                cursor += duration + pause
            return timeline

        written = []
        for scene in self.spec.get("scenes", []):
            scene_id = scene.get("id", "scene")
            total_frames = max(1, int(estimate_scene_seconds(scene) * self.fps))
            timeline = sentence_timeline(scene)
            visual_type = scene.get("layout") or (scene.get("visual") or {}).get("type")
            center_x = 640 if visual_type == "title_card" else None
            for fraction in fractions:
                frame_index = min(total_frames - 1, int(total_frames * fraction))
                frame = self.render_scene_frame(scene, frame_index, frame_index, total_frames)
                seconds = frame_index / float(self.fps)
                for start, end, sentence in timeline:
                    if start <= seconds < end:
                        frame = self.render_subtitle_pill(frame, sentence, 1.0, 1.0, center_x=center_x)
                        break
                path = os.path.join(out_dir, f"{scene_id}_{int(round(fraction * 100)):03d}.png")
                frame.save(path)
                written.append(path)
        return written

    def build(self, allow_placeholders=False, allow_low_quality=False):
        print(f"🚀 开始编译工程: {self.project_dir}")
        print(f"🎬 视频标题: {self.title}")

        errors, warnings = self.validate_storyboard(allow_placeholders=allow_placeholders)
        for warning in warnings:
            print(f"⚠️ 预检提示：{warning}")
        if errors:
            raise ValueError("剧本预检未通过，未开始渲染：\n- " + "\n- ".join(errors))

        from engine.quality_gate import format_report
        report = self.quality_report()
        print("🔬 剧本质量评估:")
        for line in format_report(report):
            print(line)
        if report["enforced"] and not report["passed"] and not allow_low_quality:
            raise ValueError(
                f"剧本质量分 {report['score']} 未达到门槛 {report['threshold']}，已阻止渲染；"
                "修复后重试，或使用 --allow-low-quality 仅做内部预览。"
            )
        if report["enforced"] and not report["passed"]:
            print("⚠️ 已用 --allow-low-quality 放行，仅可用于内部预览，不建议发布。")

        scene_timelines, global_subtitles, total_frames, total_duration, master_voice_wav = self.prepare_audio_and_timings()
        self.prepare_visual_assets()

        final_mp4 = os.path.join(self.dist_dir, "final.mp4")
        bgm_path = self.resolver.resolve_audio(self.bgm_conf.get("file", "bgm.mp3"))

        cmd = [
            "ffmpeg", "-y",
            "-f", "rawvideo",
            "-pix_fmt", "rgb24",
            "-s", f"{self.width}x{self.height}",
            "-r", str(self.fps),
            "-i", "-",
            "-i", master_voice_wav
        ]
        
        if bgm_path and os.path.exists(bgm_path):
            vol = self.bgm_conf.get("volume", 0.10)
            cmd.extend([
                "-i", bgm_path,
                "-filter_complex",
                f"[1:a]volume=1.0[voice];[2:a]volume={vol},afade=t=in:ss=0:d=1.5,afade=t=out:st={max(1.0, total_duration - 2.0)}:d=2.0[bgm];[voice][bgm]amix=inputs=2:duration=first[aout]",
                "-map", "0:v",
                "-map", "[aout]"
            ])
        else:
            cmd.extend(["-map", "0:v", "-map", "1:a"])

        cmd.extend([
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            "-preset", "fast",
            "-crf", "20",
            "-c:a", "aac",
            "-b:a", "192k",
            "-shortest",
            final_mp4
        ])

        print(f"⚡ 启动多图层视听渲染进程 (总帧数: {total_frames}, 时长: {total_duration:.2f}s)...")
        pipe = subprocess.Popen(cmd, stdin=subprocess.PIPE)

        for f in range(total_frames):
            active_scene = None
            is_transition = False
            prev_scene = None
            next_scene = None
            trans_prog = 0.0

            for idx, item in enumerate(scene_timelines):
                sf = item["start_frame"]
                ef = item["end_frame"]
                tf = item.get("transition_frames", 12)
                
                if sf <= f < ef:
                    active_scene = item["scene"]
                    local_f = f - sf
                    frame = self.render_scene_frame(active_scene, local_f, f, total_scene_frames=item["duration_frames"])
                    break
                elif tf > 0 and ef <= f < ef + tf and idx < len(scene_timelines) - 1:
                    is_transition = True
                    prev_scene = item["scene"]
                    next_scene = scene_timelines[idx + 1]["scene"]
                    trans_prog = ease_in_out_quad((f - ef) / float(tf))
                    
                    f1 = self.render_scene_frame(prev_scene, item["duration_frames"] - 1, f, total_scene_frames=item["duration_frames"])
                    f2 = self.render_scene_frame(next_scene, 0, f, total_scene_frames=scene_timelines[idx + 1]["duration_frames"])
                    
                    offset_x = int(trans_prog * self.width)
                    frame = Image.new("RGB", (self.width, self.height))
                    frame.paste(f1, (-offset_x, 0))
                    frame.paste(f2, (self.width - offset_x, 0))
                    break

            if active_scene is None and not is_transition:
                last_item = scene_timelines[-1]
                frame = self.render_scene_frame(last_item["scene"], last_item["duration_frames"] - 1, f, total_scene_frames=last_item["duration_frames"])

            # 字幕匹配
            sub_text, sub_alpha, pop_p = None, 0.0, 1.0
            for start, end, stext in global_subtitles:
                if start <= f < end:
                    sub_text = stext
                    dist_start = f - start
                    dist_end = end - f
                    sub_alpha = min(1.0, dist_start / 5.0, dist_end / 5.0)
                    pop_p = ease_out_back(min(1.0, dist_start / 8.0))
                    break

            if sub_text:
                v_type = active_scene.get("layout") or active_scene.get("visual", {}).get("type") if active_scene else None
                cx = 640 if v_type == "title_card" else None
                frame = self.render_subtitle_pill(frame, sub_text, sub_alpha, pop_p, center_x=cx)

            # 关键词高能冲击大字报 (Kinetic Typography / Keyword Punch)
            for item in scene_timelines:
                for cue in item.get("punch_cues", []):
                    cs = cue["start_frame"]
                    ce = cs + cue["duration_frames"]
                    if cs <= f < ce:
                        frame = self._render_kinetic_punch(
                            frame, cue["text"], f, cs, length=cue["duration_frames"], style=cue.get("style", "emerald")
                        )
                        break

            if f == 85:
                cover_path = os.path.join(self.dist_dir, "cover.png")
                frame.save(cover_path)

            pipe.stdin.write(frame.tobytes())

            if f % 90 == 0 or f == total_frames - 1:
                print(f"  Rendering [{f}/{total_frames}] {round(f / total_frames * 100)}% ...")

        pipe.stdin.close()
        pipe.wait()

        print("==================================================")
        print(f"🎉 编译成功！最终成果已生成至工程交付目录:")
        print(f"  🎬 视频成片: {final_mp4}")
        print(f"  🖼️ 高清封面: {os.path.join(self.dist_dir, 'cover.png')}")
        print(f"  📝 SRT字幕: {os.path.join(self.dist_dir, 'subtitles.srt')}")
        print("==================================================")
        return final_mp4

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python engine/compositor.py <project_dir>")
        sys.exit(1)
    comp = VideoCompositor(sys.argv[1])
    comp.build()
