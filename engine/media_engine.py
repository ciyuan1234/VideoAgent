#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VideoAgent Core Engine - Media Fetch Module
外部媒体、推特、YouTube、B站素材精准切片下载器。
"""

import os
import sys
import argparse
import subprocess

def download_media_clip(url, output_path, start_time=None, end_time=None, audio_only=False):
    """
    精准切片下载外部视频或音频素材
    """
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    cmd = ["yt-dlp"]

    if audio_only:
        cmd.extend(["-x", "--audio-format", "wav"])
    else:
        cmd.extend(["-f", "mp4/bestvideo+bestaudio/best"])

    if start_time and end_time:
        cmd.extend(["--download-sections", f"*{start_time}-{end_time}"])

    cmd.extend(["-o", output_path, url])
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        raise RuntimeError(f"素材下载失败: {res.stderr}")
    return os.path.abspath(output_path)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="VideoAgent Media Fetch CLI")
    parser.add_argument("url", help="视频/音频链接")
    parser.add_argument("--output", "-o", required=True, help="保存路径")
    parser.add_argument("--start", "-s", help="起始时间 (如 00:00:10)")
    parser.add_argument("--end", "-e", help="结束时间 (如 00:00:25)")
    parser.add_argument("--audio", action="store_true", help="仅提取音频")
    args = parser.parse_args()

    out = download_media_clip(args.url, args.output, args.start, args.end, args.audio)
    print(f"✅ 素材下载成功: {out}")
