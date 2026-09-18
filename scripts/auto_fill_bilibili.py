#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Bilibili Upload Form Auto-Filler via cmux browser.
自动向 Bilibili 投稿编辑表单注入视频标题、简介、标签与分类。
"""

import sys
import subprocess
import json
import time

TITLE = "深入理解 Go 协程调度器与 GMP 模型核心原理"
TAGS = ["Go语言", "Golang", "并发编程", "后端开发", "GMP模型", "操作系统", "编程技术"]
DESC = """Sakura，欢迎来到绘梨衣的计算机小课堂！
本期我们硬核拆解 Go 语言高并发的核心基石——GMP 协程调度模型与底层架构：
• 0:00 黄金前3秒：传统线程模型 vs 协程突围
• 0:15 机制对抗：单线程轮询 vs 极速工作窃取 (Work Stealing)
• 0:30 极限压测跑分：百万并发长连接性能实测
• 0:45 源码演进与调度重构：用极简代码替代百行胶水逻辑
• 1:00 核心 API 与系统调用深度剖析

视频全程由 VideoAgent 自动化管线驱动代码渲染生成，感谢观看！喜欢的小伙伴欢迎一键三连～"""

def run_cmux_eval(surface: str, js_code: str) -> str:
    # 封装安全 JS
    cmd = ["cmux", "browser", "--surface", surface, "eval", js_code]
    res = subprocess.run(cmd, capture_output=True, text=True)
    return res.stdout.strip()

def fill_bilibili_form(surface: str):
    print(f"🔍 正在检测 B站投稿编辑表单 (surface: {surface})...")
    
    js_fill = f"""
    (function() {{
        let status = [];
        
        // 1. 标题
        let titleInput = document.querySelector('input[placeholder*="标题"]') || 
                         document.querySelector('.video-title input') ||
                         document.querySelector('input[maxlength="80"]');
        if (titleInput) {{
            titleInput.value = {json.dumps(TITLE)};
            titleInput.dispatchEvent(new Event('input', {{ bubbles: true }}));
            titleInput.dispatchEvent(new Event('change', {{ bubbles: true }}));
            status.push("标题已填写");
        }} else {{
            status.push("未找到标题输入框");
        }}

        // 2. 自制单选框
        let originalRadio = document.querySelector('input[value="1"]') || 
                            Array.from(document.querySelectorAll('span, label')).find(el => el.textContent.trim() === '自制');
        if (originalRadio) {{
            originalRadio.click();
            status.push("已勾选自制");
        }}

        // 3. 简介
        let descArea = document.querySelector('textarea[placeholder*="简介"]') || 
                       document.querySelector('.video-desc textarea') ||
                       document.querySelector('.ql-editor') ||
                       document.querySelector('div[contenteditable="true"]');
        if (descArea) {{
            if (descArea.tagName === 'TEXTAREA') {{
                descArea.value = {json.dumps(DESC)};
                descArea.dispatchEvent(new Event('input', {{ bubbles: true }}));
            }} else {{
                descArea.innerText = {json.dumps(DESC)};
                descArea.dispatchEvent(new Event('input', {{ bubbles: true }}));
            }}
            status.push("简介已填写");
        }} else {{
            status.push("未找到简介框");
        }}

        return JSON.stringify(status);
    }})();
    """
    out = run_cmux_eval(surface, js_fill)
    print("📋 填写执行结果:", out)

    # 4. 注入标签
    print("🏷️ 正在注入技术标签...")
    for tag in TAGS:
        js_tag = f"""
        (function() {{
            let tagInput = document.querySelector('input[placeholder*="标签"]') ||
                           document.querySelector('.tag-container input') ||
                           document.querySelector('.label-item-v2-container input');
            if (tagInput) {{
                tagInput.focus();
                tagInput.value = {json.dumps(tag)};
                tagInput.dispatchEvent(new Event('input', {{ bubbles: true }}));
                tagInput.dispatchEvent(new KeyboardEvent('keydown', {{ key: 'Enter', keyCode: 13, bubbles: true }}));
                tagInput.dispatchEvent(new KeyboardEvent('keyup', {{ key: 'Enter', keyCode: 13, bubbles: true }}));
                return "已添加标签: " + {json.dumps(tag)};
            }}
            return "未找到标签输入框";
        }})();
        """
        tag_out = run_cmux_eval(surface, js_tag)
        print("  •", tag_out)
        time.sleep(0.3)

if __name__ == "__main__":
    surf = sys.argv[1] if len(sys.argv) > 1 else "surface:24"
    fill_bilibili_form(surf)
