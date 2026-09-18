#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VideoAgent Core Engine - Diagram Module
基于 Mermaid CLI (mmdc) 的技术架构图与时序图渲染工具。
"""

import os
import sys
import argparse
import subprocess
import tempfile

def render_diagram(mermaid_code_or_file, output_path, bg="transparent", scale=2):
    """
    渲染 Mermaid 架构/时序流程图为高清图片
    :param mermaid_code_or_file: Mermaid 源码字符串或 .mmd 脚本路径
    :param output_path: 输出图片路径
    :param bg: 背景色 (transparent, white, #f8fafc)
    :param scale: 缩放倍率 (默认 2，清晰度翻倍)
    """
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

    cleanup = False
    if os.path.isfile(mermaid_code_or_file):
        input_file = mermaid_code_or_file
    else:
        tmp = tempfile.NamedTemporaryFile(suffix=".mmd", delete=False, mode="w", encoding="utf-8")
        tmp.write(mermaid_code_or_file)
        tmp.close()
        input_file = tmp.name
        cleanup = True

    try:
        cmd = ["mmdc", "-i", input_file, "-o", output_path, "-b", bg, "-s", str(scale)]
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode != 0:
            raise RuntimeError(f"Mermaid 渲染失败: {res.stderr}")
        return os.path.abspath(output_path)
    finally:
        if cleanup and os.path.exists(input_file):
            os.remove(input_file)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="VideoAgent Diagram Engine CLI")
    parser.add_argument("code", help="Mermaid 文本或 .mmd 文件路径")
    parser.add_argument("--output", "-o", required=True, help="输出图片路径")
    parser.add_argument("--bg", "-b", default="transparent", help="背景颜色")
    parser.add_argument("--scale", "-s", type=int, default=2, help="清晰度倍率")
    args = parser.parse_args()

    out = render_diagram(args.code, args.output, bg=args.bg, scale=args.scale)
    print(f"✅ 架构图渲染成功: {out}")
