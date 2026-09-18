# VideoAgent - Agent 架构与创作指引规范

本项目采用**「四层解耦、声明式剧本驱动（Declarative Storyboard）」**架构，彻底隔离 Agent 上下文与多媒体二进制临时产物。

---

## 🎯 核心定位与设计原则

- **Agent 的角色是【编剧兼导演】**：你的核心工作是产出或调整结构化剧本（`storyboard.yaml`），关注知识萃取、台词节奏与视觉编排。
- **确定性编译引擎【视频工坊】**：图形渲染、语音合成、动效缓动、音轨对齐与 FFmpeg 压制全部交由 `engine/` 确定性执行，**不消耗 LLM 上下文 Token**。
- **严格上下文与工程隔离**：
  - 中间临时文件（分段音频、单帧图片、粒子缓存）统一丢入工程私有的 `.cache/`，已被 `.gitignore` 排除。
  - 成果物统一收拢在各工程的 `dist/` 交付目录下。
  - 严禁在根目录下倾倒临时媒体文件。

---

## ⚡ 标准生产工作流

### 模式 A: 🌟 端到端全自动导演模式 (Auto-Generate, 0 介入)
当你需要根据某个技术主题、本地技术文档（Markdown）或技术博文链接快速生产视频时，可直接使用内置 AutoDirector：
```bash
# 从技术主题直接生成并渲染出片
./video-cli auto-generate <project_id> --topic "主题描述"

# 或从本地文件生成剧本（可配合 --no-build 仅生成剧本以便微调）
./video-cli auto-generate <project_id> -f path/to/document.md --no-build
```

自动导演先分析材料再选择 `story_profile`：`tutorial`（操作演示）、`concept`（机制原理）、`code_walkthrough`（源码走读）或 `decision`（技术选型）。默认 `auto`；需要固定结构时可传入 `--story-profile code_walkthrough`，并在生成剧本的 `meta.story_profile` 中保留结果。缺少关键操作或结果素材时必须输出 `asset_requests` 与 `asset_placeholder`，不得编造跑分、终端日志或 Diff。

自动导演还会先输出 `meta.story_beats`：每项包含 `id`、`intent`、`evidence_level`、`scene_id`，随后才选择分镜。若同一材料需要稳定但不同的讲解次序，使用 `--story-variant evidence_first` 或 `--story-variant mechanism_first`；两者不得改变材料事实与最终结论。素材可在 `extra_assets/` 的文件名中包含 `demo`、`code`、`arch`、`chart` 等关键词，或由调用方提供 `tags: [operation|code|architecture|metrics]`，以匹配对应节拍。

生成后会输出 0–100 的剧本质量评分（门槛 75），并写入 `meta.quality_report`。评分覆盖镜头多样性、节奏变化、证据完整性、节拍覆盖与台词质量；`validate` 与 `build` 在低于门槛时都会阻止发布渲染，只有内部预览可以加 `--allow-low-quality`。历史工程缺少 `story_profile` 时评分仅供参考，不阻断渲染。

**指标提取纪律**：只有 `QPS`、`TPS`、`RPS`、`ms`、`MB`、`GB`、`KB`、`%` 这类无歧义单位可以直接作为证据；`x`、`倍` 属于歧义单位，必须出现在「压测/基准/吞吐/延迟/提升/降低」等性能语境附近才会被采信，且 `1920x1080` 这类分辨率会被排除。生成 `chart_benchmark` 还需满足「指标数 ≥ 2 且至少一个是无歧义单位」。不要用变焦倍率、帧率或分辨率冒充性能数据。

**运镜分配**：关键节拍会自动带上 `camera.motion`（`hook` 用 `zoom_punch`，解释类镜头用 `zoom_in`）；真实素材镜头由 `beats` 自行运动，收束镜头保持静止。新增分镜时请沿用这套分配，否则质量门禁会因镜头运动缺失或单一而扣分。

**画面体检**：改完剧本先跑 `./video-cli inspect <project>`。它会检查字幕遮挡、callout 越界、镜头跳回与全静态画面，并抽取含字幕的首/中/末帧到 `dist/inspect/qa/`（该目录不入库）。其中 `beats[].label` 是左下角短语，不是句子——渲染器会把过长的标签截断加省略号以避免压住居中字幕，体检会同时报错要求你把它改短。

### 模式 B: ✍️ 手动导演模式 (4 步法)

#### 1. 初始化独立工程
在 `projects/` 下创建隔离的视频工程：
```bash
./video-cli init <project_id> --title "你的视频标题"
```
系统会自动创建：
- `projects/<project_id>/storyboard.yaml`（分镜剧本文件）
- `projects/<project_id>/extra_assets/`（本工程独有的本地素材，如特异截图）
- `projects/<project_id>/dist/`（最终交付产物目录）

#### 2. 编排分镜剧本 (`storyboard.yaml`)
编辑 `projects/<project_id>/storyboard.yaml`。示例如下：

```yaml
meta:
  title: "深入浅出 epoll 内核机制"
  resolution: [1920, 1080]
  fps: 30
  theme: "white_grid"        # 白底网格开发者风格
  speaker: "erii"            # 绘梨衣专属音色
  bgm:
    file: "bgm.mp3"          # 自动匹配 assets/bgm.mp3
    volume: 0.10
  sfx:
    enabled: true            # 自动添加气泡、转场滑入、聚光灯提示音

scenes:
  # 场景 1: 封面大卡片与主讲人立绘
  - id: "scene1_intro"
    character_sticker: "erii_presenter"
    audio:
      text: "Sakura，欢迎来到我的计算机小课堂！今天我们来聊聊高并发的基石：Linux 的 epoll。"
      speed: 1.05
      pause: 0.45            # 句间自然呼吸停顿
    visual:
      type: "title_card"
      tag: "LINUX 内核底层剖析"
      title: "Linux 高并发的秘密"
      subtitle: "从 select 轮询到 epoll 事件驱动"
      bullets:
        - "深入拆解内核红黑树管理与就绪链表机制"
        - "从 O(n) 线性轮询到 O(1) 事件触发的底层飞跃"
        - "核心 API 解析：轻松搞定单机百万高并发网络连接"

  # 场景 2: 动态架构流向图与流动数据包
  - id: "scene2_kernel"
    character_sticker: "erii_chibi_think"
    audio:
      text: "传统 select 每次都要轮询所有连接，效率很低；而 epoll 基于红黑树和就绪事件链表，通知效率直接拉满！"
      speed: 1.05
      pause: 0.45
    visual:
      type: "custom_nodes"
      header_title: "一、内核机制：红黑树 + 就绪链表"
      header_sub: "传统 select 遍历全部 O(n)，epoll 事件触发 O(1)"
      nodes:
        - title: "客户端并发连接"
          sub: "100w Sockets"
          theme: "white"
        - title: "内核 epoll 红黑树"
          sub: "高效管理 O(log N)"
          theme: "blue"
        - title: "就绪事件双向链表"
          sub: "rdlist 就绪队列"
          theme: "amber"
        - title: "epoll_wait 返回"
          sub: "用户态极速处理 O(1)"
          theme: "green"

  # 场景 3: 核心代码卡片与聚光灯行高亮
  - id: "scene3_code"
    character_sticker: "erii_chibi_happy"
    audio:
      text: "这就是单机支撑百万并发的核心秘密哦。"
      speed: 1.05
      pause: 0.45
    visual:
      type: "code"
      header_title: "二、核心 API：epoll_create 与 epoll_wait"
      header_sub: "事件发生内核直接唤醒用户态，单机轻松支撑百万并发"
      lang: "c"
      theme: "OneHalfLight"  # 纯白/浅色高颜值代码高亮
      spotlight_line: 10     # 聚光灯聚焦呼吸框
      code: |
        int epfd = epoll_create1(0);
        epoll_ctl(epfd, EPOLL_CTL_ADD, listen_sock, &ev);
        while (1) {
            int nfds = epoll_wait(epfd, events, MAX_EVENTS, -1);
            for (int n = 0; n < nfds; ++n) {
                // 唤醒就绪事件极速响应
            }
        }
```

### 3. 一键编译渲染
运行构建指令：
```bash
./video-cli build <project_id>
```
编译器将全自动执行：
1. 断句合成绘梨衣专属配音并计算精确时间线；
2. 渲染高颜值代码卡片与架构图；
3. 生成多图层动效、缓动推镜、数据流粒子与呼吸微动效；
4. 混音配音、微音效（SFX）与背景音乐（BGM）；
5. 导出：
   - 🎬 `projects/<project_id>/dist/final.mp4`（1080P 高清成片）
   - 🖼️ `projects/<project_id>/dist/cover.png`（高清封面图）
   - 📝 `projects/<project_id>/dist/subtitles.srt`（对齐字幕文件）

### 4. 工程管理与缓存清理
- **查看所有工程状态**：`./video-cli list`
- **查看指定工程详情**：`./video-cli status <project_id>`
- **清空中间构建缓存**：`./video-cli clean <project_id>`（释放磁盘空间，保持工程轻量）

---

## 🎨 视听布局原语库 (打破模板化，灵活编排)

为彻底避免“千篇一律”的幻灯片感，编译器支持以下高表现力分镜原语，Agent 编剧可根据内容类型自由混搭：

| 分镜类型 (`visual.type` 或 `layout`) | 适用场景 | 关键参数 | 视觉特色 |
| :--- | :--- | :--- | :--- |
| **`title_card`** | 黄金前 3 秒 Hook / 视频封面 | `tag`, `title`, `subtitle`, `bullets` | 磨砂白卡、类别胶囊、绘梨衣主讲人迎宾立绘 |
| **`split_compare`** | 传统 vs 现代 / 选型对决 / 痛点PK | `left`, `right` (含 `badge`, `title`, `bullets`, `metrics`) | 左右分屏对比，中间高光 VS 徽标，红绿情绪双色调 |
| **`chart_benchmark`** | 性能压测 / 吞吐量对比 / 算法复杂度 | `data: [{label, value, unit, theme}]`, `champion_tag` | 柱状图平滑生长动画、动态数字翻牌计数器、冠军标签 |
| **`terminal`** | 实机操作 / Linux 调优 / 脚本演示 | `command`, `output_lines` | macOS 终端三色交通灯、黑客打字机敲击效果、日志淡入 |
| **`custom_nodes`** | 架构演进 / 内核拓扑 / 数据包流向 | `nodes: [{title, sub, theme}]` | 动态箭头生长、正弦发光数据包粒子穿梭流动 |
| **`code`** | 核心算法 / 关键 API / 源码深潜 | `code`, `lang`, `theme`, `spotlight_line` | Silicon 高清渲染、圆角投影、指定代码行呼吸聚光灯 |
| **`git_diff`** | 源码优化 / 逻辑重构 / 算法演进 | `file_name`, `diff`, `summary_tag` | 拟真 Git 差异对比，红删绿增两栏着色，代码增量滑入动效 |
| **`image` + `presentation: cinematic`** | 软件截图 / 产品界面讲解 | `beats: [{at, focus, scale, callout, label}]` | 真实界面全屏主导，镜头随讲解在关键区域间推移并绘制聚焦标注 |
| **`video_clip`** | 录屏 / Demo / 实拍素材 | `file`, `clip_fps`, `beats` | 将项目内 MP4 抽帧进缓存，按镜头节拍播放、推镜和标注，不再套进静态卡片 |

> 上表为横屏开发者风格（默认）。需要手机竖屏发布会风格时改用 `meta.style: launch_teaser` 与 `hero` / `statement` / `feature_stack` / `closing` 四个原语，详见下文。

### 🎥 真实素材镜头节拍（Cinematic Beats）

避免将真实截图压缩在“左文右图”卡片中。对 `image` 使用 `presentation: cinematic`，或直接使用 `video_clip`，让素材成为整幕主画面；`at` 为场景进度（0~1），其余坐标均为素材自身的归一化坐标：

```yaml
visual:
  type: "image" # 也可为 video_clip
  presentation: "cinematic"
  file: "codex_tui.png"
  beats:
    - at: 0.00
      focus: [0.50, 0.35]
      scale: 1.05
      callout: [0.20, 0.18, 0.60, 0.48]
      label: "先定位操作区域"
      accent: "indigo"
    - at: 0.50
      focus: [0.48, 0.78]
      scale: 1.32
      callout: [0.26, 0.70, 0.28, 0.16]
      label: "再推近到关键输入动作"
      accent: "gold"
```

`video_clip` 使用 `clip_fps: 12` 作为默认抽帧率；素材、抽帧和缓存必须位于工程的 `extra_assets/` 与 `.cache/`，不要放在仓库根目录。

### 💥 关键词高能冲击大字报 (Kinetic Punch)
在任意分镜中声明 `punch_words`，当台词读到对应词汇时，屏幕中央会自动爆出带触觉微震动的高能大字报，并同步混入打击音效 (`punch.wav`)：
```yaml
punch_words:
  - text: "彻底告别无用功！"
    style: "emerald"  # 可选: emerald (突破绿) / rose (痛点红) / gold (性能金) / indigo (极客蓝)
```

### 🎙️ 情绪声线调制 (Emotion Voice)
在 `audio` 配置中添加 `emotion` 属性，调整语速与起伏张力：
```yaml
audio:
  text: "性能直接暴涨了十四倍！"
  emotion: "excited"   # 可选: excited (高能充沛) / calm (理性深邃) / normal (自然讲解)
```

### 🎬 虚拟摄像机 (Virtual Camera)
在任意场景添加 `camera` 属性，让画面产生电影级推镜动感：
```yaml
camera:
  motion: "zoom_in"       # 镜头随讲解平滑推进 (1.0x -> 1.08x)
  # 或 motion: "zoom_punch" (入场冲击放大后弹性回弹)
```

### ✂️ 剪辑节奏与转场控制
```yaml
transition: "cut"         # 硬切 (Hard Cut，0帧无缝切换，干脆利落)
# transition: "slide_left"  # 平滑横向滑动推镜 (12 帧)
# transition: "fade"        # 交叉溶解 (15 帧)，适合发布会预告等柔和衔接
```

### 📱 发布会竖屏风格 (launch_teaser)

当 `meta.style: "launch_teaser"` 时，渲染切换到完全独立的竖屏视觉语言：画布 `[1080, 1920]` 深空渐变 + 中心辉光 + 暗角，巨型居中排版与细结构线，无卡片、无徽标、无主讲人立绘；字幕改为细体居中 + 柔和投影，不使用深色胶囊。

```yaml
meta:
  resolution: [1080, 1920]
  style: "launch_teaser"
  accent: "indigo"          # indigo / violet / cyan / amber
scenes:
  - id: "hero"
    camera: {motion: "zoom_in"}
    audio: {text: "Gemini 4.0，正式发布。"}
    visual:
      type: "hero"          # 开场：kicker + 巨型标题 + 强调线 + 副标题
      kicker: "GOOGLE DEEPMIND"
      title: "Gemini 4.0"
      subtitle: "正式发布"
```

该风格原生提供四个竖屏原语：`hero`（开场锁定）、`statement`（大字号观点句，支持 `lines` + `highlight`）、`feature_stack`（左侧竖条编号列表）、`closing`（收束锁定 + 页脚）。它们只在 `launch_teaser` 风格下可用，不可与经典横屏原语混用。

---

## 🛠️ 单项工具调用（调试/测试使用）

如需单独测试工具链底层引擎，可在根目录直接调用：
- **语音合成引擎**：`python engine/tts_engine.py "台词文本" -o output/test.wav`
- **代码卡片引擎**：`python engine/code_card_engine.py "代码内容" --lang python --theme OneHalfLight -o output/test_code.png`
- **架构图引擎**：`python engine/diagram_engine.py "graph LR; A-->B" -o output/test_diag.png`
- **素材截取下载**：`python engine/media_engine.py "<URL>" -s 00:00:10 -e 00:00:20 -o output/clip.mp4`
