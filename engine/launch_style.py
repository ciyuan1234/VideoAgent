#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VideoAgent Launch Style
面向手机竖屏（9:16）发布会预告片的原生渲染层，与经典开发者卡片风格完全独立。

设计语言差异：
- 画布 1080x1920 竖屏，而非 1920x1080 横屏
- 深空渐变 + 中心辉光，而非白底网格
- 巨型居中排版与细结构线，而非卡片、徽标、项目符号
- 无主讲人立绘、无卡片边框、无图标列
"""

import math
from typing import Any, Dict, Tuple

from PIL import Image, ImageChops, ImageDraw, ImageFont

from engine.fonts import FONT_HEITI, FONT_LIGHT
from engine.text_metrics import estimate_text_width, fit_text_to_width

STYLE_NAME = "launch_teaser"

LAUNCH_VISUALS = {"hero", "statement", "feature_stack", "closing"}

ACCENTS = {
    "indigo": (129, 140, 248),
    "violet": (167, 139, 250),
    "cyan": (34, 211, 238),
    "amber": (251, 191, 36),
}
DEFAULT_ACCENT = "indigo"

_BACKGROUND_CACHE: Dict[Tuple[int, int, str], Image.Image] = {}


def ease_out(t: float) -> float:
    return 1.0 - (1.0 - min(1.0, max(0.0, t))) ** 3


def _background(width: int, height: int, accent_name: str) -> Image.Image:
    """深空渐变 + 中心辉光 + 暗角，整片只生成一次并缓存。"""
    key = (width, height, accent_name)
    if key in _BACKGROUND_CACHE:
        return _BACKGROUND_CACHE[key]

    accent = ACCENTS.get(accent_name, ACCENTS[DEFAULT_ACCENT])
    top, bottom = (4, 6, 12), (11, 14, 34)
    base = Image.new("RGB", (width, height))
    draw = ImageDraw.Draw(base)
    for y in range(height):
        t = y / max(1, height - 1)
        draw.line(
            [(0, y), (width, y)],
            fill=tuple(int(top[i] + (bottom[i] - top[i]) * t) for i in range(3)),
        )

    glow = Image.new("RGB", (width, height), (0, 0, 0))
    glow_draw = ImageDraw.Draw(glow)
    cx, cy, radius = width * 0.5, height * 0.34, width * 0.95
    steps = 48
    for step in range(steps, 0, -1):
        progress = step / steps
        falloff = (1.0 - progress) ** 1.8
        rr = radius * progress
        glow_draw.ellipse(
            [cx - rr, cy - rr, cx + rr, cy + rr],
            fill=tuple(int(channel * falloff * 0.30) for channel in accent),
        )
    base = ImageChops.add(base, glow)

    # 暗角：四角压暗，把视线收束到画面中心。
    vignette = Image.new("L", (width, height), 0)
    vig_draw = ImageDraw.Draw(vignette)
    vig_draw.ellipse(
        [-width * 0.35, -height * 0.15, width * 1.35, height * 1.15], fill=255
    )
    vignette = vignette.filter(ImageFilterGaussian(radius=width * 0.08))
    dark = Image.new("RGB", (width, height), (0, 0, 0))
    base = Image.composite(base, dark, vignette)

    _BACKGROUND_CACHE[key] = base
    return base


def ImageFilterGaussian(radius):
    """延迟导入 GaussianBlur，避免模块级依赖过重。"""
    from PIL import ImageFilter

    return ImageFilter.GaussianBlur(radius=radius)


def _centered(draw, text, font, y, fill, width):
    bbox = draw.textbbox((0, 0), text, font=font)
    draw.text(((width - (bbox[2] - bbox[0])) // 2, y), text, font=font, fill=fill)


def _accent_rule(frame, width, y, progress, accent, thickness=6, span=260):
    """随讲解生长的高亮横线。"""
    if progress <= 0:
        return
    draw = ImageDraw.Draw(frame)
    half = int(span * progress) // 2
    cx = width // 2
    draw.rounded_rectangle(
        [cx - half, y, cx + half, y + thickness], radius=thickness // 2, fill=accent
    )


def render_hero(scene, local_f, total_frames, width, height, accent):
    v_conf = scene.get("visual", {})
    accent_rgb = ACCENTS.get(v_conf.get("accent", DEFAULT_ACCENT), accent)
    frame = _background(width, height, v_conf.get("accent", DEFAULT_ACCENT)).copy()
    draw = ImageDraw.Draw(frame)

    kicker = str(v_conf.get("kicker") or "")
    title = str(v_conf.get("title") or "")
    subtitle = str(v_conf.get("subtitle") or "")

    enter = ease_out(local_f / 18.0)
    rise = int((1.0 - enter) * 40)

    # 内容落在光学中心偏上，底部留给字幕带，避免中段出现大面积空白。
    block_top = int(height * 0.34)

    if kicker:
        font_kicker = ImageFont.truetype(FONT_HEITI, 28)
        spaced = "  ".join(kicker)
        _centered(draw, spaced, font_kicker, block_top + rise, accent_rgb, width)

    font_title = ImageFont.truetype(FONT_HEITI, 132)
    title = fit_text_to_width(title, width - 120, 132)
    _centered(draw, title, font_title, block_top + 84 + rise, (245, 247, 255), width)

    _accent_rule(frame, width, block_top + 268 + rise, ease_out(local_f / 26.0), accent_rgb)

    if subtitle:
        font_sub = ImageFont.truetype(FONT_LIGHT, 40)
        subtitle = fit_text_to_width(subtitle, width - 160, 40)
        _centered(draw, subtitle, font_sub, block_top + 320 + rise, (168, 178, 205), width)

    return frame


def render_statement(scene, local_f, total_frames, width, height, accent):
    v_conf = scene.get("visual", {})
    accent_rgb = ACCENTS.get(v_conf.get("accent", DEFAULT_ACCENT), accent)
    frame = _background(width, height, v_conf.get("accent", DEFAULT_ACCENT)).copy()
    draw = ImageDraw.Draw(frame)

    lines = [str(line) for line in (v_conf.get("lines") or []) if str(line).strip()]
    if not lines:
        lines = [str(v_conf.get("text") or "")]

    font = ImageFont.truetype(FONT_HEITI, 76)
    line_height = 118
    block_height = line_height * len(lines)
    start_y = (height // 2) - (block_height // 2) - 40

    for index, line in enumerate(lines):
        appear = ease_out((local_f - index * 7) / 16.0)
        if appear <= 0:
            continue
        offset = int((1.0 - appear) * 34)
        fitted = fit_text_to_width(line, width - 140, 76)
        _centered(draw, fitted, font, start_y + index * line_height + offset, (243, 245, 252), width)

    highlight = v_conf.get("highlight")
    if highlight is not None and 0 <= int(highlight) < len(lines):
        rule_y = start_y + int(highlight) * line_height + line_height - 14
        _accent_rule(frame, width, rule_y, ease_out((local_f - 18) / 22.0), accent_rgb, span=420)

    return frame


def render_feature_stack(scene, local_f, total_frames, width, height, accent):
    v_conf = scene.get("visual", {})
    accent_rgb = ACCENTS.get(v_conf.get("accent", DEFAULT_ACCENT), accent)
    frame = _background(width, height, v_conf.get("accent", DEFAULT_ACCENT)).copy()
    draw = ImageDraw.Draw(frame)

    header = str(v_conf.get("header") or "")
    items = [item for item in (v_conf.get("items") or []) if isinstance(item, dict)][:3]

    top = int(height * 0.27)
    if header:
        font_header = ImageFont.truetype(FONT_HEITI, 40)
        _centered(draw, header, font_header, top, accent_rgb, width)
        top += 118

    row_gap = 232
    card_left, card_right = 96, width - 96
    font_title = ImageFont.truetype(FONT_HEITI, 56)
    font_sub = ImageFont.truetype(FONT_LIGHT, 30)

    for index, item in enumerate(items):
        appear = ease_out((local_f - index * 9) / 18.0)
        if appear <= 0:
            continue
        y = top + index * row_gap + int((1.0 - appear) * 44)

        # 左侧编号竖条，替代经典风格的节点圆角卡
        bar_h = 128
        draw.rounded_rectangle(
            [card_left, y, card_left + 8, y + bar_h], radius=4,
            fill=tuple(int(channel * appear) for channel in accent_rgb),
        )
        num_font = ImageFont.truetype(FONT_HEITI, 30)
        draw.text((card_left + 34, y + 6), f"{index + 1:02d}", font=num_font,
                  fill=tuple(int(channel * appear) for channel in accent_rgb))

        title = fit_text_to_width(str(item.get("title") or ""), card_right - card_left - 150, 56)
        sub = fit_text_to_width(str(item.get("sub") or ""), card_right - card_left - 150, 30)
        draw.text((card_left + 118, y + 10), title, font=font_title,
                  fill=(242, 244, 252))
        draw.text((card_left + 118, y + 84), sub, font=font_sub, fill=(150, 160, 188))

    return frame


def render_closing(scene, local_f, total_frames, width, height, accent):
    v_conf = scene.get("visual", {})
    accent_rgb = ACCENTS.get(v_conf.get("accent", DEFAULT_ACCENT), accent)
    frame = _background(width, height, v_conf.get("accent", DEFAULT_ACCENT)).copy()
    draw = ImageDraw.Draw(frame)

    enter = ease_out(local_f / 22.0)
    center_y = height // 2 - 60

    dot_r = 16
    draw.ellipse(
        [width // 2 - dot_r, center_y - dot_r * 4, width // 2 + dot_r, center_y - dot_r * 2],
        fill=tuple(int(channel * enter) for channel in accent_rgb),
    )

    font_title = ImageFont.truetype(FONT_HEITI, 92)
    title = fit_text_to_width(str(v_conf.get("title") or ""), width - 140, 92)
    _centered(draw, title, font_title, center_y, (245, 247, 255), width)

    _accent_rule(frame, width, center_y + 136, ease_out((local_f - 12) / 22.0), accent_rgb)

    footer = str(v_conf.get("footer") or "")
    if footer:
        font_footer = ImageFont.truetype(FONT_LIGHT, 34)
        footer = fit_text_to_width(footer, width - 160, 34)
        _centered(draw, footer, font_footer, center_y + 190, (166, 176, 204), width)

    return frame


RENDERERS = {
    "hero": render_hero,
    "statement": render_statement,
    "feature_stack": render_feature_stack,
    "closing": render_closing,
}


def render(scene, local_f, total_frames, width, height, accent=None):
    """按 visual.type 渲染一帧竖屏发布会画面。"""
    v_type = scene.get("layout") or (scene.get("visual") or {}).get("type")
    renderer = RENDERERS.get(v_type)
    if renderer is None:
        raise ValueError(f"launch_teaser 风格不支持的 visual.type: {v_type}（可选 {sorted(RENDERERS)}）")
    accent_rgb = ACCENTS.get(accent or DEFAULT_ACCENT, ACCENTS[DEFAULT_ACCENT])
    return renderer(scene, local_f, total_frames, width, height, accent_rgb)


def render_subtitle(frame, text, alpha, width, height):
    """发布会风格字幕：细体居中 + 柔和投影，不使用深色胶囊。"""
    if not text or alpha <= 0:
        return frame
    from engine.tts_engine import split_sentences  # noqa: F401  (保持断句约定一致)

    overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    font = ImageFont.truetype(FONT_HEITI, 44)

    max_chars = 16
    if len(text) > max_chars:
        mid = len(text) // 2
        split = mid
        for index in range(max(0, mid - 5), min(len(text), mid + 5)):
            if text[index] in "，、；： ":
                split = index + 1
                break
        lines = [text[:split].strip(), text[split:].strip()]
    else:
        lines = [text]

    line_height = 62
    base_y = height - 250 - (len(lines) - 1) * line_height
    for index, line in enumerate(lines):
        bbox = draw.textbbox((0, 0), line, font=font)
        x = (width - (bbox[2] - bbox[0])) // 2
        y = base_y + index * line_height
        for dx, dy in ((2, 3), (-2, 3), (2, -2)):
            draw.text((x + dx, y + dy), line, font=font, fill=(0, 0, 0, int(150 * alpha)))
        draw.text((x, y), line, font=font, fill=(238, 241, 250, int(255 * alpha)))

    return Image.alpha_composite(frame.convert("RGBA"), overlay).convert("RGB")
