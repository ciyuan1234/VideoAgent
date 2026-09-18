# 🎬 VideoAgent - 自动化科技视频创作工坊

本项目为面向 Apple Silicon 打造的计算机科技视频自动化生产管线。
采用**「引擎层 (Engine) + 全局资产中台 (Assets) + 独立工程空间 (Projects) + 声明式剧本 (storyboard.yaml)」**的四层解耦架构，彻底释放 Agent 上下文工程潜力。

---

## 📂 解耦架构与目录布局

```text
~/Desktop/VideoAgent/
├── video-cli                    # 🚀 全局脚手架入口 (init / build / clean / list / status)
│
├── engine/                      # ⚙️ 【核心工具引擎】(无状态纯函数，跨工程通用)
│   ├── tts_engine.py            # GPT-SoVITS 专属配音合成 (断句、停顿、时间戳、分段缓存)
│   ├── code_card_engine.py      # Silicon 高颜值代码卡片渲染
│   ├── diagram_engine.py        # Mermaid CLI 架构与时序流程图生成
│   ├── media_engine.py          # yt-dlp 外部视频素材切片下载
│   ├── compositor.py            # 剪映级声明式多图层动效渲染器
│   └── cli.py                   # 脚手架命令解析器
│
├── assets/                      # 🌸 【全局共享资产】(只读模板库，无业务状态污染)
│   ├── character/               # 绘梨衣主讲人立绘 (erii_presenter) 及 Q 版贴纸库
│   ├── sfx/                     # 打击感与节奏微音效 (pop.wav, whoosh.wav, chime.wav)
│   ├── ref_audio.wav            # 零底噪 32kHz 录音棚标准音色基准
│   └── bgm.mp3                  # 治愈轻快 Lo-Fi 背景音乐
│
├── projects/                    # 📦 【独立工程空间】(单集视频物理隔离)
│   └── epoll_deepdive/          # 示例工程: Linux epoll 机制精讲
│       ├── storyboard.yaml      # 🌟 声明式剧本配置 (Agent 唯一的关注点)
│       ├── extra_assets/        # 本工程私有特异素材
│       ├── .cache/              # 临时音频与渲染中间帧缓存 (.gitignore 自动排除)
│       └── dist/                # 🎯 最终交付成果物
│           ├── final.mp4        # 1080P 全动效成片
│           ├── cover.png        # 视频封面图
│           └── subtitles.srt    # 精准时间轴外挂字幕
│
├── scripts/                     # 🔄 向后兼容层 (兼容旧单脚本调用)
├── AGENTS.md                    # Agent 创作指引与 storyboard.yaml 规范
├── HANDOVER.md                  # 📖 维护交接与排障指南 (故障排查与二次扩展)
└── start_service.sh             # GPT-SoVITS 后台推理服务守护脚本
```

---

## 🚀 极速上手使用指南

### 1. 启动 TTS 推理引擎
```bash
./start_service.sh
```

### 🌟 2. 端到端“一键成片”导演模式 (Zero-Click Auto-Generate)
输入任意技术主题、本地 Markdown / 源码，或技术博文链接，全自动完成知识萃取、剧本编排与 1080P 高清成片：
```bash
# 方式 A: 直接给技术主题（全自动编排 6 幕原语并出片）
./video-cli auto-generate goroutine_gmp --topic "Go语言协程调度器与GMP模型深度剖析"

# 方式 B: 基于本地 Markdown 或源码一键成片
./video-cli auto-generate my_paper -f ~/Desktop/paper.md

# 方式 C: 抓取技术博文 Web URL 全自动成片
./video-cli auto-generate redis_guide -u "https://redis.io/docs/latest/operate/oss_and_stack/management/optimization/latency-monitor/"

# 方式 D: 仅自动生成剧本，供人工二次精修后再构建
./video-cli auto-generate my_topic --topic "Rust 所有权与借用" --no-build

# 方式 E: 指定叙事结构；默认 auto 会从材料中自动识别
./video-cli auto-generate my_topic -f source.py --story-profile code_walkthrough --no-build

# 方式 F: 固定同一材料的叙事重点；事实与结论保持不变
./video-cli auto-generate my_topic --topic "主题" --story-variant evidence_first --no-build
```

### 3. 手动初始化与自定义编排工程
```bash
./video-cli init my_topic --title "深入浅出 Redis 事件循环"
```
系统将自动在 `projects/my_topic/` 创建标准工程骨架与初始分镜剧本 `storyboard.yaml`。

### 3. 编辑分镜剧本 (`storyboard.yaml`)
只需声明台词、分镜类型与代码内容，无需编写任何复杂的渲染代码：
```yaml
meta:
  title: "深入浅出 Redis 事件循环"
  speaker: "erii"
  theme: "white_grid"

scenes:
  - id: "intro"
    character_sticker: "erii_presenter"
    audio:
      text: "Sakura，今天我们来深入剖析 Redis 单线程为什么这么快！"
      speed: 1.05
      pause: 0.45
    visual:
      type: "title_card"
      tag: "高性能架构深度剖析"
      title: "Redis 事件循环底层揭秘"
      subtitle: "aeEventLoop 是如何支撑十万 QPS 的？"
      bullets:
        - "单线程 Reactor 反应器模式精髓"
        - "文件事件与时间事件的协同调度"
```

### 4. 一键编译与成片交付
```bash
# 先检查素材、镜头节拍、制作期占位与质量评分；发布版必须通过
./video-cli validate my_topic

./video-cli build my_topic
```

`validate` 与 `build` 都会输出 0–100 的剧本质量评分（门槛 75），分项覆盖镜头多样性、节奏变化、证据完整性、叙事节拍覆盖与台词质量。低于门槛时会阻止发布渲染；仅做内部预览时可加 `--allow-low-quality`。
渲染完成后直接在 `projects/my_topic/dist/` 取走成果：
- `final.mp4`：1080P 剪映级运镜、气泡缓动、粒子流向、纯净绘梨衣呼吸微动效、白底网格成片。
- `cover.png`：高清视频封面。
- `subtitles.srt`：自动对齐呼吸停顿的逐句字幕。

### 5. 查看与清理工程缓存
```bash
# 查看所有视频项目状态
./video-cli list

# 查看指定工程详情
./video-cli status my_topic

# 清空中间临时构建缓存 (释放空间，无污染)
./video-cli clean my_topic
```

> 自动生成的素材优先剧本会把缺失的录屏/截图写入 `asset_requests`，并以 `asset_placeholder` 标出。补齐 `extra_assets/` 中的真实素材、替换占位场景后再 build；制作期预览可使用 `./video-cli validate my_topic --allow-placeholders`。

自动导演支持 `tutorial`、`concept`、`code_walkthrough`、`decision` 四种叙事结构。它先生成可审阅的内容节拍，再映射为镜头；结果写入 `meta.story_profile`、`meta.story_variant`、`meta.story_beats` 与 `meta.content_evidence`。`--story-variant evidence_first` 会将真实证据前置，`mechanism_first` 则先解释机制。

生成时还会把评分快照写入 `meta.quality_report` 便于追溯；历史工程不带该字段，质量评分只作参考、不阻断渲染。

### 6. 回归测试
```bash
# 25 个用例：四类叙事结构快照、证据纪律、素材匹配、发布门禁与历史工程兼容
PYTHONPYCACHEPREFIX=/tmp/videoagent-pycache python -m unittest discover -s tests -t .

# 有意调整生成结果后，重建快照基线
python -m tests.update_snapshots
```

---

## 🛠️ 底层独立工具调试 (CLI)

如需独立生成单张素材或测试音色：
```bash
# 1. 独立合成语音
python engine/tts_engine.py "你好，Sakura！" -o test.wav

# 2. 独立渲染高颜值代码卡片
python engine/code_card_engine.py "int a = 1;" --lang c --theme OneHalfLight -o test_code.png

# 3. 独立渲染 Mermaid 架构图
python engine/diagram_engine.py "graph LR; A-->B" -o test_diag.png
```
