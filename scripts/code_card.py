#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Backward-compatible wrapper for engine.code_card_engine
"""
import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from engine.code_card_engine import render_code_card

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="高颜值代码卡片生成工具 (兼容接口)")
    parser.add_argument("code", help="代码文本或代码文件路径")
    parser.add_argument("--output", "-o", default=os.path.join(BASE_DIR, "output", "code_card.png"), help="输出图片路径")
    parser.add_argument("--lang", "-l", default="python", help="语言类型")
    parser.add_argument("--theme", "-t", default="OneHalfLight", help="主题名称")
    parser.add_argument("--highlight", help="高亮行号")
    args = parser.parse_args()

    out = render_code_card(args.code, args.output, lang=args.lang, theme=args.theme, highlight_lines=args.highlight)
    print(f"✅ 代码卡片已生成: {out}")
