#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VideoAgent Core Engine - Code Card Module
基于 Silicon 的高颜值代码卡片渲染工具，支持多种浅色/深色主题、行号高亮与 macOS 窗口样式。
"""

import os
import sys
import argparse
import subprocess

def render_code_card(
    code_or_file,
    output_path,
    lang="python",
    theme="OneHalfLight",
    pad_h=25,
    pad_v=25,
    shadow_blur=15,
    shadow_color="#00000033",
    highlight_lines=None
):
    """
    渲染语法高亮代码卡片图片
    :param code_or_file: 代码字符串或代码文件路径
    :param output_path: 输出图片路径
    :param lang: 语言
    :param theme: 主题 (OneHalfLight, Dracula, Nord, GitHub...)
    :param highlight_lines: 高亮行号，如 "3-5" 或 "10"
    """
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    
    cmd = [
        "silicon",
        "-l", lang,
        "--theme", theme,
        "--font", "Menlo; STHeiti",
        "--pad-horiz", str(pad_h),
        "--pad-vert", str(pad_v),
        "--shadow-blur-radius", str(shadow_blur),
        "--shadow-color", shadow_color,
        "-o", output_path
    ]

    if highlight_lines:
        cmd.extend(["--highlight-lines", str(highlight_lines)])

    if os.path.isfile(code_or_file):
        cmd.append(code_or_file)
        subprocess.run(cmd, check=True)
    else:
        p = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = p.communicate(input=code_or_file.encode("utf-8"))
        if p.returncode != 0:
            raise RuntimeError(f"Silicon 渲染失败: {stderr.decode('utf-8', errors='ignore')}")

    return os.path.abspath(output_path)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="VideoAgent Code Card Engine CLI")
    parser.add_argument("code", help="代码文本或代码文件路径")
    parser.add_argument("--output", "-o", required=True, help="输出图片路径")
    parser.add_argument("--lang", "-l", default="python", help="语言类型 (python, c, go, rust, js...)")
    parser.add_argument("--theme", "-t", default="OneHalfLight", help="主题名称 (OneHalfLight, Dracula, Nord...)")
    parser.add_argument("--highlight", help="高亮行号 (例如: 5 或 3-8)")
    args = parser.parse_args()

    out = render_code_card(args.code, args.output, lang=args.lang, theme=args.theme, highlight_lines=args.highlight)
    print(f"✅ 代码卡片渲染成功: {out}")
