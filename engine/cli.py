#!/Users/a1-6/GPT-SoVITS/venv/bin/python
# -*- coding: utf-8 -*-
"""
VideoAgent Unified CLI
统一命令行脚手架，用于工程初始化、剧本编译、临时缓存清理与状态管理。
"""

import os
import sys
import yaml
import shutil
import argparse

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)
PROJECTS_DIR = os.path.join(ROOT_DIR, "projects")

TEMPLATE_TECH_DEEPDIVE = """meta:
  title: "{title}"
  resolution: [1920, 1080]
  fps: 30
  theme: "white_grid"
  speaker: "erii"
  bgm:
    file: "bgm.mp3"
    volume: 0.10
    fade_in: 1.5
    fade_out: 2.0
  sfx:
    enabled: true

scenes:
  - id: "scene1_intro"
    character_sticker: "erii_presenter"
    audio:
      text: "Sakura，欢迎来到我的计算机小课堂！今天我们来聊聊高并发的基石：Linux 的 epoll。"
      speed: 1.05
      pause: 0.45
    visual:
      type: "title_card"
      tag: "LINUX 内核底层剖析"
      title: "{title}"
      subtitle: "从 select 轮询到 epoll 事件驱动的飞跃"
      bullets:
        - "深入拆解内核红黑树管理与就绪链表机制"
        - "从 O(n) 线性轮询到 O(1) 事件触发的底层飞跃"
        - "核心 API 解析：轻松搞定单机百万高并发网络连接"

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
      theme: "OneHalfLight"
      spotlight_line: 10
      code: |
        int epfd = epoll_create1(0);
        struct epoll_event ev, events[MAX_EVENTS];
        ev.events = EPOLLIN;
        ev.data.fd = listen_sock;
        epoll_ctl(epfd, EPOLL_CTL_ADD, listen_sock, &ev);
        while (1) {
            int nfds = epoll_wait(epfd, events, MAX_EVENTS, -1);
            for (int n = 0; n < nfds; ++n) {
                // 唤醒就绪事件极速响应
            }
        }
"""

def resolve_project_path(path_or_name):
    if os.path.isabs(path_or_name):
        return path_or_name
    # 尝试当前目录
    if os.path.exists(path_or_name):
        return os.path.abspath(path_or_name)
    # 尝试 projects/ 目录
    proj_path = os.path.join(PROJECTS_DIR, path_or_name)
    return os.path.abspath(proj_path)

def cmd_init(args):
    target = resolve_project_path(args.project)
    title = args.title or os.path.basename(target)
    os.makedirs(target, exist_ok=True)
    os.makedirs(os.path.join(target, "extra_assets"), exist_ok=True)
    os.makedirs(os.path.join(target, "dist"), exist_ok=True)

    # 写入 .gitignore 隔离缓存与生成物
    gitignore_path = os.path.join(target, ".gitignore")
    if not os.path.exists(gitignore_path):
        with open(gitignore_path, "w", encoding="utf-8") as f:
            f.write(".cache/\n")

    sb_path = os.path.join(target, "storyboard.yaml")
    if os.path.exists(sb_path) and not args.force:
        print(f"⚠️ 剧本文件已存在: {sb_path} (如需覆盖请加 --force)")
    else:
        content = TEMPLATE_TECH_DEEPDIVE.replace("{title}", title)
        with open(sb_path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"✨ 成功初始化工程: {target}")
        print(f"📄 剧本配置文件: {sb_path}")

def cmd_auto_generate(args):
    """端到端自动编剧并一键编译出片"""
    target = resolve_project_path(args.project)
    project_name = os.path.basename(target)
    os.makedirs(target, exist_ok=True)
    os.makedirs(os.path.join(target, "extra_assets"), exist_ok=True)
    os.makedirs(os.path.join(target, "dist"), exist_ok=True)

    gitignore_path = os.path.join(target, ".gitignore")
    if not os.path.exists(gitignore_path):
        with open(gitignore_path, "w", encoding="utf-8") as f:
            f.write(".cache/\n")

    # 1. 确定内容来源
    source = None
    if args.file:
        source = args.file
    elif args.url:
        source = args.url
    elif args.topic:
        source = args.topic
    else:
        # 如果未指定任何参数，将 project 参数作为主题
        source = project_name

    print(f"🎬 [AutoDirector] 正在分析内容源: {source}")
    from engine.content_extractor import ContentExtractor
    from engine.auto_director import AutoDirector

    from engine.story_planner import collect_available_assets

    extracted = ContentExtractor.extract(source)
    # 项目已经存在的真实素材是导演可直接使用的证据，而不是装饰性附件。
    available_assets = collect_available_assets(os.path.join(target, "extra_assets"))
    extracted["available_assets"] = available_assets
    print(f"📖 提取元数据完成: 标题【{extracted['title']}】 (发现 {len(extracted.get('headings', []))} 节, {len(extracted.get('code_snippets', []))} 个代码块)")
    if available_assets:
        print(f"🎞️ 已发现 {len(available_assets)} 个可直接编排的项目素材")

    # 2. 导演编写剧本
    director = AutoDirector(root_dir=ROOT_DIR)
    yaml_script = director.generate_storyboard(
        extracted,
        provider=args.provider,
        model=args.model,
        api_key=args.api_key,
        story_profile=args.story_profile,
        story_variant=args.story_variant,
    )

    sb_path = os.path.join(target, "storyboard.yaml")

    # 写入可追溯的质量报告，便于后续 validate / build 复核同一份评分
    from engine.quality_gate import evaluate_storyboard, format_report
    sb_data = yaml.safe_load(yaml_script)
    quality = evaluate_storyboard(sb_data)
    sb_data.setdefault("meta", {})["quality_report"] = quality
    yaml_script = yaml.dump(sb_data, allow_unicode=True, sort_keys=False)

    with open(sb_path, "w", encoding="utf-8") as f:
        f.write(yaml_script)
    print(f"✅ 剧本自动创作完成: {sb_path}")

    # 解析展示剧本概况
    scenes = sb_data.get("scenes", [])
    primitives = [s.get("visual", {}).get("type") for s in scenes]
    selected_profile = sb_data.get("meta", {}).get("story_profile", "unknown")
    story_variant = sb_data.get("meta", {}).get("story_variant", "unknown")
    print(f"🎭 剧本概况: profile={selected_profile} | variant={story_variant} | 共 {len(scenes)} 幕")
    print(f"🎞️ 视觉原语: {' -> '.join(primitives)}")
    print("🔬 剧本质量评估:")
    for line in format_report(quality):
        print(line)

    if quality["enforced"] and not quality["passed"] and not args.allow_low_quality:
        print("❌ 质量未达标，已跳过自动构建；修复剧本后重试，或使用 --allow-low-quality 仅做内部预览。")
        return

    # 3. 一键构建
    if not args.no_build:
        print(f"\n🚀 启动全自动渲染引擎...")
        if args.clean:
            cache_dir = os.path.join(target, ".cache")
            if os.path.exists(cache_dir):
                shutil.rmtree(cache_dir)
                print(f"🧹 已清空旧缓存: {cache_dir}")

        from engine.compositor import VideoCompositor
        compositor = VideoCompositor(target, root_dir=ROOT_DIR)
        errors, warnings = compositor.validate_storyboard(allow_placeholders=args.allow_placeholders)
        for warning in warnings:
            print(f"⚠️ 预检提示：{warning}")
        if errors:
            print("ℹ️ 自动剧本包含待补素材，已跳过成片构建。补齐素材后运行 ./video-cli validate " + project_name)
            for error in errors:
                print(f"  • {error}")
            return
        compositor.build(allow_placeholders=args.allow_placeholders)
        print(f"\n🎉 恭喜！端到端一键成片完成！")
        print(f"🎬 最终交付成片: {os.path.join(target, 'dist', 'final.mp4')}")
        print(f"🖼️ 高清封面大图: {os.path.join(target, 'dist', 'cover.png')}")
        print(f"📝 同步对齐字幕: {os.path.join(target, 'dist', 'subtitles.srt')}")
    else:
        print(f"ℹ️ 已跳过自动构建 (--no-build)，可随后手动执行: ./video-cli build {project_name}")

def cmd_build(args):
    target = resolve_project_path(args.project)
    if args.clean:
        cache_dir = os.path.join(target, ".cache")
        if os.path.exists(cache_dir):
            shutil.rmtree(cache_dir)
            print(f"🧹 已清空缓存: {cache_dir}")

    # 动态导入渲染器
    from engine.compositor import VideoCompositor
    compositor = VideoCompositor(target, root_dir=ROOT_DIR)
    compositor.build(allow_placeholders=args.allow_placeholders,
                     allow_low_quality=getattr(args, "allow_low_quality", False))

def cmd_clean(args):
    target = resolve_project_path(args.project)
    cache_dir = os.path.join(target, ".cache")
    if os.path.exists(cache_dir):
        shutil.rmtree(cache_dir)
        print(f"🧹 已成功清理工程缓存: {cache_dir}")
    else:
        print(f"ℹ️ 该工程无残留缓存: {target}")

def cmd_list(args):
    if not os.path.exists(PROJECTS_DIR):
        print("暂无已创建的项目工程。")
        return
    items = sorted(os.listdir(PROJECTS_DIR))
    print("📁 视频工程列表 (projects/):")
    for it in items:
        p = os.path.join(PROJECTS_DIR, it)
        if os.path.isdir(p):
            sb = os.path.join(p, "storyboard.yaml")
            dist_mp4 = os.path.join(p, "dist", "final.mp4")
            status = "✅ 已成片" if os.path.exists(dist_mp4) else "⏳ 待编译"
            title = it
            if os.path.exists(sb):
                try:
                    with open(sb, "r", encoding="utf-8") as f:
                        data = yaml.safe_load(f)
                        title = data.get("meta", {}).get("title", it)
                except Exception:
                    pass
            print(f"  • [{status}] {it} ({title})")

def cmd_status(args):
    target = resolve_project_path(args.project)
    sb_path = os.path.join(target, "storyboard.yaml")
    if not os.path.exists(sb_path):
        print(f"❌ 未找到工程剧本: {sb_path}")
        return
    with open(sb_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    scenes = data.get("scenes", [])
    total_chars = sum(len(s.get("audio", {}).get("text") or s.get("voice_text", "")) for s in scenes)
    dist_mp4 = os.path.join(target, "dist", "final.mp4")
    built = os.path.exists(dist_mp4)
    print(f"📊 工程状态: {target}")
    print(f"  • 视频标题: {data.get('meta', {}).get('title')}")
    print(f"  • 场景数量: {len(scenes)} 幕")
    print(f"  • 台词总字数: {total_chars} 字")
    print(f"  • 交付状态: {'✅ 已完成 (dist/final.mp4)' if built else '⏳ 待渲染'}")

def cmd_validate(args):
    """在耗时渲染前检查剧本、素材与制作期占位。"""
    target = resolve_project_path(args.project)
    from engine.compositor import VideoCompositor
    from engine.quality_gate import format_report
    compositor = VideoCompositor(target, root_dir=ROOT_DIR)
    errors, warnings = compositor.validate_storyboard(allow_placeholders=args.allow_placeholders)
    print(f"🔎 剧本预检: {target}")
    for warning in warnings:
        print(f"  ⚠️ {warning}")
    quality = compositor.quality_report()
    print("🔬 剧本质量评估:")
    for line in format_report(quality):
        print(line)
    if errors:
        for error in errors:
            print(f"  ❌ {error}")
        print("❌ 预检未通过：请补齐素材或使用 --allow-placeholders 仅做制作期预览。")
        return False
    if quality["enforced"] and not quality["passed"] and not args.allow_low_quality:
        print("❌ 质量评分未达标：修复剧本后重试，或使用 --allow-low-quality 仅做内部预览。")
        return False
    if quality["enforced"] and not quality["passed"]:
        print("⚠️ 已用 --allow-low-quality 放行，仅可用于内部预览，不建议发布。")
    print("  ✅ 预检通过，可以开始渲染。")
    return True

def main():
    parser = argparse.ArgumentParser(description="VideoAgent CLI - 模块化视频生产管线")
    subparsers = parser.add_subparsers(dest="command", help="子命令")

    # auto-generate
    p_auto = subparsers.add_parser("auto-generate", help="端到端“一键成片”导演模式（从主题、文件或 URL 全自动出片）")
    p_auto.add_argument("project", help="工程名称或目录路径")
    p_auto.add_argument("--topic", "-t", default=None, help="技术主题或内容描述")
    p_auto.add_argument("--file", "-f", default=None, help="本地 Markdown / 源码 / 技术文章路径")
    p_auto.add_argument("--url", "-u", default=None, help="技术博文或文档的 Web URL")
    p_auto.add_argument("--no-build", action="store_true", help="仅生成 storyboard.yaml 剧本，不执行渲染")
    p_auto.add_argument("--clean", "-c", action="store_true", help="渲染前清理旧缓存")
    p_auto.add_argument("--provider", default=None, help="指定大模型服务商 (deepseek, openai, gemini, offline)")
    p_auto.add_argument("--model", default=None, help="指定大模型型号 (如 deepseek-chat, gpt-4o)")
    p_auto.add_argument("--api-key", default=None, help="显式指定 API Key")
    p_auto.add_argument("--story-profile", choices=["auto", "tutorial", "concept", "code_walkthrough", "decision"], default="auto", help="叙事结构：自动识别或指定教程/原理/源码/决策")
    p_auto.add_argument("--story-variant", choices=["auto", "evidence_first", "mechanism_first"], default="auto", help="稳定叙事变体：证据先行或机制先行")
    p_auto.add_argument("--allow-placeholders", action="store_true", help="允许制作期素材占位剧本进入预览构建")
    p_auto.add_argument("--allow-low-quality", action="store_true", help="允许质量分低于门槛，仅用于内部预览")

    # init
    p_init = subparsers.add_parser("init", help="初始化全新视频工程")
    p_init.add_argument("project", help="工程名称或目录路径")
    p_init.add_argument("--title", "-t", default=None, help="视频标题")
    p_init.add_argument("--force", "-f", action="store_true", help="强制覆盖已有剧本")

    # build
    p_build = subparsers.add_parser("build", help="按 storyboard.yaml 编译工程")
    p_build.add_argument("project", help="工程名称或目录路径")
    p_build.add_argument("--clean", "-c", action="store_true", help="构建前清空缓存")
    p_build.add_argument("--allow-placeholders", action="store_true", help="允许制作期素材占位，仅用于内部预览")
    p_build.add_argument("--allow-low-quality", action="store_true", help="允许质量分低于门槛，仅用于内部预览")

    # clean
    p_clean = subparsers.add_parser("clean", help="清空指定工程的中间构建缓存")
    p_clean.add_argument("project", help="工程名称或目录路径")

    # list
    subparsers.add_parser("list", help="查看所有工程状态")

    # status
    p_status = subparsers.add_parser("status", help="查看工程详情")
    p_status.add_argument("project", help="工程名称或目录路径")

    # validate
    p_validate = subparsers.add_parser("validate", help="渲染前检查剧本、素材与占位场景")
    p_validate.add_argument("project", help="工程名称或目录路径")
    p_validate.add_argument("--allow-placeholders", action="store_true", help="允许素材占位场景，仅用于制作期预览")
    p_validate.add_argument("--allow-low-quality", action="store_true", help="允许质量分低于门槛，仅用于内部预览")

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(0)

    if args.command == "auto-generate":
        cmd_auto_generate(args)
    elif args.command == "init":
        cmd_init(args)
    elif args.command == "build":
        cmd_build(args)
    elif args.command == "clean":
        cmd_clean(args)
    elif args.command == "list":
        cmd_list(args)
    elif args.command == "status":
        cmd_status(args)
    elif args.command == "validate":
        if not cmd_validate(args):
            sys.exit(1)

if __name__ == "__main__":
    main()
