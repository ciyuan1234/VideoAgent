#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VideoAgent Fonts
CJK 字体的跨平台解析：macOS 优先，其次常见 Linux 发行版路径。
"""

import os

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
