#!/Users/a1-6/GPT-SoVITS/venv/bin/python
# -*- coding: utf-8 -*-
"""
Backward-compatible wrapper for engine.tts_engine
"""
import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from engine.tts_engine import *

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="绘梨衣专属语音合成 (兼容接口)")
    parser.add_argument("text", help="待合成文本")
    parser.add_argument("--output", "-o", default=os.path.join(BASE_DIR, "output", "speech.wav"), help="输出 WAV 音频路径")
    parser.add_argument("--speed", "-s", type=float, default=1.05, help="语速 (默认 1.05)")
    parser.add_argument("--pause", "-p", type=float, default=0.45, help="句间停顿秒数 (默认 0.45)")
    parser.add_argument("--ref", "-r", default=None, help="参考音频路径")
    parser.add_argument("--cache", "-c", default=None, help="缓存目录")
    args = parser.parse_args()

    meta = synthesize_speech(
        args.text,
        output_file=args.output,
        speed=args.speed,
        pause_sec=args.pause,
        ref_audio_path=args.ref,
        cache_dir=args.cache
    )
    print(f"✅ 语音合成完成: {meta['output_file']} (时长: {meta['total_duration']}s)")
