#!/usr/bin/env python3
import os
import sys
import argparse
import subprocess

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def download_media(url, output_path, start_time=None, end_time=None, audio_only=False):
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

    cmd = ["yt-dlp"]

    if audio_only:
        cmd.extend(["-x", "--audio-format", "wav"])
    else:
        cmd.extend(["-f", "mp4/bestvideo+bestaudio/best"])

    if start_time and end_time:
        cmd.extend(["--download-sections", f"*{start_time}-{end_time}"])

    cmd.extend(["-o", output_path, url])

    print(f"📥 正在下载素材: {url} ...")
    try:
        subprocess.run(cmd, check=True)
        print(f"✅ 素材已就绪: {output_path}")
        return True
    except Exception as e:
        print(f"❌ 下载失败: {e}")
        return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="视频/音频素材精准切片下载器")
    parser.add_argument("url", help="视频链接 (B站/YouTube/推特等)")
    parser.add_argument("--output", "-o", default=os.path.join(BASE_DIR, "output", "clip.%(ext)s"), help="保存路径")
    parser.add_argument("--start", "-s", help="起始时间戳 (例如 00:01:10)")
    parser.add_argument("--end", "-e", help="结束时间戳 (例如 00:01:25)")
    parser.add_argument("--audio", action="store_true", help="仅提取音频")
    args = parser.parse_args()

    download_media(args.url, args.output, args.start, args.end, args.audio)
