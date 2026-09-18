#!/Users/a1-6/GPT-SoVITS/venv/bin/python
# -*- coding: utf-8 -*-
"""
VideoAgent Core Engine - TTS Module
GPT-SoVITS 语音合成封装，支持自动断句、呼吸停顿、中间分段缓存以及时间戳对齐元数据输出。
"""

import os
import sys
import io
import re
import wave
import json
import time
import hashlib
import argparse
import requests
import subprocess
import numpy as np

API_URL = "http://127.0.0.1:9880/tts"
DEFAULT_REF_TEXT = "原来外面的世界是这样子的，喜欢这样的世界。"

def find_default_ref_audio():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    candidates = [
        os.path.join(base_dir, "assets", "character", "erii", "ref_audio.wav"),
        os.path.join(base_dir, "assets", "ref_audio.wav"),
    ]
    for c in candidates:
        if os.path.exists(c):
            return c
    return candidates[1]

def is_server_running(host="127.0.0.1", port=9880):
    try:
        r = requests.get(f"http://{host}:{port}/control", timeout=1)
        return True
    except Exception:
        return False

def ensure_server():
    if is_server_running():
        return True
    print("⚡ 本地 GPT-SoVITS 服务未运行，正在自动唤起后台推理引擎...")
    gpt_dir = os.path.expanduser("~/GPT-SoVITS")
    python_bin = os.path.join(gpt_dir, "venv", "bin", "python")
    config_path = os.path.join(gpt_dir, "GPT_SoVITS", "configs", "tts_infer_mac.yaml")
    
    if not os.path.exists(python_bin):
        print(f"❌ 未找到 GPT-SoVITS Python 解释器: {python_bin}")
        return False
        
    cmd = [python_bin, "api_v2.py", "-a", "127.0.0.1", "-p", "9880", "-c", config_path]
    subprocess.Popen(cmd, cwd=gpt_dir, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    for _ in range(30):
        time.sleep(1)
        if is_server_running():
            print("✅ 后台 TTS 引擎启动成功！")
            return True
    print("❌ 启动超时，请在终端手动启动 GPT-SoVITS。")
    return False

def synth_single_sentence(text, speed=1.00, ref_audio_path=None, prompt_text=None, emotion="normal"):
    if not ref_audio_path:
        ref_audio_path = find_default_ref_audio()
    if not prompt_text:
        prompt_text = DEFAULT_REF_TEXT
        
    # 教学解说声线：温和、稳定、吐字清晰、杜绝突兀起伏与电竞解说腔
    temp = 0.58
    frag_int = 0.15
    if emotion in ["excited", "hype"]:
        speed = max(speed, 1.04)
        temp = 0.62
    elif emotion in ["calm", "doubt", "curious"]:
        speed = min(speed, 0.98)
        temp = 0.55
    else:
        temp = 0.58
        speed = 1.00

    # 关键修复：绝不使用 cut5（cut5 在逗号处强制切碎导致频繁换气和大喘气）
    # 短于 45 字直接 cut0 完整呼吸，长句使用 cut2
    split_method = "cut2" if len(text) > 45 else "cut0"

    payload = {
        "text": text,
        "text_lang": "zh",
        "ref_audio_path": ref_audio_path,
        "prompt_text": prompt_text,
        "prompt_lang": "zh",
        "speed_factor": speed,
        "temperature": temp,
        "top_k": 12,
        "text_split_method": split_method,
        "fragment_interval": frag_int
    }
    res = requests.post(API_URL, json=payload, timeout=60)
    if res.status_code != 200:
        raise RuntimeError(f"TTS 接口报错 ({res.status_code}): {res.text}")
        
    with wave.open(io.BytesIO(res.content), "rb") as wf:
        n_channels = wf.getnchannels()
        sampwidth = wf.getsampwidth()
        framerate = wf.getframerate()
        frames = wf.readframes(wf.getnframes())
        data = np.frombuffer(frames, dtype=np.int16)
    return data, framerate, n_channels, sampwidth

def split_sentences(text):
    """根据中文句号/问号/感叹号/分号自然断句，保留完整语调与连贯语流，避免逗号处机械切碎造成大喘气"""
    raw_s = re.split(r"([。！？；\n]+)", text)
    initial_sentences = []
    for i in range(0, len(raw_s) - 1, 2):
        s = raw_s[i].strip() + raw_s[i+1].strip()
        if s:
            initial_sentences.append(s)
    if len(raw_s) % 2 == 1 and raw_s[-1].strip():
        initial_sentences.append(raw_s[-1].strip())

    refined = []
    for s in initial_sentences:
        # 仅当单句极端超长（> 42 字）且内部有明确逗号时才适度分段
        if len(s) > 42:
            parts = s.split("，")
            buf = ""
            for idx, p in enumerate(parts):
                clause = p + ("，" if idx < len(parts) - 1 else "")
                if len(buf) + len(clause) <= 36:
                    buf += clause
                else:
                    if buf:
                        refined.append(buf.strip())
                    buf = clause
            if buf:
                refined.append(buf.strip())
        else:
            refined.append(s)

    return refined if refined else [text]

def synthesize_speech(text, output_file, speed=1.00, pause_sec=0.22, ref_audio_path=None, prompt_text=None, cache_dir=None, emotion="normal"):
    """
    合成完整多句语音，句间插入自然停顿，支持段落缓存加速。
    返回音频时长与每句精准时间戳元数据。
    """
    if not ensure_server():
        raise RuntimeError("无法启动或连接到 GPT-SoVITS 推理服务")

    if not ref_audio_path:
        ref_audio_path = find_default_ref_audio()

    sentences = split_sentences(text)
    audio_chunks = []
    framerate = 32000
    n_channels = 1
    sampwidth = 2
    
    sentence_timings = []
    current_time = 0.0

    if cache_dir:
        os.makedirs(cache_dir, exist_ok=True)

    for idx, s in enumerate(sentences):
        chunk_data = None
        # 尝试缓存命中
        if cache_dir:
            hash_key = hashlib.md5(f"{s}_{speed}_{ref_audio_path}_{emotion}".encode("utf-8")).hexdigest()
            cache_file = os.path.join(cache_dir, f"tts_{hash_key}.npy")
            if os.path.exists(cache_file):
                try:
                    cached = np.load(cache_file, allow_pickle=True).item()
                    chunk_data = cached["data"]
                    framerate = cached["framerate"]
                    n_channels = cached["n_channels"]
                    sampwidth = cached["sampwidth"]
                except Exception:
                    chunk_data = None

        if chunk_data is None:
            chunk_data, framerate, n_channels, sampwidth = synth_single_sentence(
                s, speed=speed, ref_audio_path=ref_audio_path, prompt_text=prompt_text, emotion=emotion
            )
            if cache_dir:
                try:
                    np.save(cache_file, {
                        "data": chunk_data,
                        "framerate": framerate,
                        "n_channels": n_channels,
                        "sampwidth": sampwidth
                    })
                except Exception:
                    pass

        dur = len(chunk_data) / (framerate * n_channels)
        start_time = current_time
        end_time = current_time + dur
        
        sentence_timings.append({
            "index": idx,
            "text": s,
            "start_time": round(start_time, 3),
            "end_time": round(end_time, 3),
            "duration": round(dur, 3)
        })
        
        audio_chunks.append(chunk_data)
        current_time = end_time

        # 句间气口停顿
        if idx < len(sentences) - 1 and pause_sec > 0:
            silence_samples = int(framerate * pause_sec)
            silence = np.zeros(silence_samples, dtype=np.int16)
            audio_chunks.append(silence)
            current_time += pause_sec

    full_audio = np.concatenate(audio_chunks)
    total_dur = len(full_audio) / (framerate * n_channels)
    
    os.makedirs(os.path.dirname(os.path.abspath(output_file)), exist_ok=True)
    with wave.open(output_file, "wb") as wf:
        wf.setnchannels(n_channels)
        wf.setsampwidth(sampwidth)
        wf.setframerate(framerate)
        wf.writeframes(full_audio.tobytes())

    metadata = {
        "output_file": os.path.abspath(output_file),
        "total_duration": round(total_dur, 3),
        "framerate": framerate,
        "channels": n_channels,
        "sentences": sentence_timings
    }
    
    # 写入配套元数据 JSON 便于外部调用
    meta_path = os.path.splitext(output_file)[0] + ".json"
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)

    return metadata

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="VideoAgent TTS Engine CLI")
    parser.add_argument("text", help="待合成文本")
    parser.add_argument("--output", "-o", required=True, help="输出 WAV 音频路径")
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
    print(f"✅ 语音合成完成: {meta['output_file']} (时长: {meta['total_duration']}s, 共 {len(meta['sentences'])} 句)")
