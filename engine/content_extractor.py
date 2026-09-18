#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VideoAgent Content Extractor
从文件（Markdown/代码/纯文本）、网页 URL、或自然语言主题中提取结构化知识元数据。
"""

import os
import re
import urllib.request
import urllib.parse
from typing import Dict, Any, List

class ContentExtractor:
    """提取器：将外部输入转化为富文本结构供导演模型规划分镜"""

    @staticmethod
    def extract_from_file(file_path: str) -> Dict[str, Any]:
        """从本地文件中提取内容"""
        abs_path = os.path.abspath(os.path.expanduser(file_path))
        if not os.path.exists(abs_path):
            raise FileNotFoundError(f"文件不存在: {abs_path}")

        ext = os.path.splitext(abs_path)[1].lower()
        with open(abs_path, "r", encoding="utf-8", errors="ignore") as f:
            raw_text = f.read()

        title = os.path.basename(abs_path)
        headings = []
        code_snippets = []
        bullets = []

        if ext in [".md", ".markdown"]:
            # 提取 Markdown 标题
            h1_match = re.search(r"^#\s+(.+)$", raw_text, re.MULTILINE)
            if h1_match:
                title = h1_match.group(1).strip()
            for h in re.findall(r"^#{2,4}\s+(.+)$", raw_text, re.MULTILINE):
                headings.append(h.strip())

            # 提取代码块
            codes = re.findall(r"```([a-zA-Z0-9_\-\+]*)\n(.*?)```", raw_text, re.DOTALL)
            for lang, snippet in codes:
                snippet = snippet.strip()
                if snippet:
                    code_snippets.append({"lang": lang.strip() or "text", "code": snippet})

            # 提取列表要点
            for b in re.findall(r"^[*\-+]\s+(.+)$", raw_text, re.MULTILINE):
                cleaned = re.sub(r"\[(.*?)\]\(.*?\)", r"\1", b.strip())
                if len(cleaned) > 5 and len(cleaned) < 100:
                    bullets.append(cleaned)
        elif ext in [".py", ".c", ".cpp", ".rs", ".go", ".java", ".ts", ".js"]:
            # 代码文件直接作为代码块
            title = f"源码解析: {os.path.basename(abs_path)}"
            lang_map = {
                ".py": "python", ".c": "c", ".cpp": "cpp", ".rs": "rust",
                ".go": "go", ".java": "java", ".ts": "typescript", ".js": "javascript"
            }
            code_snippets.append({"lang": lang_map.get(ext, "text"), "code": raw_text[:2000]})
        else:
            # 纯文本文件提取首行或文件名
            lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
            if lines:
                title = lines[0][:40]

        return {
            "source_type": "file",
            "source_path": abs_path,
            "title": title,
            "raw_text": raw_text[:8000], # 避免过大
            "headings": headings[:10],
            "code_snippets": code_snippets[:5],
            "bullets": bullets[:15],
        }

    @staticmethod
    def extract_from_url(url: str) -> Dict[str, Any]:
        """从网页抓取并提取正文与代码"""
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }
        )
        with urllib.request.urlopen(req, timeout=12) as resp:
            html_content = resp.read().decode("utf-8", errors="ignore")

        # 提取标题
        title = url
        title_m = re.search(r"<title>(.*?)</title>", html_content, re.IGNORECASE | re.DOTALL)
        if title_m:
            title = re.sub(r"\s+", " ", title_m.group(1)).strip()
            title = title.split("-")[0].split("|")[0].split("_")[0].strip()

        # 去除 script/style/nav/header/footer 等噪声标签
        clean_html = re.sub(r"<(script|style|nav|header|footer|aside|noscript)[^>]*>.*?</\1>", " ", html_content, flags=re.IGNORECASE | re.DOTALL)

        # 提取 pre/code 代码块
        code_snippets = []
        for code_m in re.finditer(r"<pre[^>]*><code[^>]*>(.*?)</code></pre>", clean_html, re.IGNORECASE | re.DOTALL):
            code_text = re.sub(r"<[^>]+>", "", code_m.group(1)).strip()
            if code_text and len(code_text) > 20:
                code_snippets.append({"lang": "text", "code": code_text[:1200]})

        # 提取 h1, h2, h3 标题
        headings = []
        for h in re.findall(r"<h[1-4][^>]*>(.*?)</h[1-4]>", clean_html, re.IGNORECASE | re.DOTALL):
            h_text = re.sub(r"<[^>]+>", "", h).strip()
            if h_text and len(h_text) < 80:
                headings.append(h_text)

        # 提取主要段落
        paragraphs = []
        for p in re.findall(r"<p[^>]*>(.*?)</p>", clean_html, re.IGNORECASE | re.DOTALL):
            p_text = re.sub(r"<[^>]+>", "", p).strip()
            p_text = re.sub(r"\s+", " ", p_text)
            if len(p_text) > 30 and "cookie" not in p_text.lower():
                paragraphs.append(p_text)

        combined_text = "\n\n".join(paragraphs[:15])

        return {
            "source_type": "url",
            "source_url": url,
            "title": title or "网络技术精讲",
            "raw_text": combined_text[:8000],
            "headings": headings[:10],
            "code_snippets": code_snippets[:5],
            "bullets": [p[:80] for p in paragraphs[:10]],
        }

    @staticmethod
    def extract_from_topic(topic: str) -> Dict[str, Any]:
        """自然语言主题输入"""
        clean_topic = topic.strip()
        return {
            "source_type": "topic",
            "title": clean_topic,
            "raw_text": f"请针对主题【{clean_topic}】进行深度原理解析，包含背景痛点、核心架构对比、关键性能数据、代码演进与实机演练。",
            "headings": [
                f"{clean_topic} 核心背景与痛点",
                "架构对决与工作原理",
                "性能基准与压测跑分",
                "核心代码演进与 API 精解",
                "生产环境验证与总结"
            ],
            "code_snippets": [],
            "bullets": [
                f"深入剖析 {clean_topic} 的底层设计哲学",
                "从痛点到突破：横向机制深度对比",
                "实测压测数据与最佳生产实践"
            ],
        }

    @classmethod
    def extract(cls, source: str) -> Dict[str, Any]:
        """自动推断来源并提取"""
        source = source.strip()
        if source.startswith("http://") or source.startswith("https://"):
            return cls.extract_from_url(source)
        elif os.path.exists(os.path.expanduser(source)):
            return cls.extract_from_file(source)
        else:
            return cls.extract_from_topic(source)
