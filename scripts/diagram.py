#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Backward-compatible wrapper for engine.diagram_engine
"""
import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from engine.diagram_engine import render_diagram

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Mermaid 架构/时序图渲染工具 (兼容接口)")
    parser.add_argument("code", help="Mermaid 文本或 .mmd 文件路径")
    parser.add_argument("--output", "-o", default=os.path.join(BASE_DIR, "output", "diagram.png"), help="输出图片路径")
    parser.add_argument("--bg", "-b", default="transparent", help="背景颜色")
    parser.add_argument("--scale", "-s", type=int, default=2, help="清晰度倍率")
    args = parser.parse_args()

    out = render_diagram(args.code, args.output, bg=args.bg, scale=args.scale)
    print(f"✅ 架构图已生成: {out}")
