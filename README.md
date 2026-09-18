<div align="center">

<img src="assets/character/erii_avatar.png" width="120" height="120" alt="VideoAgent Logo" style="border-radius: 50%; box-shadow: 0 4px 16px rgba(0,0,0,0.12);" />

# 🎬 VideoAgent

### 面向 Apple Silicon 与技术博主的开源自动化科技视频工坊
**AI-Driven Tech Video Production Pipeline for Developers & Creators**

<p align="center">
  <a href="https://github.com/ciyuan1234/VideoAgent"><img src="https://img.shields.io/github/stars/ciyuan1234/VideoAgent?style=flat-square&logo=github&color=FF6B6B" alt="GitHub Stars"></a>
  <a href="https://github.com/ciyuan1234/VideoAgent/network/members"><img src="https://img.shields.io/github/forks/ciyuan1234/VideoAgent?style=flat-square&logo=github&color=4ECDC4" alt="GitHub Forks"></a>
  <a href="https://github.com/ciyuan1234/VideoAgent/blob/main/LICENSE"><img src="https://img.shields.io/badge/License-MIT-blue?style=flat-square" alt="License"></a>
  <a href="https://www.python.org/downloads/"><img src="https://img.shields.io/badge/Python-3.10%2B-blue?style=flat-square&logo=python" alt="Python 3.10+"></a>
  <img src="https://img.shields.io/badge/Platform-macOS%20(Apple%20Silicon)%20%7C%20Linux-black?style=flat-square&logo=apple" alt="Platform">
  <a href="https://github.com/ciyuan1234/VideoAgent/pulls"><img src="https://img.shields.io/badge/PRs-Welcome-brightgreen?style=flat-square" alt="PRs Welcome"></a>
</p>

<p align="center">
  <b>只需输入任意技术主题、本地 Markdown、源码或博文链接，全自动萃取知识证据并交付 1080P 科技风成片！</b>
</p>

<p align="center">
  <a href="#-成片效果展示-showcase">成片效果</a> •
  <a href="#-为什么选择-videoagent">核心优势</a> •
  <a href="#-系统架构与解耦布局">四层架构</a> •
  <a href="#-极速上手指南">3分钟上手</a> •
  <a href="#-声明式分镜剧本-storyboardyaml">剧本规范</a> •
  <a href="#-质量评分门禁机制">质量门禁</a> •
  <a href="#-cli-命令全景速查">CLI速查</a> •
  <a href="README_EN.md">English</a>
</p>

</div>

---

## 📺 成片效果展示 (Showcase)

VideoAgent 专为**计算机底层、系统架构、云原生、编程语言**等硬核技术选题打造，拥有工业级的高清渲染水准：

### 🎨 双风格视觉实况 (Horizontal & Vertical Showcases)

#### 1. 🖥️ 16:9 极简白底网格科技风 (适合 B站 / YouTube 技术深度长视频)

<p align="center">
  <img src="projects/codex_tutorial/dist/cover.png" width="48%" alt="Codex Tutorial Cover" />
  <img src="projects/showdown_epoll/dist/cover.png" width="48%" alt="Epoll Showdown Cover" />
</p>
<p align="center">
  <img src="projects/goroutine_gmp/dist/cover.png" width="48%" alt="Go GMP Model Cover" />
  <img src="projects/redis_reactor/dist/cover.png" width="48%" alt="Redis Reactor Cover" />
</p>

<p align="center">
  <img src="projects/codex_tutorial/dist/inspect/cinematic_1.png" width="32%" alt="Cinematic Scene 1" />
  <img src="projects/codex_tutorial/dist/inspect/cinematic_2.png" width="32%" alt="Cinematic Scene 2" />
  <img src="projects/codex_tutorial/dist/inspect/cinematic_3.png" width="32%" alt="Cinematic Scene 3" />
</p>

> **✨ 横屏视觉特性**：极简科技白底网格 • 动态高光语法高亮代码卡片 • 交互式 Mermaid 架构/时序图 • 绘梨衣看板娘呼吸微动效 • 像素级逐字对齐字幕 • 打击感微音效 (SFX) 与治愈 Lo-Fi BGM 智能混音。

#### 2. 📱 9:16 电影感暗色发布会风格 `launch_teaser` (适合 抖音 / 小红书 / TikTok / Shorts)

<p align="center">
  <img src="projects/gemini_launch/dist/inspect/hero.png" width="23%" alt="Launch Hero" />
  <img src="projects/gemini_launch/dist/inspect/statement.png" width="23%" alt="Launch Statement" />
  <img src="projects/gemini_launch/dist/inspect/feature_stack.png" width="23%" alt="Launch Feature Stack" />
  <img src="projects/gemini_launch/dist/inspect/closing.png" width="23%" alt="Launch Closing" />
</p>

> **✨ 竖屏视觉特性**：1080×1920 深空渐变 • 居中放射光晕 • 巨幅观点句 (statement) 动态高亮 • 细线条编号清单 (feature_stack) • 电影级 15 帧淡入溶解 (fade)。

---

## 💡 竞品对比与生态定位 (Ecosystem Comparison)

为什么已有 MoneyPrinterTurbo、VideoLingo 和 Manim，技术界依然渴望 **VideoAgent**？

| 对比维度 | 🎬 **VideoAgent (本项目)** | 💸 **MoneyPrinterTurbo** | 🌐 **VideoLingo** | 📐 **Manim** |
| :--- | :--- | :--- | :--- | :--- |
| **核心应用定位** | **硬核技术/源码/架构视频自动化生成** | 泛娱乐/营销号短视频批量生成 | 现有外语视频汉化与双语字幕配音 | 数学公式与几何动画编程式渲染 |
| **视觉呈现载体** | **Silicon 代码卡片 + 原生 Mermaid 架构图 + 极简网格** | Pexels / Pixabay 泛风景、生活空镜素材 | 原视频画面裁剪与字幕贴附 | 矢量几何、LaTeX 公式动态形变 |
| **知识与数据纪律** | **硬指标约束 (QPS/延时/内存) + 真实源码 AST 提取** | 泛文案生成，无技术事实核验机制 | 依赖原视频已有内容，无法原创生成 | 纯数学逻辑，无文档知识提取引擎 |
| **制作交互方式** | **声明式分镜 YAML + 一键导演端到端出片** | WebUI 输入主题关键词一键生成 | WebUI 上传视频/YouTube 链接一键处理 | 编写纯 Python 脚本逐帧计算坐标 |
| **音频与音效流水线**| **32kHz 录音棚音色 + 智能呼吸停顿 + 节奏微音效 (SFX)** | 基础 Edge-TTS / 普通商用语音 | WhisperX 字幕分割 + CosyVoice 声音克隆 | 无原生配音管线（需外部挂载） |
| **质量控制与门禁** | **5 维确定性评分 (低于 75 分直接拦截)** | 无质量门禁，输出稳定性依赖模型盲盒 | 人工在 UI 中逐句校对字幕 | 靠开发者手动调试视觉对齐 |
| **成片风格覆盖** | **16:9 横屏深度长视频 + 9:16 竖屏发布会质感预告片** | 主要面向 9:16 移动端竖屏短视频 | 保持原视频比例与长宽比 | 默认 16:9 横屏视频 |
| **本地加速与隐私** | **Apple Silicon MPS/Metal 硬件加速，零成本离线跑** | 依赖第三方商用 API 充值 | 本地 GPU 或云端 API | 本地 Python + FFmpeg 渲染 |

---

## 🌟 核心特性亮点

### 1. 🤖 端到端一键导演模式 (Zero-Click Auto-Director)
输入任意技术主题、本地 Markdown / 源码，或技术博文链接，内置的内容提取器 (`content_extractor.py`) 会全自动：
- **结构化语法提取**：按语言识别代码块、标题层级与要点清单；
- **量化指标事实提炼**：自动识别 QPS、TPS、延迟 (ms)、吞吐量与内存占用等可观测硬指标；
- **全流程自动驱动**：知识萃取 ➔ 叙事节拍编排 ➔ 剧本生成 ➔ 质量评分 ➔ 渲染出片，真正实现零摩擦交付。

### 2. 🎭 4 大硬核叙事结构引擎 (Narrative Profiles)
拒绝千篇一律的套路视频！针对不同技术场景，内置 4 种专业叙事策略：
- **`tutorial`（实战教程）**：痛点切入 ➔ 环境配置 ➔ 核心运行 ➔ 关键代码 ➔ 避坑指南 ➔ 验证成果；
- **`concept`（机制原理）**：痛点引入 ➔ 架构拆解 ➔ 核心原语 ➔ 运行流程 ➔ 总结拔高；
- **`code_walkthrough`（源码走读）**：顶层数据结构 ➔ 核心驱动函数 ➔ 关键逻辑分支 ➔ 复杂度与边界；
- **`decision`（技术选型）**：方案对比 ➔ 适用边界 ➔ 真实约束证据位 ➔ 收敛建议（缺证据时留素材位，不编造基准）。

> 💡 **叙事变体**：支持 `--story-variant evidence_first`（证据与指标前置）与 `mechanism_first`（原理解析前置）。

### 3. 🛡️ 5 维确定性质量门禁 (Quality Gate)
为了杜绝流水线式无用废话，VideoAgent 独创基于多维度的确定性评分系统（满分 100，默认及格线 75）：
- **镜头多样性 (Visual Diversity, 20分)**：杜绝单一镜头连续刷屏；
- **叙事节奏变化 (Rhythm Variety, 15分)**：长短句交替，音画停顿错落有致；
- **事实证据完整性 (Evidence Integrity, 25分)**：严禁空洞说教，核心结论必须有代码、终端命令或架构图支撑；
- **内容节拍覆盖度 (Beat Coverage, 20分)**：确保起承转合全闭环；
- **台词口语化质量 (Narration Quality, 20分)**：单句字数限制，贴合真实口播习惯。

### 4. 🎨 工业级图层渲染合成器 (Compositor)
- 纯 Python + FFmpeg 硬件加速流水线；
- 镜头平滑缩放平移（Ken Burns 运镜）、气泡缓动、动态高光卡片；
- 看板娘立绘（绘梨衣）伴随讲解状态切换呼吸、思考、打气等贴纸表情；
- 打击感微音效（Whoosh, Pop, Chime, Punch）伴随画面元素自动触发。

---

## 📂 系统架构与解耦布局

项目采用**「引擎层 + 全局资产中台 + 独立工程空间 + 声明式剧本」**的四层解耦架构，为 AI Agent 和人类创作者提供清晰的分工边界：

```text
VideoAgent/
├── video-cli                    # 🚀 全局统一命令行脚手架入口
│
├── engine/                      # ⚙️ 【核心工具引擎】(无状态纯函数，跨工程通用)
│   ├── auto_director.py         # 一键成片自动导演 (LLM 知识萃取与故事映射)
│   ├── story_planner.py         # 确定性叙事节拍规划器 (支持 4 种专业叙事模式)
│   ├── quality_gate.py          # 5 维剧本确定性质量门禁 (及格线 75 分拦截)
│   ├── content_extractor.py     # 技术文档标题、代码块与要点结构化提取器
│   ├── tts_engine.py            # GPT-SoVITS 专属配音合成 (断句、呼吸停顿与时间戳)
│   ├── code_card_engine.py      # Silicon 级极简高颜值代码卡片渲染
│   ├── diagram_engine.py        # Mermaid CLI 架构与时序流程图生成
│   ├── media_engine.py          # 外部视频切片与素材精准截取
│   └── compositor.py            # 剪映级声明式多图层全动效渲染引擎
│
├── assets/                      # 🌸 【全局共享资产中台】(只读模板，无业务污染)
│   ├── character/               # 主讲人立绘 (erii_presenter) 及丰富 Q 版表情包
│   ├── sfx/                     # 节奏微音效 (pop.wav, whoosh.wav, chime.wav)
│   ├── ref_audio.wav            # 零底噪 32kHz 录音棚标准音色参考基准
│   └── bgm.mp3                  # 治愈轻快 Lo-Fi 背景音乐
│
├── projects/                    # 📦 【独立工程沙盒】(单集视频物理隔离)
│   └── epoll_deepdive/          # 示例工程: Linux epoll 机制精讲
│       ├── storyboard.yaml      # 🌟 声明式剧本配置 (Agent / 人工唯一输入)
│       ├── extra_assets/        # 本工程私有特异素材
│       ├── .cache/              # 临时音频与渲染中间帧缓存 (.gitignore 自动排除)
│       └── dist/                # 🎯 最终交付成果物 (final.mp4, cover.png, subtitles.srt)
│
├── AGENTS.md                    # 🤖 LLM Agent 创作编排协议与剧本语法全景手册
├── HANDOVER.md                  # 📖 开发者交接与底层排障指南
└── start_service.sh             # 🎙️ GPT-SoVITS 本地服务守护进程
```

---

## 🚀 极速上手指南

### 1. 准备依赖环境

```bash
# 推荐使用 Python 3.10+
git clone https://github.com/ciyuan1234/VideoAgent.git
cd VideoAgent

# 安装 Python 依赖
pip install -r <(echo "pyyaml requests")

# 确保本地已安装 ffmpeg 与 node 环境
brew install ffmpeg node
npm install -g @mermaid-js/mermaid-cli
```

### 2. 启动语音推理引擎 (可选)
如果使用本地 GPT-SoVITS 录音棚级音色合成：
```bash
./start_service.sh
```

### 🌟 3. 一键成片（推荐体验）

```bash
# 方式 A: 直接指定一个硬核技术主题（全自动编排出片）
./video-cli auto-generate goroutine_gmp --topic "Go语言协程调度器与GMP模型深度剖析"

# 方式 B: 基于本地 Markdown 文档或技术源码一键出片
./video-cli auto-generate my_paper -f ~/Desktop/paper.md

# 方式 C: 抓取在线官方技术文档/博文全自动出片
./video-cli auto-generate redis_guide -u "https://redis.io/docs/latest/operate/oss_and_stack/management/optimization/latency-monitor/"

# 方式 D: 仅自动生成剧本 yaml 供人工审阅与二创
./video-cli auto-generate rust_guide --topic "Rust 所有权机制与借用检查器" --no-build
```

### 4. 预览与成果验收
构建完成后，直接在目标工程目录下取走你的 1080P 成片：
```bash
# 在 projects/goroutine_gmp/dist/ 目录下查收：
# ├── final.mp4      (1080P / 30FPS 最终成片，fps 由 meta.fps 决定)
# ├── cover.png      (高清视频封面)
# └── subtitles.srt  (高精度外挂字幕)
open projects/goroutine_gmp/dist/final.mp4
```

---

## 📝 声明式分镜剧本 (`storyboard.yaml`)

无需编写复杂的音视频渲染与卡点代码，你（或 AI Agent）只需要以 YAML 声明每个分镜的台词与呈现内容：

```yaml
meta:
  title: "深入浅出 Redis 事件循环"
  speaker: "erii"
  theme: "white_grid"
  story_profile: "concept"
  story_variant: "evidence_first"

scenes:
  - id: "intro"
    character_sticker: "erii_presenter"
    audio:
      text: "Sakura，今天我们来深入剖析 Redis 单线程为什么这么快！"
      speed: 1.05
      pause: 0.45
    visual:
      type: "title_card"
      tag: "高性能系统架构"
      title: "Redis 事件循环底层揭秘"
      subtitle: "aeEventLoop 如何支撑 100,000+ QPS？"
      bullets:
        - "单线程 Reactor 反应器模式精髓"
        - "文件事件与时间事件的高效分发"

  - id: "code_analysis"
    character_sticker: "erii_chibi_think"
    audio:
      text: "我们直接看 aeProcessEvents 的核心处理函数。"
      speed: 1.0
      pause: 0.3
    visual:
      type: "code_card"
      lang: "c"
      theme: "OneHalfLight"
      title: "ae.c - 事件循环主循环"
      code: |
        int aeProcessEvents(aeEventLoop *eventLoop, int flags) {
            int processed = 0, numevents;
            numevents = aeApiPoll(eventLoop, tvp);
            // ...
        }
```

---

## 🧭 CLI 命令全景速查

| 命令 | 用途 | 典型参数示例 |
| :--- | :--- | :--- |
| `auto-generate` | **端到端一键成片** | `./video-cli auto-generate demo --topic "epoll" --model gemini-1.5-flash` |
| `init` | 初始化新建视频工程骨架 | `./video-cli init my_video --title "Rust入门指南"` |
| `validate` | 剧本质量门禁与素材依赖校验 | `./video-cli validate my_video` |
| `inspect` | 画面体检：布局遮挡检查 + 按幕抽帧 | `./video-cli inspect my_video` |
| `build` | 编译渲染成 1080P 高清成片 | `./video-cli build my_video` |
| `list` | 查看当前工作区所有工程状态 | `./video-cli list` |
| `status` | 查看指定工程标题、幕数与交付状态 | `./video-cli status my_video` |
| `clean` | 安全清理中间构建音频与帧缓存 | `./video-cli clean my_video` |

---

## 📈 质量评分门禁机制

运行 `validate` 或 `build` 时，系统会自动执行质量门禁诊断：

```text
🔎 剧本预检: projects/demo
  ⚠️ 待补录素材: extra_assets/runtime_evidence.mp4（展示关键操作、状态变化或运行结果）
🔬 剧本质量评估:
  • 质量评分: 92/100 (门槛 75)
      - visual_diversity: 20/20 · 6 幕使用 5 种镜头，相邻重复 0 处
      - rhythm_variety: 14/15 · 主导转场占比 67%，角色出镜 2/6 幕，镜头运动 4 处 / 2 种
      - evidence_integrity: 18/25 · 真实素材镜头 0 幕，占位 1 幕，素材请求 1 项
      - beat_coverage: 20/20 · 6 个节拍覆盖 6 种意图
      - narration_quality: 20/20 · 6 条台词，重复 0 条，超长句 0 处
      ⚠️ 仍有素材占位场景: runtime_evidence
      💡 当前最弱分项是 evidence_integrity（18/25）
```

> 上例输出为真实运行结果（以本 README 自身为输入）。若评分低于 75 分或存在阻断项，`validate` 返回失败、`build` 抛错且不进入渲染；内部预览时可加 `--allow-low-quality`。

---

## 🧪 回归测试

```bash
# 30 个用例：四类叙事结构快照、指标提取纪律、素材匹配、发布门禁与历史工程兼容
python -m unittest discover -s tests -t .

# 有意调整生成结果并确认无误后，重建快照基线
python -m tests.update_snapshots
```

`tests/fixtures/` 存放固定输入，`tests/snapshots/` 存放剧本指纹基线（profile、variant、节拍、场景 id、镜头序列、素材请求与 evidence 标记），不含任何二进制产物。

---

## 🔍 画面体检 (Visual QA)

内容层合格不代表画面层没问题。`inspect` 会做确定性布局检查，并把每幕的首/中/末帧（含字幕）抽到 `dist/inspect/qa/` 供人工目视（该目录不入库，`dist/inspect/` 根目录保留人工策展的展示图）：

```bash
./video-cli inspect my_video            # 静态检查 + 抽帧（9 张/3 幕）
./video-cli inspect my_video --no-frames  # 只做静态检查
```

检查项来自渲染器的真实布局常量，而不是经验猜测：

- **字幕遮挡**：左下角镜头标签不得侵入居中字幕胶囊；超长标签在渲染时会被强制截断并加省略号，同时体检报错要求作者缩短。
- **callout 越界 / 过小**：标注框必须落在素材归一化范围内且不低于 4% 边长。
- **镜头跳回**：`beats[].at` 必须递增，首帧应从 0 开始。
- **静态镜头**：既无 `camera.motion` 也无 `beats` 的场景会被点名；全片皆静态则直接阻断。
- **标签重复**：同一标签在多幕复用会提示，避免节拍失去区分度。
- **节点文字溢出**：节点卡固定 320×150，超宽标题会被截断并提示压缩到约 11 个汉字以内。
- **不可渲染字形**：来源文档标题里的 emoji 会被自动剔除，避免输出豆腐块方块。

> 抽帧时按字数估算时长与逐句字幕（不调用 TTS），因此检查帧与成片高度一致，可快速定位遮挡、越界类问题。

---

## 📱 第二套风格：发布会竖屏 (launch_teaser)

同一套引擎可以输出与开发者卡片风格**完全独立**的竖屏视觉语言：`1080×1920` 深空渐变、中心辉光、巨型居中排版、细结构线与溶解转场，无卡片、无徽标、无主讲人立绘，字幕也改为细体居中加投影而非深色胶囊。

```yaml
meta:
  resolution: [1080, 1920]
  style: "launch_teaser"
  accent: "indigo"        # indigo / violet / cyan / amber
scenes:
  - id: "hero"
    camera: {motion: "zoom_in"}
    audio: {text: "Gemini 4.0，正式发布。"}
    visual:
      type: "hero"
      kicker: "GOOGLE DEEPMIND"
      title: "Gemini 4.0"
      subtitle: "正式发布"
```

竖屏原生提供四个原语：`hero`（开场锁定）、`statement`（大字号观点句，支持 `lines` + `highlight`）、`feature_stack`（左侧竖条编号列表）、`closing`（收束锁定 + 页脚）。它们只在 `launch_teaser` 风格下可用，不能与横屏原语混用。转场新增 `fade`（15 帧交叉溶解），与 `cut`、`slide_left` 并存。

<p align="center">
  <img src="projects/gemini_launch/dist/inspect/hero.png" width="24%" alt="Launch Hero" />
  <img src="projects/gemini_launch/dist/inspect/statement.png" width="24%" alt="Launch Statement" />
  <img src="projects/gemini_launch/dist/inspect/feature_stack.png" width="24%" alt="Launch Feature Stack" />
  <img src="projects/gemini_launch/dist/inspect/closing.png" width="24%" alt="Launch Closing" />
</p>

> 示例工程 `projects/gemini_launch` 为风格样片：文案只覆盖发布事实与信息边界，**不包含未经官方确认的能力、数据或开放范围**，这些一律以官方公告为准。

---

## 📦 依赖与环境

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt          # Pillow / numpy / requests / PyYAML
brew install ffmpeg silicon mermaid-cli yt-dlp   # 渲染所需外部二进制
```

语音合成需本地 GPT-SoVITS 服务（默认 `127.0.0.1:9880`），见 `start_service.sh`。`video-cli` 与 `engine/*.py` 的 shebang 指向本机 GPT-SoVITS 虚拟环境解释器，换机器时需调整，或改用 `python engine/cli.py ...`。

---

## ❓ 常见问题解答 (FAQ)

<details>
<summary><b>Q1: VideoAgent 需要付费购买云端 API 才能运行吗？</b></summary>
<br/>
<b>完全不需要！</b> VideoAgent 优先面向本地开发环境设计：
<ul>
  <li><b>知识提取与剧本编写</b>：支持本地 Ollama（如 Llama 3、DeepSeek、Qwen 等开源模型），也支持标准 OpenAI 兼容接口或 Gemini 免费层 API；</li>
  <li><b>配音合成</b>：内置 GPT-SoVITS 专属服务，本地调用 <code>./start_service.sh</code> 即可合成 32kHz 录音棚级音色；</li>
  <li><b>渲染与合成</b>：完全由本地 Python、FFmpeg 与 Silicon / Mermaid-cli 驱动，零云端渲染月费，且完全保护你的专有代码与私密文档。</li>
</ul>
</details>

<details>
<summary><b>Q2: 相比市面上的“AI 批量短视频生成器”，VideoAgent 有什么本质区别？</b></summary>
<br/>
市面上绝大部分短视频生成工具主要面向“泛娱乐营销号”，通过去素材库搜刮大量与内容弱相关的风景、生活空镜来拼接画面。<b>这类工具完全无法胜任计算机科学与硬核技术题材。</b><br/><br/>
VideoAgent 专注于严肃技术传播：
<ul>
  <li><b>代码级颗粒度</b>：真实解析源码 AST 语法树，渲染高颜值代码卡片；</li>
  <li><b>逻辑可视化</b>：原生将技术逻辑编译为 Mermaid 架构图与时序流程图；</li>
  <li><b>严苛证据纪律</b>：强制提取 QPS、TPS、内存占用、时延等量化指标作为分镜支撑，绝不生成空洞废话。</li>
</ul>
</details>

<details>
<summary><b>Q3: 剧本质量门禁（Quality Gate）提示低于 75 分被拦截，该如何处理？</b></summary>
<br/>
质量门禁是 VideoAgent 保证成片工业级水准的独创机制。当运行 <code>validate</code> 或 <code>build</code> 分数低于 75 分时，终端会打印详尽的失分诊断（如：<i>缺少代码或运行证据、相邻镜头布局重复、单句台词超长缺乏停顿</i>）。<br/>
你只需根据终端指引在 <code>storyboard.yaml</code> 中补齐缺失的原语或微调台词即可；若当前仅为快速验证草稿，可追加 <code>--allow-low-quality</code> 参数跳过门禁直接渲染。
</details>

<details>
<summary><b>Q4: 可以替换自定义的主讲人形象与配音音色吗？</b></summary>
<br/>
<b>非常简单！</b>
<ul>
  <li><b>立绘形象</b>：将你的透明背景 PNG 图片放入 <code>assets/character/</code> 目录，并在剧本的 <code>character_sticker</code> 声明文件名即可；</li>
  <li><b>音色基准</b>：将一段 5~10 秒的干净人声音频保存为 <code>assets/ref_audio.wav</code>，GPT-SoVITS 即可克隆出你的专属音色。</li>
</ul>
</details>

<details>
<summary><b>Q5: 生成的视频支持直接发布到各大视频平台吗？</b></summary>
<br/>
原生完美兼容！每次渲染完成后，工程目录的 <code>dist/</code> 会一键打包：
<ul>
  <li><code>final.mp4</code>：标准 H.264 / AAC 编码的高清视频（支持 16:9 横屏与 9:16 竖屏）；</li>
  <li><code>cover.png</code>：高清对齐封面图；</li>
  <li><code>subtitles.srt</code>：与音频毫秒级对齐的独立外挂字幕。可以直接拖拽上传至 B 站、YouTube、抖音、小红书等主流平台。</li>
</ul>
</details>

---

## 🗺️ 路线图 (Roadmap)

- [x] **v1.0**：解耦四层架构设计、Silicon 代码卡片、Mermaid 架构图与声明式图层合成
- [x] **v1.2**：端到端“一键成片”自动导演模式与 4 大叙事结构引擎
- [x] **v1.5**：5 维确定性剧本质量门禁拦截系统与快照回归测试
- [x] **v1.8**：`launch_teaser` 竖屏发布会风格与画面布局体检系统
- [ ] **v2.0 (规划中)**：
  - [ ] 桌面端交互式 WebUI 剧本可视化编排器
  - [ ] 更多风格看板娘与主讲人立绘角色库（赛博朋克、极客风、商务科技等）
  - [ ] 多平台一键发布插件（B站、YouTube、小红书标签与简介自动填充）
  - [ ] 支持 Remotion 现代前端动效渲染器后端

---

## 🤝 参与贡献 (Contributing)

欢迎任何形式的贡献！无论是新镜头视觉原语、叙事模板、新角色立绘还是文档改进：
1. Fork 本仓库并新建分支 (`git checkout -b feature/AmazingFeature`)
2. 提交代码更改 (`git commit -m 'feat: Add some AmazingFeature'`)
3. 推送分支 (`git push origin feature/AmazingFeature`)
4. 提交 Pull Request

<div align="center">
  <br/>
  <a href="https://github.com/ciyuan1234/VideoAgent/graphs/contributors">
    <img src="https://contrib.rocks/image?repo=ciyuan1234/VideoAgent" alt="Contributors" />
  </a>
</div>

---

## 🌟 Star History

如果你觉得 VideoAgent 对你的技术创作有帮助，欢迎点亮右上角的 **Star ⭐️** 支持我们！

[![Star History Chart](https://api.star-history.com/svg?repos=ciyuan1234/VideoAgent&type=Date)](https://star-history.com/#ciyuan1234/VideoAgent&Date)

---

## 📄 开源许可证

本项目基于 [MIT License](LICENSE) 开源发布。
欢迎自由用于个人学习、开源分享与商业化技术内容创作！
