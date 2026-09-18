#!/bin/bash
# 启动绘梨衣音色克隆后台服务
DIR="$(cd "$(dirname "$0")" && pwd)"
GPT_DIR="$HOME/GPT-SoVITS"

echo "🚀 正在启动本地 GPT-SoVITS 语音合成引擎..."
cd "$GPT_DIR" || exit 1
./venv/bin/python api_v2.py -a 127.0.0.1 -p 9880 -c GPT_SoVITS/configs/tts_infer_mac.yaml
