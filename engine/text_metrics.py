#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VideoAgent Text Metrics
字体度量与宽度适配：供内容层（排版预算）与画面层（防溢出）共用，避免层级互相依赖。

估算规则：CJK 按整字号计宽，ASCII 按半字号，与渲染器使用的 CJK 字体行为近似。
"""


def estimate_text_width(text: str, font_size: int) -> float:
    """粗略估算渲染宽度：CJK 按整字号，ASCII 按半字号。"""
    return sum(font_size if ord(ch) > 127 else font_size * 0.5 for ch in str(text))


def fit_text_to_width(text: str, max_width: float, font_size: int, ellipsis: str = "…") -> str:
    """按估算宽度截断文本并追加省略号，保证不溢出容器。"""
    value = str(text or "")
    if estimate_text_width(value, font_size) <= max_width:
        return value
    for cut in range(len(value) - 1, 0, -1):
        candidate = value[:cut] + ellipsis
        if estimate_text_width(candidate, font_size) <= max_width:
            return candidate
    return ellipsis


def max_chars_for_width(max_width: float, font_size: int) -> int:
    """在给定像素预算下，最多可容纳多少个汉字。"""
    return max(1, int(max_width // font_size))
